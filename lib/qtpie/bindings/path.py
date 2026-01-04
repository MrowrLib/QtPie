"""Path resolver for binding paths."""

# pyright: reportPrivateUsage=false

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

from observant import Observable, ObservableDict, ObservableList, ObservableProxy

if TYPE_CHECKING:
    from qtpie.variable import Variable
    from qtpie.widget import Widget

# Return type for binding sources
type BindingSource = Variable[Any] | Observable[Any] | ObservableList[Any] | ObservableDict[Any, Any] | ObservableProxy[Any]


def resolve_binding_source(widget: Widget[Any], path: str) -> BindingSource | None:
    """Resolve a binding path to its source Observable/Variable.

    Resolution order:
    1. self.<path> as attribute (Variable or regular value)
    2. self.record.<path> if Widget[T]

    The path is normalized by stripping leading underscores.
    'dog.breed?.name' is passed through to observable_for_path().

    Args:
        widget: The Widget instance to resolve from.
        path: The binding path like 'name', 'dog.breed', or 'dog.breed?.name'.

    Returns:
        The Variable, Observable, or ObservableProxy at the path, or None if not found.
    """
    from qtpie.variable import Variable

    # Strip leading underscore for field lookup
    lookup_path = path.lstrip("_")

    # Split into first segment and rest
    parts = lookup_path.replace("?.", ".").split(".", 1)
    first = parts[0]
    rest = parts[1] if len(parts) > 1 else None

    # Also check with underscore prefix for private fields
    first_with_underscore = f"_{first}"

    # Try direct attribute (with underscore first, then without)
    for attr_name in [first_with_underscore, first]:
        if hasattr(widget, attr_name):
            raw_attr = getattr(widget, attr_name)
            if isinstance(raw_attr, Variable):
                attr = cast("Variable[Any]", raw_attr)
                if rest:
                    # Nested path into Variable[ComplexType]
                    # Rebuild the path with optional chaining preserved
                    nested_path = path.lstrip("_").split(".", 1)[1] if "." in path.lstrip("_") else ""
                    observable = attr.observable
                    if nested_path and isinstance(observable, ObservableProxy):
                        return observable.observable_for_path(nested_path)
                return attr
            # Regular attribute - not bindable for now
            break

    # Try record if Widget[T]
    if hasattr(widget, "_qtpie_config"):
        config = widget._qtpie_config
        if config.record_type is not None:
            try:
                record = widget.record
                # RecordVariable.observable always returns ObservableProxy
                return record.observable.observable_for_path(lookup_path)
            except (TypeError, AttributeError):
                # record access failed (e.g., no type param)
                pass

    return None
