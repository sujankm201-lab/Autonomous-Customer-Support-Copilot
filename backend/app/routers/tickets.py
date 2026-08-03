from fastapi import APIRouter, Depends, HTTPException, status
from ..schemas.ticket import TicketCreate, TicketOut
from ..services.ticket_service import create_user_ticket, fetch_ticket, list_user_tickets
from ..routers.users import get_current_user
from .. import db as db_module

router = APIRouter(prefix="/tickets", tags=["tickets"])


@router.post("/", response_model=TicketOut)
async def create_ticket_endpoint(payload: TicketCreate, current_user=Depends(get_current_user)):
    ticket = await create_user_ticket(db_module.db, current_user["_id"], payload)
    return ticket


@router.get("/{ticket_id}", response_model=TicketOut)
async def get_ticket(ticket_id: str, current_user=Depends(get_current_user)):
    ticket = await fetch_ticket(db_module.db, ticket_id)
    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")
    if ticket.get("user_id") != current_user["_id"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
    return ticket


@router.get("/", response_model=list[TicketOut])
async def list_tickets(current_user=Depends(get_current_user)):
    items = await list_user_tickets(db_module.db, current_user["_id"])
    return items
