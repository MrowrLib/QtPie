from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from observant import ObservableList

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
    XML = "xml"
    TEXT = "text"
    FORM_URLENCODED = "form_urlencoded"
    FORM_DATA = "form_data"


BODY_TYPE_LABELS: dict[BodyType, str] = {
    BodyType.NONE: "No Body",
    BodyType.JSON: "JSON",
    BodyType.XML: "XML",
    BodyType.TEXT: "Plain Text",
    BodyType.FORM_URLENCODED: "Form URL Encoded",
    BodyType.FORM_DATA: "Multipart Form Data",
}


@dataclass
class KeyValue:
    key: str = ""
    value: str = ""
    enabled: bool = True
    secret: bool = False  # If True, value is sensitive (hidden in UI, excluded from git export)


@dataclass
class Request:
    name: str
    method: HttpMethod = HttpMethod.GET
    url: str = ""
    headers: list[KeyValue] = field(default_factory=lambda: [])
    query_params: list[KeyValue] = field(default_factory=lambda: [])
    body: str = ""  # For text-based bodies (JSON, XML, TEXT)
    body_fields: list[KeyValue] = field(default_factory=lambda: [])  # For form bodies
    body_type: BodyType = BodyType.NONE
    auth: Auth | None = None
    collection: Collection | None = field(default=None, repr=False)


@dataclass
class Collection:
    name: str
    items: ObservableList[Request | Collection] = field(default_factory=lambda: ObservableList[Request | Collection]())
    parent: Collection | None = field(default=None, repr=False)


@dataclass
class Environment:
    name: str
    variables: list[KeyValue] = field(default_factory=lambda: [])


@dataclass
class Workspace:
    name: str
    collections: ObservableList[Collection] = field(default_factory=lambda: ObservableList[Collection]())
    environments: list[Environment] = field(default_factory=lambda: [])
    active_environment: str | None = None
