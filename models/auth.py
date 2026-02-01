import os
import jwt
from datetime import datetime, timedelta
from fastapi import HTTPException, Request


API_KEY = os.getenv("API_KEY", "default-secret-key")
SECRET_KEY = os.getenv("SECRET_KEY", "default-secret-key")
JWT_SECRET = os.getenv("JWT_SECRET", "jwt-secret-key-change-in-production")
TOKEN_EXPIRY_MINUTES = 60


def create_access_token(secret_key: str) -> str:
    """Validate secret key and return JWT token."""
    if secret_key != SECRET_KEY:
        raise HTTPException(status_code=401, detail="Invalid secret key")
    
    payload = {
        "secret_key": secret_key,
        "exp": datetime.utcnow() + timedelta(minutes=TOKEN_EXPIRY_MINUTES),
        "iat": datetime.utcnow(),
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm="HS256")
    return token


def verify_token(token: str) -> dict:
    """Verify and decode JWT token."""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        if payload.get("secret_key") != SECRET_KEY:
            raise HTTPException(status_code=403, detail="Token secret key mismatch")
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=403, detail="Invalid token")


async def verify_api_key(request: Request):
    """Verify API key from Authorization header."""
    if request.method == "GET":
        return

    path = request.url.path
    if path == "/" or path.startswith("/static") or path == "/token":
        return

    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")

    token = auth_header[7:]
    if token == API_KEY:
        return
    
    verify_token(token)

