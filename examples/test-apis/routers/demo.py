"""Demo router - extra demo endpoints for testing."""

import asyncio

from fastapi import APIRouter, Body, HTTPException, Query, Request, Response, status

router = APIRouter()


@router.api_route("/echo", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def echo(request: Request, body: str | None = Body(None)):
    """Echo back request details (any method)."""
    return {
        "method": request.method,
        "path": str(request.url.path),
        "headers": dict(request.headers),
        "cookies": dict(request.cookies),
        "query_params": dict(request.query_params),
        "body": body,
    }


@router.get("/slow")
async def slow_endpoint(delay: float = Query(default=2.0, ge=0, le=30)):
    """Slow endpoint with configurable delay (for testing loading states)."""
    await asyncio.sleep(delay)
    return {
        "message": f"Response after {delay} seconds",
        "delay_seconds": delay,
    }


@router.get("/large")
async def large_response(size: int = Query(default=100, ge=1, le=10000)):
    """Large response with configurable size (for testing size display)."""
    items = [{"id": i, "value": f"Item {i}", "data": "x" * 50} for i in range(size)]
    return {
        "count": size,
        "items": items,
    }


@router.get("/error/{code}")
async def error_endpoint(code: int):
    """Return specific HTTP error code (for testing error handling)."""
    error_messages = {
        400: "Bad Request - The request was malformed",
        401: "Unauthorized - Authentication required",
        403: "Forbidden - You don't have permission",
        404: "Not Found - Resource doesn't exist",
        422: "Unprocessable Entity - Validation failed",
        429: "Too Many Requests - Rate limit exceeded",
        500: "Internal Server Error - Something went wrong",
        502: "Bad Gateway - Upstream server error",
        503: "Service Unavailable - Try again later",
    }

    if code not in error_messages:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown error code: {code}. Supported: {list(error_messages.keys())}",
        )

    raise HTTPException(status_code=code, detail=error_messages[code])


@router.get("/cookies/set")
async def set_cookies(response: Response):
    """Set various cookies for testing."""
    response.set_cookie(key="simple", value="simple_value")
    response.set_cookie(key="secret", value="secret_value", httponly=True)
    response.set_cookie(key="protected", value="protected_value", secure=True)
    response.set_cookie(key="expiring", value="expiring_value", max_age=60)
    return {"message": "Cookies set", "cookies": ["simple", "secret", "protected", "expiring"]}


@router.get("/cookies/check")
async def check_cookies(request: Request):
    """Check what cookies were sent."""
    return {
        "received_cookies": dict(request.cookies),
        "count": len(request.cookies),
    }


@router.get("/headers")
async def custom_headers(response: Response):
    """Return response with various custom headers."""
    response.headers["X-Custom-Header"] = "custom-value"
    response.headers["X-Another-Header"] = "another-value"
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return {
        "message": "Response with custom headers",
        "custom_headers": [
            "X-Custom-Header",
            "X-Another-Header",
            "Cache-Control",
            "X-Content-Type-Options",
        ],
    }
