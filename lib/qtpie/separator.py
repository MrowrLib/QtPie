"""separator() - Factory function for menu separators."""

from typing import Any

from .new_field import NewField


def separator() -> Any:
    """Create a menu separator.

    Use in @menu decorated classes to add a visual separator between items.

    Example:
        @menu("&File")
        class FileMenu(QMenu):
            new: QAction = new("&New")
            open: QAction = new("&Open")
            sep1: QAction = separator()  # Visual separator
            exit: QAction = new("E&xit")

    Returns:
        A NewField marker that @menu recognizes as a separator.
    """
    from qtpy.QtGui import QAction

    field = NewField()
    field.field_type = QAction
    field.kwargs["_separator"] = True
    return field
