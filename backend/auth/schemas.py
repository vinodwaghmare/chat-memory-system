from pydantic import BaseModel


class GoogleAuthRequest(BaseModel):
    id_token: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user_id: str
    email: str
    name: str | None = None
    picture: str | None = None


class RefreshRequest(BaseModel):
    refresh_token: str
