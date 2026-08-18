"""Main RAG pipeline orchestrating all components."""

import logging
from typing import Dict, List, Any
from dataclasses import dataclass, asdict

from .document_loader import DocumentLoader, Document
from .text_chunker import TextChunker
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
        self.collection_name = collection_name
        self.persist_directory = persist_directory
        self.embedding_model = embedding_model
        self.llm_model = llm_model
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.top_k = top_k
        self.confidence_threshold = confidence_threshold

        # ---------------------------------------------------------
        # Initialize components
        # ---------------------------------------------------------

        self.document_loader = DocumentLoader()

        self.text_chunker = TextChunker(
            chunk_size,
            chunk_overlap,
        )

        self.embeddings = EmbeddingsService(
            embedding_model
        )

        self.vector_db = VectorDatabaseService(
            collection_name,
            persist_directory,
        )

        self.llm = LLMService(
            llm_model
        )

        logger.info(
            "RAG Pipeline initialized successfully"
        )

    # =============================================================
    # INDEX DOCUMENTS
    # =============================================================

    def index_documents(
        self,
        documents: List[Document],
    ) -> int:
        """
        Index documents into the knowledge base.

        Returns:
            Number of chunks indexed.
        """

        if not documents:
            logger.warning(
                "No documents supplied for indexing."
            )
            return 0

        logger.info(
            "Indexing %d documents...",
            len(documents),
        )

        # ---------------------------------------------------------
        # Chunk documents
        # ---------------------------------------------------------

        chunks = self.text_chunker.chunk_documents(
            documents
        )

        logger.info(
            "Created %d chunks from %d documents",
            len(chunks),
            len(documents),
        )

        if not chunks:
            return 0

        # ---------------------------------------------------------
        # Generate embeddings
        # ---------------------------------------------------------

        texts_to_embed = [
            chunk.text
            for chunk in chunks
        ]

        embeddings = self.embeddings.embed_texts(
            texts_to_embed
        )

        logger.info(
            "Generated %d embeddings",
            len(embeddings),
        )

        # ---------------------------------------------------------
        # Add to vector database
        # ---------------------------------------------------------

        num_added = self.vector_db.add_documents(
            chunks,
            embeddings,
        )

        # Modern ChromaDB PersistentClient automatically persists.
        # Keep this compatibility call because vector_db.persist()
        # safely does nothing when explicit persistence is unnecessary.
        self.vector_db.persist()

        logger.info(
            "Indexed %d chunks into knowledge base",
            num_added,
        )

        return num_added

    # =============================================================
    # INDEX DIRECTORY
    # =============================================================

    def index_from_directory(
        self,
        directory_path: str,
    ) -> int:
        """
        Load documents from a directory and index them.
        """

        logger.info(
            "Loading documents from %s...",
            directory_path,
        )

        documents = (
            self.document_loader.load_directory(
                directory_path
            )
        )

        if not documents:
            logger.warning(
                "No documents found in %s",
                directory_path,
            )
            return 0

        return self.index_documents(
            documents
        )

    # =============================================================
    # QUERY
    # =============================================================

    def query(
        self,
        query_text: str,
        return_source: bool = True,
    ) -> RAGResult:
        """
        Query the RAG pipeline.
        """

        if not query_text or not query_text.strip():
            raise ValueError(
                "Query text cannot be empty."
            )

        logger.info(
            "Processing query: %s",
            query_text,
        )

        try:

            # -----------------------------------------------------
            # Generate query embedding
            # -----------------------------------------------------

            query_embedding = (
                self.embeddings.embed_text(
                    query_text
                )
            )

            # -----------------------------------------------------
            # Retrieve documents
            # -----------------------------------------------------

            results = self.vector_db.query(
                query_embedding,
                n_results=self.top_k,
            )

            retrieved_docs = (
                results.get(
                    "documents",
                    [[]],
                )[0]
            )

            logger.info(
                "Retrieved %d relevant documents",
                len(retrieved_docs),
            )

            # -----------------------------------------------------
            # Build context
            # -----------------------------------------------------

            retrieved_context = "\n\n".join(
                retrieved_docs
            )

            # -----------------------------------------------------
            # Generate answer
            # -----------------------------------------------------

            qa_prompt = get_prompt(
                "detailed_qa"
            )

            answer = self.llm.generate_with_context(
                context=retrieved_context,
                query=query_text,
                prompt_template=qa_prompt.template,
            )

            logger.info(
                "Answer generated by LLM"
            )

            # -----------------------------------------------------
            # Confidence score
            # -----------------------------------------------------

            confidence_score = (
                self._calculate_confidence(
                    query_text,
                    answer,
                    retrieved_context,
                )
            )

            # -----------------------------------------------------
            # Source documents
            # -----------------------------------------------------

            source_docs: List[str] = []

            if return_source:

                metadatas = results.get(
                    "metadatas",
                    [[]],
                )

                if metadatas:

                    for metadata in metadatas[0]:

                        if (
                            isinstance(metadata, dict)
                            and "source" in metadata
                        ):
                            source_docs.append(
                                str(
                                    metadata["source"]
                                )
                            )

            # Remove duplicate sources while
            # preserving order.
            source_docs = list(
                dict.fromkeys(source_docs)
            )

            # -----------------------------------------------------
            # Create result
            # -----------------------------------------------------

            result = RAGResult(
                answer=answer,
                confidence_score=confidence_score,
                source_documents=source_docs,
                retrieved_context=retrieved_context,
                query=query_text,
                model_used=self.llm_model,
            )

            logger.info(
                "Query processing completed successfully"
            )

            return result

        except Exception as e:

            logger.exception(
                "Error processing query: %s",
                e,
            )

            raise

    # =============================================================
    # CONFIDENCE
    # =============================================================

    def _calculate_confidence(
        self,
        query: str,
        answer: str,
        context: str,
    ) -> float:
        """
        Calculate confidence score between 0 and 1.
        """

        try:

            if not context.strip():
                return 0.0

            # -----------------------------------------------------
            # Context relevance
            # -----------------------------------------------------

            query_emb = (
                self.embeddings.embed_text(
                    query
                )
            )

            context_emb = (
                self.embeddings.embed_text(
                    context
                )
            )

            relevance_score = (
                self.embeddings.compute_similarity(
                    query_emb,
                    context_emb,
                )
            )

            # -----------------------------------------------------
            # Answer length
            # -----------------------------------------------------

            answer_length = len(
                answer.split()
            )

            length_factor = min(
                answer_length / 50,
                1.0,
            )

            # -----------------------------------------------------
            # Query/context word coverage
            # -----------------------------------------------------

            context_words = set(
                context.lower().split()
            )

            query_words = set(
                query.lower().split()
            )

            coverage = (
                len(
                    query_words
                    & context_words
                )
                / max(
                    len(query_words),
                    1,
                )
            )

            # -----------------------------------------------------
            # Weighted score
            # -----------------------------------------------------

            confidence = (
                relevance_score * 0.5
                + length_factor * 0.2
                + coverage * 0.3
            )

            return max(
                0.0,
                min(
                    1.0,
                    float(confidence),
                ),
            )

        except Exception as e:

            logger.warning(
                "Error calculating confidence: %s",
                e,
            )

            return 0.5

    # =============================================================
    # CLEAR KNOWLEDGE BASE
    # =============================================================

    def clear_knowledge_base(
        self,
    ) -> None:
        """
        Clear the entire knowledge base.
        """

        try:

            self.vector_db.clear_collection()

            logger.info(
                "Knowledge base cleared"
            )

        except Exception as e:

            logger.exception(
                "Error clearing knowledge base: %s",
                e,
            )

            raise

    # =============================================================
    # GET STATS
    # =============================================================

    def get_stats(
        self,
    ) -> Dict[str, Any]:
        """
        Get statistics about the knowledge base.
        """

        try:

            stats = (
                self.vector_db.get_collection_stats()
            )

            stats.update(
                {
                    "embedding_model": self.embedding_model,
                    "llm_model": self.llm_model,
                    "chunk_size": self.chunk_size,
                    "chunk_overlap": self.chunk_overlap,
                    "top_k": self.top_k,
                    "confidence_threshold": (
                        self.confidence_threshold
                    ),
                }
            )

            return stats

        except Exception as e:

            logger.exception(
                "Error getting stats: %s",
                e,
            )

            raise

    # =============================================================
    # TO DICT
    # =============================================================

    @staticmethod
    def to_dict(
        result: RAGResult,
    ) -> Dict[str, Any]:
        """
        Convert RAGResult to dictionary.
        """

        return asdict(result)

    # =============================================================
    # CLOSE
    # =============================================================

    def close(self) -> None:
        """
        Close vector database resources.
        """

        try:
            self.vector_db.close()
        except Exception as e:
            logger.debug(
                "RAG pipeline close note: %s",
                e,
            )