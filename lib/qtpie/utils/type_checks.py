"""Qt type checking utilities for NewField and other modules."""

from typing import Any, get_args, get_origin


def _is_subclass_of(cls: type | None, *targets: type, exclude: tuple[type, ...] = ()) -> bool:
    """Check if cls is a subclass of any target type, optionally excluding some.

    Args:
        cls: The type to check (can be None or a generic alias).
        *targets: Qt classes to check against.
        exclude: Tuple of classes to exclude (return False if cls is subclass of these).

    Returns:
        True if cls is a proper type and subclass of any target, and not a subclass of excluded.
    """
    if cls is None:
        return False
    if not isinstance(cls, type):  # pyright: ignore[reportUnnecessaryIsInstance]
        return False
    if not issubclass(cls, targets):
        return False
    if exclude and issubclass(cls, exclude):
        return False
    return True


def is_qwidget(cls: type | None) -> bool:
    """Check if cls is a QWidget subclass."""
    from qtpy.QtWidgets import QWidget

    return _is_subclass_of(cls, QWidget)


def is_qobject(cls: type | None, *, exclude_qwidget: bool = False) -> bool:
    """Check if cls is a QObject subclass."""
    from qtpy.QtCore import QObject
    from qtpy.QtWidgets import QWidget

    exclude = (QWidget,) if exclude_qwidget else ()
    return _is_subclass_of(cls, QObject, exclude=exclude)


def is_qaction(cls: type | None) -> bool:
    """Check if cls is QAction or a subclass."""
    from qtpy.QtGui import QAction

    return _is_subclass_of(cls, QAction)


def is_qtableview(cls: type | None) -> bool:
    """Check if cls is a QTableView subclass."""
    from qtpy.QtWidgets import QTableView

    return _is_subclass_of(cls, QTableView)


def is_qlistview(cls: type | None, *, exclude_table_tree: bool = False) -> bool:
    """Check if cls is a QListView subclass."""
    from qtpy.QtWidgets import QListView, QTableView, QTreeView

    exclude = (QTableView, QTreeView) if exclude_table_tree else ()
    return _is_subclass_of(cls, QListView, exclude=exclude)


def is_qtreeview(cls: type | None) -> bool:
    """Check if cls is a QTreeView subclass."""
    from qtpy.QtWidgets import QTreeView

    return _is_subclass_of(cls, QTreeView)


def is_qcombobox(cls: type | None) -> bool:
    """Check if cls is a QComboBox subclass."""
    from qtpy.QtWidgets import QComboBox

    return _is_subclass_of(cls, QComboBox)


def is_qtabwidget(cls: type | None) -> bool:
    """Check if cls is a QTabWidget subclass."""
    from qtpy.QtWidgets import QTabWidget

    return _is_subclass_of(cls, QTabWidget)


def is_qspaceritem(cls: type | None) -> bool:
    """Check if cls is exactly QSpacerItem (identity check, not subclass)."""
    from qtpy.QtWidgets import QSpacerItem

    return cls is QSpacerItem


def is_qlayout(cls: type | None) -> bool:
    """Check if cls is a QLayout subclass."""
    from qtpy.QtWidgets import QLayout

    return _is_subclass_of(cls, QLayout)


def is_qsplitter(cls: type | None) -> bool:
    """Check if cls is a QSplitter subclass."""
    from qtpy.QtWidgets import QSplitter

    return _is_subclass_of(cls, QSplitter)


def is_qgroupbox(cls: type | None) -> bool:
    """Check if cls is a QGroupBox subclass."""
    from qtpy.QtWidgets import QGroupBox

    return _is_subclass_of(cls, QGroupBox)


def is_qframe(cls: type | None) -> bool:
    """Check if cls is a QFrame subclass (but not QGroupBox or other derived types)."""
    from qtpy.QtWidgets import (
        QAbstractScrollArea,
        QFrame,
        QGroupBox,
        QLabel,
        QStackedWidget,
    )

    # QFrame is base class for many widgets - only match actual QFrame usage
    # Exclude QGroupBox (handled separately), QLabel, QStackedWidget
    # Also exclude QAbstractScrollArea subclasses (QListView, QTableView, QTreeView, etc.)
    if cls is None:
        return False
    if not _is_subclass_of(cls, QFrame):
        return False
    # Exclude types that inherit from QFrame but aren't used as container frames
    if _is_subclass_of(cls, QGroupBox, QLabel, QStackedWidget, QAbstractScrollArea):
        return False
    # Only match QFrame itself or custom subclasses that aren't the above
    return cls is QFrame or (issubclass(cls, QFrame) and not _is_subclass_of(cls, QGroupBox, QLabel, QStackedWidget, QAbstractScrollArea))


def is_model_widget(cls: type | None) -> bool:
    """Check if cls is a model widget (QComboBox, QListView, QTableView, QTreeView)."""
    from qtpy.QtWidgets import QComboBox, QListView, QTableView, QTreeView

    return _is_subclass_of(cls, QComboBox, QListView, QTableView, QTreeView)


def is_qtext_editor(cls: type | None) -> bool:
    """Check if cls is a QPlainTextEdit or QTextEdit subclass."""
    from qtpy.QtWidgets import QPlainTextEdit, QTextEdit

    return _is_subclass_of(cls, QPlainTextEdit, QTextEdit)


def is_dock_generic(type_to_check: Any) -> bool:
    """Check if type_to_check is a Dock[T] generic alias."""
    if type_to_check is None:
        return False
    from qtpie.dock import Dock

    return get_origin(type_to_check) is Dock


def extract_record_type_from_bases(
    cls: type,
    *target_bases: type,
    filter_typevar: bool = False,
) -> type | None:
    """Extract T from Widget[T] (or similar), even through intermediate generic classes.

    For example, if you have:
        class DeleteWidget[T](Widget[T]): ...
        class DeleteRequestKeyValueWidget(DeleteWidget[RequestKeyValue]): ...

    This will correctly extract RequestKeyValue as the record type.

    Args:
        cls: The class to inspect (e.g., DeleteRequestKeyValueWidget)
        *target_bases: The base generic classes to look for (e.g., Widget, Window, Dialog).
                       Multiple can be provided (e.g., AppBase, App).
        filter_typevar: If True, filter out TypeVar and NoneType results (return None instead).

    Returns:
        The concrete type T, or None if not found (or filtered out).
    """
    from typing import TypeVar

    def _is_valid_type(t: Any) -> bool:
        if t is None:
            return False
        if filter_typevar:
            if t is type(None) or isinstance(t, TypeVar):
                return False
        return True

    for base in getattr(cls, "__orig_bases__", ()):
        origin = get_origin(base)
        # Check if origin matches any target base directly
        if origin in target_bases:
            args = get_args(base)
            if args and _is_valid_type(args[0]):
                return args[0]
            continue
        # Check if origin is itself a generic subclass of any target_base
        if origin is not None and isinstance(origin, type):
            for target_base in target_bases:
                if issubclass(origin, target_base):
                    args = get_args(base)
                    if args and _is_valid_type(args[0]):
                        return args[0]
                    break
    return None
