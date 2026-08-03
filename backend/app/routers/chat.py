import logging
from fastapi import APIRouter, Depends, HTTPException, status
from ..schemas.chat import MessageCreate, ChatOut, MessageOut
from ..services.chat_service import (
    create_user_chat,
    fetch_chat,
    fetch_chat_by_ticket,
    list_user_chats,
    add_chat_message,
    remove_chat,
)
from ..routers.users import get_current_user
from .. import db as db_module

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/chats", tags=["chats"])


@router.post("/{ticket_id}", response_model=ChatOut)
async def create_chat_endpoint(ticket_id: str, current_user=Depends(get_current_user)):
    """Create a new chat session for a ticket."""
    logger.info(f"Creating chat for ticket {ticket_id}")
    chat = await create_user_chat(db_module.db, current_user["_id"], ticket_id)
    if not chat:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to create chat")
    return chat


@router.get("/{chat_id}", response_model=ChatOut)
async def get_chat_endpoint(chat_id: str, current_user=Depends(get_current_user)):
    """Get a specific chat by ID."""
    chat = await fetch_chat(db_module.db, chat_id)
    if not chat:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat not found")
    if chat.get("user_id") != current_user["_id"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
    return chat


@router.get("/", response_model=list[ChatOut])
async def list_chats_endpoint(current_user=Depends(get_current_user)):
    """Get all chats for the current user."""
    chats = await list_user_chats(db_module.db, current_user["_id"])
    return chats


@router.post("/{chat_id}/messages", response_model=ChatOut)
async def add_message_endpoint(chat_id: str, payload: MessageCreate, current_user=Depends(get_current_user)):
    """Add a message to a chat."""
    logger.info(f"Adding message to chat {chat_id}")
    chat = await fetch_chat(db_module.db, chat_id)
    if not chat:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat not found")
    if chat.get("user_id") != current_user["_id"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
    
    updated_chat = await add_chat_message(
        db_module.db, chat_id, current_user["_id"], payload.content, sender_type="user"
    )
    return updated_chat


@router.delete("/{chat_id}")
async def delete_chat_endpoint(chat_id: str, current_user=Depends(get_current_user)):
    """Delete a chat."""
    chat = await fetch_chat(db_module.db, chat_id)
    if not chat:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat not found")
    if chat.get("user_id") != current_user["_id"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
    
    success = await remove_chat(db_module.db, chat_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to delete chat")
    return {"message": "Chat deleted successfully"}
