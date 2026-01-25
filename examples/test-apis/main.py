"""Forc Test API Server - FastAPI app for testing the Forc REST client."""

import uuid
from collections.abc import Awaitable, Callable

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from routers import (
    auth_router,
    content_types_router,
    demo_router,
    posts_router,
    users_router,
)

RequestResponseEndpoint = Callable[[Request], Awaitable[Response]]

app = FastAPI(
    title="Forc Test API",
    description="Test API server for the Forc REST client",
    version="1.0.0",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_custom_headers(request: Request, call_next: RequestResponseEndpoint) -> Response:
    """Add custom headers to all responses."""
    response = await call_next(request)
    response.headers["X-Request-ID"] = str(uuid.uuid4())
    response.headers["X-RateLimit-Remaining"] = "99"
    response.headers["X-RateLimit-Limit"] = "100"
    return response


# Include routers
app.include_router(auth_router)
app.include_router(users_router, prefix="/users", tags=["Users"])
app.include_router(posts_router, prefix="/posts", tags=["Posts"])
app.include_router(demo_router, prefix="/demo", tags=["Demo"])
app.include_router(content_types_router, prefix="/content", tags=["Content Types"])


@app.get("/")
async def root():
    """Root endpoint - API info."""
    return {
        "name": "Forc Test API",
        "version": "1.0.0",
        "endpoints": {
            "auth": ["/auth/login", "/auth/profile"],
            "data": ["/data/secure", "/data/public"],
            "users": ["/users", "/users/{id}", "/users/{id}/avatar"],
            "posts": ["/posts", "/posts/{id}/comments"],
            "demo": ["/demo/echo", "/demo/slow", "/demo/large", "/demo/error/{code}"],
            "content": [
                "/content/html/simple",
                "/content/html/styled",
                "/content/xml/simple",
                "/content/json/detailed",
                "/content/text/plain",
                "/content/files",
                "/content/files/{filename}",
            ],
        },
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
