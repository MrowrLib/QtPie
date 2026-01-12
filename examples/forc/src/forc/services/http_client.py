"""HTTP client service for sending requests."""

import time

import httpx

from forc.domain.models import (
    ApiKeyAuth,
    BasicAuth,
    BearerAuth,
    BodyType,
    Request,
    Response,
)


class HttpClientService:
    """Service for sending HTTP requests."""

    def __init__(self, client: httpx.Client | None = None) -> None:
        """Initialize with optional custom client (for testing)."""
        self._client = client
        self._owns_client = client is None

    def _get_client(self) -> httpx.Client:
        """Get or create the HTTP client."""
        if self._client is None:
            self._client = httpx.Client()
        return self._client

    def close(self) -> None:
        """Close the client if we own it."""
        if self._owns_client and self._client is not None:
            self._client.close()
            self._client = None

    def send(self, request: Request, base_url: str = "") -> Response:
        """Send an HTTP request and return the response.

        Args:
            request: The request to send
            base_url: Optional base URL to prepend to request URL

        Returns:
            Response object with status, headers, body, timing
        """
        client = self._get_client()

        # Build URL
        url = request.url
        if base_url and not url.startswith(("http://", "https://")):
            url = base_url.rstrip("/") + "/" + url.lstrip("/")

        # Build headers
        headers: dict[str, str] = {}
        for kv in request.headers:
            if kv.enabled:
                headers[kv.key] = kv.value

        # Build query params
        params: dict[str, str] = {}
        for kv in request.query_params:
            if kv.enabled:
                params[kv.key] = kv.value

        # Build body
        content: str | bytes | None = None
        if request.body and request.body_type != BodyType.NONE:
            content = request.body
            # Set content-type if not already set
            if "Content-Type" not in headers and "content-type" not in headers:
                match request.body_type:
                    case BodyType.JSON:
                        headers["Content-Type"] = "application/json"
                    case BodyType.FORM:
                        headers["Content-Type"] = "application/x-www-form-urlencoded"
                    case BodyType.XML:
                        headers["Content-Type"] = "application/xml"
                    case BodyType.TEXT:
                        headers["Content-Type"] = "text/plain"

        # Handle auth
        auth: httpx.BasicAuth | None = None
        if request.auth is not None:
            if isinstance(request.auth, BasicAuth):
                auth = httpx.BasicAuth(request.auth.username, request.auth.password)
            elif isinstance(request.auth, BearerAuth):
                headers["Authorization"] = f"Bearer {request.auth.token}"
            elif isinstance(request.auth, ApiKeyAuth):
                if request.auth.location == "header":
                    headers[request.auth.key] = request.auth.value
                else:  # query
                    params[request.auth.key] = request.auth.value

        # Send request with timing
        start = time.perf_counter()
        httpx_response = client.request(
            method=request.method.value,
            url=url,
            headers=headers,
            params=params,
            content=content,
            auth=auth,
        )
        elapsed_ms = (time.perf_counter() - start) * 1000

        # Build response
        return Response(
            status_code=httpx_response.status_code,
            status_text=httpx_response.reason_phrase,
            headers=dict(httpx_response.headers),
            body=httpx_response.content,
            time_ms=elapsed_ms,
            size_bytes=len(httpx_response.content),
        )
