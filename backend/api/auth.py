from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token as google_id_token
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.auth.dependencies import get_current_user_id
from backend.auth.jwt import create_access_token, create_refresh_token, decode_token
from backend.auth.schemas import GoogleAuthRequest, RefreshRequest, TokenResponse
from backend.config.settings import get_settings
from backend.database.models import UserORM
from backend.database.postgres import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.post("/google", response_model=TokenResponse)
async def google_login(
    body: GoogleAuthRequest,
    session: AsyncSession = Depends(get_db),
) -> TokenResponse:
    cfg = get_settings()
    if not cfg.google_client_id:
        raise HTTPException(status_code=500, detail="Google OAuth not configured")

    try:
        idinfo = google_id_token.verify_oauth2_token(
            body.id_token,
            google_requests.Request(),
            cfg.google_client_id,
        )
    except ValueError as exc:
        logger.warning("Google token verification failed: %s", exc)
        raise HTTPException(status_code=401, detail="Invalid Google token")

    google_id = idinfo["sub"]
    email = idinfo.get("email", "")
    name = idinfo.get("name")
    picture = idinfo.get("picture")

    stmt = select(UserORM).where(UserORM.google_id == google_id)
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()

    if user:
        user.name = name
        user.picture = picture
        await session.commit()
    else:
        user = UserORM(
            email=email.lower().strip(),
            name=name,
            picture=picture,
            google_id=google_id,
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        logger.info("New user created: %s (%s)", email, user.id)

    user_id = str(user.id)
    return TokenResponse(
        access_token=create_access_token(user_id),
        refresh_token=create_refresh_token(user_id),
        user_id=user_id,
        email=user.email,
        name=user.name,
        picture=user.picture,
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    body: RefreshRequest,
    session: AsyncSession = Depends(get_db),
) -> TokenResponse:
    from jose import JWTError

    try:
        payload = decode_token(body.refresh_token)
        user_id = payload.get("sub")
        token_type = payload.get("type")
        if not user_id or token_type != "refresh":
            raise HTTPException(status_code=401, detail="Invalid refresh token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")

    import uuid as uuid_mod
    stmt = select(UserORM).where(UserORM.id == uuid_mod.UUID(user_id))
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or deactivated")

    return TokenResponse(
        access_token=create_access_token(user_id),
        refresh_token=create_refresh_token(user_id),
        user_id=user_id,
        email=user.email,
        name=user.name,
        picture=user.picture,
    )


@router.get("/me")
async def get_me(
    user_id: str = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db),
) -> dict:
    import uuid as uuid_mod
    stmt = select(UserORM).where(UserORM.id == uuid_mod.UUID(user_id))
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return {
        "user_id": str(user.id),
        "email": user.email,
        "name": user.name,
        "picture": user.picture,
    }
