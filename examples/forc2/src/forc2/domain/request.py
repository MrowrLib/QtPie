# pyright: reportUnknownVariableType=false
"""Request - the atomic unit of an HTTP request definition."""

from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from qtpie import Event, State, Var, new, state

from .auth import Auth
from .body import BodyType


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
class RequestKeyValue:
    name: str = ""
    value: str = ""
    enabled: bool = True


@state(on_save="_do_save")
class Request(State):
    ### Variables ###
    name: Var[str] = new("")
    method: Var[HttpMethod] = new(HttpMethod.GET)
    url: Var[str] = new("")
    headers: Var[list[RequestKeyValue]] = new([])
    query_params: Var[list[RequestKeyValue]] = new([])
    body: Var[str] = new("")
    body_type: Var[BodyType] = new(BodyType.NONE)
    body_fields: Var[list[RequestKeyValue]] = new([])  # For form bodies
    auth: Var[Auth | None] = new(None)
    filename: Var[str | None] = new(None)

    # Events
    on_save: Event

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
