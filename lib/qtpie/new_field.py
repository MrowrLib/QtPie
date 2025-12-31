"""NewField - Stores field configuration for deferred instantiation."""

from typing import Any, get_origin, get_type_hints

from .variable import Variable


class NewField:
    """Stores args/kwargs for deferred field instantiation.

    For Variable[T] annotations: replaces itself with a Variable descriptor.
    For other types: @new_fields handles instantiation.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.args = args
        self.kwargs = kwargs
        self.name: str = ""
        self.field_type: type | None = None

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
