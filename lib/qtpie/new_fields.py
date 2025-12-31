"""new_fields - Decorator that processes new() fields."""

from typing import Any, get_origin

from .new_field import NewField
from .variable import Variable


def new_fields[T](cls: type[T]) -> type[T]:
    """Decorator that processes NewField instances for non-Variable types.

    Variable[T] fields are handled automatically by NewField.__set_name__,
    which replaces the NewField with a Variable descriptor.

    This decorator handles non-Variable types by instantiating them in __init__.
    """
    # Check if already processed
    if getattr(cls, "__new_fields_processed__", False):
        return cls

    # Find all remaining NewField instances (non-Variable types)
    fields: dict[str, NewField] = {}
    for name, value in list(cls.__dict__.items()):
        if isinstance(value, NewField):
            fields[name] = value

    # If no NewField instances remain, nothing to do
    if not fields:
        cls.__new_fields_processed__ = True  # type: ignore[attr-defined]
        return cls

    # Wrap __init__ to instantiate non-Variable fields
    original_init = cls.__init__ if hasattr(cls, "__init__") else None

    def new_init(self: Any, *args: Any, **kwargs: Any) -> None:
        # Instantiate non-Variable fields
        for fname, field in fields.items():
            origin = get_origin(field.field_type)
            if origin is not Variable and field.field_type is not Variable:
                if field.field_type is not None:
                    instance = field.field_type(*field.args, **field.kwargs)
                    setattr(self, fname, instance)

        # Call original __init__
        if original_init is not None:
            original_init(self, *args, **kwargs)

    cls.__init__ = new_init  # type: ignore[method-assign]
    cls.__new_fields_processed__ = True  # type: ignore[attr-defined]

    return cls
