"""Comprehensive unit tests for RAG module."""

import pytest
import tempfile
import shutil
from pathlib import Path

from app.rag.document_loader import DocumentLoader, Document
from app.rag.text_chunker import TextChunker, Chunk
from app.rag.embeddings import EmbeddingsService
from app.rag.vector_db import VectorDatabaseService
from app.rag.llm_service import LLMService
from app.rag.prompts import get_prompt, AVAILABLE_PROMPTS
from app.rag.rag_pipeline import RAGPipeline
from app.rag.knowledge_base_manager import KnowledgeBaseManager


class TestDocumentLoader:
    """Tests for DocumentLoader."""

    def test_load_txt_file(self):
        """Test loading text file."""

        # Create temporary file
        with tempfile.NamedTemporaryFile(
            mode="w",
            suffix=".txt",
            delete=False,
            encoding="utf-8",
        ) as f:
            file_path = f.name
            f.write("This is a test document.")

        # File is now CLOSED before we try to delete it
        try:
            loader = DocumentLoader()
            content = loader.load_txt(file_path)

            assert content is not None
            assert "test document" in content

        finally:
            Path(file_path).unlink(missing_ok=True)

    def test_load_file_with_metadata(self):
        """Test loading file with metadata."""

        # Create temporary file
        with tempfile.NamedTemporaryFile(
            mode="w",
            suffix=".txt",
            delete=False,
            encoding="utf-8",
        ) as f:
            file_path = f.name
            f.write("Sample content for testing.")

        # File is closed before load/delete operations
        try:
            loader = DocumentLoader()
            doc = loader.load_file(file_path)

            assert doc is not None
            assert isinstance(doc, Document)
            assert doc.content == "Sample content for testing."

            assert "source" in doc.metadata
            assert doc.metadata["file_type"] == ".txt"
            assert doc.metadata["file_name"] == Path(file_path).name

        finally:
            Path(file_path).unlink(missing_ok=True)

    def test_load_directory(self):
        """Test loading multiple documents from directory."""

        with tempfile.TemporaryDirectory() as tmpdir:

            # Create test files
            file1 = Path(tmpdir) / "file1.txt"
            file2 = Path(tmpdir) / "file2.txt"

            file1.write_text(
                "Document 1",
                encoding="utf-8",
            )

            file2.write_text(
                "Document 2",
                encoding="utf-8",
            )

            loader = DocumentLoader()

            docs = loader.load_directory(
                tmpdir,
                file_types=[".txt"],
            )

            assert len(docs) == 2


class TestTextChunker:
    """Tests for TextChunker."""

    def test_chunk_text_basic(self):
        """Test basic text chunking."""

        chunker = TextChunker(
            chunk_size=50,
            chunk_overlap=10,
        )

        text = "This is a sample document. " * 10

        chunks = chunker.chunk_text(text)

        assert len(chunks) > 0
        assert all(
            isinstance(c, Chunk)
            for c in chunks
        )

        assert all(
            len(c.text) <= 60
            for c in chunks
        )

    def test_chunk_text_with_metadata(self):
        """Test chunking with metadata."""

        chunker = TextChunker(
            chunk_size=50,
            chunk_overlap=10,
        )

        text = "Sample text for chunking. " * 5

        metadata = {
            "source": "test.txt"
        }

        chunks = chunker.chunk_text(
            text,
            metadata,
        )

        assert len(chunks) > 0

        for chunk in chunks:
            assert "source" in chunk.metadata
            assert chunk.metadata["source"] == "test.txt"

    def test_chunk_by_sentences(self):
        """Test sentence-based chunking."""

        text = (
            "First sentence. "
            "Second sentence. "
            "Third sentence. "
            "Fourth sentence."
        )

        chunks = TextChunker.chunk_by_sentences(
            text,
            sentences_per_chunk=2,
        )

        assert len(chunks) == 2

        assert "First sentence" in chunks[0].text
        assert "Third sentence" in chunks[1].text


