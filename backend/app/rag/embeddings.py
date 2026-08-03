"""Embeddings service using Sentence Transformers with a fallback for restricted environments."""
import hashlib
import logging
from typing import List, Optional
import numpy as np

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except Exception as exc:
    SentenceTransformer = None  # type: ignore[assignment]
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    logging.getLogger(__name__).warning(
        "SentenceTransformers import failed: %s. Falling back to deterministic embeddings.",
        str(exc),
    )

logger = logging.getLogger(__name__)
DEFAULT_EMBEDDING_DIMENSION = 384


def _deterministic_embedding(text: str, dimension: int) -> np.ndarray:
    """Generate deterministic fallback embeddings using a hash-based vector."""
    digest = hashlib.sha256(text.encode("utf-8")).digest()
    values = np.frombuffer(digest, dtype=np.uint8).astype(np.float32)
    values = np.resize(values, dimension)
    return values / 255.0 - 0.5


class EmbeddingsService:
    """Service for generating embeddings using Sentence Transformers."""

    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        """
        Initialize EmbeddingsService.
        
        Args:
            model_name: HuggingFace model name for embeddings
        """
        self.model_name = model_name
        self.model: Optional[SentenceTransformer] = None
        self._load_model()

    def _load_model(self):
        """Load the embedding model or configure a fallback."""
        if not SENTENCE_TRANSFORMERS_AVAILABLE:
            logger.warning(
                "SentenceTransformers is unavailable. Using deterministic fallback embeddings."
            )
            self.embedding_dim = DEFAULT_EMBEDDING_DIMENSION
            return

        try:
            logger.info(f"Loading embeddings model: {self.model_name}")
            self.model = SentenceTransformer(self.model_name)
            self.embedding_dim = self.model.get_sentence_embedding_dimension()
            logger.info("Embeddings model loaded successfully")
        except Exception as e:
            logger.warning(
                "Failed to load SentenceTransformers model: %s. Using deterministic fallback embeddings.",
                str(e),
            )
            self.model = None
            self.embedding_dim = DEFAULT_EMBEDDING_DIMENSION

    def embed_text(self, text: str) -> np.ndarray:
        """
        Generate embedding for a single text.
        
        Args:
            text: Text to embed
        
        Returns:
            Embedding as numpy array
        """
        try:
            if self.model is not None:
                embedding = self.model.encode(text, convert_to_numpy=True)
            else:
                embedding = _deterministic_embedding(text, self.embedding_dim)
            return embedding
        except Exception as e:
            logger.error(f"Error generating embedding: {str(e)}")
            raise

    def embed_texts(self, texts: List[str], batch_size: int = 32) -> List[np.ndarray]:
        """
        Generate embeddings for multiple texts.
        
        Args:
            texts: List of texts to embed
            batch_size: Batch size for encoding
        
        Returns:
            List of embeddings as numpy arrays
        """
        try:
            if self.model is not None:
                embeddings = self.model.encode(
                    texts,
                    batch_size=batch_size,
                    convert_to_numpy=True,
                    show_progress_bar=False,
                )
                return list(embeddings)
            return [_deterministic_embedding(text, self.embedding_dim) for text in texts]
        except Exception as e:
            logger.error(f"Error generating embeddings batch: {str(e)}")
            raise

    def get_embedding_dimension(self) -> int:
        """Get the dimension of embeddings."""
        return self.embedding_dim

    def compute_similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """
        Compute cosine similarity between two embeddings.
        
        Args:
            embedding1: First embedding
            embedding2: Second embedding
        
        Returns:
            Similarity score (0-1)
        """
        # Normalize embeddings
        norm1 = np.linalg.norm(embedding1)
        norm2 = np.linalg.norm(embedding2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        similarity = np.dot(embedding1, embedding2) / (norm1 * norm2)
        return float(similarity)

    def compute_similarities(
        self, embedding: np.ndarray, embeddings_list: List[np.ndarray]
    ) -> List[float]:
        """
        Compute similarities between one embedding and a list of embeddings.
        
        Args:
            embedding: Query embedding
            embeddings_list: List of embeddings to compare
        
        Returns:
            List of similarity scores
        """
        similarities = []
        for emb in embeddings_list:
            sim = self.compute_similarity(embedding, emb)
            similarities.append(sim)
        return similarities
