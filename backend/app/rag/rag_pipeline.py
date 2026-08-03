"""Main RAG pipeline orchestrating all components."""
import logging
import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from .document_loader import DocumentLoader, Document
from .text_chunker import TextChunker, Chunk
from .embeddings import EmbeddingsService
from .vector_db import VectorDatabaseService
from .llm_service import LLMService
from .prompts import get_prompt

logger = logging.getLogger(__name__)


@dataclass
class RAGResult:
    """Result from RAG pipeline."""
    answer: str
    confidence_score: float
    source_documents: List[str]
    retrieved_context: str
    query: str
    model_used: str


class RAGPipeline:
    """Complete RAG pipeline for document-based question answering."""

    def __init__(
        self,
        collection_name: str = "support_docs",
        persist_directory: str = "./data/chroma_db",
        embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2",
        llm_model: str = "gpt-3.5-turbo",
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        top_k: int = 5,
        confidence_threshold: float = 0.5,
    ):
        """
        Initialize RAG Pipeline.
        
        Args:
            collection_name: ChromaDB collection name
            persist_directory: Directory for persisting ChromaDB
            embedding_model: Sentence transformer model name
            llm_model: LLM model name
            chunk_size: Size of text chunks
            chunk_overlap: Overlap between chunks
            top_k: Number of documents to retrieve
            confidence_threshold: Minimum confidence score threshold
        """
        self.collection_name = collection_name
        self.persist_directory = persist_directory
        self.embedding_model = embedding_model
        self.llm_model = llm_model
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.top_k = top_k
        self.confidence_threshold = confidence_threshold

        # Initialize components
        self.document_loader = DocumentLoader()
        self.text_chunker = TextChunker(chunk_size, chunk_overlap)
        self.embeddings = EmbeddingsService(embedding_model)
        self.vector_db = VectorDatabaseService(collection_name, persist_directory)
        self.llm = LLMService(llm_model)

        logger.info("RAG Pipeline initialized successfully")

    def index_documents(self, documents: List[Document]) -> int:
        """
        Index documents into the knowledge base.
        
        Args:
            documents: List of Document objects to index
        
        Returns:
            Number of chunks indexed
        """
        logger.info(f"Indexing {len(documents)} documents...")

        # Chunk documents
        chunks = self.text_chunker.chunk_documents(documents)
        logger.info(f"Created {len(chunks)} chunks from {len(documents)} documents")

        # Generate embeddings
        texts_to_embed = [chunk.text for chunk in chunks]
        embeddings = self.embeddings.embed_texts(texts_to_embed)
        logger.info(f"Generated {len(embeddings)} embeddings")

        # Add to vector database
        num_added = self.vector_db.add_documents(chunks, embeddings)
        self.vector_db.persist()

        logger.info(f"Indexed {num_added} chunks into knowledge base")
        return num_added

    def index_from_directory(self, directory_path: str) -> int:
        """
        Load documents from a directory and index them.
        
        Args:
            directory_path: Path to directory containing documents
        
        Returns:
            Number of chunks indexed
        """
        logger.info(f"Loading documents from {directory_path}...")
        documents = self.document_loader.load_directory(directory_path)
        
        if not documents:
            logger.warning(f"No documents found in {directory_path}")
            return 0

        return self.index_documents(documents)

    def query(self, query_text: str, return_source: bool = True) -> RAGResult:
        """
        Query the RAG pipeline and get an answer with confidence scoring.
        
        Args:
            query_text: User query
            return_source: Whether to include source documents
        
        Returns:
            RAGResult with answer and metadata
        """
        logger.info(f"Processing query: {query_text}")

        try:
            # Generate query embedding
            query_embedding = self.embeddings.embed_text(query_text)
            logger.debug("Query embedding generated")

            # Retrieve relevant documents
            results = self.vector_db.query(query_embedding, n_results=self.top_k)
            logger.info(f"Retrieved {len(results['documents'][0])} relevant documents")

            # Combine retrieved documents as context
            retrieved_docs = results['documents'][0]
            retrieved_context = "\n\n".join(retrieved_docs)

            # Generate answer using LLM
            qa_prompt = get_prompt("detailed_qa")
            answer = self.llm.generate_with_context(
                context=retrieved_context,
                query=query_text,
                prompt_template=qa_prompt.template
            )
            logger.info("Answer generated by LLM")

            # Calculate confidence score
            confidence_score = self._calculate_confidence(
                query_text, answer, retrieved_context
            )
            logger.info(f"Confidence score: {confidence_score}")

            # Prepare source documents
            source_docs = []
            if return_source and results['metadatas']:
                for metadata in results['metadatas'][0]:
                    if isinstance(metadata, dict) and 'source' in metadata:
                        source_docs.append(metadata['source'])

            # Create result
            result = RAGResult(
                answer=answer,
                confidence_score=confidence_score,
                source_documents=source_docs,
                retrieved_context=retrieved_context,
                query=query_text,
                model_used=self.llm_model,
            )

            logger.info("Query processing completed successfully")
            return result

        except Exception as e:
            logger.error(f"Error processing query: {str(e)}")
            raise

    def _calculate_confidence(
        self, query: str, answer: str, context: str
    ) -> float:
        """
        Calculate confidence score for the answer.
        
        Args:
            query: Original query
            answer: Generated answer
            context: Retrieved context
        
        Returns:
            Confidence score between 0 and 1
        """
        try:
            # Calculate based on multiple factors
            # 1. Context relevance (embedding similarity)
            query_emb = self.embeddings.embed_text(query)
            context_emb = self.embeddings.embed_text(context)
            relevance_score = self.embeddings.compute_similarity(query_emb, context_emb)

            # 2. Answer length (longer answers typically more confident)
            answer_length = len(answer.split())
            length_factor = min(answer_length / 50, 1.0)  # Normalize to 0-1

            # 3. Context coverage
            context_words = set(context.lower().split())
            query_words = set(query.lower().split())
            coverage = len(query_words & context_words) / max(len(query_words), 1)

            # Weighted average
            confidence = (
                relevance_score * 0.5 +
                length_factor * 0.2 +
                coverage * 0.3
            )

            # Clamp to [0, 1]
            return max(0, min(1, confidence))
        except Exception as e:
            logger.warning(f"Error calculating confidence: {str(e)}")
            return 0.5  # Return neutral confidence on error

    def clear_knowledge_base(self):
        """Clear the entire knowledge base."""
        try:
            self.vector_db.clear_collection()
            logger.info("Knowledge base cleared")
        except Exception as e:
            logger.error(f"Error clearing knowledge base: {str(e)}")
            raise

    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the knowledge base."""
        try:
            stats = self.vector_db.get_collection_stats()
            stats.update({
                "embedding_model": self.embedding_model,
                "llm_model": self.llm_model,
                "chunk_size": self.chunk_size,
                "chunk_overlap": self.chunk_overlap,
            })
            return stats
        except Exception as e:
            logger.error(f"Error getting stats: {str(e)}")
            raise

    def to_dict(self) -> Dict:
        """Convert result to dictionary."""
        # Helper function for results
        pass
