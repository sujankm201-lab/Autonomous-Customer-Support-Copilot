"""RAG API routes."""
import logging
from fastapi import APIRouter, File, UploadFile, HTTPException, status, Depends
from pydantic import BaseModel
from typing import Optional, List
from ..rag.rag_pipeline import RAGPipeline
from ..routers.users import get_current_user

logger = logging.getLogger(__name__)

# Lazily initialize RAG pipeline to avoid heavy imports at module import time
_rag_pipeline = None


def get_rag_pipeline():
    global _rag_pipeline
    if _rag_pipeline is None:
        _rag_pipeline = RAGPipeline(
            collection_name="support_docs",
            persist_directory="./data/chroma_db",
        )
    return _rag_pipeline

router = APIRouter(prefix="/rag", tags=["rag"])


class QueryRequest(BaseModel):
    """RAG query request."""
    query: str


class QueryResponse(BaseModel):
    """RAG query response."""
    answer: str
    confidence_score: float
    source_documents: List[str]
    query: str


@router.post("/query", response_model=QueryResponse)
async def query_knowledge_base(
    request: QueryRequest,
    current_user=Depends(get_current_user),
):
    """Query the knowledge base."""
    logger.info(f"User {current_user['_id']} queried: {request.query}")
    
    try:
        result = get_rag_pipeline().query(request.query)
        return QueryResponse(
            answer=result.answer,
            confidence_score=result.confidence_score,
            source_documents=result.source_documents,
            query=result.query,
        )
    except Exception as e:
        logger.exception("Error querying RAG")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error processing query"
        )


@router.get("/stats")
async def get_rag_stats(current_user: dict = Depends(get_current_user)):
    """Get RAG system statistics."""
    try:
        stats = get_rag_pipeline().get_stats()
        return stats
    except Exception as e:
        logger.exception("Error getting RAG stats")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving statistics"
        )


@router.post("/index")
async def index_documents(
    directory: str = "./data/documents",
    current_user: dict = Depends(get_current_user),
):
    """Index documents from a directory."""
    # Check admin permission
    if not current_user.get("is_admin", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    try:
        logger.info(f"Indexing documents from {directory}")
        num_indexed = get_rag_pipeline().index_from_directory(directory)
        return {"message": f"Indexed {num_indexed} chunks", "chunks_indexed": num_indexed}
    except Exception as e:
        logger.exception("Error indexing documents")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.delete("/clear")
async def clear_knowledge_base(current_user: dict = Depends(get_current_user)):
    """Clear the knowledge base (admin only)."""
    # Check admin permission
    if not current_user.get("is_admin", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    try:
        logger.warning("Clearing knowledge base")
        get_rag_pipeline().clear_knowledge_base()
        return {"message": "Knowledge base cleared"}
    except Exception as e:
        logger.exception("Error clearing knowledge base")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error clearing knowledge base"
        )
