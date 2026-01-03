"""NewField - Stores field configuration for deferred instantiation."""

from typing import Any, get_origin, get_type_hints

from .variable import Variable


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

    def __set_name__(self, owner: type, name: str) -> None:
        self.name = name
        # Get the type annotation
        hints = get_type_hints(owner)
        self.field_type = hints.get(name)

        # If it's a Variable, replace self with a Variable descriptor
        origin = get_origin(self.field_type)
        if origin is Variable or self.field_type is Variable:
            default = self._get_variable_default()
            setattr(owner, name, Variable(default))
            return

        # Handle layout kwarg for QWidget types only
        # For QWidgets: layout=False → exclude from layout, then consume the kwarg
        # For non-QWidgets: leave layout= in kwargs so it passes to constructor
        if self._is_qwidget_type():
            layout_kwarg = self.kwargs.pop("layout", None)
            if layout_kwarg is False:
                self.exclude_from_layout = True

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
