"""Shared utilities for repeater classes."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from observant import Observable, ObservableProxy
from qtpy.QtWidgets import QHBoxLayout, QVBoxLayout, QWidget

from qtpie.utils.common import HANDLER_SPEC_RE, PLACEHOLDER_RE, is_primitive_type
from qtpie.utils.properties import resolve_nested_property


def resolve_sort[T](
    sort: bool | str | Callable[[T], Any] | None,
    parent_widget: Any | None,
) -> bool | Callable[[T], Any] | None:
    """Resolve sort= parameter, converting string method names to callables.

    Args:
        sort: The sort parameter value.
        parent_widget: The parent widget for resolving method names.

    Returns:
        Resolved sort value (bool, callable, or None).

    Raises:
        AttributeError: If a string method name cannot be resolved.
    """
    if sort is None or isinstance(sort, bool) or callable(sort):
        return sort
    # String method name - resolve from parent widget
    if parent_widget is not None:
        method = getattr(parent_widget, sort, None)
        if method is not None and callable(method):
            return method
        raise AttributeError(f"sort='{sort}' - method not found on {type(parent_widget).__name__}")
    raise AttributeError(f"sort='{sort}' - cannot resolve method name without parent widget")


def create_item_wrapper(
    item: Any,
    item_type: type | None,
) -> Observable[Any] | ObservableProxy[Any]:
    """Create the appropriate wrapper for an item.

    Args:
        item: The item to wrap.
        item_type: The type of the item.

    Returns:
        Observable for primitives, ObservableProxy for objects.
    """
    if is_primitive_type(item_type):
        return Observable(item)
    else:
        return ObservableProxy(item)


def create_styled_widget(
    widget_type: type,
    widget_args: tuple[Any, ...],
    widget_kwargs: dict[str, Any],
    object_name: str | None,
    css_classes: list[str],
    widget_props: dict[str, Any],
) -> QWidget:
    """Create a widget with styling applied.

    This is the shared widget creation logic for repeaters.

    Args:
        widget_type: The widget class to instantiate.
        widget_args: Positional arguments for constructor.
        widget_kwargs: Keyword arguments for constructor.
        object_name: objectName to set (if any).
        css_classes: CSS classes to apply.
        widget_props: Widget properties to apply via setXxx().

    Returns:
        The created and styled widget.
    """
    widget = widget_type(*widget_args, **widget_kwargs)

    # Apply objectName if specified
    if object_name is not None:
        widget.setObjectName(object_name)

    # Apply CSS classes if specified
    if css_classes:
        from qtpie.styles import set_classes

        set_classes(widget, list(css_classes))

    # Apply widget props (styleSheet="X" → setStyleSheet("X"))
    for prop_name, value in widget_props.items():
        setter_name = f"set{prop_name[0].upper()}{prop_name[1:]}"
        setter = getattr(widget, setter_name, None)
        if setter is not None and callable(setter):
            setter(value)

    return widget


def setup_repeater_layout(
    parent: QWidget,
    layout_type: str,
) -> QVBoxLayout | QHBoxLayout:
    """Set up a repeater's layout.

    Args:
        parent: The parent widget to set layout on.
        layout_type: "vertical" or "horizontal".

    Returns:
        The created layout.
    """
    if layout_type == "horizontal":
        layout = QHBoxLayout(parent)
    else:
        layout = QVBoxLayout(parent)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(0)
    return layout


def create_signal_handler(
    spec: str | Callable[..., Any],
    wrapper: Observable[Any] | ObservableProxy[Any],
    widget: QWidget,
    parent_widget: Any | None,
    *,
    index_holder: list[int] | None = None,
    key_wrapper: Observable[Any] | ObservableProxy[Any] | None = None,
) -> Callable[..., Any]:
    """Create a signal handler that resolves placeholders at call time.

    This is shared logic for WidgetRepeater, DictWidgetRepeater, and SetWidgetRepeater.

    Supports:
    - "method_name" → passes signal's args only (shorthand for method_name(#args))
    - "method_name()" → passes nothing
    - "method_name(#args)" → passes signal's args
    - "method_name(#value, #index, #args)" → passes value, index, then signal args

    Placeholders:
    - #value: The item/value
    - #widget: The child widget instance
    - #index: The item index (WidgetRepeater only)
    - #key: The dict key (DictWidgetRepeater only)
    - #args: Spread of signal's own arguments

    Args:
        spec: Handler specification (method name or callable).
        wrapper: Observable or ObservableProxy wrapping the value.
        widget: The child widget instance.
        parent_widget: The parent Widget instance for resolving handler methods.
        index_holder: Optional mutable [int] for list index (WidgetRepeater).
        key_wrapper: Optional key wrapper (DictWidgetRepeater).

    Returns:
        Callable handler function.

    Raises:
        ValueError: If spec is invalid or parent_widget is missing.
        AttributeError: If method not found on parent_widget.
    """
    if callable(spec):
        return spec

    # Parse handler spec
    match = HANDLER_SPEC_RE.match(spec)
    if not match:
        raise ValueError(f"Invalid handler spec: {spec}")

    method_name = match.group(1)
    args_spec = match.group(2)  # May be None (no parens) or "" (empty parens)

    # Get the method from parent widget
    if parent_widget is None:
        raise ValueError(f"Cannot connect signal: no parent widget for handler '{method_name}'")

    parent_method = getattr(parent_widget, method_name, None)
    if parent_method is None:
        raise AttributeError(f"{type(parent_widget).__name__} has no method '{method_name}' for signal connection")
    if not callable(parent_method):
        raise AttributeError(f"{type(parent_widget).__name__}.{method_name} is not callable")

    # Determine what args to pass
    if args_spec is None:
        # No parens: "method_name" → pass signal args only (like #args)
        placeholders = ["#args"]
    elif args_spec.strip() == "":
        # Empty parens: "method_name()" → pass nothing
        placeholders = []
    else:
        # Parse placeholders: "method_name(#value, #index, #args)"
        placeholders = [p.strip() for p in args_spec.split(",") if p.strip()]

    # Create the handler closure
    def handler(*signal_args: Any) -> Any:
        call_args: list[Any] = []
        for placeholder in placeholders:
            if placeholder == "#value":
                # Get the item/value
                if isinstance(wrapper, Observable):
                    call_args.append(wrapper.get())
                else:
                    call_args.append(wrapper.unwrap())
            elif placeholder == "#widget":
                call_args.append(widget)
            elif placeholder == "#index":
                if index_holder is not None:
                    call_args.append(index_holder[0])
                else:
                    call_args.append(-1)  # No index available (e.g., SetWidgetRepeater)
            elif placeholder == "#key":
                if key_wrapper is not None:
                    if isinstance(key_wrapper, Observable):
                        call_args.append(key_wrapper.get())
                    else:
                        call_args.append(key_wrapper.unwrap())
                else:
                    call_args.append(None)  # No key available
            elif placeholder == "#args":
                # Spread signal args
                call_args.extend(signal_args)
            else:
                # Unknown placeholder - pass as-is (could be a literal)
                call_args.append(placeholder)

        return parent_method(*call_args)

    return handler


def bind_callable_format(
    widget: QWidget,
    wrapper: Observable[Any] | ObservableProxy[Any],
    formatter: Callable[[Any], str],
) -> None:
    """Bind a widget to a callable formatter (one-way only).

    Shared binding logic for repeaters using callable formatters.

    Args:
        widget: The widget to bind.
        wrapper: Observable or ObservableProxy wrapping the item.
        formatter: Callable that takes the item and returns a string.
    """
    from qtpie.bindings.registry import get_binding_registry

    registry = get_binding_registry()
    default_prop = registry.get_default_prop(widget)
    adapter = registry.get(widget, default_prop)
    if adapter is None or adapter.setter is None:
        return

    setter = adapter.setter

    def compute_value() -> str:
        if isinstance(wrapper, Observable):
            item = wrapper.get()
        else:
            item = wrapper.unwrap()
        return formatter(item)

    # Set initial value
    setter(widget, compute_value())

    # Subscribe to changes
    def on_change(_: Any) -> None:
        setter(widget, compute_value())

    if isinstance(wrapper, Observable):
        wrapper.on_change(on_change)
    else:
        wrapper.on_change(lambda: on_change(None))


def bind_computed_format(
    widget: QWidget,
    wrapper: Observable[Any] | ObservableProxy[Any],
    format_str: str,
    *,
    index_holder: list[int] | None = None,
    key_wrapper: Observable[Any] | ObservableProxy[Any] | None = None,
) -> None:
    """Bind a widget to a computed format string (one-way only).

    Shared binding logic for repeaters using format strings.

    Supports placeholders:
    - {#self} - the item value
    - {#index} - the item index (WidgetRepeater only)
    - {#key} - the dict key (DictWidgetRepeater only)
    - {#value} - the dict value (DictWidgetRepeater only)
    - {#self.property} - nested property on item
    - {property} - item.property (for objects)
    - {property.nested} - nested property access

    Args:
        widget: The widget to bind.
        wrapper: Observable or ObservableProxy wrapping the value.
        format_str: Format string with placeholders.
        index_holder: Optional mutable [int] for list index.
        key_wrapper: Optional key wrapper for dict repeaters.
    """
    from qtpie.bindings.registry import get_binding_registry

    registry = get_binding_registry()
    default_prop = registry.get_default_prop(widget)
    adapter = registry.get(widget, default_prop)
    if adapter is None or adapter.setter is None:
        return

    setter = adapter.setter

    def compute_value() -> str:
        result = format_str

        for match in PLACEHOLDER_RE.finditer(format_str):
            placeholder = match.group(1)
            full_match = match.group(0)

            value: Any
            if placeholder == "#self" or placeholder == "#value":
                if isinstance(wrapper, Observable):
                    value = wrapper.get()
                else:
                    value = wrapper.unwrap()
            elif placeholder == "#index":
                if index_holder is not None:
                    value = index_holder[0]
                else:
                    value = "<no-index>"
            elif placeholder == "#key":
                if key_wrapper is not None:
                    if isinstance(key_wrapper, Observable):
                        value = key_wrapper.get()
                    else:
                        value = key_wrapper.unwrap()
                else:
                    value = "<no-key>"
            elif placeholder.startswith("#self."):
                prop_path = placeholder[6:]
                if isinstance(wrapper, Observable):
                    value = resolve_nested_property(wrapper.get(), prop_path)
                else:
                    value = resolve_nested_property(wrapper, prop_path)
            elif isinstance(wrapper, ObservableProxy):
                value = resolve_nested_property(wrapper, placeholder)
            else:
                value = f"<unknown:{placeholder}>"

            result = result.replace(full_match, str(value), 1)

        return result

    # Set initial value
    setter(widget, compute_value())

    # Subscribe to changes
    def on_change(_: Any) -> None:
        setter(widget, compute_value())

    if isinstance(wrapper, Observable):
        wrapper.on_change(on_change)
    else:
        # For ObservableProxy, subscribe to property observables mentioned
        for match in PLACEHOLDER_RE.finditer(format_str):
            placeholder = match.group(1)
            if placeholder in ("#self", "#index", "#key", "#value"):
                continue
            if placeholder.startswith("#self."):
                prop_name = placeholder[6:].split(".")[0]
                prop_obs: Any = getattr(wrapper, prop_name, None)
                if isinstance(prop_obs, Observable):
                    prop_obs.on_change(on_change)  # pyright: ignore[reportUnknownMemberType]
            elif not placeholder.startswith("#"):
                prop_name = placeholder.split(".")[0]
                prop_obs = getattr(wrapper, prop_name, None)
                if isinstance(prop_obs, Observable):
                    prop_obs.on_change(on_change)  # pyright: ignore[reportUnknownMemberType]

    # Also subscribe key wrapper if provided
    if key_wrapper is not None:
        if isinstance(key_wrapper, Observable):
            key_wrapper.on_change(on_change)
        else:
            key_wrapper.on_change(lambda: on_change(None))


def rebind_child_widgets(parent: QWidget) -> None:
    """Re-apply bindings on child Widget[T] instances that bind to parent's record.

    When a parent Widget[T] gets its record set AFTER its children were created,
    those children may have failed to resolve their bind="record" bindings.
    This method walks through child widgets and re-applies their bindings.

    Args:
        parent: The parent widget whose children should be rebound.
    """
    from qtpie.bindings.apply import apply_auto_bindings
    from qtpie.bindings.bind import is_widget_with_record
    from qtpie.variable import RecordVariable

    for child in parent.findChildren(QWidget):
        child_config = getattr(type(child), "_qtpie_config", None)
        if child_config is None:
            continue

        # Check if this child has a record type
        child_record_type = getattr(child_config, "record_type", None)
        if child_record_type is None:
            continue

        # Check the child's fields for bind="record" patterns
        fields = getattr(child_config, "fields", {})
        needs_rebind = False
        for field_info in fields.values():
            bind_val = getattr(field_info, "bind", None)
            if bind_val == "record":
                needs_rebind = True
                break

        if needs_rebind or is_widget_with_record(child):
            # The child Widget[T] should inherit parent's record
            parent_record = getattr(parent, "record", None)
            if parent_record is not None and isinstance(parent_record, RecordVariable):
                # Share the parent's ObservableProxy with the child
                child_record_var: RecordVariable[Any] = RecordVariable(parent_record.observable)  # pyright: ignore[reportUnknownMemberType, reportUnknownArgumentType]
                child.record = child_record_var  # type: ignore[union-attr]
                # Re-apply bindings on child
                apply_auto_bindings(child, child_config)  # type: ignore[arg-type]


def connect_child_signals(
    widget: QWidget,
    wrapper: Observable[Any] | ObservableProxy[Any],
    signal_connections: dict[str, str | Callable[..., Any]],
    parent_widget: Any | None,
    *,
    index_holder: list[int] | None = None,
    key_wrapper: Observable[Any] | ObservableProxy[Any] | None = None,
) -> None:
    """Connect child widget signals to parent handlers.

    Shared logic for all repeater classes.

    Args:
        widget: The child widget instance.
        wrapper: Observable or ObservableProxy wrapping the item/value.
        signal_connections: Dict of signal_name -> handler_spec.
        parent_widget: The parent Widget instance for resolving handlers.
        index_holder: Optional mutable [int] for list index (WidgetRepeater).
        key_wrapper: Optional key wrapper (DictWidgetRepeater).
    """
    if not signal_connections or parent_widget is None:
        return

    for signal_name, handler_spec in signal_connections.items():
        signal = getattr(widget, signal_name, None)
        if signal is None:
            continue

        handler = create_signal_handler(
            handler_spec,
            wrapper,
            widget,
            parent_widget,
            index_holder=index_holder,
            key_wrapper=key_wrapper,
        )
        signal.connect(handler)