class TestEmbeddingsService:
    """Tests for EmbeddingsService."""

    @pytest.fixture
    def embeddings_service(self):
        """Create EmbeddingsService instance."""

        return EmbeddingsService()

    def test_embed_text(
        self,
        embeddings_service,
    ):
        """Test embedding a single text."""

        embedding = embeddings_service.embed_text(
            "This is a test sentence."
        )

        assert embedding is not None
        assert len(embedding) > 0

        assert (
            embeddings_service.get_embedding_dimension()
            == len(embedding)
        )

    def test_embed_texts_batch(
        self,
        embeddings_service,
    ):
        """Test embedding multiple texts."""

        texts = [
            "First test sentence.",
            "Second test sentence.",
            "Third test sentence.",
        ]

        embeddings = (
            embeddings_service.embed_texts(texts)
        )

        assert len(embeddings) == 3

        assert all(
            len(e)
            == embeddings_service.get_embedding_dimension()
            for e in embeddings
        )

    def test_compute_similarity(
        self,
        embeddings_service,
    ):
        """Test similarity computation."""

        text1 = "The cat sat on the mat."
        text2 = "The cat sat on a mat."
        text3 = "The dog barked loudly."

        emb1 = embeddings_service.embed_text(text1)
        emb2 = embeddings_service.embed_text(text2)
        emb3 = embeddings_service.embed_text(text3)

        sim_12 = (
            embeddings_service.compute_similarity(
                emb1,
                emb2,
            )
        )

        sim_13 = (
            embeddings_service.compute_similarity(
                emb1,
                emb3,
            )
        )

        assert 0 <= sim_12 <= 1
        assert 0 <= sim_13 <= 1

        # Similar texts should have higher similarity
        assert sim_12 > sim_13


class TestPrompts:
    """Tests for prompt templates."""

    def test_get_prompt_qa(self):
        """Test getting QA prompt."""

        prompt = get_prompt("qa")

        assert prompt is not None
        assert "context" in prompt.input_variables
        assert "question" in prompt.input_variables

    def test_get_all_prompts(self):
        """Test all available prompts."""

        assert len(AVAILABLE_PROMPTS) >= 5

        for name in AVAILABLE_PROMPTS:
            prompt = get_prompt(name)
            assert prompt is not None

    def test_invalid_prompt(self):
        """Test invalid prompt name."""

        with pytest.raises(ValueError):
            get_prompt("invalid_prompt_name")


class TestLLMService:
    """Tests for LLMService."""

    def test_llm_initialization(self):
        """Test LLM service initialization."""

        llm = LLMService(
            model="gpt-3.5-turbo"
        )

        assert llm.model == "gpt-3.5-turbo"
        assert llm.llm is not None

    def test_llm_generate(self):
        """Test LLM text generation."""

        llm = LLMService()

        response = llm.generate(
            "Complete this sentence: The answer is"
        )

        assert response is not None
        assert isinstance(response, str)
        assert len(response) > 0

    def test_token_counting(self):
        """Test approximate token counting."""

        llm = LLMService()

        text = (
            "This is a test sentence "
            "with several words."
        )

        token_count = llm.count_tokens(text)

        assert token_count > 0

        # Simple heuristic
        assert 5 <= token_count <= 15


class TestVectorDatabase:
    """Tests for VectorDatabaseService."""

    @pytest.fixture
    def temp_db(self):
        """Create temporary database directory."""

        tmpdir = tempfile.mkdtemp()

        try:
            yield tmpdir

        finally:
            # ChromaDB can keep files open briefly on Windows.
            # Ignore cleanup errors rather than failing the test.
            if Path(tmpdir).exists():
                try:
                    shutil.rmtree(
                        tmpdir,
                        ignore_errors=True,
                    )
                except Exception:
                    pass

    def test_vector_db_initialization(
        self,
        temp_db,
    ):
        """Test vector database initialization."""

        db = VectorDatabaseService(
            collection_name="test_collection",
            persist_directory=temp_db,
        )

        assert db.collection is not None
        assert (
            db.collection_name
            == "test_collection"
        )

    def test_add_and_query_documents(
        self,
        temp_db,
    ):
        """Test adding and querying documents."""

        db = VectorDatabaseService(
            collection_name="test",
            persist_directory=temp_db,
        )

        embeddings_service = EmbeddingsService()

        # Create sample chunks
        chunks = [
            Chunk(
                text="Machine learning is a subset of AI.",
                chunk_index=0,
                metadata={},
            ),
            Chunk(
                text="Deep learning uses neural networks.",
                chunk_index=1,
                metadata={},
            ),
        ]

        # Generate embeddings
        texts = [
            chunk.text
            for chunk in chunks
        ]

        embeddings = (
            embeddings_service.embed_texts(
                texts
            )
        )

        # Add documents
        num_added = db.add_documents(
            chunks,
            embeddings,
        )

        assert num_added == 2

        # Query
        query_embedding = (
            embeddings_service.embed_text(
                "What is AI?"
            )
        )

        results = db.query(
            query_embedding,
            n_results=2,
        )

        assert len(
            results["documents"][0]
        ) > 0


