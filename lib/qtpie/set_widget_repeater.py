"""SetWidgetRepeater - Container that manages repeated widgets bound to set items."""

from __future__ import annotations

import re
from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from observant import Observable, ObservableProxy, ObservableSet
from qtpy.QtWidgets import QHBoxLayout, QVBoxLayout, QWidget

from .bindings import bind
from .variable import Variable

if TYPE_CHECKING:
    from .widget import Widget

# Regex to find placeholders like {#self}, {name}, {age}, {#self.age}
# Note: No {#index} for sets - sets are unordered
_PLACEHOLDER_RE = re.compile(r"\{(#?\w+(?:\.\w+)*)\}")

# Regex to parse handler spec like "method_name(#value, #args)"
_HANDLER_SPEC_RE = re.compile(r"^(\w+)(?:\((.*)\))?$")


def _is_primitive_type(t: type | None) -> bool:
    """Check if type is a primitive."""
    return t in (str, int, float, bool, type(None))


class SetWidgetRepeater[T](QWidget):
    """Container that manages repeated widgets bound to set items.

    Creates one widget per set item. Uses granular callbacks (on_add,
    on_remove, on_clear) to efficiently sync the widget list
    with the underlying ObservableSet.

    Key differences from WidgetRepeater:
    - No {#index} placeholder (sets have no indices)
    - Display order: insertion order by default, or sorted if sort= is set
    - Uses widget_for_item(item) instead of widget_at(index)

    Usage:
        # Variable[set[int], QLabel] creates this automatically
        # Each QLabel is bound to one set item
    """

    def __init__(
        self,
        observable_set: ObservableSet[T],
        item_type: type | None,
        widget_type: type,
        widget_args: tuple[Any, ...] = (),
        widget_kwargs: dict[str, Any] | None = None,
        widget_props: dict[str, Any] | None = None,
        bind_expr: str | Callable[[T], str] = "{#self}",
        sort: bool | str | Callable[[T], Any] | None = None,
        layout_type: str = "vertical",
        object_name: str | None = None,
        css_classes: list[str] | None = None,
        signal_connections: dict[str, str | Callable[..., Any]] | None = None,
        parent_widget: Widget[Any] | None = None,
    ) -> None:
        """Initialize the set widget repeater.

        Args:
            observable_set: The ObservableSet to sync with.
            item_type: The type of items in the set (e.g., int, str, Dog).
            widget_type: The widget type to create for each item.
            widget_args: Positional args for widget constructor.
            widget_kwargs: Keyword args for widget constructor.
            widget_props: Widget properties to apply via setXxx() after creation.
            bind_expr: Binding expression or callable formatter (default "{#self}").
            sort: Sorting option - False/None (insertion order), True (sorted()),
                  or callable (key function for sorted()).
            layout_type: "vertical" or "horizontal".
            object_name: objectName to set on each created widget.
            css_classes: CSS classes to apply to each created widget.
            signal_connections: Signal connections from child widget to parent handlers.
            parent_widget: The parent Widget instance for resolving handler methods.
        """
        super().__init__()

        self._obs_set = observable_set
        self._item_type = item_type
        self._widget_type = widget_type
        self._widget_args = widget_args
        self._widget_kwargs = widget_kwargs or {}
        self._widget_props = widget_props or {}
        self._bind_expr: str | Callable[[T], str] = bind_expr
        # Resolve sort= string method name to callable
        self._sort: bool | Callable[[T], Any] | None = self._resolve_sort(sort, parent_widget)
        self._is_primitive = _is_primitive_type(item_type)
        self._object_name = object_name
        self._css_classes = css_classes or []
        self._signal_connections = signal_connections or {}
        self._parent_widget = parent_widget

        # Track: item -> (widget, item_wrapper)
        # item_wrapper is Observable[T] for primitives, ObservableProxy[T] for objects
        self._entries: dict[T, tuple[QWidget, Observable[Any] | ObservableProxy[Any]]] = {}
        # Maintain insertion order for layout (like dict's _key_order)
        self._item_order: list[T] = []

        # Setup layout
        if layout_type == "horizontal":
            self._layout = QHBoxLayout(self)
        else:
            self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)

        # Create initial widgets for existing items (in display order)
        for item in self._get_display_order(list(observable_set)):
            self._item_order.append(item)
            self._create_and_add_widget(item)

        # Subscribe to granular callbacks
        observable_set.on_add(self._on_add)
        observable_set.on_remove(self._on_remove)
        observable_set.on_clear(self._on_clear)

    def _resolve_sort(
        self,
        sort: bool | str | Callable[[T], Any] | None,
        parent_widget: Widget[Any] | None,
    ) -> bool | Callable[[T], Any] | None:
        """Resolve sort= parameter, converting string method names to callables."""
        if sort is None or isinstance(sort, bool) or callable(sort):
            return sort
        # String method name - resolve from parent widget
        # At this point, sort must be a string (only remaining type)
        if parent_widget is not None:
            method = getattr(parent_widget, sort, None)
            if method is not None and callable(method):
                return method
            raise AttributeError(f"sort='{sort}' - method not found on {type(parent_widget).__name__}")
        raise AttributeError(f"sort='{sort}' - cannot resolve method name without parent widget")

    def _get_display_order(self, items: list[T]) -> list[T]:
        """Get items in display order based on sort= setting.

        Args:
            items: Items to order.

        Returns:
            Items in display order.
        """
        if not self._sort:
            # No sorting - return as-is (insertion order)
            return items

        if self._sort is True:
            # Use default sorted()
            try:
                return sorted(items)  # type: ignore[type-var]
            except TypeError:
                # Items not comparable - fall back to original order
                return items

        # Custom key function
        try:
            return sorted(items, key=self._sort)  # type: ignore[type-var]
        except TypeError:
            return items

    def _find_insert_position(self, item: T) -> int:
        """Find where to insert a new item in the layout based on sort order."""
        if not self._sort:
            # No sorting - append at end
            return len(self._item_order)

        # Get display order including new item
        all_items = list(self._item_order) + [item]
        ordered = self._get_display_order(all_items)

        # Find position of item in ordered list
        try:
            return ordered.index(item)
        except ValueError:
            return len(self._item_order)

    def _create_item_wrapper(self, item: T) -> Observable[Any] | ObservableProxy[Any]:
        """Create the appropriate wrapper for an item."""
        if self._is_primitive:
            return Observable(item)
        else:
            return ObservableProxy(item)

    def _create_widget_for_item(self) -> QWidget:
        """Create a new widget instance."""
        widget = self._widget_type(*self._widget_args, **self._widget_kwargs)

        # Apply objectName if specified
        if self._object_name is not None:
            widget.setObjectName(self._object_name)

        # Apply CSS classes if specified
        if self._css_classes:
            from .styles import set_classes

            set_classes(widget, list(self._css_classes))

        # Apply widget props (styleSheet="X" -> setStyleSheet("X"))
        for prop_name, value in self._widget_props.items():
            setter_name = f"set{prop_name[0].upper()}{prop_name[1:]}"
            setter = getattr(widget, setter_name, None)
            if setter is not None and callable(setter):
                setter(value)
        return widget

    def _bind_widget_to_item(
        self,
        widget: QWidget,
        item: T,
        wrapper: Observable[Any] | ObservableProxy[Any],
    ) -> None:
        """Bind a widget to an item wrapper."""
        bind_expr = self._bind_expr

        # Case 0: Callable formatter - one-way computed binding
        if callable(bind_expr):
            self._bind_callable_format(widget, wrapper, bind_expr)
            return

        # Find all placeholders in the bind expression
        placeholders = _PLACEHOLDER_RE.findall(bind_expr)

        # Case 1: Simple {#self} - bind directly to item value (two-way)
        if bind_expr == "{#self}":
            var: Variable[Any] = Variable(wrapper)
            bind(var).to(widget)
            return

        # Case 2: Single property {name} - bind to that property (two-way for objects)
        if len(placeholders) == 1 and bind_expr == f"{{{placeholders[0]}}}":
            prop_name = placeholders[0]
            if prop_name.startswith("#"):
                # Special placeholder like {#self} - one-way computed
                self._bind_computed_format(widget, wrapper, bind_expr)
            elif isinstance(wrapper, ObservableProxy):
                # Property on object - get Observable for that property
                prop_obs: Observable[Any] = getattr(wrapper, prop_name)
                var = Variable(prop_obs)
                bind(var).to(widget)
            else:
                # Primitive with property access doesn't make sense, fall back to format
                self._bind_computed_format(widget, wrapper, bind_expr)
            return

        # Case 3: Format string with multiple placeholders - one-way computed binding
        self._bind_computed_format(widget, wrapper, bind_expr)

    def _bind_callable_format(
        self,
        widget: QWidget,
        wrapper: Observable[Any] | ObservableProxy[Any],
        formatter: Callable[[Any], str],
    ) -> None:
        """Bind using a callable formatter (one-way only)."""
        from .bindings.registry import get_binding_registry

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

    def _resolve_nested_property(self, obj: Any, path: str) -> Any:
        """Resolve a dotted property path like 'breed.name' on an object."""
        parts = path.split(".")
        current: Any = obj
        for part in parts:
            if isinstance(current, Observable):
                current = current.get()  # pyright: ignore[reportUnknownVariableType, reportUnknownMemberType]
            if isinstance(current, ObservableProxy):
                prop_obs = getattr(current, part, None)  # pyright: ignore[reportUnknownArgumentType]
                if isinstance(prop_obs, Observable):
                    current = prop_obs.get()  # pyright: ignore[reportUnknownVariableType, reportUnknownMemberType]
                else:
                    current = prop_obs  # pyright: ignore[reportUnknownVariableType]
            elif hasattr(current, part):  # pyright: ignore[reportUnknownArgumentType]
                current = getattr(current, part)  # pyright: ignore[reportUnknownArgumentType, reportUnknownVariableType]
            else:
                return f"<unknown:{path}>"
        if isinstance(current, Observable):
            current = current.get()  # pyright: ignore[reportUnknownVariableType, reportUnknownMemberType]
        return current  # pyright: ignore[reportUnknownVariableType]

    def _bind_computed_format(
        self,
        widget: QWidget,
        wrapper: Observable[Any] | ObservableProxy[Any],
        format_str: str,
    ) -> None:
        """Bind a computed format string to widget (one-way only).

        Supports placeholders:
        - {#self} - the item value
        - {#self.property} - nested property on item
        - {property} - item.property (for objects)
        - {property.nested} - nested property access

        Note: No {#index} - sets are unordered.
        """
        from .bindings.registry import get_binding_registry

        registry = get_binding_registry()
        default_prop = registry.get_default_prop(widget)
        adapter = registry.get(widget, default_prop)
        if adapter is None or adapter.setter is None:
            return

        setter = adapter.setter

        def compute_value() -> str:
            result = format_str

            for match in _PLACEHOLDER_RE.finditer(format_str):
                placeholder = match.group(1)
                full_match = match.group(0)

                value: Any
                if placeholder == "#self":
                    if isinstance(wrapper, Observable):
                        value = wrapper.get()
                    else:
                        value = wrapper.unwrap()
                elif placeholder.startswith("#self."):
                    prop_path = placeholder[6:]  # Remove "#self."
                    if isinstance(wrapper, Observable):
                        value = self._resolve_nested_property(wrapper.get(), prop_path)
                    else:
                        value = self._resolve_nested_property(wrapper, prop_path)
                elif isinstance(wrapper, ObservableProxy):
                    value = self._resolve_nested_property(wrapper, placeholder)
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
            # Subscribe to property observables mentioned in format
            for match in _PLACEHOLDER_RE.finditer(format_str):
                placeholder = match.group(1)
                if placeholder in ("#self",):
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

    def _connect_child_signals(
        self,
        widget: QWidget,
        item: T,
        wrapper: Observable[Any] | ObservableProxy[Any],
    ) -> None:
        """Connect child widget signals to parent handlers."""
        if not self._signal_connections or self._parent_widget is None:
            return

        for signal_name, handler_spec in self._signal_connections.items():
            signal = getattr(widget, signal_name, None)
            if signal is None:
                continue

            handler = self._create_signal_handler(handler_spec, item, wrapper, widget)
            signal.connect(handler)

    def _create_signal_handler(
        self,
        spec: str | Callable[..., Any],
        item: T,
        wrapper: Observable[Any] | ObservableProxy[Any],
        widget: QWidget,
    ) -> Callable[..., Any]:
        """Create a handler that resolves placeholders at call time.

        Placeholders:
        - #value: The set item value
        - #widget: The child widget instance
        - #args: Spread of signal's own arguments

        Note: No #index - sets are unordered.
        """
        if callable(spec):
            return spec

        match = _HANDLER_SPEC_RE.match(spec)
        if not match:
            raise ValueError(f"Invalid handler spec: {spec}")

        method_name = match.group(1)
        args_spec = match.group(2)

        if self._parent_widget is None:
            raise ValueError(f"Cannot connect signal: no parent widget for handler '{method_name}'")

        parent_method = getattr(self._parent_widget, method_name, None)
        if parent_method is None:
            raise AttributeError(f"{type(self._parent_widget).__name__} has no method '{method_name}'")
        if not callable(parent_method):
            raise AttributeError(f"{type(self._parent_widget).__name__}.{method_name} is not callable")

        if args_spec is None:
            placeholders = ["#args"]
        elif args_spec.strip() == "":
            placeholders = []
        else:
            placeholders = [p.strip() for p in args_spec.split(",") if p.strip()]

        def handler(*signal_args: Any) -> Any:
            call_args: list[Any] = []
            for placeholder in placeholders:
                if placeholder == "#value":
                    if isinstance(wrapper, Observable):
                        call_args.append(wrapper.get())
                    else:
                        call_args.append(wrapper.unwrap())
                elif placeholder == "#widget":
                    call_args.append(widget)
                elif placeholder == "#args":
                    call_args.extend(signal_args)
                else:
                    call_args.append(placeholder)
            return parent_method(*call_args)

        return handler

    def _create_and_add_widget(self, item: T, position: int | None = None) -> None:
        """Create a widget for an item and add it to the layout."""
        wrapper = self._create_item_wrapper(item)
        widget = self._create_widget_for_item()

        self._bind_widget_to_item(widget, item, wrapper)
        self._connect_child_signals(widget, item, wrapper)

        self._entries[item] = (widget, wrapper)

        if position is not None:
            self._layout.insertWidget(position, widget)
        else:
            self._layout.addWidget(widget)

    def _on_add(self, item: T) -> None:
        """Handle item addition."""
        if self._sort:
            # Find correct position based on sort order
            position = self._find_insert_position(item)
            self._item_order.insert(position, item)
            self._create_and_add_widget(item, position)
        else:
            # No sorting - append at end
            self._item_order.append(item)
            self._create_and_add_widget(item)

    def _on_remove(self, item: T) -> None:
        """Handle item removal."""
        if item in self._entries:
            widget, _ = self._entries.pop(item)
            self._item_order.remove(item)
            self._layout.removeWidget(widget)
            widget.deleteLater()

    def _on_clear(self, removed_items: set[T]) -> None:
        """Handle set clear."""
        for widget, _ in self._entries.values():
            self._layout.removeWidget(widget)
            widget.deleteLater()
        self._entries.clear()
        self._item_order.clear()

    def widget_for_item(self, item: T) -> QWidget | None:
        """Get the widget for a specific item."""
        entry = self._entries.get(item)
        return entry[0] if entry else None

    def widget_count(self) -> int:
        """Get the number of widgets."""
        return len(self._entries)

    # Set-like interface
    def __contains__(self, item: T) -> bool:
        """Check if item has a widget."""
        return item in self._entries

    def __len__(self) -> int:
        """Return number of widgets."""
        return len(self._entries)

    def __iter__(self):
        """Iterate over widgets in display order."""
        for item in self._item_order:
            if item in self._entries:
                yield self._entries[item][0]

    def items(self):
        """Iterate over (item, widget) pairs in display order."""
        for item in self._item_order:
            if item in self._entries:
                yield item, self._entries[item][0]
