"""Path resolver for binding paths."""

# pyright: reportPrivateUsage=false

from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING, Any, cast

from observant import Observable, ObservableDict, ObservableList, ObservableProxy, ObservableSet

if TYPE_CHECKING:
    from qtpie.variable import Variable
    from qtpie.widget import Widget
    from qtpie.window import Window

# Return type for binding sources
type BindingSource = Variable[Any] | Observable[Any] | ObservableList[Any] | ObservableDict[Any, Any] | ObservableSet[Any] | ObservableProxy[Any]


def resolve_binding_source(widget: Widget[Any] | Window[Any], path: str) -> BindingSource | None:
    """Resolve a binding path to its source Observable/Variable.

    Resolution order (on widget, then parent hierarchy):
    1. Original path: self.<path> exactly as written (e.g., '_dogs' -> widget._dogs)
    2. Stripped path: self.<path_without_underscore> (e.g., '_dogs' -> widget.dogs)
    3. Record: self.record.<path> if Widget[T]
    4. Underscore fallback: self._<path> if no match (e.g., 'name' -> widget._name)
    5. Parent hierarchy: Walk up parent() chain looking for Variables

    'dog.breed?.name' is passed through to observable_for_path().

    Args:
        widget: The Widget instance to resolve from.
        path: The binding path like 'name', '_dogs', 'dog.breed', or 'dog.breed?.name'.

    Returns:
        The Variable, Observable, or ObservableProxy at the path, or None if not found.
    """
    from qtpie.variable import Variable

    # Handle #record prefix - strip it and resolve through record directly
    # e.g., "#record?.collection?.items" -> resolve "collection?.items" on the record
    if path.startswith("#record"):
        # Strip "#record" and any following "." or "?."
        record_path = path[7:]  # len("#record") == 7
        if record_path.startswith("?."):
            record_path = record_path[2:]
        elif record_path.startswith("."):
            record_path = record_path[1:]

        # If there's a path after #record, resolve it on the record proxy
        if record_path and hasattr(widget, "_qtpie_config"):
            config = widget._qtpie_config
            if config.record_type is not None:
                record = widget.record
                proxy = record.observable
                target = object.__getattribute__(proxy, "_target")
                if target is not None:
                    try:
                        return proxy.observable_for_path(record_path)
                    except ValueError:
                        return None
        # If just "#record" with no path, return the record proxy itself
        elif not record_path and hasattr(widget, "_qtpie_config"):
            config = widget._qtpie_config
            if config.record_type is not None:
                record = widget.record
                return record.observable
        return None

    # Keep original path for exact matching, strip for fallback lookup
    original_path = path
    lookup_path = path.lstrip("_")
    has_leading_underscore = path.startswith("_")

    # Split into first segment and rest (for nested paths)
    original_parts = original_path.replace("?.", ".").split(".", 1)
    original_first = original_parts[0]
    rest = original_parts[1] if len(original_parts) > 1 else None

    stripped_parts = lookup_path.replace("?.", ".").split(".", 1)
    stripped_first = stripped_parts[0]
    underscore_first = f"_{stripped_first}"

    # Helper to check if an attribute is a valid binding source on any object
    def try_resolve_attr_on(obj: Any, attr_name: str, nested_rest: str | None = None) -> BindingSource | None:
        try:
            if not hasattr(obj, attr_name):
                return None
            raw_attr = getattr(obj, attr_name)
        except Exception:
            return None
        if isinstance(raw_attr, Variable):
            attr = cast("Variable[Any]", raw_attr)
            if nested_rest:
                # Check if rest is a property on Variable itself (e.g., validation_error_messages)
                if hasattr(attr, nested_rest) and not nested_rest.startswith("_"):
                    prop_val = getattr(attr, nested_rest)
                    if isinstance(prop_val, (Observable, ObservableList, ObservableDict, ObservableSet, ObservableProxy)):
                        return cast(BindingSource, prop_val)
                # Nested path into Variable[ComplexType]
                observable = attr.observable
                if isinstance(observable, ObservableProxy):
                    try:
                        return observable.observable_for_path(nested_rest)
                    except ValueError:
                        return None
            return attr
        # Handle Observable properties directly (e.g., is_dirty, is_valid)
        if isinstance(raw_attr, ObservableProxy):
            # If there's a nested path, resolve it on the proxy
            if nested_rest:
                try:
                    return raw_attr.observable_for_path(nested_rest)
                except ValueError:
                    return None
            return cast(BindingSource, raw_attr)
        if isinstance(raw_attr, (Observable, ObservableList, ObservableDict, ObservableSet)):
            return cast(BindingSource, raw_attr)
        return None

    # Try exact and stripped variants on a given object (NOT underscore fallback)
    def try_exact_variants_on(obj: Any) -> BindingSource | None:
        # 1. Try original path first (e.g., '_dogs' -> obj._dogs)
        result = try_resolve_attr_on(obj, original_first, rest)
        if result is not None:
            return result

        # 2. Try stripped path if different (e.g., '_dogs' stripped to 'dogs' -> obj.dogs)
        if has_leading_underscore:
            result = try_resolve_attr_on(obj, stripped_first, rest)
            if result is not None:
                return result

        return None

    # Try all name variants including underscore fallback (for parent hierarchy)
    def try_all_variants_on(obj: Any) -> BindingSource | None:
        # 1. Try exact variants first
        result = try_exact_variants_on(obj)
        if result is not None:
            return result

        # 2. Try underscore fallback (e.g., 'name' -> obj._name)
        if not has_leading_underscore:
            result = try_resolve_attr_on(obj, underscore_first, rest)
            if result is not None:
                return result

        return None

    # First, try exact match on the widget itself (NOT underscore fallback)
    result = try_exact_variants_on(widget)
    if result is not None:
        return result

    # Ensure _qtpie state exists for widget-level property access
    from qtpie.qt_pie_state import QtPieState

    if not hasattr(widget, "_qtpie"):
        widget._qtpie = QtPieState(widget)  # type: ignore[attr-defined]

    # Try record if Widget[T] - use ORIGINAL path first, then stripped
    if hasattr(widget, "_qtpie_config"):
        config = widget._qtpie_config
        if config.record_type is not None:
            record = widget.record
            proxy = record.observable
            # Only try record binding if the record target is not None
            # Otherwise observable_for_path returns Observable(None) for any path
            # which would incorrectly bind and clear widget values
            target = object.__getattribute__(proxy, "_target")
            if target is not None:

                def _get_enum_field_observable(path_str: str, parent_proxy: ObservableProxy[Any]) -> BindingSource | None:
                    """Get field Observable for enum values (simple or nested paths).

                    For selection bindings to work with enums, we need the field Observable
                    (which has .get()/.set()) instead of the ObservableProxy wrapper.

                    For simple paths like "body_type", use the record proxy directly.
                    For nested paths like "auth.type", find the parent proxy and get the field from there.
                    """
                    try:
                        result = parent_proxy.observable_for_path(path_str)
                    except ValueError:
                        # Can't traverse this path (e.g., path goes through an Observable)
                        return None
                    if not isinstance(result, ObservableProxy):
                        return None

                    wrapped: Any = object.__getattribute__(result, "_target")
                    if not isinstance(wrapped, Enum):
                        return None

                    # Handle simple paths (no dots) - field is on the record proxy
                    # Remove optional chaining markers for path analysis
                    clean_path = path_str.replace("?.", ".")
                    if "." not in clean_path:
                        return parent_proxy._get_or_create_field_observable(path_str)

                    # Handle nested paths like "auth.type" - field is on the parent object's proxy
                    # Split to get field name (we reconstruct parent path with markers below)
                    parts = clean_path.rsplit(".", 1)
                    field_name = parts[1]

                    # Reconstruct parent path preserving optional markers
                    # e.g., "auth?.type" -> parent_path_with_markers = "auth?"
                    parent_path_with_markers = path_str[: path_str.rfind(field_name) - 1]
                    if parent_path_with_markers.endswith("?"):
                        parent_path_with_markers = parent_path_with_markers[:-1]

                    try:
                        nested_proxy = parent_proxy.observable_for_path(parent_path_with_markers)
                        if isinstance(nested_proxy, ObservableProxy):
                            return nested_proxy._get_or_create_field_observable(field_name)
                    except (AttributeError, ValueError):
                        pass

                    return None

                try:
                    # Try original path first (e.g., "dogs" or "_dogs" or "auth.type")
                    # Check if it's an enum field that needs special handling
                    enum_obs = _get_enum_field_observable(original_path, proxy)
                    if enum_obs is not None:
                        return enum_obs

                    # Not an enum, return the normal result
                    result = proxy.observable_for_path(original_path)
                    return cast(BindingSource, result)
                except (AttributeError, ValueError):
                    # AttributeError: Field not found on record
                    # ValueError: Can't traverse path through Observable (e.g., nested path through atomic value)
                    pass
                # If original path had underscore, also try stripped path on record
                if has_leading_underscore:
                    try:
                        enum_obs = _get_enum_field_observable(lookup_path, proxy)
                        if enum_obs is not None:
                            return enum_obs

                        result = proxy.observable_for_path(lookup_path)
                        return cast(BindingSource, result)
                    except (AttributeError, ValueError):
                        # AttributeError: Field not found on record
                        # ValueError: Can't traverse path through Observable
                        pass

    # Underscore fallback on widget itself (e.g., 'name' -> widget._name)
    # This comes AFTER record check to prioritize record fields
    if not has_leading_underscore:
        result = try_resolve_attr_on(widget, underscore_first, rest)
        if result is not None:
            return result

    # Walk up parent hierarchy looking for Variables
    from qtpy.QtWidgets import QApplication

    current: Any = widget
    while True:
        if not hasattr(current, "parent") or not callable(current.parent):
            break
        parent: Any = current.parent()
        if parent is None:
            break

        # Try all name variants on parent
        result = try_all_variants_on(parent)
        if result is not None:
            return result

        current = parent

    # Fallback: check QApplication.instance()
    app = QApplication.instance()
    if app is not None:
        result = try_all_variants_on(app)
        if result is not None:
            return result

    return None
