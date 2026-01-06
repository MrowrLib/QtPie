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
        # Instantiate non-Variable fields (skip list widgets - handled in widget.py)
        for fname, field in fields.items():
            origin = get_origin(field.field_type)
            if origin is not Variable and field.field_type is not Variable:
                # Skip list[QWidget] fields - they're created as WidgetRepeaters in widget.py
                if field.is_list_widget:
                    continue
                if field.field_type is not None:
                    instance = field.field_type(*field.args, **field.kwargs)

                    # Apply objectName: use explicit name if set, otherwise default to field name for QWidgets
                    from PySide6.QtWidgets import QWidget

                    if isinstance(instance, QWidget):
                        if field.object_name is not None:
                            instance.setObjectName(field.object_name)
                        else:
                            instance.setObjectName(fname)

                        # Apply CSS classes if specified
                        if field.css_classes:
                            from .styles import set_classes

                            set_classes(instance, field.css_classes)

                    # Apply widget props (windowTitle="X" → setWindowTitle("X"))
                    for prop_name, value in field.widget_props.items():
                        setter_name = f"set{prop_name[0].upper()}{prop_name[1:]}"
                        setter = getattr(instance, setter_name, None)
                        if setter is not None and callable(setter):
                            setter(value)
                    setattr(self, fname, instance)

        # Call original __init__
        if original_init is not None:
            original_init(self, *args, **kwargs)

    cls.__init__ = new_init  # type: ignore[method-assign]
    cls.__new_fields_processed__ = True  # type: ignore[attr-defined]

    return cls
