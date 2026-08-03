"""Automatic knowledge base indexing service."""
import logging
from typing import Optional
from pathlib import Path
from .rag_pipeline import RAGPipeline
from .document_loader import DocumentLoader

logger = logging.getLogger(__name__)


class KnowledgeBaseManager:
    """Manages automatic indexing and updates of the knowledge base."""

    def __init__(
        self,
        rag_pipeline: RAGPipeline,
        watch_directory: Optional[str] = None,
    ):
        """
        Initialize KnowledgeBaseManager.
        
        Args:
            rag_pipeline: RAGPipeline instance
            watch_directory: Optional directory to watch for new documents
        """
        self.rag_pipeline = rag_pipeline
        self.watch_directory = watch_directory
        self.indexed_files = set()
        self.document_loader = DocumentLoader()
        
        logger.info("KnowledgeBaseManager initialized")

    def initialize_knowledge_base(self, documents_directory: str) -> int:
        """
        Initialize knowledge base with documents from a directory.
        
        Args:
            documents_directory: Path to directory containing documents
        
        Returns:
            Number of chunks indexed
        """
        logger.info(f"Initializing knowledge base from {documents_directory}")
        
        # Load documents
        documents = self.document_loader.load_directory(documents_directory)
        
        if not documents:
            logger.warning(f"No documents found in {documents_directory}")
            return 0
        
        # Index documents
        num_indexed = self.rag_pipeline.index_documents(documents)
        
        # Track indexed files
        for doc in documents:
            if hasattr(doc, 'metadata') and 'source' in doc.metadata:
                self.indexed_files.add(doc.metadata['source'])
        
        logger.info(f"Knowledge base initialization complete. Indexed {num_indexed} chunks from {len(documents)} documents")
        return num_indexed

    def add_documents(self, documents_directory: str) -> int:
        """
        Add new documents to the knowledge base.
        
        Args:
            documents_directory: Path to directory containing new documents
        
        Returns:
            Number of new chunks indexed
        """
        logger.info(f"Adding documents from {documents_directory}")
        
        documents = self.document_loader.load_directory(documents_directory)
        
        if not documents:
            logger.info(f"No new documents found in {documents_directory}")
            return 0
        
        # Index new documents
        num_indexed = self.rag_pipeline.index_documents(documents)
        
        # Track indexed files
        for doc in documents:
            if hasattr(doc, 'metadata') and 'source' in doc.metadata:
                self.indexed_files.add(doc.metadata['source'])
        
        logger.info(f"Added {num_indexed} new chunks to knowledge base")
        return num_indexed

    def reindex_all(self, documents_directory: str) -> int:
        """
        Clear existing knowledge base and reindex all documents.
        
        Args:
            documents_directory: Path to directory containing documents
        
        Returns:
            Number of chunks indexed
        """
        logger.info(f"Reindexing all documents from {documents_directory}")
        
        # Clear existing knowledge base
        self.rag_pipeline.clear_knowledge_base()
        self.indexed_files.clear()
        
        # Reinitialize
        return self.initialize_knowledge_base(documents_directory)

    def get_knowledge_base_stats(self) -> dict:
        """
        Get statistics about the knowledge base.
        
        Returns:
            Dictionary with knowledge base statistics
        """
        stats = self.rag_pipeline.get_stats()
        stats['indexed_files'] = len(self.indexed_files)
        return stats

    def health_check(self) -> bool:
        """
        Check if knowledge base is healthy and accessible.
        
        Returns:
            True if healthy, False otherwise
        """
        try:
            stats = self.get_knowledge_base_stats()
            logger.info(f"Knowledge base health check: {stats['document_count']} documents")
            return True
        except Exception as e:
            logger.error(f"Knowledge base health check failed: {str(e)}")
            return False
