import logging
from fastapi import APIRouter, Depends, HTTPException, status
from ..routers.users import get_current_user
from .. import db as db_module
from bson.objectid import ObjectId

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/admin", tags=["admin"])


async def verify_admin(current_user=Depends(get_current_user)):
    """Verify that the current user is an admin."""
    if not current_user.get("is_admin", False):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return current_user


@router.get("/users", dependencies=[Depends(verify_admin)])
async def list_all_users():
    """Get all users (admin only)."""
    logger.info("Admin requested list of all users")
    cursor = db_module.db.users.find({})
    users = []
    async for doc in cursor:
        doc["_id"] = str(doc["_id"])
        doc.pop("password", None)
        users.append(doc)
    return users


@router.get("/tickets", dependencies=[Depends(verify_admin)])
async def list_all_tickets():
    """Get all tickets (admin only)."""
    logger.info("Admin requested list of all tickets")
    cursor = db_module.db.tickets.find({}).sort("created_at", -1)
    tickets = []
    async for doc in cursor:
        doc["_id"] = str(doc["_id"])
        tickets.append(doc)
    return tickets


@router.get("/chats", dependencies=[Depends(verify_admin)])
async def list_all_chats():
    """Get all chats (admin only)."""
    logger.info("Admin requested list of all chats")
    cursor = db_module.db.chats.find({}).sort("updated_at", -1)
    chats = []
    async for doc in cursor:
        doc["_id"] = str(doc["_id"])
        chats.append(doc)
    return chats


@router.put("/users/{user_id}/admin", dependencies=[Depends(verify_admin)])
async def set_admin_status(user_id: str, is_admin: bool):
    """Set admin status for a user (admin only)."""
    logger.warning(f"Admin toggling admin status for user {user_id} to {is_admin}")
    try:
        oid = ObjectId(user_id)
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid user ID")
    
    result = await db_module.db.users.update_one({"_id": oid}, {"$set": {"is_admin": is_admin}})
    if result.matched_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    return {"message": f"User admin status updated to {is_admin}"}


@router.patch("/tickets/{ticket_id}/status", dependencies=[Depends(verify_admin)])
async def update_ticket_status(ticket_id: str, status_value: str):
    """Update ticket status (admin only)."""
    logger.warning(f"Admin updating ticket {ticket_id} status to {status_value}")
    
    valid_statuses = ["open", "in_progress", "resolved", "closed"]
    if status_value not in valid_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status. Must be one of: {valid_statuses}",
        )
    
    try:
        oid = ObjectId(ticket_id)
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid ticket ID")
    
    result = await db_module.db.tickets.update_one({"_id": oid}, {"$set": {"status": status_value}})
    if result.matched_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")
    
    return {"message": f"Ticket status updated to {status_value}"}


@router.delete("/users/{user_id}", dependencies=[Depends(verify_admin)])
async def delete_user(user_id: str):
    """Delete a user (admin only)."""
    logger.warning(f"Admin deleting user {user_id}")
    try:
        oid = ObjectId(user_id)
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid user ID")
    
    result = await db_module.db.users.delete_one({"_id": oid})
    if result.deleted_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    # Also delete associated tickets and chats
    await db_module.db.tickets.delete_many({"user_id": user_id})
    await db_module.db.chats.delete_many({"user_id": user_id})
    
    return {"message": "User and associated data deleted successfully"}


@router.get("/stats", dependencies=[Depends(verify_admin)])
async def get_stats():
    """Get statistics (admin only)."""
    logger.info("Admin requested statistics")
    users_count = await db_module.db.users.count_documents({})
    tickets_count = await db_module.db.tickets.count_documents({})
    chats_count = await db_module.db.chats.count_documents({})
    
    return {
        "total_users": users_count,
        "total_tickets": tickets_count,
        "total_chats": chats_count,
    }
