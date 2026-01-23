"""Collection - a folder that contains Requests and sub-Collections."""

from __future__ import annotations

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
    def add_request(self, name: str = "") -> Request:
        """Create and add a new Request to this collection."""
        from .request import Request

        request = Request()
        request.name.value = name  # Set name before adding (avoid recursion)
        self.items.append(request)  # This wires up on_changed bubbling
        return request

    def add_collection(self, name: str = "") -> Collection:
        """Create and add a new sub-Collection to this collection."""
        collection = Collection()
        collection.name.value = name  # Set name before adding (avoid recursion)
        self.items.append(collection)  # This wires up on_changed bubbling
        return collection
