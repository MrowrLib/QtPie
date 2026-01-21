"""Posts router - /posts/* endpoints."""

from data import COMMENTS, POSTS
from fastapi import APIRouter, HTTPException, status
from models import CommentResponse, PostResponse

router = APIRouter()


@router.get("", response_model=list[PostResponse])
async def get_all_posts():
    """Get all posts (no auth)."""
    return POSTS


@router.get("/{post_id}", response_model=PostResponse)
async def get_post_by_id(post_id: int):
    """Get post by ID (no auth)."""
    for post in POSTS:
        if post["id"] == post_id:
            return post
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Post {post_id} not found")


@router.get("/{post_id}/comments", response_model=list[CommentResponse])
async def get_post_comments(
    post_id: int,
    limit: int = 10,
    offset: int = 0,
):
    """Get comments for a post (paginated, no auth)."""
    # Check post exists
    post_exists = any(p["id"] == post_id for p in POSTS)
    if not post_exists:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Post {post_id} not found")

    # Filter comments for this post
    post_comments = [c for c in COMMENTS if c["postId"] == post_id]

    # Apply pagination
    return post_comments[offset : offset + limit]
