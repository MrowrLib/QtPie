"""Collection - a folder that contains Requests and sub-Collections."""

from __future__ import annotations

from typing import TYPE_CHECKING

from qtpie import State, Variable, new, state

if TYPE_CHECKING:
    from .request import Request


# Type alias for tree items
type TreeItem = Request | Collection


@state
class Collection(State):
    ### Variables ###
    name: Variable[str] = new("")
    items: Variable[list[TreeItem]] = new([])
    filename: Variable[str | None] = new(None)

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
