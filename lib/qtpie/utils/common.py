"""Common utility functions shared across QtPie modules."""

import re
import types

# Regex to find placeholders like {#self}, {#index}, {name}, {age}, {#self.age}
PLACEHOLDER_RE = re.compile(r"\{(#?\w+(?:\.\w+)*)\}")

# Regex to parse handler spec like "method_name(#value, #index, #args)"
HANDLER_SPEC_RE = re.compile(r"^(\w+)(?:\((.*)\))?$")


def is_primitive_type(t: type | types.UnionType | None) -> bool:
    """Check if type is a primitive."""
    return t in (str, int, float, bool, type(None))


def is_signal(obj: object) -> bool:
    """Check if obj is a Qt Signal (bound signal instance).

    Works with both PySide6 (SignalInstance) and PyQt6 (pyqtBoundSignal).
    """
    type_name = type(obj).__name__
    return type_name in ("SignalInstance", "pyqtBoundSignal")


def is_signal_on_type(name: str, target_type: type) -> bool:
    """Check if name is a signal on the given type.

    Different from is_signal() which checks an object instance.
    This checks if a named attribute on a type is a Signal definition.
    """
    try:
        attr = getattr(target_type, name, None)
        if attr is None:
            return False
        # qtpy signals at class level have type name 'Signal'
        return type(attr).__name__ == "Signal"
    except Exception:
        return False


def detect_required_bindings(
    cls: type,
    config_attr: str,
    variable_type: type,
    descriptor_factory: type,
) -> None:
    """Detect bare Variable[T] annotations as required bindings.

    A bare annotation like `count: Variable[int]` (no `= new()`) indicates
    the Variable must be provided by the parent widget/window/menu via binding.

    Creates a descriptor for each bare Variable annotation.

    Args:
        cls: The class to process.
        config_attr: Name of the config attribute on the class (e.g., "_qtpie_config").
        variable_type: The Variable type to check for.
        descriptor_factory: Factory to create descriptors (e.g., _RequiredBindingDescriptor).
    """
    from typing import Any, get_args, get_origin

    annotations = getattr(cls, "__annotations__", {})
    config = getattr(cls, config_attr)

    for name, annotation in annotations.items():
        origin = get_origin(annotation)
        if origin is not variable_type and annotation is not variable_type:
            continue

        # Check if there's a value in __dict__
        if name in cls.__dict__:
            continue

        # Bare Variable[T] - mark as required
        config.required_bindings.add(name)

        # Extract inner type
        inner_type: type[Any] | None = None
        if origin is variable_type:
            args = get_args(annotation)
            inner_type = args[0] if args else None

        # Create descriptor
        descriptor = descriptor_factory(name, inner_type)
        setattr(cls, name, descriptor)
