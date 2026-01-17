"""HTTP client service for sending requests."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

import httpx
from observant import ObservableList

from forc.domain.models import (
    ApiKeyAuth,
    ApiKeyLocation,
    BasicAuth,
    BearerAuth,
    BodyType,
    Cookie,
    Request,
    Response,
)

if TYPE_CHECKING:
    from forc.services.workspace import WorkspaceService


class HttpClientService:
    """Service for sending HTTP requests."""

    def __init__(
        self,
        workspace_service: WorkspaceService | None = None,
        client: httpx.Client | None = None,
    ) -> None:
        """Initialize with workspace service for variable resolution.

        Args:
            workspace_service: Service for resolving ${VAR} placeholders
            client: Optional httpx client (for testing)
        """
        self._workspace = workspace_service
        self._client = client
        self._owns_client = client is None
        self.cookies: ObservableList[Cookie] = ObservableList([])

    def _get_client(self) -> httpx.Client:
        """Get or create the HTTP client."""
        if self._client is None:
            self._client = httpx.Client()
        return self._client

    def _resolve(self, text: str) -> str:
        """Resolve ${VAR} placeholders using workspace service."""
        if self._workspace is None:
            raise RuntimeError(f"HttpClientService has no workspace_service - cannot resolve variables in: {text}")
        return self._workspace.resolve_variables(text)

    def close(self) -> None:
        """Close the client if we own it."""
        if self._owns_client and self._client is not None:
            self._client.close()
            self._client = None

    def clear_cookies(self) -> None:
        """Clear all cookies from the cookie jar."""
        self.cookies.clear()

    def add_cookie(self) -> Cookie:
        """Add an empty cookie to the cookie jar for UI editing."""
        cookie = Cookie(name="", value="")
        self.cookies.append(cookie)
        return cookie

    def _build_httpx_cookies(self) -> httpx.Cookies:
        """Convert our Cookie list to httpx.Cookies for requests."""
        jar = httpx.Cookies()
        for cookie in self.cookies:
            jar.set(cookie.name, cookie.value, domain=cookie.domain, path=cookie.path)
        return jar

    def _update_cookies_from_response(self, response_cookies: httpx.Cookies) -> None:
        """Update our cookie list from response cookies."""
        for cookie in response_cookies.jar:
            # Update existing or add new
            domain = cookie.domain or ""
            existing = next(
                (c for c in self.cookies if c.name == cookie.name and c.domain == domain),
                None,
            )
            new_cookie = Cookie(
                name=cookie.name,
                value=cookie.value or "",
                domain=cookie.domain or "",
                path=cookie.path or "",
                expires=cookie.expires,
                secure=cookie.secure,
                httponly=bool(cookie.get_nonstandard_attr("HttpOnly")),
                samesite=cookie.get_nonstandard_attr("SameSite") or "",
            )
            if existing:
                idx = self.cookies.index(existing)
                self.cookies[idx] = new_cookie
            else:
                self.cookies.append(new_cookie)

    def send(self, request: Request, base_url: str = "") -> Response:
        """Send an HTTP request and return the response.

        Args:
            request: The request to send
            base_url: Optional base URL to prepend to request URL

        Returns:
            Response object with status, headers, body, timing
        """
        client = self._get_client()

        # Build URL (resolve variables)
        url = self._resolve(request.url)
        if base_url and not url.startswith(("http://", "https://")):
            url = base_url.rstrip("/") + "/" + url.lstrip("/")

        # Build headers (resolve variables in values)
        headers: dict[str, str] = {}
        for kv in request.headers:
            if kv.enabled:
                headers[kv.key] = self._resolve(kv.value)

        # Build query params (resolve variables in values)
        params: dict[str, str] = {}
        for kv in request.query_params:
            if kv.enabled:
                params[kv.key] = self._resolve(kv.value)

        # Build body (resolve variables)
        content: str | bytes | None = None
        data: dict[str, str] | None = None  # For form data
        files: list[tuple[str, tuple[str, str]]] | None = None  # For multipart

        match request.body_type:
            case BodyType.NONE:
                pass
            case BodyType.JSON:
                content = self._resolve(request.body)
                if "Content-Type" not in headers and "content-type" not in headers:
                    headers["Content-Type"] = "application/json"
            case BodyType.XML:
                content = self._resolve(request.body)
                if "Content-Type" not in headers and "content-type" not in headers:
                    headers["Content-Type"] = "application/xml"
            case BodyType.TEXT:
                content = self._resolve(request.body)
                if "Content-Type" not in headers and "content-type" not in headers:
                    headers["Content-Type"] = "text/plain"
            case BodyType.FORM_URLENCODED:
                data = {kv.key: self._resolve(kv.value) for kv in request.body_fields if kv.enabled}
            case BodyType.FORM_DATA:
                # Multipart form data - use files param for proper multipart encoding
                files = [(kv.key, ("", self._resolve(kv.value))) for kv in request.body_fields if kv.enabled]

        # Handle auth (resolve variables in auth values)
        auth: httpx.BasicAuth | None = None
        if request.auth is not None:
            if isinstance(request.auth, BasicAuth):
                auth = httpx.BasicAuth(
                    self._resolve(request.auth.username),
                    self._resolve(request.auth.password),
                )
            elif isinstance(request.auth, BearerAuth):
                headers["Authorization"] = f"Bearer {self._resolve(request.auth.token)}"
            elif isinstance(request.auth, ApiKeyAuth):
                if request.auth.location == ApiKeyLocation.HEADER:
                    headers[request.auth.key] = self._resolve(request.auth.value)
                else:
                    params[request.auth.key] = self._resolve(request.auth.value)

        # Send request with timing (set cookies on client, not per-request)
        client.cookies = self._build_httpx_cookies()
        start = time.perf_counter()
        httpx_response = client.request(
            method=request.method.value,
            url=url,
            headers=headers,
            params=params,
            content=content,
            data=data,
            files=files,
            auth=auth,
        )
        elapsed_ms = (time.perf_counter() - start) * 1000

        # Update cookie jar with response cookies
        self._update_cookies_from_response(httpx_response.cookies)

        # Extract cookies from response
        cookies: list[Cookie] = []
        for cookie in httpx_response.cookies.jar:
            cookies.append(
                Cookie(
                    name=cookie.name,
                    value=cookie.value or "",
                    domain=cookie.domain or "",
                    path=cookie.path or "",
                    expires=cookie.expires,
                    secure=cookie.secure,
                    httponly=bool(cookie.get_nonstandard_attr("HttpOnly")),
                    samesite=cookie.get_nonstandard_attr("SameSite") or "",
                )
            )

        # Build response (lowercase header names for consistent case-insensitive access)
        return Response(
            status_code=httpx_response.status_code,
            status_text=httpx_response.reason_phrase,
            headers={k.lower(): v for k, v in httpx_response.headers.items()},
            body=httpx_response.content,
            time_ms=elapsed_ms,
            size_bytes=len(httpx_response.content),
            cookies=cookies,
        )
