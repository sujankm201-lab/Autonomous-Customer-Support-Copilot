"""ChromaDB vector database service for storing and retrieving embeddings."""

import logging
from typing import List, Optional, Dict
import chromadb

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
            # New ChromaDB API:
            # PersistentClient automatically saves data to disk
            self.client = chromadb.PersistentClient(
                path=self.persist_directory
            )

            logger.info(
                f"ChromaDB client initialized at {self.persist_directory}"
            )

            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"},
            )

            logger.info(
                f"Collection '{self.collection_name}' initialized"
            )

        except Exception as e:
            logger.exception("Error initializing ChromaDB")
            raise

    def add_documents(
        self,
        chunks: List,
        embeddings: List,
        metadatas: Optional[List[Dict]] = None,
    ) -> int:
        """
        Add documents/chunks to the vector database.
        """

        if len(chunks) != len(embeddings):
            raise ValueError(
                "Number of chunks must match number of embeddings"
            )

        try:
            ids = [
                f"doc_{i}"
                for i in range(len(chunks))
            ]

            documents = [
                chunk.text if hasattr(chunk, "text") else chunk
                for chunk in chunks
            ]

            if metadatas is None:
                metadatas = []

                for chunk in chunks:
                    if hasattr(chunk, "metadata"):
                        metadatas.append(chunk.metadata)
                    else:
                        metadatas.append({})

            self.collection.add(
                ids=ids,
                embeddings=embeddings,
                documents=documents,
                metadatas=metadatas,
            )

            logger.info(
                f"Added {len(chunks)} documents to collection"
            )

            return len(chunks)

        except Exception:
            logger.exception(
                "Error adding documents to ChromaDB"
            )
            raise

    def query(
        self,
        query_embedding: List,
        n_results: int = 5,
    ) -> Dict:
        """
        Query vector database.
        """

        try:
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
            )

            logger.debug(
                f"Query returned {len(results['documents'][0])} results"
            )

            return results

        except Exception:
            logger.exception(
                "Error querying ChromaDB"
            )
            raise

    def update_document(
        self,
        doc_id: str,
        embedding: List,
        text: str,
        metadata: Dict = None,
    ):
        """
        Update a document.
        """

        try:
            self.collection.update(
                ids=[doc_id],
                embeddings=[embedding],
                documents=[text],
                metadatas=[metadata] if metadata else None,
            )

            logger.info(
                f"Updated document {doc_id}"
            )

        except Exception:
            logger.exception(
                "Error updating document in ChromaDB"
            )
            raise

    def delete_document(self, doc_id: str):
        """
        Delete a document.
        """

        try:
            self.collection.delete(
                ids=[doc_id]
            )

            logger.info(
                f"Deleted document {doc_id}"
            )

        except Exception:
            logger.exception(
                "Error deleting document from ChromaDB"
            )
            raise

    def clear_collection(self):
        """
        Clear all documents from collection.
        """

        try:
            all_docs = self.collection.get()

            if all_docs["ids"]:
                self.collection.delete(
                    ids=all_docs["ids"]
                )

            logger.info(
                f"Cleared collection '{self.collection_name}'"
            )

        except Exception:
            logger.exception(
                "Error clearing collection"
            )
            raise

    def get_collection_stats(self) -> Dict:
        """
        Get collection statistics.
        """

        try:
            all_docs = self.collection.get()

            return {
                "collection_name": self.collection_name,
                "document_count": len(all_docs["ids"]),
                "ids": all_docs["ids"][:10],
            }

        except Exception:
            logger.exception(
                "Error getting collection stats"
            )
            raise

    def persist(self):
        """
        Compatibility method.

        ChromaDB PersistentClient automatically persists changes.
        No manual persist call is required.
        """

        logger.info(
            "ChromaDB persistence handled automatically"
        )