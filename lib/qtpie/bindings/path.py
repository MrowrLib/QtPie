"""Path resolver for binding paths."""

# pyright: reportPrivateUsage=false

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

from observant import Observable, ObservableDict, ObservableList, ObservableProxy, ObservableSet

if TYPE_CHECKING:
    from qtpie.variable import Variable
    from qtpie.widget import Widget

# Return type for binding sources
type BindingSource = Variable[Any] | Observable[Any] | ObservableList[Any] | ObservableDict[Any, Any] | ObservableSet[Any] | ObservableProxy[Any]


def resolve_binding_source(widget: Widget[Any], path: str) -> BindingSource | None:
    """Resolve a binding path to its source Observable/Variable.

    Resolution order:
    1. Original path: self.<path> exactly as written (e.g., '_dogs' -> widget._dogs)
    2. Stripped path: self.<path_without_underscore> (e.g., '_dogs' -> widget.dogs)
    3. Record: self.record.<path> if Widget[T]
    4. Underscore fallback: self._<path> if no match (e.g., 'name' -> widget._name)

    'dog.breed?.name' is passed through to observable_for_path().

    Args:
        widget: The Widget instance to resolve from.
        path: The binding path like 'name', '_dogs', 'dog.breed', or 'dog.breed?.name'.

    Returns:
        The Variable, Observable, or ObservableProxy at the path, or None if not found.
    """
    from qtpie.variable import Variable

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

    # Helper to check if an attribute is a valid binding source
    def try_resolve_attr(attr_name: str, nested_rest: str | None = None) -> BindingSource | None:
        if hasattr(widget, attr_name):
            raw_attr = getattr(widget, attr_name)
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
                        return observable.observable_for_path(nested_rest)
                return attr
            # Handle Observable properties directly (e.g., is_dirty, is_valid)
            if isinstance(raw_attr, (Observable, ObservableList, ObservableDict, ObservableSet, ObservableProxy)):
                return cast(BindingSource, raw_attr)
        return None

    # 1. Try original path first (e.g., '_dogs' -> widget._dogs)
    result = try_resolve_attr(original_first, rest)
    if result is not None:
        return result

    # 2. Try stripped path if different (e.g., '_dogs' stripped to 'dogs' -> widget.dogs)
    if has_leading_underscore:
        result = try_resolve_attr(stripped_first, rest)
        if result is not None:
            return result

    # Ensure _qtpie state exists for widget-level property access
    from qtpie.state import QtPieState

    if not hasattr(widget, "_qtpie"):
        widget._qtpie = QtPieState(widget)  # type: ignore[attr-defined]

    # 3. Try record if Widget[T] - use ORIGINAL path first, then stripped
    if hasattr(widget, "_qtpie_config"):
        config = widget._qtpie_config
        if config.record_type is not None:
            record = widget.record
            proxy = record.observable
            try:
                # Try original path first (e.g., "dogs" or "_dogs")
                result = proxy.observable_for_path(original_path)
                return result
            except AttributeError:
                # Field not found on record, continue to fallback
                pass
            # If original path had underscore, also try stripped path on record
            if has_leading_underscore:
                try:
                    result = proxy.observable_for_path(lookup_path)
                    return result
                except AttributeError:
                    pass

    # 4. Underscore fallback (e.g., 'name' -> widget._name)
    if not has_leading_underscore:
        first_with_underscore = f"_{stripped_first}"
        result = try_resolve_attr(first_with_underscore, rest)
        if result is not None:
            return result

    return None
