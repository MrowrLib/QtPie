"""CSS-like class helpers for Qt widgets.

Qt doesn't have native CSS classes, but we can use dynamic properties
to achieve similar functionality. These helpers manage a "class" property
as a list of strings, and handle the unpolish/polish dance to refresh styles.

Usage:
    from qtpie.styles import add_class, remove_class, toggle_class

    add_class(widget, "error")
    toggle_class(widget, "active")
    if has_class(widget, "selected"):
        remove_class(widget, "selected")

In QSS, match classes with attribute selectors:
    QPushButton[class~="primary"] { background: blue; }
    QLabel[class~="error"] { color: red; }
"""

from typing import cast

from qtpy.QtCore import QObject
from qtpy.QtWidgets import QWidget


def get_classes(widget: QObject) -> list[str]:
    """Get the list of CSS classes on a widget."""
    classes = widget.property("class")
    if isinstance(classes, list):
        return [str(c) for c in cast(list[object], classes)]
    return []


def set_classes(widget: QObject, classes: list[str], *, refresh: bool = True) -> None:
    """Set the CSS classes on a widget, optionally refreshing styles."""
    widget.setProperty("class", classes)
    if refresh and isinstance(widget, QWidget):
        style = widget.style()
        style.unpolish(widget)
        style.polish(widget)


def add_class(widget: QObject, class_name: str) -> None:
    """Add a CSS class to a widget (no-op if already present)."""
    classes = get_classes(widget)
    if class_name not in classes:
        classes.append(class_name)
        set_classes(widget, classes)


def add_classes(widget: QObject, class_names: list[str]) -> None:
    """Add multiple CSS classes to a widget."""
    classes = get_classes(widget)
    changed = False
    for class_name in class_names:
        if class_name not in classes:
            classes.append(class_name)
            changed = True
    if changed:
        set_classes(widget, classes)


def has_class(widget: QObject, class_name: str) -> bool:
    """Check if a widget has a CSS class."""
    return class_name in get_classes(widget)


def has_any_class(widget: QObject, class_names: list[str]) -> bool:
    """Check if a widget has any of the given CSS classes."""
    classes = get_classes(widget)
    return any(name in classes for name in class_names)


def remove_class(widget: QObject, class_name: str) -> None:
    """Remove a CSS class from a widget (no-op if not present)."""
    classes = get_classes(widget)
    if class_name in classes:
        classes.remove(class_name)
        set_classes(widget, classes)


def replace_class(widget: QObject, old_class: str, new_class: str) -> None:
    """Replace one CSS class with another (no-op if old class not present)."""
    classes = get_classes(widget)
    if old_class in classes:
        index = classes.index(old_class)
        classes[index] = new_class
        set_classes(widget, classes)


def toggle_class(widget: QObject, class_name: str) -> None:
    """Toggle a CSS class on a widget."""
    classes = get_classes(widget)
    if class_name in classes:
        classes.remove(class_name)
    else:
        classes.append(class_name)
    set_classes(widget, classes)
