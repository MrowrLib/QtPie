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
