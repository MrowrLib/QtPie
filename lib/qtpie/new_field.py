"""NewField - Stores field configuration for deferred instantiation."""

from collections.abc import Callable
from typing import Any, get_args, get_origin, get_type_hints

from .variable import Variable, create_variable_descriptor


class NewField:
    """Stores args/kwargs for deferred field instantiation.

    For Variable[T] annotations: replaces itself with a Variable descriptor.
    For QWidget types: tracks layout inclusion/exclusion.
    For other types: @new_fields handles instantiation, passing all args/kwargs.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.args = args
        self.kwargs = kwargs
        self.name: str = ""
        self.field_type: type | None = None
        self.exclude_from_layout = False
        self.bind: str | None = None  # Extracted for QWidgets in __set_name__
        self.signal_connections: dict[str, str | Callable[..., Any]] = {}  # signal_name -> method_name or callable

    def __set_name__(self, owner: type, name: str) -> None:
        self.name = name
        # Get the type annotation
        hints = get_type_hints(owner)
        self.field_type = hints.get(name)

        # If it's a Variable, replace self with a Variable descriptor
        origin = get_origin(self.field_type)
        if origin is Variable or self.field_type is Variable:
            default = self._get_variable_default()
            # Extract inner type from Variable[T] and optional widget type from Variable[T, W]
            inner_type: type | None = None
            widget_type: type | None = None
            if origin is Variable:
                args = get_args(self.field_type)
                inner_type = args[0] if args else None
                widget_type = args[1] if len(args) > 1 else None
            setattr(owner, name, create_variable_descriptor(default, name, inner_type, widget_type))
            return

        # Handle QWidget-specific kwargs only
        # For non-QWidgets: leave bind= and layout= in kwargs so they pass to constructor
        if self._is_qwidget_type():
            # Extract bind= for QtPie binding system
            self.bind = self.kwargs.pop("bind", None)

            # layout=False → exclude from layout
            layout_kwarg = self.kwargs.pop("layout", None)
            if layout_kwarg is False:
                self.exclude_from_layout = True

            # Extract signal connections (e.g., clicked="on_clicked")
            self._extract_signal_connections()

    def _is_qwidget_type(self) -> bool:
        """Check if the field type is a QWidget subclass."""
        if self.field_type is None:
            return False
        try:
            from PySide6.QtWidgets import QWidget

            # field_type could be a generic alias, so check it's a proper type
            return isinstance(self.field_type, type) and issubclass(self.field_type, QWidget)  # pyright: ignore[reportUnnecessaryIsInstance]
        except (ImportError, TypeError):
            return False

    def _is_signal(self, name: str) -> bool:
        """Check if name is a signal on the field type."""
        if self.field_type is None:
            return False
        try:
            attr = getattr(self.field_type, name, None)
            if attr is None:
                return False
            # PySide6 signals at class level have type name 'Signal'
            return type(attr).__name__ == "Signal"
        except Exception:
            return False

    def _extract_signal_connections(self) -> None:
        """Extract signal=handler kwargs for QWidgets.

        Supports both callables and string method names:
            clicked=lambda: print("clicked")
            clicked="on_clicked"
        """
        to_remove: list[str] = []
        for key, value in self.kwargs.items():
            # Check if this kwarg name matches a signal on the widget type
            if self._is_signal(key):
                # Value must be a string (method name) or callable
                if isinstance(value, str) or callable(value):
                    self.signal_connections[key] = value
                    to_remove.append(key)

        for key in to_remove:
            del self.kwargs[key]

    def _get_variable_default(self) -> Any:
        """Extract default value for a Variable field."""
        # Check for explicit default= kwarg
        if "default" in self.kwargs:
            return self.kwargs["default"]
        # Check for single primitive arg
        if len(self.args) == 1:
            arg = self.args[0]
            if isinstance(arg, (str, int, float, bool)):
                return arg
        return None
