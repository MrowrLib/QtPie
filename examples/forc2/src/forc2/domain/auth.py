"""Auth - authentication types for HTTP requests."""

from dataclasses import dataclass
from enum import Enum


class AuthType(Enum):
    """Authentication types supported by Forc."""

    NONE = "none"
    BASIC = "basic"
    BEARER = "bearer"
    API_KEY = "api_key"


AUTH_TYPE_LABELS: dict[AuthType, str] = {
    AuthType.NONE: "No Auth",
    AuthType.BASIC: "Basic Auth",
    AuthType.BEARER: "Bearer Token",
    AuthType.API_KEY: "API Key",
}


class ApiKeyLocation(Enum):
    """Where to send the API key."""

    HEADER = "header"
    QUERY = "query"


API_KEY_LOCATION_LABELS: dict[ApiKeyLocation, str] = {
    ApiKeyLocation.HEADER: "Header",
    ApiKeyLocation.QUERY: "Query Param",
}


@dataclass
class Auth:
    """Base auth class."""

    type: AuthType = AuthType.NONE


@dataclass
class BasicAuth(Auth):
    """HTTP Basic authentication."""

    username: str = ""
    password: str = ""

    def __post_init__(self) -> None:
        self.type = AuthType.BASIC


@dataclass
class BearerAuth(Auth):
    """Bearer token authentication."""

    token: str = ""

    def __post_init__(self) -> None:
        self.type = AuthType.BEARER


@dataclass
class ApiKeyAuth(Auth):
    """API Key authentication."""

    name: str = ""
    value: str = ""
    location: ApiKeyLocation = ApiKeyLocation.HEADER

    def __post_init__(self) -> None:
        self.type = AuthType.API_KEY
