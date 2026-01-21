"""Collection - a folder that contains Requests and sub-Collections."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

from observant import ObservableList

from qtpie import Event, State, Variable, new, state

if TYPE_CHECKING:
    from .request import Request


# Type alias for tree items
type TreeItem = Request | Collection


@state
class Collection(State):
    """A folder in the request tree.

    Collections form a tree structure:
    - A Collection contains items (Requests or sub-Collections)
    - Each item's `state_parent` points back to its containing Collection
    - Top-level Collections have `state_parent = None` (or point to Workspace)

    The auto-parenting from QtPie's State system handles setting `state_parent`
    when items are added to the `items` list.
    """

    ### Variables ###
    name: Variable[str] = new("")
    items: Variable[list[TreeItem]] = new([])
    filename: Variable[str | None] = new(None)

    ### Events ###
    # TODO: remove unless we need these, no one ever asked for these ever:
    on_changed: Event  # Fires when this collection or any descendant changes
    on_item_added: Event[TreeItem]  # Fires when an item is added
    on_item_removed: Event[TreeItem]  # Fires when an item is removed

    ### Methods ###

    # TODO: DO NOT USE __setup__ REMOVE THIS unless we NEED it
    def __setup__(self) -> None:
        # Wire name changes to on_changed (lambda discards value arg)
        self.name.on_change(lambda _: self.on_changed.emit())

        # Hook into the items list for add/remove events
        # Cast is safe because Variable[list[T]] always uses ObservableList[T]
        items_list = cast(ObservableList[TreeItem], self.items.observable)
        items_list.on_insert(self._on_item_inserted)
        items_list.on_remove(self._on_item_removed)

    def _on_item_inserted(self, index: int, item: TreeItem) -> None:
        """Called when an item is added to the items list."""
        # Connect child's on_changed to bubble up to this collection
        # item.on_changed.connect(lambda: self.on_changed.emit())

        self.on_item_added.emit(item)
        self.on_changed.emit()

    def _on_item_removed(self, index: int, item: TreeItem) -> None:
        """Called when an item is removed from the items list."""
        self.on_item_removed.emit(item)
        self.on_changed.emit()

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

    def remove(self, item: TreeItem) -> bool:
        """Remove an item from this collection. Returns True if found and removed."""
        try:
            self.items.remove(item)
            return True
        except ValueError:
            return False
