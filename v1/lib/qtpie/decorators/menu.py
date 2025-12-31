"""The @menu decorator - transforms classes into Qt menus."""

from collections.abc import Callable
from dataclasses import MISSING, dataclass, fields
from typing import (
    Any,
    dataclass_transform,
    get_type_hints,
    overload,
)

from qtpy.QtGui import QAction
from qtpy.QtWidgets import QMenu

from qtpie.factories.make import SIGNALS_METADATA_KEY
from qtpie.factories.separator import SEPARATOR_METADATA_KEY


@overload
@dataclass_transform()
def menu[T: QMenu](
    _cls_or_text: type[T],
    *,
    text: str | None = ...,
) -> type[T]: ...


@overload
@dataclass_transform()
def menu[T: QMenu](
    _cls_or_text: None = None,
    *,
    text: str | None = ...,
) -> Callable[[type[T]], type[T]]: ...


@overload
@dataclass_transform()
def menu[T: QMenu](
    _cls_or_text: str,
) -> Callable[[type[T]], type[T]]: ...


@dataclass_transform()
def menu[T: QMenu](
    _cls_or_text: type[T] | str | None = None,
    *,
    text: str | None = None,
) -> Callable[[type[T]], type[T]] | type[T]:
    """
    Decorator that transforms a class into a Qt menu.

    Args:
        text: Menu title (shown in menu bar). Can be passed as first positional arg.

    Features:
        - QAction fields are auto-added via addAction()
        - QMenu fields are auto-added via addMenu() (submenus)
        - Fields are added in declaration order

    Example:
        @menu("&File")
        class FileMenu(QMenu):
            new_action: NewAction = make(NewAction)
            open_action: OpenAction = make(OpenAction)
            recent_menu: RecentMenu = make(RecentMenu)  # submenu
            exit_action: ExitAction = make(ExitAction)

        # Or without text (set later or use class name)
        @menu
        class EditMenu(QMenu):
            undo: UndoAction = make(UndoAction)
    """
    # Handle @menu("&File") - text as first positional arg
    if isinstance(_cls_or_text, str):
        text = _cls_or_text
        _cls_or_text = None

    def decorator(cls: type[T]) -> type[T]:
        # Apply @dataclass to register fields
        cls = dataclass(cls)  # type: ignore[assignment]

        def new_init(self: QMenu, *args: object, **kwargs: object) -> None:
            # Initialize QMenu base class first
            QMenu.__init__(self)

            # Manually set dataclass fields (with default_factory support)
            for f in fields(cls):  # type: ignore[arg-type]
                if f.name in kwargs:
                    setattr(self, f.name, kwargs[f.name])
                elif f.default is not MISSING:
                    setattr(self, f.name, f.default)
                elif f.default_factory is not MISSING:  # type: ignore[arg-type]
                    setattr(self, f.name, f.default_factory())  # type: ignore[misc]

            # Connect signals from make() metadata
            for f in fields(cls):  # type: ignore[arg-type]
                potential_signals = f.metadata.get(SIGNALS_METADATA_KEY)
                if potential_signals:
                    instance = getattr(self, f.name, None)
                    if instance is not None:
                        _connect_signals(self, instance, potential_signals)

            # Set menu title
            if text:
                self.setTitle(text)
            else:
                # Auto-generate from class name
                menu_title = cls.__name__
                if menu_title.endswith("Menu"):
                    menu_title = menu_title[:-4]
                self.setTitle(menu_title)

            # Auto-add QAction and QMenu fields
            type_hints = get_type_hints(cls)
            for f in fields(cls):  # type: ignore[arg-type]
                if f.name.startswith("_"):
                    continue

                # Check for separator() marker in metadata
                if f.metadata.get(SEPARATOR_METADATA_KEY):
                    separator_action = self.addSeparator()
                    setattr(self, f.name, separator_action)
                    continue

                field_type = type_hints.get(f.name)
                instance = getattr(self, f.name, None)

                if isinstance(instance, QMenu):
                    self.addMenu(instance)
                elif isinstance(instance, QAction):
                    self.addAction(instance)
                # Check if field type is QAction subclass (for typed but not yet instantiated)
                elif isinstance(field_type, type):
                    if issubclass(field_type, QMenu) and isinstance(instance, QMenu):
                        self.addMenu(instance)
                    elif issubclass(field_type, QAction) and isinstance(instance, QAction):
                        self.addAction(instance)

            # Call lifecycle hooks if they exist
            _call_if_exists(self, "setup")

        cls.__init__ = new_init  # type: ignore[method-assign]
        return cls

    if _cls_or_text is not None and not isinstance(_cls_or_text, str):
        return decorator(_cls_or_text)
    return decorator


def _connect_signals(
    parent: object,
    instance: object,
    potential_signals: dict[str, str | Callable[..., Any]],
) -> None:
    """Connect signals from make() metadata to methods or callables."""
    for attr_name, handler in potential_signals.items():
        attr = getattr(instance, attr_name, None)
        if attr is not None and hasattr(attr, "connect"):
            if isinstance(handler, str):
                method = getattr(parent, handler, None)
                if method is not None:
                    attr.connect(method)
            elif callable(handler):
                attr.connect(handler)


def _call_if_exists(obj: object, method_name: str, *args: object) -> None:
    """Call a method on obj if it exists and is callable."""
    method = getattr(obj, method_name, None)
    if method is not None and callable(method):
        method(*args)
