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
    """A single HTTP request definition.

    Request is a leaf node in the collection tree. It holds all the data
    needed to construct and send an HTTP request.

    The parent Collection is accessed via `state_parent`.
    """

    name: Variable[str] = new("")
    method: Variable[HttpMethod] = new(HttpMethod.GET)
    url: Variable[str] = new("")
    headers: Variable[list[KeyValue]] = new([])
    query_params: Variable[list[KeyValue]] = new([])
    body: Variable[str] = new("")

    # File tracking - stem of source file (set on load)
    filename: Variable[str | None] = new(None)

    # Events
    # on_changed: Event  # Fires when any field changes # TODO REMOVE WHAT THE FUCK IS THIS FOR?
    on_save: Event  # Fires to trigger save

    # def __setup__(self) -> None:
    #     # Wire up change tracking - any field change fires on_changed
    #     self.name.on_change(lambda _: self.on_changed.emit())  # TODO REMOVE ALL OF THESE DUMBASS THINGS
    #     self.method.on_change(lambda _: self.on_changed.emit())
    #     self.url.on_change(lambda _: self.on_changed.emit())
    #     self.headers.on_change(lambda: self.on_changed.emit())
    #     self.query_params.on_change(lambda: self.on_changed.emit())
    #     self.body.on_change(lambda _: self.on_changed.emit())

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
                # Skip the root collection (direct child of Workspace) - its path
                # is already represented by workspace.path
                if not isinstance(current.state_parent, Workspace):
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
