from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class MessageCreate(BaseModel):
    content: str
    ticket_id: str


class MessageOut(BaseModel):
    id: str = Field(alias="_id")
    ticket_id: str
    user_id: str
    content: str
    sender_type: str  # "user" or "assistant"
    created_at: datetime

    class Config:
        populate_by_name = True


class ChatOut(BaseModel):
    id: str = Field(alias="_id")
    ticket_id: str
    user_id: str
    messages: List[MessageOut] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        populate_by_name = True
