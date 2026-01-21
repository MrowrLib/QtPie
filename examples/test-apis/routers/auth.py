"""Auth router - /auth/* and /data/* endpoints."""

import uuid

from data import CURRENT_USER_PROFILE, PUBLIC_DATA, SECURE_DATA, VALID_BEARER_TOKEN
from dependencies import ApiKeyHeader, ApiKeyQuery, BasicAuth, BearerToken
from fastapi import APIRouter, Response

router = APIRouter(tags=["Auth"])


@router.get("/data/secure")
async def get_secure_data(api_key: ApiKeyHeader):
    """Get secure data (requires API key in header)."""
    return SECURE_DATA


@router.get("/data/public")
async def get_public_data(api_key: ApiKeyQuery):
    """Get public data (requires API key in query param)."""
    return PUBLIC_DATA


@router.post("/auth/login")
async def login(credentials: BasicAuth, response: Response):
    """Login with Basic Auth credentials."""
    username, _ = credentials

    # Set a session cookie
    session_id = str(uuid.uuid4())
    response.set_cookie(
        key="session",
        value=session_id,
        httponly=True,
        max_age=3600,  # 1 hour
        samesite="lax",
    )

    return {
        "message": "Login successful",
        "token": VALID_BEARER_TOKEN,
        "user": {
            "username": username,
            "role": "admin",
        },
    }


@router.get("/auth/profile")
async def get_profile(token: BearerToken):
    """Get user profile (requires Bearer token)."""
    return CURRENT_USER_PROFILE
