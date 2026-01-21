"""Authentication dependencies for FastAPI."""

import base64
import secrets
from typing import Annotated

from data import VALID_API_KEY, VALID_API_KEY_PUBLIC, VALID_BEARER_TOKEN, VALID_PASSWORD, VALID_USERNAME
from fastapi import Cookie, Depends, Header, HTTPException, Query, status


def verify_api_key_header(x_api_key: Annotated[str | None, Header()] = None) -> str:
    """Verify API key from header."""
    if not x_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing X-API-Key header",
        )
    if not secrets.compare_digest(x_api_key, VALID_API_KEY):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API key",
        )
    return x_api_key


def verify_api_key_query(api_key: Annotated[str | None, Query()] = None) -> str:
    """Verify API key from query parameter."""
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing api_key query parameter",
        )
    if not secrets.compare_digest(api_key, VALID_API_KEY_PUBLIC):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API key",
        )
    return api_key


def verify_basic_auth(authorization: Annotated[str | None, Header()] = None) -> tuple[str, str]:
    """Verify Basic authentication."""
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header",
            headers={"WWW-Authenticate": "Basic"},
        )

    if not authorization.startswith("Basic "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization scheme",
            headers={"WWW-Authenticate": "Basic"},
        )

    try:
        encoded = authorization[6:]  # Remove "Basic "
        decoded = base64.b64decode(encoded).decode("utf-8")
        username, password = decoded.split(":", 1)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials format",
            headers={"WWW-Authenticate": "Basic"},
        ) from None

    if not (secrets.compare_digest(username, VALID_USERNAME) and secrets.compare_digest(password, VALID_PASSWORD)):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Basic"},
        )

    return username, password


def verify_bearer_token(authorization: Annotated[str | None, Header()] = None) -> str:
    """Verify Bearer token authentication."""
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization scheme",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = authorization[7:]  # Remove "Bearer "

    if not secrets.compare_digest(token, VALID_BEARER_TOKEN):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return token


def verify_session_cookie(session: Annotated[str | None, Cookie()] = None) -> str:
    """Verify session cookie (set by login endpoint)."""
    if not session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing session cookie. Please login first.",
        )
    # In a real app, we'd verify the session token
    return session


# Type aliases for cleaner dependency injection
ApiKeyHeader = Annotated[str, Depends(verify_api_key_header)]
ApiKeyQuery = Annotated[str, Depends(verify_api_key_query)]
BasicAuth = Annotated[tuple[str, str], Depends(verify_basic_auth)]
BearerToken = Annotated[str, Depends(verify_bearer_token)]
SessionCookie = Annotated[str, Depends(verify_session_cookie)]
