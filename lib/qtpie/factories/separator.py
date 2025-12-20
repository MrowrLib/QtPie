"""The separator() factory function for adding separators to menus."""

from dataclasses import field
from typing import Any

from qtpy.QtGui import QAction

# Metadata key used to store separator info for the @menu decorator
SEPARATOR_METADATA_KEY = "qtpie_separator"


def separator() -> QAction:
    """
    Create a separator for menus.

    Examples:
        @menu("&File")
        class FileMenu(QMenu):
            new: NewAction = make(NewAction)
            open_file: OpenAction = make(OpenAction)
            sep1: QAction = separator()
            exit_app: ExitAction = make(ExitAction)

        # Multiple separators
        @menu("&Edit")
        class EditMenu(QMenu):
            undo: UndoAction = make(UndoAction)
            redo: RedoAction = make(RedoAction)
            sep1: QAction = separator()
            cut: CutAction = make(CutAction)
            copy: CopyAction = make(CopyAction)
            paste: PasteAction = make(PasteAction)
            sep2: QAction = separator()
            select_all: SelectAllAction = make(SelectAllAction)

    Returns:
        At type-check time: QAction
        At runtime: a dataclass field that the @menu decorator processes

    Note:
        - Do NOT use underscore prefix - underscore fields are completely ignored
        - Separators are only processed in @menu decorated classes
        - The actual QAction (from addSeparator()) is stored on the instance
    """
    # Store marker in metadata for the menu decorator to detect
    metadata: dict[str, Any] = {SEPARATOR_METADATA_KEY: True}

    # We use init=False because the menu decorator will create and assign the separator
    return field(init=False, default=None, metadata=metadata)  # type: ignore[return-value]
