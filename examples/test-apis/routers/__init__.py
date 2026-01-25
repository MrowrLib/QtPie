from .auth import router as auth_router
from .content_types import router as content_types_router
from .demo import router as demo_router
from .posts import router as posts_router
from .users import router as users_router

__all__ = [
    "auth_router",
    "content_types_router",
    "demo_router",
    "posts_router",
    "users_router",
]
