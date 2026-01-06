"""The @menu decorator - transforms classes into Qt menus."""

from collections.abc import Callable
from typing import Any, overload

from qtpy.QtGui import QAction
from qtpy.QtWidgets import QMenu

from .new_field import NewField


@overload
def menu[T: QMenu](cls_or_text: type[T]) -> type[T]: ...


@overload
def menu[T: QMenu](
    cls_or_text: None = None,
    *,
    text: str | None = None,
) -> Callable[[type[T]], type[T]]: ...


@overload
def menu[T: QMenu](
    cls_or_text: str,
) -> Callable[[type[T]], type[T]]: ...


def menu[T: QMenu](
    cls_or_text: type[T] | str | None = None,
    *,
    text: str | None = None,
) -> Callable[[type[T]], type[T]] | type[T]:
    """
    Decorator that transforms a class into a Qt menu.

    Args:
        text: Menu title (shown in menu bar). Can be passed as first positional arg.
              If not provided, derived from class name (strips "Menu" suffix).

    Features:
        - QAction fields are auto-added via addAction()
        - QMenu fields are auto-added via addMenu() (submenus)
        - Fields are added in declaration order
        - Fields starting with _ are not added to the menu

    Example:
        @menu("&File")
        class FileMenu(QMenu):
            new: QAction = new("&New", shortcut="Ctrl+N", triggered="on_new")
            save: QAction = new("&Save", shortcut="Ctrl+S", triggered="on_save")
            sep1: QAction = separator()
            exit: QAction = new("E&xit", triggered="on_exit")

            def on_new(self) -> None:
                print("New file")

        # Or without text (uses class name)
        @menu
        class EditMenu(QMenu):
            undo: QAction = new("&Undo", shortcut="Ctrl+Z")
    """
    # Handle @menu("&File") - text as first positional arg
    if isinstance(cls_or_text, str):
        text = cls_or_text
        cls_or_text = None

    def decorator(cls: type[T]) -> type[T]:
        # Collect NewField instances before wrapping
        field_names: list[str] = []
        fields: dict[str, NewField] = {}
        for name in getattr(cls, "__annotations__", {}):
            value = getattr(cls, name, None)
            if isinstance(value, NewField):
                field_names.append(name)
                fields[name] = value

        def new_init(self: QMenu, *args: Any, **kwargs: Any) -> None:
            # Initialize QMenu base class
            QMenu.__init__(self)

            # Set menu title
            menu_title = text
            if menu_title is None:
                menu_title = cls.__name__
                if menu_title.endswith("Menu"):
                    menu_title = menu_title[:-4]
            self.setTitle(menu_title)

            # Instantiate fields
            for fname in field_names:
                field = fields[fname]
                # Skip separators - they're created later via addSeparator()
                if field.kwargs.get("_separator"):
                    continue
                if field.field_type is not None:
                    instance = field.field_type(*field.args, **field.kwargs)
                    # Apply widget props
                    for prop_name, value in field.widget_props.items():
                        setter_name = f"set{prop_name[0].upper()}{prop_name[1:]}"
                        setter = getattr(instance, setter_name, None)
                        if setter is not None and callable(setter):
                            setter(value)
                    setattr(self, fname, instance)

            # Connect signals
            for fname in field_names:
                field = fields[fname]
                instance = getattr(self, fname, None)
                if instance is not None:
                    for signal_name, handler in field.signal_connections.items():
                        signal = getattr(instance, signal_name, None)
                        if signal is not None:
                            if isinstance(handler, str):
                                method = getattr(self, handler, None)
                                if method is not None:
                                    signal.connect(method)
                            elif callable(handler):
                                signal.connect(handler)

            # Auto-add QAction and QMenu fields (in declaration order)
            for fname in field_names:
                if fname.startswith("_"):
                    continue

                field = fields[fname]
                instance = getattr(self, fname, None)

                # Check for separator marker
                if field.kwargs.get("_separator"):
                    separator_action = self.addSeparator()
                    setattr(self, fname, separator_action)
                    continue

                if isinstance(instance, QMenu):
                    self.addMenu(instance)
                elif isinstance(instance, QAction):
                    self.addAction(instance)

            # Call __setup__ hook if defined
            setup = getattr(self, "__setup__", None)
            if setup is not None and callable(setup):
                setup()

        cls.__init__ = new_init  # type: ignore[method-assign]
        return cls

    if cls_or_text is not None and not isinstance(cls_or_text, str):
        return decorator(cls_or_text)
    return decorator
