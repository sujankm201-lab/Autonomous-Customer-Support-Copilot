import logging
from ..adapters.chat_repo import (
    create_chat,
    get_chat_by_id,
    get_chat_by_ticket_id,
    list_chats_for_user,
    add_message_to_chat,
    delete_chat,
)

logger = logging.getLogger(__name__)


async def create_user_chat(db, user_id: str, ticket_id: str):
    """Create a new chat session for a ticket."""
    logger.info(f"Creating chat for user {user_id} on ticket {ticket_id}")
    chat_doc = {
        "user_id": user_id,
        "ticket_id": ticket_id,
    }
    return await create_chat(db, chat_doc)


async def fetch_chat(db, chat_id: str):
    """Fetch a chat by ID."""
    logger.debug(f"Fetching chat {chat_id}")
    return await get_chat_by_id(db, chat_id)


async def fetch_chat_by_ticket(db, ticket_id: str):
    """Fetch a chat by ticket ID."""
    logger.debug(f"Fetching chat for ticket {ticket_id}")
    return await get_chat_by_ticket_id(db, ticket_id)


async def list_user_chats(db, user_id: str):
    """List all chats for a user."""
    logger.info(f"Listing chats for user {user_id}")
    return await list_chats_for_user(db, user_id)


async def add_chat_message(db, chat_id: str, user_id: str, content: str, sender_type: str = "user"):
    """Add a message to a chat."""
    logger.info(f"Adding message to chat {chat_id} from {sender_type}")
    message = {
        "user_id": user_id,
        "content": content,
        "sender_type": sender_type,
    }
    return await add_message_to_chat(db, chat_id, message)


async def remove_chat(db, chat_id: str):
    """Delete a chat."""
    logger.info(f"Deleting chat {chat_id}")
    return await delete_chat(db, chat_id)
