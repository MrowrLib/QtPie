from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from .auth import Auth


class HttpMethod(Enum):
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    PATCH = "PATCH"
    DELETE = "DELETE"
    HEAD = "HEAD"
    OPTIONS = "OPTIONS"


class BodyType(Enum):
    NONE = "none"
    JSON = "json"
    FORM = "form"
    TEXT = "text"
    XML = "xml"


@dataclass
class KeyValue:
    key: str
    value: str
    enabled: bool = True
    secret: bool = False  # If True, value is sensitive (hidden in UI, excluded from git export)


@dataclass
class Request:
    name: str
    method: HttpMethod = HttpMethod.GET
    url: str = ""
    headers: list[KeyValue] = field(default_factory=lambda: [])
    query_params: list[KeyValue] = field(default_factory=lambda: [])
    body: str = ""
    body_type: BodyType = BodyType.NONE
    auth: Auth | None = None


@dataclass
class Collection:
    name: str
    items: list[Request | Collection] = field(default_factory=lambda: [])


@dataclass
class Environment:
    name: str
    variables: list[KeyValue] = field(default_factory=lambda: [])


@dataclass
class Workspace:
    name: str
    collections: list[Collection] = field(default_factory=lambda: [])
    environments: list[Environment] = field(default_factory=lambda: [])
    active_environment: str | None = None
