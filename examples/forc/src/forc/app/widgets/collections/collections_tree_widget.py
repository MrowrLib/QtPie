from qtpy.QtWidgets import QLabel

from qtpie import Widget, new, widget


@widget
class CollectionsTreeWidget(Widget):
    """Tree view of collections and requests. Placeholder for now."""

    _placeholder: QLabel = new("Collections Tree Placeholder")
