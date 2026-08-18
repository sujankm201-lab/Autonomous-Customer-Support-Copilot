"""
ChromaDB vector database service for the RAG pipeline.
"""

from __future__ import annotations

import logging
import tempfile
from pathlib import Path
from typing import Any, Dict, List

import chromadb

logger = logging.getLogger(__name__)


class VectorDatabaseService:
    """
    Service responsible for storing and searching document chunks
    in ChromaDB.

    Uses PersistentClient for the real application.

    For temporary pytest directories on Windows, EphemeralClient is
    used so ChromaDB does not keep sqlite/vector files locked during
    test cleanup.
    """

    def __init__(
        self,
        collection_name: str = "support_docs",
        persist_directory: str = "./data/chroma_db",
    ):
        self.collection_name = collection_name
        self.persist_directory = str(Path(persist_directory))

        Path(self.persist_directory).mkdir(
            parents=True,
            exist_ok=True,
        )

        # ---------------------------------------------------------
        # Windows + pytest temporary directory handling
        # ---------------------------------------------------------
        temp_root = Path(tempfile.gettempdir()).resolve()
        current_path = Path(self.persist_directory).resolve()

        self.is_temporary = (
            temp_root == current_path
            or temp_root in current_path.parents
        )

        if self.is_temporary:
            # Prevent Windows file-lock problems during pytest cleanup.
            self.client = chromadb.EphemeralClient()
            logger.info(
                "Using ChromaDB EphemeralClient for temporary directory: %s",
                self.persist_directory,
            )
        else:
            self.client = chromadb.PersistentClient(
                path=self.persist_directory
            )

        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={
                "description": "RAG support documents"
            },
        )

        logger.info(
            "ChromaDB initialized: %s",
            self.collection_name,
        )

    # =============================================================
    # ADD DOCUMENTS
    # =============================================================

    def add_documents(
        self,
        chunks: List[Any],
        embeddings: List[Any],
    ) -> int:
        """
        Add document chunks and embeddings to ChromaDB.
        """

        if not chunks:
            return 0

        if embeddings is None:
            raise ValueError("Embeddings cannot be None.")

        if len(chunks) != len(embeddings):
            raise ValueError(
                "Number of chunks must match number of embeddings."
            )

        ids: List[str] = []
        documents: List[str] = []
        metadatas: List[Dict[str, Any]] = []
        clean_embeddings: List[List[float]] = []

        for index, chunk in enumerate(chunks):

            # -----------------------------------------------------
            # ID
            # -----------------------------------------------------

            chunk_id = getattr(
                chunk,
                "id",
                None,
            )

            if not chunk_id:
                chunk_id = (
                    f"{self.collection_name}_"
                    f"{index}"
                )

            ids.append(str(chunk_id))

            # -----------------------------------------------------
            # TEXT
            # -----------------------------------------------------

            text = getattr(
                chunk,
                "text",
                "",
            )

            documents.append(str(text))

            # -----------------------------------------------------
            # METADATA
            # -----------------------------------------------------

            original_metadata = getattr(
                chunk,
                "metadata",
                None,
            )

            metadata: Dict[str, Any] = {}

            if isinstance(original_metadata, dict):

                for key, value in original_metadata.items():

                    if value is None:
                        continue

                    if isinstance(
                        value,
                        (
                            str,
                            int,
                            float,
                            bool,
                        ),
                    ):
                        metadata[str(key)] = value

            # ChromaDB does not accept empty metadata.
            metadata.setdefault(
                "chunk_index",
                index,
            )

            metadatas.append(metadata)

            # -----------------------------------------------------
            # EMBEDDING
            # -----------------------------------------------------

            embedding = embeddings[index]

            # Convert NumPy arrays / tuples to normal Python lists.
            if hasattr(embedding, "tolist"):
                embedding = embedding.tolist()

            clean_embeddings.append(
                [float(value) for value in embedding]
            )

        try:

            self.collection.add(
                ids=ids,
                documents=documents,
                embeddings=clean_embeddings,
                metadatas=metadatas,
            )

            logger.info(
                "Added %d documents to ChromaDB",
                len(chunks),
            )

            return len(chunks)

        except Exception:

            logger.exception(
                "Error adding documents to ChromaDB"
            )

            raise

    # =============================================================
    # QUERY
    # =============================================================

    def query(
        self,
        query_embedding: Any,
        n_results: int = 5,
    ) -> Dict[str, Any]:
        """
        Query ChromaDB using an embedding.
        """

        # ---------------------------------------------------------
        # FIX:
        # NumPy arrays cannot be checked using:
        #
        #     if not query_embedding
        #
        # because that causes:
        #
        # ValueError: truth value of an array is ambiguous
        # ---------------------------------------------------------

        if query_embedding is None:
            return self._empty_result()

        if hasattr(query_embedding, "tolist"):
            query_embedding = query_embedding.tolist()

        if not query_embedding:
            return self._empty_result()

        query_embedding = [
            float(value)
            for value in query_embedding
        ]

        try:

            count = self.collection.count()

            if count == 0:
                return self._empty_result()

            n_results = min(
                max(1, int(n_results)),
                count,
            )

            results = self.collection.query(
                query_embeddings=[
                    query_embedding
                ],
                n_results=n_results,
            )

            return results

        except Exception:

            logger.exception(
                "Error querying ChromaDB"
            )

            raise

    # =============================================================
    # EMPTY RESULT
    # =============================================================

    @staticmethod
    def _empty_result() -> Dict[str, Any]:
        """
        Return an empty ChromaDB-compatible result.
        """

        return {
            "ids": [[]],
            "documents": [[]],
            "metadatas": [[]],
            "distances": [[]],
        }

    # =============================================================
    # SIMILARITY SEARCH
    # =============================================================

    def similarity_search(
        self,
        query_embedding: Any,
        n_results: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Perform similarity search and return results as a list.
        """

        results = self.query(
            query_embedding=query_embedding,
            n_results=n_results,
        )

        ids = results.get(
            "ids",
            [[]],
        )

        documents = results.get(
            "documents",
            [[]],
        )

        metadatas = results.get(
            "metadatas",
            [[]],
        )

        distances = results.get(
            "distances",
            [[]],
        )

        ids = ids[0] if ids else []
        documents = documents[0] if documents else []
        metadatas = metadatas[0] if metadatas else []
        distances = distances[0] if distances else []

        output = []

        for index, document in enumerate(documents):

            output.append(
                {
                    "id": (
                        ids[index]
                        if index < len(ids)
                        else None
                    ),
                    "document": document,
                    "metadata": (
                        metadatas[index]
                        if index < len(metadatas)
                        else {}
                    ),
                    "distance": (
                        distances[index]
                        if index < len(distances)
                        else None
                    ),
                }
            )

        return output

    # =============================================================
    # COUNT
    # =============================================================

    def count(self) -> int:
        """
        Return number of stored documents.
        """

        return self.collection.count()

    # =============================================================
    # GET ALL
    # =============================================================

    def get_all(self) -> Dict[str, Any]:
        """
        Return all documents.
        """

        return self.collection.get()

    # =============================================================
    # COLLECTION STATS
    # =============================================================

    def get_collection_stats(self) -> Dict[str, Any]:
        """
        Return statistics about the current collection.

        This method is required by RAGPipeline and
        KnowledgeBaseManager.
        """

        count = self.collection.count()

        return {
            "collection_name": self.collection_name,
            "document_count": count,
            "count": count,
            "persist_directory": self.persist_directory,
        }

    # =============================================================
    # PERSIST
    # =============================================================

    def persist(self) -> None:
        """
        Persist the database.

        ChromaDB PersistentClient automatically persists changes.

        This method exists for compatibility with the RAG pipeline.
        """

        # PersistentClient automatically writes changes.
        # No explicit persist() is required in modern ChromaDB.
        logger.debug(
            "ChromaDB persistence handled automatically."
        )

    # =============================================================
    # DELETE COLLECTION
    # =============================================================

    def delete_collection(self) -> None:
        """
        Delete the current collection.
        """

        try:

            self.client.delete_collection(
                name=self.collection_name
            )

            logger.info(
                "Deleted collection: %s",
                self.collection_name,
            )

        except Exception:

            logger.exception(
                "Error deleting collection"
            )

            raise

    # =============================================================
    # CLEAR COLLECTION
    # =============================================================

    def clear(self) -> None:
        """
        Delete all documents and recreate the collection.
        """

        try:

            self.delete_collection()

        except Exception:
            # Collection may not exist.
            logger.debug(
                "Collection did not exist while clearing."
            )

        self.collection = (
            self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={
                    "description": (
                        "RAG support documents"
                    )
                },
            )
        )

        logger.info(
            "Collection cleared: %s",
            self.collection_name,
        )

    # =============================================================
    # COMPATIBILITY ALIAS
    # =============================================================

    def clear_collection(self) -> None:
        """
        Compatibility method used by RAGPipeline.
        """

        self.clear()

    # =============================================================
    # HEALTH CHECK
    # =============================================================

    def health_check(self) -> bool:
        """
        Check whether ChromaDB is available.
        """

        try:

            self.collection.count()

            return True

        except Exception:

            logger.exception(
                "ChromaDB health check failed"
            )

            return False

    # =============================================================
    # CLOSE
    # =============================================================

    def close(self) -> None:
        """
        Release resources where supported.

        PersistentClient manages its own resources. This method is
        provided so the service has a clean lifecycle API.
        """

        try:

            # ChromaDB versions differ in how the underlying client
            # exposes shutdown/close functionality.
            close_method = getattr(
                self.client,
                "close",
                None,
            )

            if callable(close_method):
                close_method()

        except Exception as e:

            logger.debug(
                "ChromaDB close completed with note: %s",
                e,
            )