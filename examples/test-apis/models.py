"""Pydantic models for request/response validation."""

from pydantic import BaseModel


class UserCreate(BaseModel):
    """Request model for creating a user."""

    name: str
    username: str
    email: str


class UserResponse(BaseModel):
    """Response model for a user."""

    id: int
    name: str
    username: str
    email: str
    avatar: str | None = None


class PostResponse(BaseModel):
    """Response model for a post."""

    id: int
    userId: int
    title: str
    body: str


class CommentResponse(BaseModel):
    """Response model for a comment."""

    id: int
    postId: int
    name: str
    email: str
    body: str


class LoginResponse(BaseModel):
    """Response model for login."""

    message: str
    token: str
    user: dict[str, str | int]


class ProfileResponse(BaseModel):
    """Response model for user profile."""

    id: int
    name: str
    username: str
    email: str
    role: str
    created_at: str


class AvatarUploadResponse(BaseModel):
    """Response model for avatar upload."""

    message: str
    user_id: int
    filename: str
    description: str | None = None
    tags: list[str] = []


class ErrorResponse(BaseModel):
    """Response model for errors."""

    error: str
    message: str
    status_code: int


class EchoResponse(BaseModel):
    """Response model for echo endpoint."""

    method: str
    path: str
    headers: dict[str, str]
    cookies: dict[str, str]
    query_params: dict[str, str]
    body: str | None = None
