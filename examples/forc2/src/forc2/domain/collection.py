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
    name: Var[str] = new("", validate="_validate_name_unique")
    items: Var[list[TreeItem]] = new([])
    filename: Var[str | None] = new(None)

    ### Validators ###
    def _validate_name_unique(self, value: str) -> str | None:
        """Validate that name doesn't conflict with siblings."""
        from ..format import slugify

        parent = self.state_parent
        if not isinstance(parent, Collection):
            return None  # No parent collection, no conflict possible

        new_slug = slugify(value)

        for item in parent.items.value:
            if item is self:
                continue  # Skip self
            item_filename = item.filename.value
            if item_filename == new_slug:
                return f"Name conflicts with existing item '{item.name.value}'"

        return None

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
        Automatically renames the folder if name has changed (except for root collection).
        Does nothing if validation fails (e.g., name conflict).
        """
        import shutil

        from ..format import save_collection, slugify
        from .workspace import Workspace

        # Don't save if validation fails
        if not self.is_valid.get():
            return

        if path is not None:
            # Explicit path provided - just save there
            save_collection(self, path)
            return

        # Root collection (parent is Workspace) keeps its folder name "collections"
        is_root_collection = isinstance(self.state_parent, Workspace)

        if is_root_collection:
            # Don't rename root collection folder
            path = self._get_full_path()
            if path:
                save_collection(self, path)
            return

        # Get old path (using current filename)
        old_path = self._get_full_path()

        # Compute new filename from name
        new_filename = slugify(self.name.value)

        # Update filename to new value
        self.filename.value = new_filename

        # Get new path (now using updated filename)
        new_path = self._get_full_path()

        if new_path is None:
            return

        # If old folder exists at different path, move it
        if old_path and old_path != new_path and old_path.exists():
            # Move contents to new location
            shutil.move(str(old_path), str(new_path))
            # save_collection will update the _collection.yaml metadata

        save_collection(self, new_path)

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

    def delete(self) -> None:
        """Delete this collection from disk and remove from parent collection."""
        import shutil

        # Delete from disk if path exists
        path = self._get_full_path()
        if path and path.exists():
            shutil.rmtree(path)

        # Remove from parent collection
        parent = self.state_parent
        if isinstance(parent, Collection):
            items = parent.items()
            if self in items:
                parent.items.remove(self)
            self.state_parent = None
