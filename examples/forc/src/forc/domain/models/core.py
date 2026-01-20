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
    filename: str | None = field(default=None, repr=False)  # Actual filename on disk (set on load)


@dataclass
class Collection:
    name: str
    items: ObservableList[Request | Collection] = field(default_factory=lambda: ObservableList[Request | Collection]())
    parent: Collection | None = field(default=None, repr=False)
    folder: str | None = field(default=None, repr=False)  # Actual folder name on disk (set on load)


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


def validate_request_name(
    name: str,
    collection: Collection | None = None,
    exclude: Request | None = None,
) -> None | str | list[str]:
    """Validate a request name.

    Args:
        name: The name to validate
        collection: The collection to check for slug collisions (optional)
        exclude: A request to exclude from collision check (for renames)

    Returns:
        None if valid, or error message(s) if invalid
    """
    from forc.domain.formats.yaml_format import slugify

    errors: list[str] = []

    # Check empty
    if not name or not name.strip():
        errors.append("Name cannot be empty")
        return errors[0] if len(errors) == 1 else errors

    # Check slug is valid (not empty after slugify)
    slug = slugify(name)
    if not slug:
        errors.append("Name must contain at least one alphanumeric character")

    # Check for slug collision in collection
    if collection is not None:
        for item in collection.items:
            if isinstance(item, Request) and item is not exclude:
                if slugify(item.name) == slug:
                    errors.append(f"Name conflicts with existing request '{item.name}'")
                    break

    if not errors:
        return None
    return errors[0] if len(errors) == 1 else errors


def validate_collection_name(
    name: str,
    parent: Collection | None = None,
    workspace: Workspace | None = None,
    exclude: Collection | None = None,
) -> None | str | list[str]:
    """Validate a collection name.

    Args:
        name: The name to validate
        parent: The parent collection to check for slug collisions (optional)
        workspace: The workspace to check for top-level collisions (if no parent)
        exclude: A collection to exclude from collision check (for renames)

    Returns:
        None if valid, or error message(s) if invalid
    """
    from forc.domain.formats.yaml_format import slugify

    errors: list[str] = []

    # Check empty
    if not name or not name.strip():
        errors.append("Name cannot be empty")
        return errors[0] if len(errors) == 1 else errors

    # Check slug is valid (not empty after slugify)
    slug = slugify(name)
    if not slug:
        errors.append("Name must contain at least one alphanumeric character")

    # Check for slug collision
    items_to_check: list[Request | Collection] = []
    if parent is not None:
        items_to_check = list(parent.items)
    elif workspace is not None:
        items_to_check = list(workspace.collections)  # type: ignore[arg-type]

    for item in items_to_check:
        if isinstance(item, Collection) and item is not exclude:
            if slugify(item.name) == slug:
                errors.append(f"Name conflicts with existing collection '{item.name}'")
                break

    if not errors:
        return None
    return errors[0] if len(errors) == 1 else errors
