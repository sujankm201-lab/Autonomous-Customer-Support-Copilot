from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import OAuth2PasswordRequestForm
from ..schemas.user import UserCreate, Token, UserOut
from ..services.auth_service import register_user, authenticate_user
from .. import db as db_module

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserOut)
async def register(payload: UserCreate):
    try:
        user = await register_user(db_module.db, payload)
        user.pop("password", None)
        return user
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    auth = await authenticate_user(
        db_module.db,
        form_data.username,
        form_data.password
    )
    if not auth:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    return {
        "access_token": auth["access_token"],
        "token_type": "bearer"
    }