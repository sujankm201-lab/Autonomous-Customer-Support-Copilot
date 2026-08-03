"""Domain models for core business entities."""
from typing import Optional, List
from datetime import datetime


class User:
    """User domain model."""

    def __init__(
        self,
        id: str,
        email: str,
        full_name: Optional[str] = None,
        is_admin: bool = False,
        created_at: Optional[datetime] = None,
    ):
        self.id = id
        self.email = email
        self.full_name = full_name
        self.is_admin = is_admin
        self.created_at = created_at or datetime.utcnow()

    def __repr__(self):
        return f"<User {self.id}: {self.email}>"


class Ticket:
    """Ticket domain model."""

    def __init__(
        self,
        id: str,
        user_id: str,
        title: str,
        description: str,
        status: str = "open",
        attachments: Optional[List[str]] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
    ):
        self.id = id
        self.user_id = user_id
        self.title = title
        self.description = description
        self.status = status
        self.attachments = attachments or []
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at or datetime.utcnow()

    def __repr__(self):
        return f"<Ticket {self.id}: {self.title} ({self.status})>"


class Message:
    """Chat message domain model."""

    def __init__(
        self,
        id: str,
        chat_id: str,
        user_id: str,
        content: str,
        sender_type: str = "user",
        created_at: Optional[datetime] = None,
    ):
        self.id = id
        self.chat_id = chat_id
        self.user_id = user_id
        self.content = content
        self.sender_type = sender_type  # "user" or "assistant"
        self.created_at = created_at or datetime.utcnow()

    def __repr__(self):
        return f"<Message {self.id}: from {self.sender_type}>"


class Chat:
    """Chat session domain model."""

    def __init__(
        self,
        id: str,
        user_id: str,
        ticket_id: str,
        messages: Optional[List[Message]] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
    ):
        self.id = id
        self.user_id = user_id
        self.ticket_id = ticket_id
        self.messages = messages or []
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at or datetime.utcnow()

    def add_message(self, message: Message):
        """Add a message to the chat."""
        self.messages.append(message)
        self.updated_at = datetime.utcnow()

    def __repr__(self):
        return f"<Chat {self.id}: ticket {self.ticket_id} ({len(self.messages)} messages)>"
