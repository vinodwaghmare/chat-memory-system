"""Authentication dependencies for FastAPI.

Phase 0-9: extract user_id from X-User-ID header (simple).
Phase 10+: replace with JWT validation.
This enforces Invariant 1 at the API boundary.
"""

from __future__ import annotations

from fastapi import Header, HTTPException


async def get_current_user_id(
    x_user_id: str = Header(default=""),
) -> str:
    if not x_user_id:
        raise HTTPException(status_code=401, detail="X-User-ID header required")
    return x_user_id
