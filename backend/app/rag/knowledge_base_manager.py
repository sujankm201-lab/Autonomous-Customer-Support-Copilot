"""Automatic knowledge base indexing service."""

import logging
from typing import Optional

from .rag_pipeline import RAGPipeline
from .document_loader import DocumentLoader


logger = logging.getLogger(__name__)


class KnowledgeBaseManager:
    """
    Manages automatic indexing and updates
    of the knowledge base.
    """

    def __init__(
        self,
        rag_pipeline: RAGPipeline,
        watch_directory: Optional[str] = None,
    ):
        self.rag_pipeline = rag_pipeline
        self.watch_directory = watch_directory
        self.indexed_files = set()
        self.document_loader = DocumentLoader()

        logger.info(
            "KnowledgeBaseManager initialized"
        )

    # =============================================================
    # INITIALIZE
    # =============================================================

    def initialize_knowledge_base(
        self,
        documents_directory: str,
    ) -> int:
        """
        Initialize knowledge base with documents.
        """

        logger.info(
            "Initializing knowledge base from %s",
            documents_directory,
        )

        documents = (
            self.document_loader.load_directory(
                documents_directory
            )
        )

        if not documents:

            logger.warning(
                "No documents found in %s",
                documents_directory,
            )

            return 0

        num_indexed = (
            self.rag_pipeline.index_documents(
                documents
            )
        )

        for doc in documents:

            if (
                hasattr(doc, "metadata")
                and isinstance(doc.metadata, dict)
                and "source" in doc.metadata
            ):

                self.indexed_files.add(
                    doc.metadata["source"]
                )

        logger.info(
            "Knowledge base initialization complete. "
            "Indexed %d chunks from %d documents",
            num_indexed,
            len(documents),
        )

        return num_indexed

    # =============================================================
    # ADD DOCUMENTS
    # =============================================================

    def add_documents(
        self,
        documents_directory: str,
    ) -> int:
        """
        Add documents to the knowledge base.
        """

        logger.info(
            "Adding documents from %s",
            documents_directory,
        )

        documents = (
            self.document_loader.load_directory(
                documents_directory
            )
        )

        if not documents:

            logger.info(
                "No documents found in %s",
                documents_directory,
            )

            return 0

        num_indexed = (
            self.rag_pipeline.index_documents(
                documents
            )
        )

        for doc in documents:

            if (
                hasattr(doc, "metadata")
                and isinstance(doc.metadata, dict)
                and "source" in doc.metadata
            ):

                self.indexed_files.add(
                    doc.metadata["source"]
                )

        logger.info(
            "Added %d new chunks to knowledge base",
            num_indexed,
        )

        return num_indexed

    # =============================================================
    # REINDEX
    # =============================================================

    def reindex_all(
        self,
        documents_directory: str,
    ) -> int:
        """
        Clear existing knowledge base and
        reindex all documents.
        """

        logger.info(
            "Reindexing all documents from %s",
            documents_directory,
        )

        self.rag_pipeline.clear_knowledge_base()

        self.indexed_files.clear()

        return self.initialize_knowledge_base(
            documents_directory
        )

    # =============================================================
    # STATS
    # =============================================================

    def get_knowledge_base_stats(
        self,
    ) -> dict:
        """
        Get knowledge base statistics.
        """

        stats = (
            self.rag_pipeline.get_stats()
        )

        stats["indexed_files"] = len(
            self.indexed_files
        )

        return stats

    # =============================================================
    # HEALTH CHECK
    # =============================================================

    def health_check(self) -> bool:
        """
        Check whether knowledge base is healthy.
        """

        try:

            stats = (
                self.get_knowledge_base_stats()
            )

            logger.info(
                "Knowledge base health check: "
                "%s documents",
                stats.get(
                    "document_count",
                    0,
                ),
            )

            return True

        except Exception as e:

            logger.error(
                "Knowledge base health check failed: %s",
                e,
            )

            return False

    # =============================================================
    # CLOSE
    # =============================================================

    def close(self) -> None:
        """
        Close resources used by the knowledge base.
        """

        try:

            self.rag_pipeline.close()

        except Exception as e:

            logger.debug(
                "Knowledge base close note: %s",
                e,
            )