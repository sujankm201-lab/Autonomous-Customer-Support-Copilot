from ..adapters.user_repo import get_user_by_email, create_user
from ..utils.hash import hash_password, verify_password
from ..utils.jwt import create_access_token


async def register_user(db, user_in):
    existing = await get_user_by_email(db, user_in.email)
    if existing:
        raise ValueError("Email already registered")
    user_doc = {"email": user_in.email, "password": hash_password(user_in.password), "full_name": user_in.full_name}
    user = await create_user(db, user_doc)
    return user


async def authenticate_user(db, email: str, password: str):
    user = await get_user_by_email(db, email)
    if not user:
        return None
    if not verify_password(password, user.get("password", "")):
        return None
    token = create_access_token(subject=user["_id"])
    return {"access_token": token, "token_type": "bearer", "user": user}
