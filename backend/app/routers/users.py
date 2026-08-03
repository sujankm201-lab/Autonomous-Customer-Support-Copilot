from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from .. import db as db_module
from ..adapters.user_repo import get_user_by_id
from ..utils.jwt import decode_access_token
from ..schemas.user import UserOut

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")
router = APIRouter(prefix="/users", tags=["users"])


async def get_current_user(token: str = Depends(oauth2_scheme)):
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    user_id = payload.get("sub")
    user = await get_user_by_id(db_module.db, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    user.pop("password", None)
    return user


@router.get("/me", response_model=UserOut)
async def read_me(current_user=Depends(get_current_user)):
    return current_user
