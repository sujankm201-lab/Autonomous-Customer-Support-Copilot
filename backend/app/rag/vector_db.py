"""ChromaDB vector database service for storing and retrieving embeddings."""
import logging
from typing import List, Optional, Dict
import chromadb
from chromadb.config import Settings as ChromaSettings

logger = logging.getLogger(__name__)


class VectorDatabaseService:
    """Service for managing vector embeddings in ChromaDB."""

    def __init__(
        self,
        collection_name: str = "support_docs",
        persist_directory: str = "./data/chroma_db",
    ):
        """
        Initialize VectorDatabaseService.
        
        Args:
            collection_name: Name of the ChromaDB collection
            persist_directory: Directory to persist ChromaDB
        """
        self.collection_name = collection_name
        self.persist_directory = persist_directory
        self.client = None
        self.collection = None
        self._initialize_database()

    def _initialize_database(self):
        """Initialize ChromaDB client and collection."""
        try:
            # Create ChromaDB settings with the current client API
            settings = ChromaSettings(
                persist_directory=self.persist_directory,
                anonymized_telemetry=False,
            )
            
            # Create client
            self.client = chromadb.Client(settings=settings)
            logger.info(f"ChromaDB client initialized at {self.persist_directory}")

            # Get or create collection
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"},
            )
            logger.info(f"Collection '{self.collection_name}' initialized")
        except Exception as e:
            logger.error(f"Error initializing ChromaDB: {str(e)}")
            raise

    def add_documents(
        self,
        chunks: List,
        embeddings: List,
        metadatas: Optional[List[Dict]] = None,
    ) -> int:
        """
        Add documents/chunks to the vector database.
        
        Args:
            chunks: List of text chunks
            embeddings: List of embeddings
            metadatas: Optional metadata dicts for each chunk
        
        Returns:
            Number of documents added
        """
        if len(chunks) != len(embeddings):
            raise ValueError("Number of chunks must match number of embeddings")

        try:
            # Generate IDs
            ids = [f"doc_{i}" for i in range(len(chunks))]

            # Prepare documents (chunk texts)
            documents = [chunk.text if hasattr(chunk, 'text') else chunk for chunk in chunks]

            # Prepare metadata
            if metadatas is None:
                metadatas = []
                for chunk in chunks:
                    if hasattr(chunk, 'metadata'):
                        metadatas.append(chunk.metadata)
                    else:
                        metadatas.append({})

            # Add to collection
            self.collection.add(
                ids=ids,
                embeddings=embeddings,
                documents=documents,
                metadatas=metadatas,
            )

            logger.info(f"Added {len(chunks)} documents to collection")
            return len(chunks)
        except Exception as e:
            logger.error(f"Error adding documents to ChromaDB: {str(e)}")
            raise

    def query(
        self,
        query_embedding: List,
        n_results: int = 5,
    ) -> Dict:
        """
        Query the vector database for similar documents.
        
        Args:
            query_embedding: Query embedding
            n_results: Number of results to return
        
        Returns:
            Dictionary with results and metadatas
        """
        try:
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
            )
            logger.debug(f"Query returned {len(results['documents'][0])} results")
            return results
        except Exception as e:
            logger.error(f"Error querying ChromaDB: {str(e)}")
            raise

    def update_document(self, doc_id: str, embedding: List, text: str, metadata: Dict = None):
        """
        Update a document in the vector database.
        
        Args:
            doc_id: Document ID
            embedding: New embedding
            text: New text
            metadata: New metadata
        """
        try:
            self.collection.update(
                ids=[doc_id],
                embeddings=[embedding],
                documents=[text],
                metadatas=[metadata] if metadata else None,
            )
            logger.info(f"Updated document {doc_id}")
        except Exception as e:
            logger.error(f"Error updating document in ChromaDB: {str(e)}")
            raise

    def delete_document(self, doc_id: str):
        """Delete a document from the vector database."""
        try:
            self.collection.delete(ids=[doc_id])
            logger.info(f"Deleted document {doc_id}")
        except Exception as e:
            logger.error(f"Error deleting document from ChromaDB: {str(e)}")
            raise

    def clear_collection(self):
        """Clear all documents from the collection."""
        try:
            # Delete all documents by getting IDs first
            all_docs = self.collection.get()
            if all_docs["ids"]:
                self.collection.delete(ids=all_docs["ids"])
            logger.info(f"Cleared collection '{self.collection_name}'")
        except Exception as e:
            logger.error(f"Error clearing collection: {str(e)}")
            raise

    def get_collection_stats(self) -> Dict:
        """Get statistics about the collection."""
        try:
            all_docs = self.collection.get()
            return {
                "collection_name": self.collection_name,
                "document_count": len(all_docs["ids"]),
                "ids": all_docs["ids"][:10],  # First 10 IDs
            }
        except Exception as e:
            logger.error(f"Error getting collection stats: {str(e)}")
            raise

    def persist(self):
        """Persist the database to disk."""
        try:
            self.client.persist()
            logger.info("Database persisted to disk")
        except Exception as e:
            logger.error(f"Error persisting database: {str(e)}")
            raise
