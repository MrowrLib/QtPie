"""QtPie utility modules for shared functionality."""

from qtpie.utils.common import (
    HANDLER_SPEC_RE,
    PLACEHOLDER_RE,
    detect_required_bindings,
    is_primitive_type,
    is_signal,
    is_signal_on_type,
)
from qtpie.utils.layouts import (
    IconType,
    add_to_layout,
    apply_layout_margins,
    apply_object_name_and_classes,
    apply_widget_props,
    create_layout,
    resolve_icon,
)
from qtpie.utils.properties import resolve_nested_property

__all__ = [
    "HANDLER_SPEC_RE",
    "PLACEHOLDER_RE",
    "IconType",
    "add_to_layout",
    "apply_layout_margins",
    "apply_object_name_and_classes",
    "apply_widget_props",
    "create_layout",
    "detect_required_bindings",
    "is_primitive_type",
    "is_signal",
    "is_signal_on_type",
    "resolve_icon",
    "resolve_nested_property",
]
