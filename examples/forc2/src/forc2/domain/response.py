"""Response - HTTP response snapshot (runtime only, not persisted)."""

from dataclasses import dataclass, field


@dataclass
class Cookie:
    """A single HTTP cookie from a response."""

    name: str
    value: str
    domain: str = ""
    path: str = ""
    expires: int | None = None  # Unix timestamp
    secure: bool = False
    httponly: bool = False
    samesite: str = ""


@dataclass
class Response:
    """HTTP response - runtime only, not persisted."""

    status_code: int
    status_text: str
    headers: dict[str, str]
    body: bytes
    time_ms: float
    size_bytes: int
    cookies: list[Cookie] = field(default_factory=lambda: [])

    @property
    def is_text_body(self) -> bool:
        """Check if the response body is text-based (displayable as string)."""
        content_type = self.headers.get("content-type", "")
        mime_type = content_type.split(";")[0].strip().lower()

        # text/* is always text
        if mime_type.startswith("text/"):
            return True

        # Common text-based application types
        if mime_type in {
            "application/json",
            "application/xml",
            "application/javascript",
            "application/xhtml+xml",
            "application/x-www-form-urlencoded",
        }:
            return True

        # Structured syntax suffixes (+json, +xml, +yaml)
        if mime_type.endswith(("+json", "+xml", "+yaml")):
            return True

        return False

    @property
    def body_text(self) -> str | None:
        """Return body as string if text-based, None otherwise."""
        if not self.is_text_body:
            return None

        # Try to extract charset from Content-Type header
        content_type = self.headers.get("content-type", "")
        charset = "utf-8"  # sensible default
        for part in content_type.split(";"):
            part = part.strip()
            if part.lower().startswith("charset="):
                charset = part[8:].strip().strip('"')
                break

        try:
            return self.body.decode(charset)
        except (UnicodeDecodeError, LookupError):
            # LookupError for unknown charset, fallback to utf-8 with replace
            return self.body.decode("utf-8", errors="replace")
