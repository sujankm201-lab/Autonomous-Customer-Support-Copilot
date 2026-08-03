"""Configuration for RAG module."""
from pathlib import Path

# Paths
DATA_DIR = Path("data")
CHROMA_DB_DIR = DATA_DIR / "chroma_db"
DOCUMENTS_DIR = DATA_DIR / "documents"

# Chunking configuration
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200

# Embeddings configuration
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

# ChromaDB configuration
COLLECTION_NAME = "support_docs"
PERSIST_DIRECTORY = str(CHROMA_DB_DIR)

# LLM configuration
MODEL_NAME = "gpt-3.5-turbo"  # Can be changed to other models
TEMPERATURE = 0.7
MAX_TOKENS = 1000

# Retrieval configuration
TOP_K = 5  # Number of documents to retrieve
CONFIDENCE_THRESHOLD = 0.5

# Ensure directories exist
DATA_DIR.mkdir(exist_ok=True)
CHROMA_DB_DIR.mkdir(exist_ok=True)
DOCUMENTS_DIR.mkdir(exist_ok=True)
