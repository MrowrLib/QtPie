"""Collection - a folder that contains Requests and sub-Collections."""

from __future__ import annotations

from pathlib import Path

from qtpie import State, Var, new, state

# Import Request at runtime (not just TYPE_CHECKING) because the 'type TreeItem = ...'
# statement is evaluated lazily and needs Request to be in scope when resolved.
from .request import Request

# Type alias for tree items
type TreeItem = Request | Collection


@state
class Collection(State):
    ### Variables ###
    name: Var[str] = new("")
    items: Var[list[TreeItem]] = new([])
    filename: Var[str | None] = new(None)

    ### Methods ###
    def _get_full_path(self) -> Path | None:
        """Walk state_parent chain to build full path to this collection."""
        from .workspace import Workspace

        parts: list[str] = []
        current: State | None = self

        while current is not None:
            if isinstance(current, Collection) and current.filename.value:
                parts.insert(0, current.filename.value)
            elif isinstance(current, Workspace) and current.path.value:
                # Root collection filename is "collections", so path is correct
                return current.path.value / Path(*parts)
            current = current.state_parent

        return None

    def save(self, path: Path | None = None) -> None:
        """Save this collection to disk.

        If path is not provided, walks the state_parent chain to determine it.
        """
        from ..format import save_collection

        if path is None:
            path = self._get_full_path()
        if path:
            save_collection(self, path)

    def add_request(self, name: str = "") -> Request:
        """Create and add a new Request to this collection."""
        from .request import Request

        request = Request()
        request.name.value = name  # Set name before adding (avoid recursion)
        request.state_parent = self
        self.items.append(request)
        return request

    def add_collection(self, name: str = "") -> Collection:
        """Create and add a new sub-Collection to this collection."""
        collection = Collection()
        collection.name.value = name  # Set name before adding (avoid recursion)
        collection.state_parent = self
        self.items.append(collection)
        return collection
