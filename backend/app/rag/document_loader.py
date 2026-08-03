"""Document loader for RAG module supporting multiple file formats."""
import logging
from pathlib import Path
from typing import List, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class Document:
    """Document data class."""
    content: str
    metadata: dict


class DocumentLoader:
    """Handles loading documents from various formats."""

    @staticmethod
    def load_pdf(file_path: str) -> Optional[str]:
        """Load content from a PDF file."""
        try:
            import PyPDF2
            text = ""
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    text += page.extract_text()
            logger.info(f"Successfully loaded PDF: {file_path}")
            return text
        except ImportError:
            logger.warning("PyPDF2 not installed. Install it with: pip install PyPDF2")
            return None
        except Exception as e:
            logger.error(f"Error loading PDF {file_path}: {str(e)}")
            return None

    @staticmethod
    def load_txt(file_path: str) -> Optional[str]:
        """Load content from a text file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                text = file.read()
            logger.info(f"Successfully loaded TXT: {file_path}")
            return text
        except Exception as e:
            logger.error(f"Error loading text file {file_path}: {str(e)}")
            return None

    @staticmethod
    def load_markdown(file_path: str) -> Optional[str]:
        """Load content from a markdown file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                text = file.read()
            logger.info(f"Successfully loaded Markdown: {file_path}")
            return text
        except Exception as e:
            logger.error(f"Error loading markdown file {file_path}: {str(e)}")
            return None

    @staticmethod
    def load_file(file_path: str) -> Optional[Document]:
        """
        Load a file and return a Document object.
        Automatically detects file type.
        """
        path = Path(file_path)
        suffix = path.suffix.lower()

        content = None
        if suffix == '.pdf':
            content = DocumentLoader.load_pdf(file_path)
        elif suffix == '.txt':
            content = DocumentLoader.load_txt(file_path)
        elif suffix in ['.md', '.markdown']:
            content = DocumentLoader.load_markdown(file_path)
        else:
            logger.warning(f"Unsupported file format: {suffix}")
            return None

        if content is None:
            return None

        metadata = {
            "source": str(file_path),
            "file_name": path.name,
            "file_type": suffix,
        }

        return Document(content=content, metadata=metadata)

    @staticmethod
    def load_directory(directory_path: str, file_types: Optional[List[str]] = None) -> List[Document]:
        """
        Load all documents from a directory.
        
        Args:
            directory_path: Path to directory containing documents
            file_types: List of file extensions to load (e.g., ['.pdf', '.txt', '.md'])
        
        Returns:
            List of Document objects
        """
        if file_types is None:
            file_types = ['.pdf', '.txt', '.md', '.markdown']

        documents = []
        directory = Path(directory_path)

        if not directory.exists():
            logger.warning(f"Directory not found: {directory_path}")
            return documents

        for file_path in directory.rglob('*'):
            if file_path.is_file() and file_path.suffix.lower() in file_types:
                doc = DocumentLoader.load_file(str(file_path))
                if doc:
                    documents.append(doc)

        logger.info(f"Loaded {len(documents)} documents from {directory_path}")
        return documents
