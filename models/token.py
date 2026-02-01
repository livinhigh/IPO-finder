from pydantic import BaseModel


class SecretKeyRequest(BaseModel):
    secret_key: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
