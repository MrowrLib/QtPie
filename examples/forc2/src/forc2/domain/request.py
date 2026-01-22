# pyright: reportUnknownVariableType=false
"""Request - the atomic unit of an HTTP request definition."""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

from qtpie import Event, State, Variable, new, state


class HttpMethod(Enum):
    """HTTP methods supported by Forc."""

    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    PATCH = "PATCH"
    DELETE = "DELETE"
    HEAD = "HEAD"
    OPTIONS = "OPTIONS"


@dataclass
class KeyValue:
    """A key-value pair for headers, query params, etc."""

    key: str = ""
    value: str = ""
    enabled: bool = True
    secret: bool = False  # If true, value stored in keychain


@dataclass
class RequestData:
    """Plain data for a Request (for serialization)."""

    name: str = ""
    method: HttpMethod = field(default=HttpMethod.GET)
    url: str = ""
    headers: list[KeyValue] = field(default_factory=list)
    query_params: list[KeyValue] = field(default_factory=list)
    body: str = ""


@state(on_save="_do_save")
class Request(State):
    ### Variables ###
    name: Variable[str] = new("")
    method: Variable[HttpMethod] = new(HttpMethod.GET)
    url: Variable[str] = new("")
    headers: Variable[list[KeyValue]] = new([])
    query_params: Variable[list[KeyValue]] = new([])
    body: Variable[str] = new("")
    filename: Variable[str | None] = new(None)

    # Events
    on_save: Event  # Fires to trigger save

    ### Methods ###
    def _get_full_path(self) -> Path | None:
        """Walk state_parent chain to build full path to this request."""
        from .collection import Collection
        from .workspace import Workspace

        parts: list[str] = []
        current: State | None = self

        while current is not None:
            if isinstance(current, Request) and current.filename.value:
                parts.insert(0, f"{current.filename.value}.yaml")
            elif isinstance(current, Collection) and current.filename.value:
                # Include all collection folder names in the path
                parts.insert(0, current.filename.value)
            elif isinstance(current, Workspace) and current.path.value:
                return current.path.value / Path(*parts)
            current = current.state_parent

        return None

    def _do_save(self) -> None:
        """Save this request to disk."""
        from ..format import save_request

        path = self._get_full_path()
        if path:
            save_request(self, path)
