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


def resolve_signal_from_hierarchy(widget: object, name: str) -> object | None:
    """Search up the parent hierarchy for a signal or callable by name.

    Resolution order:
    1. widget.parent() (Qt parent)
    2. parent().parent(), etc.
    3. QApplication.instance()

    Returns the signal or callable if found, None otherwise.
    """
    from typing import Any

    from qtpy.QtWidgets import QApplication, QWidget

    current: Any = widget
    while True:
        if not isinstance(current, QWidget):
            break
        parent: Any = current.parent()
        if parent is None:
            break

        # Try to find signal/method on parent
        target = getattr(parent, name, None)
        if target is not None:
            if is_signal(target) or callable(target):
                return target

        current = parent

    # Fallback: check QApplication.instance()
    app = QApplication.instance()
    if app is not None:
        target = getattr(app, name, None)
        if target is not None:
            if is_signal(target) or callable(target):
                return target

    return None


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

    Handles both regular annotations and string annotations (from
    `from __future__ import annotations`).

    Args:
        cls: The class to process.
        config_attr: Name of the config attribute on the class (e.g., "_qtpie_config").
        variable_type: The Variable type to check for.
        descriptor_factory: Factory to create descriptors (e.g., _RequiredBindingDescriptor).
    """
    from typing import Any, get_args, get_origin, get_type_hints

    raw_annotations = getattr(cls, "__annotations__", {})
    config = getattr(cls, config_attr)

    # Try to get resolved type hints (handles string annotations from __future__)
    # Fall back to raw annotations if get_type_hints fails
    try:
        # Include Variable type in namespace for resolution
        namespace = {"Variable": variable_type}
        # Also include the class itself for self-references
        namespace[cls.__name__] = cls
        resolved_annotations = get_type_hints(cls, localns=namespace, include_extras=True)
    except Exception:
        # If get_type_hints fails (e.g., unresolvable forward refs), use raw
        resolved_annotations = raw_annotations

    for name in raw_annotations:
        # Get resolved annotation if available, otherwise use raw
        annotation = resolved_annotations.get(name, raw_annotations[name])

        # Handle string annotations that weren't resolved
        if isinstance(annotation, str):
            # Check if the string looks like a Variable annotation
            if not (annotation.startswith("Variable[") or annotation == "Variable"):
                continue
        else:
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
        if not isinstance(annotation, str):
            origin = get_origin(annotation)
            if origin is variable_type:
                args = get_args(annotation)
                inner_type = args[0] if args else None

        # Create descriptor
        descriptor = descriptor_factory(name, inner_type)
        setattr(cls, name, descriptor)
