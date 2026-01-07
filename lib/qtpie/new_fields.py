"""new_fields - Decorator that processes new() fields."""

from typing import Any, get_origin

from .new_field import NewField
from .variable import Variable

# Default property mapping for common widget types
# Used to determine which property to set for positional Translatable args
_DEFAULT_TEXT_PROPS: dict[str, str] = {
    "QLabel": "text",
    "QPushButton": "text",
    "QCheckBox": "text",
    "QRadioButton": "text",
    "QToolButton": "text",
    "QGroupBox": "title",
    "QMenu": "title",
    "QLineEdit": "text",
    "QAction": "text",
    "QAbstractButton": "text",
}


def _get_default_prop(widget: Any) -> str | None:
    """Get the default text property name for a widget type."""
    for cls_name, prop in _DEFAULT_TEXT_PROPS.items():
        # Check if the widget's class name or parent class matches
        for cls in type(widget).__mro__:
            if cls.__name__ == cls_name:
                return prop
    return None


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
        from qtpie.translations.translatable import Translatable

        # Instantiate non-Variable fields (skip list widgets - handled in widget.py)
        for fname, field in fields.items():
            origin = get_origin(field.field_type)
            if origin is not Variable and field.field_type is not Variable:
                # Skip list[QWidget] fields - they're created as WidgetRepeaters in widget.py
                if field.is_list_widget:
                    continue
                if field.field_type is not None:
                    # Resolve Translatable markers in args before construction
                    resolved_args = list(field.args)
                    for idx, translatable in field.translatable_args:
                        if idx < len(resolved_args):
                            resolved_args[idx] = translatable.resolve()

                    # Resolve Translatable markers in kwargs before construction
                    resolved_kwargs = dict(field.kwargs)
                    for key, translatable in field.translatable_kwargs.items():
                        if key in resolved_kwargs and isinstance(resolved_kwargs[key], Translatable):
                            resolved_kwargs[key] = translatable.resolve()

                    instance = field.field_type(*resolved_args, **resolved_kwargs)

                    # Apply objectName: use explicit name if set, otherwise default to field name for QWidgets
                    from qtpy.QtWidgets import QWidget

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
                    # Also resolve Translatable markers in widget_props
                    for prop_name, value in field.widget_props.items():
                        # Resolve if it's a Translatable
                        if isinstance(value, Translatable):
                            value = value.resolve()

                        setter_name = f"set{prop_name[0].upper()}{prop_name[1:]}"
                        setter = getattr(instance, setter_name, None)
                        if setter is not None and callable(setter):
                            setter(value)
                        # Special case: tooltip on QAction also sets statusTip
                        if prop_name == "toolTip":
                            from qtpy.QtGui import QAction

                            if isinstance(instance, QAction):
                                instance.setStatusTip(value)

                    # Register translation bindings for hot-reload
                    from qtpie.translations.store import register_binding

                    # Register bindings for positional args
                    for _idx, translatable in field.translatable_args:
                        default_prop = _get_default_prop(instance)
                        if default_prop:
                            register_binding(
                                instance,
                                default_prop,
                                translatable.text,
                                translatable.context,
                            )

                    # Register bindings for kwargs and widget_props
                    for prop_name, translatable in field.translatable_kwargs.items():
                        register_binding(
                            instance,
                            prop_name,
                            translatable.text,
                            translatable.context,
                        )

                    setattr(self, fname, instance)

        # Call original __init__
        if original_init is not None:
            original_init(self, *args, **kwargs)

    cls.__init__ = new_init  # type: ignore[method-assign]
    cls.__new_fields_processed__ = True  # type: ignore[attr-defined]

    return cls
