from dataclasses import dataclass
from enum import Enum


class AuthType(Enum):
    NONE = "none"
    BASIC = "basic"
    BEARER = "bearer"
    API_KEY = "api_key"


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
    location: str = "header"  # "header" or "query"

    def __post_init__(self) -> None:
        self.type = AuthType.API_KEY
