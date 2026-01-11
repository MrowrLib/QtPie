"""WidgetRepeater - Container that manages repeated widgets bound to list items."""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from observant import Observable, ObservableList, ObservableProxy
from qtpy.QtWidgets import QHBoxLayout, QVBoxLayout, QWidget

from .bindings import bind
from .utils.common import HANDLER_SPEC_RE, PLACEHOLDER_RE, is_primitive_type
from .utils.properties import resolve_nested_property
from .variable import Variable

if TYPE_CHECKING:
    from .widget import Widget


class WidgetRepeater[T](QWidget):
    """Container that manages repeated widgets bound to list items.

    Creates one widget per list item. Uses granular callbacks (on_insert,
    on_remove, on_replace, on_clear) to efficiently sync the widget list
    with the underlying ObservableList.

    Usage:
        # Variable[list[int], QLineEdit] creates this automatically
        # Each QLineEdit is bound to one list item
    """

    def __init__(
        self,
        observable_list: ObservableList[T],
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
        """Initialize the widget repeater.

        Args:
            observable_list: The ObservableList to sync with.
            item_type: The type of items in the list (e.g., int, str, Dog).
            widget_type: The widget type to create for each item.
            widget_args: Positional args for widget constructor.
            widget_kwargs: Keyword args for widget constructor.
            widget_props: Widget properties to apply via setXxx() after creation.
            bind_expr: Binding expression or callable formatter (default "{#self}").
            sort: Sorting option - False/None (list order), True (sorted()),
                  callable (key function), or string method name. Note: {#index} still
                  refers to the underlying list index, not display position.
            layout_type: "vertical" or "horizontal".
            object_name: objectName to set on each created widget.
            css_classes: CSS classes to apply to each created widget.
            signal_connections: Signal connections from child widget to parent handlers.
                e.g., {"on_delete": "remove_item(#index)"} connects child.on_delete
                to parent.remove_item with the item index.
            parent_widget: The parent Widget instance for resolving handler methods.
        """
        super().__init__()

        self._obs_list = observable_list
        self._item_type = item_type
        self._widget_type = widget_type
        self._widget_args = widget_args
        self._widget_kwargs = widget_kwargs or {}
        self._widget_props = widget_props or {}
        self._bind_expr: str | Callable[[T], str] = bind_expr
        # Resolve sort= string method name to callable
        self._sort: bool | Callable[[T], Any] | None = self._resolve_sort(sort, parent_widget)
        self._is_primitive = is_primitive_type(item_type)
        self._object_name = object_name
        self._css_classes = css_classes or []
        self._signal_connections = signal_connections or {}
        self._parent_widget = parent_widget

        # Track: (widget, item_wrapper, index_holder)
        # item_wrapper is Observable[T] for primitives, ObservableProxy[T] for objects
        # index_holder is [int] so closures can access updated index
        self._items: list[tuple[QWidget, Observable[Any] | ObservableProxy[Any], list[int]]] = []

        # Track layout ordering for sorted display
        self._layout_indices: list[int] = []  # Maps layout position -> list index

        # Setup layout
        if layout_type == "horizontal":
            self._layout = QHBoxLayout(self)
        else:
            self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)

        # Create initial widgets for existing items
        for i, item in enumerate(observable_list):
            self._create_and_add_widget(i, item)

        # Apply sorting if enabled
        if self._sort:
            self._rebuild_layout_order()

        # Subscribe to granular callbacks
        observable_list.on_insert(self._on_insert)
        observable_list.on_remove(self._on_remove)
        observable_list.on_replace(self._on_replace)
        observable_list.on_clear(self._on_clear)

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

    def _create_item_wrapper(self, item: T) -> Observable[Any] | ObservableProxy[Any]:
        """Create the appropriate wrapper for an item."""
        if self._is_primitive:
            return Observable(item)
        else:
            return ObservableProxy(item)

    def _get_display_order(self) -> list[int]:
        """Get the display order of items (list indices in display order).

        Returns indices into self._items for layout ordering.
        If sort=False/None, returns natural order [0, 1, 2, ...].
        If sort=True, returns sorted order using default comparison.
        If sort=callable, uses it as key function for sorting.
        """
        n = len(self._items)
        if n == 0:
            return []

        if not self._sort:
            # No sorting - natural list order
            return list(range(n))

        # Build (index, item_value) pairs for sorting
        pairs: list[tuple[int, Any]] = []
        for i, (_, wrapper, _) in enumerate(self._items):
            if isinstance(wrapper, Observable):
                value = wrapper.get()
            else:
                value = wrapper.unwrap()
            pairs.append((i, value))

        # Sort by value
        if callable(self._sort):
            # Use provided key function
            sort_fn = self._sort
            pairs.sort(key=lambda p: sort_fn(p[1]))  # pyright: ignore[reportOptionalCall, reportUnknownLambdaType]
        else:
            # sort=True, use default sorted()
            pairs.sort(key=lambda p: p[1])

        return [idx for idx, _ in pairs]

    def _rebuild_layout_order(self) -> None:
        """Rebuild the layout widget order based on current sort settings."""
        new_order = self._get_display_order()

        # Only rebuild if order changed
        if new_order == self._layout_indices:
            return

        self._layout_indices = new_order

        # Remove all widgets from layout (but don't delete them)
        for widget, _, _ in self._items:
            self._layout.removeWidget(widget)

        # Re-add widgets in sorted order
        for list_idx in self._layout_indices:
            widget = self._items[list_idx][0]
            self._layout.addWidget(widget)

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

        # Apply widget props (styleSheet="X" → setStyleSheet("X"))
        for prop_name, value in self._widget_props.items():
            setter_name = f"set{prop_name[0].upper()}{prop_name[1:]}"
            setter = getattr(widget, setter_name, None)
            if setter is not None and callable(setter):
                setter(value)
        return widget

    def _bind_widget_to_item(
        self,
        widget: QWidget,
        wrapper: Observable[Any] | ObservableProxy[Any],
        index_holder: list[int],
    ) -> None:
        """Bind a widget to an item wrapper with two-way sync to the list.

        Args:
            widget: The widget to bind.
            wrapper: Observable or ObservableProxy wrapping the item.
            index_holder: Mutable [int] for tracking index changes.
        """
        bind_expr = self._bind_expr

        # Case 0: Callable formatter - one-way computed binding
        if callable(bind_expr):
            self._bind_callable_format(widget, wrapper, index_holder, bind_expr)
            return

        # Find all placeholders in the bind expression
        placeholders = PLACEHOLDER_RE.findall(bind_expr)

        # Case 1: Simple {#self} - bind directly to item value (two-way)
        if bind_expr == "{#self}":
            var: Variable[Any] = Variable(wrapper)
            bind(var).to(widget)
            self._setup_primitive_sync(wrapper, index_holder)
            return

        # Case 2: Single property {name} - bind to that property (two-way for objects)
        if len(placeholders) == 1 and bind_expr == f"{{{placeholders[0]}}}":
            prop_name = placeholders[0]
            if prop_name.startswith("#"):
                # Special placeholder like {#index} - one-way computed
                self._bind_computed_format(widget, wrapper, index_holder, bind_expr)
            elif isinstance(wrapper, ObservableProxy):
                # Property on object - get Observable for that property
                prop_obs: Observable[Any] = getattr(wrapper, prop_name)
                var = Variable(prop_obs)
                bind(var).to(widget)
                # No need for sync - ObservableProxy auto-syncs to object
            else:
                # Primitive with property access doesn't make sense, fall back to format
                self._bind_computed_format(widget, wrapper, index_holder, bind_expr)
            return

        # Case 3: Format string with multiple placeholders - one-way computed binding
        self._bind_computed_format(widget, wrapper, index_holder, bind_expr)

    def _setup_primitive_sync(
        self,
        wrapper: Observable[Any] | ObservableProxy[Any],
        index_holder: list[int],
    ) -> None:
        """Set up sync from primitive Observable back to list."""
        if isinstance(wrapper, Observable):
            # Prevent infinite loop: track if we're updating
            updating = {"active": False}

            def sync_to_list(new_val: Any, idx: list[int] = index_holder, upd: dict[str, bool] = updating) -> None:
                if upd["active"]:
                    return
                upd["active"] = True
                try:
                    self._obs_list[idx[0]] = new_val
                finally:
                    upd["active"] = False

            wrapper.on_change(sync_to_list)

    def _bind_callable_format(
        self,
        widget: QWidget,
        wrapper: Observable[Any] | ObservableProxy[Any],
        index_holder: list[int],
        formatter: Callable[[Any], str],
    ) -> None:
        """Bind using a callable formatter (one-way only).

        Args:
            widget: The widget to bind.
            wrapper: Observable or ObservableProxy wrapping the item.
            index_holder: Mutable [int] for tracking index changes.
            formatter: Callable that takes the item and returns a string.
        """
        from .bindings.registry import get_binding_registry

        # Get the setter for the widget's default property
        registry = get_binding_registry()
        default_prop = registry.get_default_prop(widget)
        adapter = registry.get(widget, default_prop)
        if adapter is None or adapter.setter is None:
            return

        setter = adapter.setter

        def compute_value() -> str:
            """Compute the formatted string using the callable."""
            if isinstance(wrapper, Observable):
                item = wrapper.get()
            else:
                item = wrapper.unwrap()
            return formatter(item)

        # Set initial value
        setter(widget, compute_value())

        # Subscribe to changes and update widget
        def on_change(_: Any) -> None:
            setter(widget, compute_value())

        if isinstance(wrapper, Observable):
            wrapper.on_change(on_change)
        else:
            # For ObservableProxy, subscribe to on_change which fires for any field change
            wrapper.on_change(lambda: on_change(None))

    def _bind_computed_format(
        self,
        widget: QWidget,
        wrapper: Observable[Any] | ObservableProxy[Any],
        index_holder: list[int],
        format_str: str,
    ) -> None:
        """Bind a computed format string to widget (one-way only).

        Supports placeholders:
        - {#self} - the item value
        - {#index} - the item index
        - {#self.property} - nested property on item
        - {property} - item.property (for objects)
        - {property.nested} - nested property access
        """
        from .bindings.registry import get_binding_registry

        # Get the setter for the widget's default property
        registry = get_binding_registry()
        default_prop = registry.get_default_prop(widget)
        adapter = registry.get(widget, default_prop)
        if adapter is None or adapter.setter is None:
            return

        setter = adapter.setter

        def compute_value() -> str:
            """Compute the formatted string from current values."""
            result = format_str

            # Find and replace all placeholders
            for match in PLACEHOLDER_RE.finditer(format_str):
                placeholder = match.group(1)
                full_match = match.group(0)

                value: Any
                if placeholder == "#self":
                    if isinstance(wrapper, Observable):
                        value = wrapper.get()
                    else:
                        value = wrapper.unwrap()
                elif placeholder == "#index":
                    value = index_holder[0]
                elif placeholder.startswith("#self."):
                    # Nested property on item: #self.age -> item.age
                    prop_path = placeholder[6:]  # Remove "#self."
                    if isinstance(wrapper, Observable):
                        value = resolve_nested_property(wrapper.get(), prop_path)
                    else:
                        value = resolve_nested_property(wrapper, prop_path)
                elif isinstance(wrapper, ObservableProxy):
                    # Property access on object (may be nested like breed.name)
                    value = resolve_nested_property(wrapper, placeholder)
                else:
                    value = f"<unknown:{placeholder}>"

                result = result.replace(full_match, str(value), 1)  # pyright: ignore[reportUnknownArgumentType]

            return result

        # Set initial value
        setter(widget, compute_value())

        # Subscribe to changes and update widget
        def on_change(_: Any) -> None:
            setter(widget, compute_value())

        if isinstance(wrapper, Observable):
            wrapper.on_change(on_change)
        else:
            # For ObservableProxy, subscribe to all property observables mentioned
            for match in PLACEHOLDER_RE.finditer(format_str):
                placeholder = match.group(1)
                # Skip special placeholders
                if placeholder in ("#self", "#index"):
                    continue
                # Handle #self.prop
                if placeholder.startswith("#self."):
                    prop_name = placeholder[6:].split(".")[0]
                    prop_obs: Any = getattr(wrapper, prop_name, None)
                    if isinstance(prop_obs, Observable):
                        prop_obs.on_change(on_change)  # pyright: ignore[reportUnknownMemberType]
                elif not placeholder.startswith("#"):
                    # Direct property (may be nested)
                    prop_name = placeholder.split(".")[0]
                    prop_obs = getattr(wrapper, prop_name, None)
                    if isinstance(prop_obs, Observable):
                        prop_obs.on_change(on_change)  # pyright: ignore[reportUnknownMemberType]

    def _connect_child_signals(
        self,
        widget: QWidget,
        wrapper: Observable[Any] | ObservableProxy[Any],
        index_holder: list[int],
    ) -> None:
        """Connect child widget signals to parent handlers.

        Args:
            widget: The child widget instance.
            wrapper: Observable or ObservableProxy wrapping the item.
            index_holder: Mutable [int] for tracking index changes.
        """
        if not self._signal_connections or self._parent_widget is None:
            return

        for signal_name, handler_spec in self._signal_connections.items():
            # Get the signal from child widget
            signal = getattr(widget, signal_name, None)
            if signal is None:
                continue

            # Create handler that resolves placeholders at call time
            handler = self._create_signal_handler(handler_spec, wrapper, index_holder, widget)
            signal.connect(handler)

    def _create_signal_handler(
        self,
        spec: str | Callable[..., Any],
        wrapper: Observable[Any] | ObservableProxy[Any],
        index_holder: list[int],
        widget: QWidget,
    ) -> Callable[..., Any]:
        """Create a handler that resolves placeholders at call time.

        Supports:
        - "method_name" → passes signal's args only (shorthand for method_name(#args))
        - "method_name()" → passes nothing
        - "method_name(#args)" → passes signal's args
        - "method_name(#value, #index, #args)" → passes item, index, then signal args

        Placeholders:
        - #value: The list item value
        - #widget: The child widget instance
        - #index: The list index
        - #args: Spread of signal's own arguments
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
        if self._parent_widget is None:
            raise ValueError(f"Cannot connect signal: no parent widget for handler '{method_name}'")

        parent_method = getattr(self._parent_widget, method_name, None)
        if parent_method is None:
            raise AttributeError(f"{type(self._parent_widget).__name__} has no method '{method_name}' for signal connection")
        if not callable(parent_method):
            raise AttributeError(f"{type(self._parent_widget).__name__}.{method_name} is not callable")

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
                    # Get the item value
                    if isinstance(wrapper, Observable):
                        call_args.append(wrapper.get())
                    else:
                        call_args.append(wrapper.unwrap())
                elif placeholder == "#widget":
                    call_args.append(widget)
                elif placeholder == "#index":
                    call_args.append(index_holder[0])
                elif placeholder == "#args":
                    # Spread signal args
                    call_args.extend(signal_args)
                else:
                    # Unknown placeholder - pass as-is (could be a literal)
                    call_args.append(placeholder)

            return parent_method(*call_args)

        return handler

    def _create_and_add_widget(self, index: int, item: T) -> None:
        """Create a widget for an item and add it to the layout."""
        wrapper = self._create_item_wrapper(item)
        widget = self._create_widget_for_item()
        index_holder = [index]

        self._bind_widget_to_item(widget, wrapper, index_holder)
        self._connect_child_signals(widget, wrapper, index_holder)

        # Insert at correct position
        self._items.insert(index, (widget, wrapper, index_holder))
        self._layout.insertWidget(index, widget)

        # Update indices for items after this one
        for i in range(index + 1, len(self._items)):
            self._items[i][2][0] = i

    def _on_insert(self, index: int, item: T) -> None:
        """Handle item insertion."""
        self._create_and_add_widget(index, item)
        if self._sort:
            self._rebuild_layout_order()

    def _on_remove(self, index: int, item: T) -> None:
        """Handle item removal."""
        if index < len(self._items):
            widget, _, _ = self._items.pop(index)
            self._layout.removeWidget(widget)
            widget.deleteLater()

            # Update indices for remaining items
            for i in range(index, len(self._items)):
                self._items[i][2][0] = i

            if self._sort:
                self._rebuild_layout_order()

    def _on_replace(self, index: int, old_item: T, new_item: T) -> None:
        """Handle item replacement."""
        if index < len(self._items):
            widget, wrapper, index_holder = self._items[index]

            if isinstance(wrapper, Observable):
                # Primitives: just update the Observable
                wrapper.set(new_item)
            else:
                # Complex objects: remove old widget and create new one
                self._layout.removeWidget(widget)
                widget.deleteLater()

                new_wrapper = self._create_item_wrapper(new_item)
                new_widget = self._create_widget_for_item()
                self._bind_widget_to_item(new_widget, new_wrapper, index_holder)
                self._connect_child_signals(new_widget, new_wrapper, index_holder)

                self._items[index] = (new_widget, new_wrapper, index_holder)
                self._layout.insertWidget(index, new_widget)

            # Re-sort if value changed and sorting is enabled
            if self._sort:
                self._rebuild_layout_order()

    def _on_clear(self, removed_items: list[T]) -> None:
        """Handle list clear."""
        # Remove all widgets
        for widget, _, _ in self._items:
            self._layout.removeWidget(widget)
            widget.deleteLater()
        self._items.clear()
        self._layout_indices.clear()

    def widget_at(self, index: int) -> QWidget | None:
        """Get the widget at a specific index."""
        if 0 <= index < len(self._items):
            return self._items[index][0]
        return None

    def widget_count(self) -> int:
        """Get the number of widgets."""
        return len(self._items)

    # List-like interface so list[QLabel] annotation isn't a total lie
    def __getitem__(self, index: int) -> QWidget:
        """Get widget at index (list-like access)."""
        if index < 0:
            index = len(self._items) + index
        if 0 <= index < len(self._items):
            return self._items[index][0]
        raise IndexError(f"index {index} out of range")

    def __len__(self) -> int:
        """Return number of widgets."""
        return len(self._items)

    def __iter__(self):
        """Iterate over widgets."""
        for widget, _, _ in self._items:
            yield widget
