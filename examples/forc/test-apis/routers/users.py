"""Users router - /users/* endpoints."""

from data import USERS
from dependencies import ApiKeyHeader, BearerToken
from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status
from models import AvatarUploadResponse, UserCreate, UserResponse

router = APIRouter()

# Track next user ID for creation
_next_user_id = len(USERS) + 1


@router.get("", response_model=list[UserResponse])
async def get_all_users(api_key: ApiKeyHeader):
    """Get all users (requires API key in header)."""
    return USERS


@router.get("/{user_id}", response_model=UserResponse)
async def get_user_by_id(user_id: int, token: BearerToken):
    """Get user by ID (requires Bearer token)."""
    for user in USERS:
        if user["id"] == user_id:
            return user
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User {user_id} not found")


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(user: UserCreate):
    """Create a new user (JSON body, no auth)."""
    global _next_user_id
    new_user = {
        "id": _next_user_id,
        "name": user.name,
        "username": user.username,
        "email": user.email,
        "avatar": None,
    }
    _next_user_id += 1
    USERS.append(new_user)
    return new_user


@router.post("/form", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user_form(
    name: str = Form(...),
    username: str = Form(...),
    email: str = Form(...),
):
    """Create a new user (form-urlencoded body, no auth)."""
    global _next_user_id
    new_user = {
        "id": _next_user_id,
        "name": name,
        "username": username,
        "email": email,
        "avatar": None,
    }
    _next_user_id += 1
    USERS.append(new_user)
    return new_user


@router.post("/{user_id}/avatar", response_model=AvatarUploadResponse)
async def upload_avatar(
    user_id: int,
    file: UploadFile = File(None),  # noqa: B008
    description: str = Form(None),
    tags: str = Form(None),
):
    """Upload user avatar (multipart form-data, no auth)."""
    # Check user exists
    user = None
    for u in USERS:
        if u["id"] == user_id:
            user = u
            break

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User {user_id} not found")

    # Parse tags
    tag_list = []
    if tags:
        tag_list = [t.strip() for t in tags.split(",")]

    filename = file.filename if file and file.filename else "no-file-uploaded"

    return AvatarUploadResponse(
        message="Avatar uploaded successfully",
        user_id=user_id,
        filename=filename,
        description=description,
        tags=tag_list,
    )
