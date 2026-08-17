from ..adapters.ticket_repo import (
    create_ticket,
    get_ticket_by_id,
    list_tickets_for_user,
)
from .intent_service import intent_service


# Maps detected intent to the responsible department
DEPARTMENT_MAP = {
    "Billing": "Billing Team",
    "Technical": "Technical Support",
    "Account": "Account Support",
    "Refund": "Refunds Team",
    "General": "General Support",
}


async def create_user_ticket(db, user_id: str, ticket_in):
    # Combine title and description for better intent detection
    text = f"{ticket_in.title} {ticket_in.description}"

    # Detect intent using the existing intent detection service
    intent_result = intent_service.classify(text)

    intent = intent_result["intent"]
    confidence = intent_result["confidence"]

    # Find the department for the detected intent
    department = DEPARTMENT_MAP.get(intent, "General Support")

    # Create ticket document
    ticket_doc = {
        "title": ticket_in.title,
        "description": ticket_in.description,
        "attachments": ticket_in.attachments or [],
        "user_id": user_id,

        # Smart Ticket Routing fields
        "intent": intent,
        "confidence": confidence,
        "department": department,
    }

    return await create_ticket(db, ticket_doc)


async def fetch_ticket(db, ticket_id: str):
    return await get_ticket_by_id(db, ticket_id)


async def list_user_tickets(db, user_id: str):
    return await list_tickets_for_user(db, user_id)