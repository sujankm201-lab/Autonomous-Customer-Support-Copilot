from ..adapters.ticket_repo import create_ticket, get_ticket_by_id, list_tickets_for_user


async def create_user_ticket(db, user_id: str, ticket_in):
    ticket_doc = {
        "title": ticket_in.title,
        "description": ticket_in.description,
        "attachments": ticket_in.attachments or [],
        "user_id": user_id,
    }
    return await create_ticket(db, ticket_doc)


async def fetch_ticket(db, ticket_id: str):
    return await get_ticket_by_id(db, ticket_id)


async def list_user_tickets(db, user_id: str):
    return await list_tickets_for_user(db, user_id)
