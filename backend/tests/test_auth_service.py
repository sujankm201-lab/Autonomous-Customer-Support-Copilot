import pytest

from app.services import auth_service


@pytest.mark.asyncio
async def test_register_user_success(monkeypatch):
    class DummyUserIn:
        email = "test@example.com"
        password = "secret"
        full_name = "Tester"

    async def fake_get_user_by_email(db, email):
        return None

    async def fake_create_user(db, user_doc):
        user_doc["_id"] = "123"
        return user_doc

    monkeypatch.setattr(auth_service, "get_user_by_email", fake_get_user_by_email)
    monkeypatch.setattr(auth_service, "create_user", fake_create_user)
    # also avoid hashing complexity
    monkeypatch.setattr(auth_service, "hash_password", lambda p: "hashed")

    user = await auth_service.register_user(None, DummyUserIn)
    assert user["email"] == "test@example.com"
    assert user["password"] == "hashed"


@pytest.mark.asyncio
async def test_authenticate_user_success(monkeypatch):
    async def fake_get_user_by_email(db, email):
        return {"_id": "123", "email": email, "password": "hashed"}

    monkeypatch.setattr(auth_service, "get_user_by_email", fake_get_user_by_email)
    monkeypatch.setattr(auth_service, "verify_password", lambda a, b: True)
    monkeypatch.setattr(auth_service, "create_access_token", lambda subject: "token123")

    auth = await auth_service.authenticate_user(None, "test@example.com", "secret")
    assert auth is not None
    assert auth["access_token"] == "token123"
