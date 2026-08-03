"""Text chunking utilities for document preprocessing."""
import logging
from typing import List
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class Chunk:
    """Represents a text chunk."""
    text: str
    chunk_index: int
    metadata: dict


class TextChunker:
    """Handles text chunking with configurable size and overlap."""

    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        """
        Initialize TextChunker.
        
        Args:
            chunk_size: Number of characters per chunk
            chunk_overlap: Number of overlapping characters between chunks
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
        if chunk_overlap >= chunk_size:
            logger.warning("Chunk overlap should be less than chunk size")

    def chunk_text(self, text: str, metadata: dict = None) -> List[Chunk]:
        """
        Split text into chunks with overlap.
        
        Args:
            text: Text to chunk
            metadata: Additional metadata for chunks
        
        Returns:
            List of Chunk objects
        """
        if metadata is None:
            metadata = {}

        chunks = []
        start = 0
        chunk_index = 0

        while start < len(text):
            end = start + self.chunk_size
            chunk_text = text[start:end]
            
            # Avoid cutting in the middle of a word
            if end < len(text):
                last_space = chunk_text.rfind(' ')
                if last_space > self.chunk_size * 0.8:  # If word boundary is found
                    end = start + last_space
                    chunk_text = text[start:end]

            # Skip empty chunks
            if chunk_text.strip():
                chunk_metadata = metadata.copy()
                chunk_metadata.update({
                    "chunk_index": chunk_index,
                    "start_char": start,
                    "end_char": end,
                    "chunk_char_count": len(chunk_text),
                })
                
                chunks.append(Chunk(
                    text=chunk_text.strip(),
                    chunk_index=chunk_index,
                    metadata=chunk_metadata,
                ))
                chunk_index += 1

            # Move to next chunk with overlap
            start = end - self.chunk_overlap

        logger.debug(f"Created {len(chunks)} chunks from text")
        return chunks

    def chunk_documents(self, documents: List, metadata_key: str = "source") -> List[Chunk]:
        """
        Chunk multiple documents.
        
        Args:
            documents: List of Document objects with 'content' and optional 'metadata'
            metadata_key: Key to extract from document metadata
        
        Returns:
            List of Chunk objects from all documents
        """
        all_chunks = []

        for doc in documents:
            # Handle different document formats
            if hasattr(doc, 'content'):
                content = doc.content
                doc_metadata = getattr(doc, 'metadata', {})
            elif isinstance(doc, dict):
                content = doc.get('content', '')
                doc_metadata = doc.get('metadata', {})
            else:
                logger.warning(f"Unsupported document format: {type(doc)}")
                continue

            chunks = self.chunk_text(content, doc_metadata)
            all_chunks.extend(chunks)

        logger.info(f"Created {len(all_chunks)} total chunks from {len(documents)} documents")
        return all_chunks

    @staticmethod
    def chunk_by_sentences(text: str, sentences_per_chunk: int = 5, metadata: dict = None) -> List[Chunk]:
        """
        Chunk text by sentences instead of character count.
        
        Args:
            text: Text to chunk
            sentences_per_chunk: Number of sentences per chunk
            metadata: Additional metadata for chunks
        
        Returns:
            List of Chunk objects
        """
        if metadata is None:
            metadata = {}

        # Simple sentence splitting (can be improved with NLTK)
        sentences = text.replace('!', '.').replace('?', '.').split('.')
        sentences = [s.strip() for s in sentences if s.strip()]

        chunks = []
        chunk_index = 0

        for i in range(0, len(sentences), sentences_per_chunk):
            sentence_group = sentences[i:i + sentences_per_chunk]
            chunk_text = '. '.join(sentence_group) + '.'

            if chunk_text.strip():
                chunk_metadata = metadata.copy()
                chunk_metadata.update({
                    "chunk_index": chunk_index,
                    "sentence_count": len(sentence_group),
                })

                chunks.append(Chunk(
                    text=chunk_text.strip(),
                    chunk_index=chunk_index,
                    metadata=chunk_metadata,
                ))
                chunk_index += 1

        logger.debug(f"Created {len(chunks)} chunks by sentences")
        return chunks
