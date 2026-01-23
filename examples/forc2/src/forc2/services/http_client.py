"""HTTP client service for sending requests."""

import re
import time

import httpx

from ..domain import (
    ApiKeyAuth,
    ApiKeyLocation,
    BasicAuth,
    BearerAuth,
    BodyType,
    Cookie,
    Request,
    Response,
)
from ..domain.workspace import Workspace


class HttpClient:
    """Service for sending HTTP requests."""

    def __init__(
        self,
        workspace: Workspace | None = None,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        """Initialize with workspace for variable resolution.

        Args:
            workspace: Workspace for resolving ${VAR} placeholders
            client: Optional httpx async client (for testing)
        """
        self._workspace = workspace
        self._client = client
        self._owns_client = client is None
        self.cookies: list[Cookie] = []

    def _get_client(self) -> httpx.AsyncClient:
        """Get or create the HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient()
        return self._client

    def _resolve(self, text: str) -> str:
        """Resolve ${VAR} placeholders using workspace's active environment."""
        if self._workspace is None:
            return text

        env = self._workspace.active_environment()
        if env is None:
            return text

        def replace_var(match: re.Match[str]) -> str:
            var_name = match.group(1)
            variables = env.variables()
            if var_name in variables:
                env_var = variables[var_name]
                if env_var.enabled:
                    return env_var.value
            return match.group(0)  # Return original if not found

        return re.sub(r"\$\{(\w+)\}", replace_var, text)

    async def close(self) -> None:
        """Close the client if we own it."""
        if self._owns_client and self._client is not None:
            await self._client.aclose()
            self._client = None

    def clear_cookies(self) -> None:
        """Clear all cookies from the cookie jar."""
        self.cookies.clear()

    def _build_httpx_cookies(self) -> httpx.Cookies:
        """Convert our Cookie list to httpx.Cookies for requests."""
        jar = httpx.Cookies()
        for cookie in self.cookies:
            jar.set(cookie.name, cookie.value, domain=cookie.domain, path=cookie.path)
        return jar

    def _update_cookies_from_response(self, response_cookies: httpx.Cookies) -> None:
        """Update our cookie list from response cookies."""
        for cookie in response_cookies.jar:
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

    async def send(self, request: Request, base_url: str = "") -> Response:
        """Send an HTTP request and return the response.

        Args:
            request: The request to send
            base_url: Optional base URL to prepend to request URL

        Returns:
            Response object with status, headers, body, timing
        """
        client = self._get_client()

        # Build URL (resolve variables)
        url = self._resolve(request.url())
        if base_url and not url.startswith(("http://", "https://")):
            url = base_url.rstrip("/") + "/" + url.lstrip("/")

        # Build headers (resolve variables in values)
        headers: dict[str, str] = {}
        for h in request.headers():
            if h.enabled:
                headers[h.name] = self._resolve(h.value)

        # Build query params (resolve variables in values)
        params: dict[str, str] = {}
        for p in request.query_params():
            if p.enabled:
                params[p.name] = self._resolve(p.value)

        # Build body (resolve variables)
        content: str | bytes | None = None
        data: dict[str, str] | None = None  # For form data
        files: list[tuple[str, tuple[str, str]]] | None = None  # For multipart

        body_type = request.body_type()
        match body_type:
            case BodyType.NONE:
                pass
            case BodyType.JSON:
                content = self._resolve(request.body())
                if "Content-Type" not in headers and "content-type" not in headers:
                    headers["Content-Type"] = "application/json"
            case BodyType.XML:
                content = self._resolve(request.body())
                if "Content-Type" not in headers and "content-type" not in headers:
                    headers["Content-Type"] = "application/xml"
            case BodyType.TEXT:
                content = self._resolve(request.body())
                if "Content-Type" not in headers and "content-type" not in headers:
                    headers["Content-Type"] = "text/plain"
            case BodyType.FORM_URLENCODED:
                data = {h.name: self._resolve(h.value) for h in request.body_fields() if h.enabled}
            case BodyType.FORM_DATA:
                # Multipart form data
                files = [(h.name, ("", self._resolve(h.value))) for h in request.body_fields() if h.enabled]

        # Handle auth (resolve variables in auth values)
        auth: httpx.BasicAuth | None = None
        request_auth = request.auth()
        if request_auth is not None:
            if isinstance(request_auth, BasicAuth):
                auth = httpx.BasicAuth(
                    self._resolve(request_auth.username),
                    self._resolve(request_auth.password),
                )
            elif isinstance(request_auth, BearerAuth):
                headers["Authorization"] = f"Bearer {self._resolve(request_auth.token)}"
            elif isinstance(request_auth, ApiKeyAuth):
                if request_auth.location == ApiKeyLocation.HEADER:
                    headers[request_auth.name] = self._resolve(request_auth.value)
                else:
                    params[request_auth.name] = self._resolve(request_auth.value)

        # Send request with timing
        client.cookies = self._build_httpx_cookies()
        start = time.perf_counter()
        httpx_response = await client.request(
            method=request.method().value,
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
        response_cookies: list[Cookie] = []
        for cookie in httpx_response.cookies.jar:
            response_cookies.append(
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
            cookies=response_cookies,
        )