class TestRAGPipeline:
    """Tests for RAGPipeline."""

    @pytest.fixture
    def temp_rag(self):
        """Create temporary RAG pipeline."""

        tmpdir = tempfile.mkdtemp()

        rag = RAGPipeline(
            collection_name="test_rag",
            persist_directory=tmpdir,
        )

        try:
            yield rag

        finally:
            # Give ChromaDB cleanup a safe attempt.
            try:
                del rag
            except Exception:
                pass

            if Path(tmpdir).exists():
                shutil.rmtree(
                    tmpdir,
                    ignore_errors=True,
                )

    def test_rag_initialization(
        self,
        temp_rag,
    ):
        """Test RAG pipeline initialization."""

        assert temp_rag.embeddings is not None
        assert temp_rag.vector_db is not None
        assert temp_rag.llm is not None

    def test_rag_indexing(
        self,
        temp_rag,
    ):
        """Test document indexing."""

        documents = [
            Document(
                content=(
                    "Python is a programming language."
                ),
                metadata={
                    "source": "doc1.txt"
                },
            ),
            Document(
                content=(
                    "Machine learning is about "
                    "training models."
                ),
                metadata={
                    "source": "doc2.txt"
                },
            ),
        ]

        num_indexed = (
            temp_rag.index_documents(
                documents
            )
        )

        assert num_indexed > 0

    def test_rag_query(
        self,
        temp_rag,
    ):
        """Test RAG query."""

        # Index documents first
        documents = [
            Document(
                content=(
                    "Python is a versatile "
                    "programming language used "
                    "for web development, "
                    "data science, and "
                    "machine learning."
                ),
                metadata={
                    "source": "python.txt"
                },
            ),
        ]

        temp_rag.index_documents(
            documents
        )

        # Query
        result = temp_rag.query(
            "What is Python?"
        )

        assert result.answer is not None
        assert len(result.answer) > 0

        assert (
            0
            <= result.confidence_score
            <= 1
        )

        assert (
            result.model_used
            == "gpt-3.5-turbo"
        )

    def test_rag_confidence_scoring(
        self,
        temp_rag,
    ):
        """Test confidence scoring."""

        query = "What is AI?"

        answer = (
            "Artificial Intelligence is "
            "the simulation of human intelligence."
        )

        context = (
            "AI refers to the capability of "
            "a computer or machine to mimic "
            "cognitive functions."
        )

        confidence = (
            temp_rag._calculate_confidence(
                query,
                answer,
                context,
            )
        )

        assert 0 <= confidence <= 1


class TestKnowledgeBaseManager:
    """Tests for KnowledgeBaseManager."""

    @pytest.fixture
    def temp_kb(self):
        """Create temporary knowledge base."""

        tmpdir = tempfile.mkdtemp()

        rag = RAGPipeline(
            collection_name="test_kb",
            persist_directory=tmpdir,
        )

        kb = KnowledgeBaseManager(
            rag,
            tmpdir,
        )

        try:
            yield kb

        finally:
            try:
                del kb
                del rag
            except Exception:
                pass

            if Path(tmpdir).exists():
                shutil.rmtree(
                    tmpdir,
                    ignore_errors=True,
                )

    def test_kb_health_check(
        self,
        temp_kb,
    ):
        """Test knowledge base health check."""

        is_healthy = (
            temp_kb.health_check()
        )

        assert is_healthy

    def test_kb_stats(
        self,
        temp_kb,
    ):
        """Test getting knowledge base stats."""

        stats = (
            temp_kb.get_knowledge_base_stats()
        )

        assert "document_count" in stats
        assert "indexed_files" in stats
        assert "embedding_model" in stats


class TestRAGIdentitylization:
    """Integration tests for complete RAG workflow."""

    def test_end_to_end_rag_workflow(self):
        """Test complete end-to-end RAG workflow."""

        with tempfile.TemporaryDirectory() as tmpdir:

            # Initialize RAG pipeline
            rag = RAGPipeline(
                collection_name="integration_test",
                persist_directory=tmpdir,
            )

            # Create documents
            documents = [
                Document(
                    content=(
                        "FastAPI is a modern web "
                        "framework for building "
                        "APIs with Python."
                    ),
                    metadata={
                        "source": "fastapi.txt"
                    },
                ),
                Document(
                    content=(
                        "Django is a high-level "
                        "web framework for web "
                        "development."
                    ),
                    metadata={
                        "source": "django.txt"
                    },
                ),
            ]

            # Index documents
            num_indexed = (
                rag.index_documents(
                    documents
                )
            )

            assert num_indexed > 0

            # Query RAG
            result = rag.query(
                "What is FastAPI?"
            )

            assert result.answer is not None
            assert len(result.answer) > 0
            assert (
                result.confidence_score > 0
            )

            # Get statistics
            stats = rag.get_stats()

            assert (
                stats["document_count"] > 0
            )