from dataclasses import dataclass


@dataclass
class Response:
    """HTTP response - runtime only, not persisted."""

    status_code: int
    status_text: str
    headers: dict[str, str]
    body: bytes
    time_ms: float
    size_bytes: int
