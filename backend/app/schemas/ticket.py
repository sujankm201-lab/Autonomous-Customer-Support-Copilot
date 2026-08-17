from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class TicketCreate(BaseModel):
    title: str
    description: str
    attachments: Optional[List[str]] = []


class TicketOut(BaseModel):
    id: str = Field(alias="_id")
    title: str
    description: str
    status: str
    user_id: str
    created_at: datetime

    # Smart Ticket Routing fields
    intent: str
    confidence: float
    department: str