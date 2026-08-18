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

            with open(file_path, "rb") as file:
                pdf_reader = PyPDF2.PdfReader(file)

                for page in pdf_reader.pages:
                    page_text = page.extract_text()

                    if page_text:
                        text += page_text + "\n"

            logger.info("Successfully loaded PDF: %s", file_path)

            return text

        except ImportError:
            logger.warning(
                "PyPDF2 is not installed. "
                "Install it with: pip install PyPDF2"
            )
            return None

        except Exception as e:
            logger.error(
                "Error loading PDF %s: %s",
                file_path,
                e,
            )
            return None

    @staticmethod
    def load_txt(file_path: str) -> Optional[str]:
        """Load content from a text file."""

        try:
            # IMPORTANT:
            # Open and close the file completely before returning.
            # This prevents Windows file-locking problems.
            with open(
                file_path,
                "r",
                encoding="utf-8",
            ) as file:
                text = file.read()

            logger.info(
                "Successfully loaded TXT: %s",
                file_path,
            )

            return text

        except Exception as e:
            logger.error(
                "Error loading text file %s: %s",
                file_path,
                e,
            )
            return None

    @staticmethod
    def load_markdown(file_path: str) -> Optional[str]:
        """Load content from a Markdown file."""

        try:
            with open(
                file_path,
                "r",
                encoding="utf-8",
            ) as file:
                text = file.read()

            logger.info(
                "Successfully loaded Markdown: %s",
                file_path,
            )

            return text

        except Exception as e:
            logger.error(
                "Error loading Markdown file %s: %s",
                file_path,
                e,
            )
            return None

    @staticmethod
    def load_file(file_path: str) -> Optional[Document]:
        """
        Load a file and return a Document object.

        Automatically detects the file type.
        """

        path = Path(file_path)

        if not path.exists():
            logger.warning(
                "File not found: %s",
                file_path,
            )
            return None

        if not path.is_file():
            logger.warning(
                "Path is not a file: %s",
                file_path,
            )
            return None

        suffix = path.suffix.lower()

        content: Optional[str] = None

        if suffix == ".pdf":
            content = DocumentLoader.load_pdf(
                file_path
            )

        elif suffix == ".txt":
            content = DocumentLoader.load_txt(
                file_path
            )

        elif suffix in (
            ".md",
            ".markdown",
        ):
            content = DocumentLoader.load_markdown(
                file_path
            )

        else:
            logger.warning(
                "Unsupported file format: %s",
                suffix,
            )
            return None

        if content is None:
            return None

        metadata = {
            "source": str(file_path),
            "file_name": path.name,
            "file_type": suffix,
        }

        return Document(
            content=content,
            metadata=metadata,
        )

    @staticmethod
    def load_directory(
        directory_path: str,
        file_types: Optional[List[str]] = None,
    ) -> List[Document]:
        """
        Load all supported documents from a directory.

        Args:
            directory_path:
                Directory containing documents.

            file_types:
                File extensions to load.
                Example:
                ['.pdf', '.txt', '.md']

        Returns:
            List of Document objects.
        """

        if file_types is None:
            file_types = [
                ".pdf",
                ".txt",
                ".md",
                ".markdown",
            ]

        # Normalize extensions
        normalized_types = {
            extension.lower()
            if extension.startswith(".")
            else f".{extension.lower()}"
            for extension in file_types
        }

        documents: List[Document] = []

        directory = Path(directory_path)

        if not directory.exists():
            logger.warning(
                "Directory not found: %s",
                directory_path,
            )
            return documents

        if not directory.is_dir():
            logger.warning(
                "Path is not a directory: %s",
                directory_path,
            )
            return documents

        for file_path in directory.rglob("*"):

            if not file_path.is_file():
                continue

            if file_path.suffix.lower() not in normalized_types:
                continue

            try:
                document = DocumentLoader.load_file(
                    str(file_path)
                )

                if document is not None:
                    documents.append(document)

            except Exception as e:
                logger.error(
                    "Failed to load file %s: %s",
                    file_path,
                    e,
                )

        logger.info(
            "Loaded %d documents from %s",
            len(documents),
            directory_path,
        )

        return documents