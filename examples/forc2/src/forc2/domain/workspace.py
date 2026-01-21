# pyright: reportUnknownVariableType=false
"""Workspace - the root state that holds a collection and its path."""

from pathlib import Path

from qtpie import Event, State, Variable, new, state

from .collection import Collection


@state(on_save="_do_save")
class Workspace(State):
    """The root container for a Forc workspace.

    A workspace has a path (directory) and a collection loaded from that path.
    Setting the path reactively loads/unloads the collection.
    """

    ### Variables ###
    collection: Variable[Collection | None] = new(None)
    path: Variable[Path | None] = new(None, onChange="_on_path_changed")

    ### Events ###
    on_save: Event  # Fires to trigger save

    ### Methods ###
    def _on_path_changed(self) -> None:
        """Load or unload collection when path changes."""
        print("Workspace: Path changed, loading collection...")

        from ..format import load_collection

        path = self.path.value
        if path is not None and path.exists():
            collection = load_collection(path)
            print(f"Workspace: Loaded collection from {path}")
            print(f"Length: {len(collection.items())}")
            collection.state_parent = self
            self.collection = collection
            print(f"Workspace: Loaded collection from {path}")
        elif self.collection() is not None:
            # Only set to None if not already None (avoids recursion with
            # ObservableProxy sibling notifications for None singleton)
            self.collection = None
            print("Workspace: Unloaded collection (path is None or does not exist)")

    def _do_save(self) -> None:
        """Save the collection to disk."""
        from ..format import save_collection

        if self.collection.value is not None and self.path.value is not None:
            save_collection(self.collection.value, self.path.value)
