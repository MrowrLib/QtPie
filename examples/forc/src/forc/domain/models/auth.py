from dataclasses import dataclass
from enum import Enum


class AuthType(Enum):
    NONE = "none"
    BASIC = "basic"
    BEARER = "bearer"
    API_KEY = "api_key"


class ApiKeyLocation(Enum):
    HEADER = "header"
    QUERY = "query"


API_KEY_LOCATION_LABELS: dict[ApiKeyLocation, str] = {
    ApiKeyLocation.HEADER: "Header",
    ApiKeyLocation.QUERY: "Query Param",
}


AUTH_TYPE_LABELS: dict[AuthType, str] = {
    AuthType.NONE: "No Auth",
    AuthType.BASIC: "Basic Auth",
    AuthType.BEARER: "Bearer Token",
    AuthType.API_KEY: "API Key",
}


@dataclass
class Auth:
    type: AuthType = AuthType.NONE


@dataclass
class BasicAuth(Auth):
    username: str = ""
    password: str = ""

    def __post_init__(self) -> None:
        self.type = AuthType.BASIC


@dataclass
class BearerAuth(Auth):
    token: str = ""

    def __post_init__(self) -> None:
        self.type = AuthType.BEARER


@dataclass
class ApiKeyAuth(Auth):
    key: str = ""
    value: str = ""
    location: ApiKeyLocation = ApiKeyLocation.HEADER

    def __post_init__(self) -> None:
        self.type = AuthType.API_KEY
