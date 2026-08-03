import pytest

from app.services import ticket_service


@pytest.mark.asyncio
async def test_create_user_ticket(monkeypatch):
    class DummyTicketIn:
        title = "Issue"
        description = "Details"
        attachments = []

    async def fake_create_ticket(db, ticket_doc):
        ticket_doc["_id"] = "t1"
        ticket_doc["created_at"] = "now"
        return ticket_doc

    monkeypatch.setattr(ticket_service, "create_ticket", fake_create_ticket)

    ticket = await ticket_service.create_user_ticket(None, "user1", DummyTicketIn)
    assert ticket["_id"] == "t1"
    assert ticket["user_id"] == "user1"


@pytest.mark.asyncio
async def test_list_user_tickets(monkeypatch):
    async def fake_list_tickets_for_user(db, user_id):
        return [{"_id": "t1", "user_id": user_id}]

    monkeypatch.setattr(ticket_service, "list_tickets_for_user", fake_list_tickets_for_user)

    items = await ticket_service.list_user_tickets(None, "user1")
    assert len(items) == 1
    assert items[0]["user_id"] == "user1"
