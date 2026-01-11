"""DictWidgetRepeater - Container that manages repeated widgets bound to dict entries."""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from observant import Observable, ObservableDict, ObservableProxy
from qtpy.QtWidgets import QHBoxLayout, QVBoxLayout, QWidget

from .bindings import bind
from .utils.common import HANDLER_SPEC_RE, PLACEHOLDER_RE, is_primitive_type
from .utils.properties import resolve_nested_property
from .variable import Variable

if TYPE_CHECKING:
    from .widget import Widget


class DictWidgetRepeater[K, V](QWidget):
    """Container that manages repeated widgets bound to dict entries.

    Creates one widget per key-value pair. Uses granular callbacks (on_insert,
    on_remove, on_replace, on_clear) to efficiently sync the widget list
    with the underlying ObservableDict.

    Binding placeholders:
    - {#key} - the dictionary key
    - {#value} - the dictionary value
    - {#self} - same as {#value} (the value is the context)
    - {property} - property on the value (e.g., {name} for Dog.name)
    - {#key.property} - nested property on key (e.g., {#key.name} for complex keys)
    - {#value.property} or {#self.property} - explicit nested property on value

    Usage:
        # Variable[dict[str, Dog], QLabel] creates this automatically
        # Each QLabel shows "{#key} is {age} years old"
    """

    def __init__(
        self,
        observable_dict: ObservableDict[K, V],
        key_type: type | None,
        value_type: type | None,
        widget_type: type,
        widget_args: tuple[Any, ...] = (),
        widget_kwargs: dict[str, Any] | None = None,
        widget_props: dict[str, Any] | None = None,
        bind_expr: str | Callable[[K, V], str] = "{#key} = {#value}",
        sort: bool | str | Callable[[K], Any] | None = None,
        layout_type: str = "vertical",
        object_name: str | None = None,
        css_classes: list[str] | None = None,
        signal_connections: dict[str, str | Callable[..., Any]] | None = None,
        parent_widget: Widget[Any] | None = None,
    ) -> None:
        """Initialize the dict widget repeater.

        Args:
            observable_dict: The ObservableDict to sync with.
            key_type: The type of keys in the dict (e.g., str, Dog).
            value_type: The type of values in the dict (e.g., int, Dog).
            widget_type: The widget type to create for each entry.
            widget_args: Positional args for widget constructor.
            widget_kwargs: Keyword args for widget constructor.
            widget_props: Widget properties to apply via setXxx() after creation.
            bind_expr: Binding expression or callable(key, value) -> str.
            sort: Sorting option - False/None (insertion order), True (sorted by key),
                  or callable (key function for sorting keys).
            layout_type: "vertical" or "horizontal".
            object_name: objectName to set on each created widget.
            css_classes: CSS classes to apply to each created widget.
            signal_connections: Signal connections from child widget to parent handlers.
                e.g., {"on_delete": "remove_item(#key)"} connects child.on_delete
                to parent.remove_item with the dict key.
            parent_widget: The parent Widget instance for resolving handler methods.
        """
        super().__init__()

        self._obs_dict = observable_dict
        self._key_type = key_type
        self._value_type = value_type
        self._widget_type = widget_type
        self._widget_args = widget_args
        self._widget_kwargs = widget_kwargs or {}
        self._widget_props = widget_props or {}
        self._bind_expr: str | Callable[[K, V], str] = bind_expr
        # Resolve sort= string method name to callable
        self._sort: bool | Callable[[K], Any] | None = self._resolve_sort(sort, parent_widget)
        self._is_key_primitive = is_primitive_type(key_type)
        self._is_value_primitive = is_primitive_type(value_type)
        self._object_name = object_name
        self._css_classes = css_classes or []
        self._signal_connections = signal_connections or {}
        self._parent_widget = parent_widget

        # Track: key -> (widget, key_wrapper, value_wrapper)
        # key_wrapper is Observable[K] for primitives, ObservableProxy[K] for objects
        # value_wrapper is Observable[V] for primitives, ObservableProxy[V] for objects
        self._entries: dict[K, tuple[QWidget, Observable[Any] | ObservableProxy[Any], Observable[Any] | ObservableProxy[Any]]] = {}
        # Maintain insertion order for layout
        self._key_order: list[K] = []
        # Track layout ordering for sorted display
        self._layout_order: list[K] = []  # Keys in display order

        # Setup layout
        if layout_type == "horizontal":
            self._layout = QHBoxLayout(self)
        else:
            self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)

        # Create initial widgets for existing items
        for key, value in observable_dict.items():
            self._create_and_add_widget(key, value)

        # Apply sorting if enabled
        if self._sort:
            self._rebuild_layout_order()

        # Subscribe to granular callbacks
        observable_dict.on_insert(self._on_insert)
        observable_dict.on_remove(self._on_remove)
        observable_dict.on_replace(self._on_replace)
        observable_dict.on_clear(self._on_clear)

    def _resolve_sort(
        self,
        sort: bool | str | Callable[[K], Any] | None,
        parent_widget: Widget[Any] | None,
    ) -> bool | Callable[[K], Any] | None:
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

    def _create_key_wrapper(self, key: K) -> Observable[Any] | ObservableProxy[Any]:
        """Create the appropriate wrapper for a key."""
        if self._is_key_primitive:
            return Observable(key)
        else:
            return ObservableProxy(key)

    def _create_value_wrapper(self, value: V) -> Observable[Any] | ObservableProxy[Any]:
        """Create the appropriate wrapper for a value."""
        if self._is_value_primitive:
            return Observable(value)
        else:
            return ObservableProxy(value)

    def _get_display_order(self) -> list[K]:
        """Get the display order of keys.

        If sort=False/None, returns insertion order (_key_order).
        If sort=True, returns sorted keys using default comparison.
        If sort=callable, uses it as key function for sorting.
        """
        if not self._sort:
            # No sorting - insertion order
            return list(self._key_order)

        # Sort keys
        if callable(self._sort):
            # Use provided key function
            return sorted(self._key_order, key=self._sort)  # pyright: ignore[reportCallIssue, reportUnknownVariableType]
        else:
            # sort=True, use default sorted()
            return sorted(self._key_order)  # pyright: ignore[reportArgumentType, reportUnknownVariableType]

    def _rebuild_layout_order(self) -> None:
        """Rebuild the layout widget order based on current sort settings."""
        new_order = self._get_display_order()

        # Only rebuild if order changed
        if new_order == self._layout_order:
            return

        self._layout_order = new_order

        # Remove all widgets from layout (but don't delete them)
        for key in self._key_order:
            widget = self._entries[key][0]
            self._layout.removeWidget(widget)

        # Re-add widgets in sorted order
        for key in self._layout_order:
            widget = self._entries[key][0]
            self._layout.addWidget(widget)

    def _create_widget_for_entry(self) -> QWidget:
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

    def _bind_widget_to_entry(
        self,
        widget: QWidget,
        key: K,
        key_wrapper: Observable[Any] | ObservableProxy[Any],
        value_wrapper: Observable[Any] | ObservableProxy[Any],
    ) -> None:
        """Bind a widget to a key-value pair.

        Args:
            widget: The widget to bind.
            key: The original key (for dict updates).
            key_wrapper: Observable or ObservableProxy wrapping the key.
            value_wrapper: Observable or ObservableProxy wrapping the value.
        """
        bind_expr = self._bind_expr

        # Case 0: Callable formatter - one-way computed binding
        if callable(bind_expr):
            self._bind_callable_format(widget, key, key_wrapper, value_wrapper, bind_expr)
            return

        # Find all placeholders in the bind expression
        placeholders = PLACEHOLDER_RE.findall(bind_expr)

        # Case 1: Simple {#value} or {#self} - bind directly to value (two-way)
        if bind_expr in ("{#value}", "{#self}"):
            var: Variable[Any] = Variable(value_wrapper)
            bind(var).to(widget)
            self._setup_value_sync(value_wrapper, key)
            return

        # Case 2: Single property {name} - bind to value's property (two-way for objects)
        if len(placeholders) == 1 and bind_expr == f"{{{placeholders[0]}}}":
            prop_path = placeholders[0]
            if not prop_path.startswith("#") and isinstance(value_wrapper, ObservableProxy):
                # Simple property on value object
                if "." not in prop_path:
                    prop_obs: Observable[Any] = getattr(value_wrapper, prop_path)
                    var = Variable(prop_obs)
                    bind(var).to(widget)
                    return
            # Fall through to computed format for nested or special placeholders

        # Case 3: Format string with placeholders - one-way computed binding
        self._bind_computed_format(widget, key, key_wrapper, value_wrapper, bind_expr)

    def _setup_value_sync(
        self,
        value_wrapper: Observable[Any] | ObservableProxy[Any],
        key: K,
    ) -> None:
        """Set up sync from primitive Observable back to dict."""
        if isinstance(value_wrapper, Observable):
            # Prevent infinite loop: track if we're updating
            updating = {"active": False}

            def sync_to_dict(new_val: Any, k: K = key, upd: dict[str, bool] = updating) -> None:
                if upd["active"]:
                    return
                upd["active"] = True
                try:
                    self._obs_dict[k] = new_val
                finally:
                    upd["active"] = False

            value_wrapper.on_change(sync_to_dict)

    def _bind_callable_format(
        self,
        widget: QWidget,
        key: K,
        key_wrapper: Observable[Any] | ObservableProxy[Any],
        value_wrapper: Observable[Any] | ObservableProxy[Any],
        formatter: Callable[[Any, Any], str],
    ) -> None:
        """Bind using a callable formatter (one-way only).

        Args:
            widget: The widget to bind.
            key: The original key.
            key_wrapper: Observable or ObservableProxy wrapping the key.
            value_wrapper: Observable or ObservableProxy wrapping the value.
            formatter: Callable(key, value) -> str.
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
            if isinstance(key_wrapper, Observable):
                k = key_wrapper.get()
            else:
                k = key_wrapper.unwrap()
            if isinstance(value_wrapper, Observable):
                v = value_wrapper.get()
            else:
                v = value_wrapper.unwrap()
            return formatter(k, v)

        # Set initial value
        setter(widget, compute_value())

        # Subscribe to changes and update widget
        def on_change(_: Any) -> None:
            setter(widget, compute_value())

        if isinstance(key_wrapper, Observable):
            key_wrapper.on_change(on_change)
        else:
            key_wrapper.on_change(lambda: on_change(None))

        if isinstance(value_wrapper, Observable):
            value_wrapper.on_change(on_change)
        else:
            value_wrapper.on_change(lambda: on_change(None))

    def _bind_computed_format(
        self,
        widget: QWidget,
        key: K,
        key_wrapper: Observable[Any] | ObservableProxy[Any],
        value_wrapper: Observable[Any] | ObservableProxy[Any],
        format_str: str,
    ) -> None:
        """Bind a computed format string to widget (one-way only).

        Supports placeholders:
        - {#key} - the key
        - {#value} or {#self} - the value
        - {#key.property} - nested property on key
        - {#value.property} or {#self.property} - nested property on value
        - {property} - property on value (shorthand)
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

                resolved: Any
                if placeholder == "#key":
                    if isinstance(key_wrapper, Observable):
                        resolved = key_wrapper.get()
                    else:
                        resolved = key_wrapper.unwrap()
                elif placeholder == "#value" or placeholder == "#self":
                    if isinstance(value_wrapper, Observable):
                        resolved = value_wrapper.get()
                    else:
                        resolved = value_wrapper.unwrap()
                elif placeholder.startswith("#key."):
                    # Nested property on key: #key.name -> key.name
                    prop_path = placeholder[5:]  # Remove "#key."
                    if isinstance(key_wrapper, Observable):
                        resolved = resolve_nested_property(key_wrapper.get(), prop_path)
                    else:
                        resolved = resolve_nested_property(key_wrapper, prop_path)
                elif placeholder.startswith("#value.") or placeholder.startswith("#self."):
                    # Nested property on value: #value.age or #self.age -> value.age
                    prop_path = placeholder.split(".", 1)[1]
                    if isinstance(value_wrapper, Observable):
                        resolved = resolve_nested_property(value_wrapper.get(), prop_path)
                    else:
                        resolved = resolve_nested_property(value_wrapper, prop_path)
                elif isinstance(value_wrapper, ObservableProxy):
                    # Property access on value object (shorthand)
                    resolved = resolve_nested_property(value_wrapper, placeholder)
                else:
                    resolved = f"<unknown:{placeholder}>"

                result = result.replace(full_match, str(resolved), 1)

            return result

        # Set initial value
        setter(widget, compute_value())

        # Subscribe to changes and update widget
        def on_change(_: Any) -> None:
            setter(widget, compute_value())

        # Subscribe to key changes (for complex keys)
        if isinstance(key_wrapper, Observable):
            key_wrapper.on_change(on_change)
        else:
            # For ObservableProxy keys, subscribe to all property observables mentioned
            for match in PLACEHOLDER_RE.finditer(format_str):
                placeholder = match.group(1)
                if placeholder.startswith("#key."):
                    prop_name = placeholder[5:].split(".")[0]
                    prop_obs: Any = getattr(key_wrapper, prop_name, None)
                    if isinstance(prop_obs, Observable):
                        prop_obs.on_change(on_change)  # pyright: ignore[reportUnknownMemberType]

        # Subscribe to value changes
        if isinstance(value_wrapper, Observable):
            value_wrapper.on_change(on_change)
        else:
            # For ObservableProxy values, subscribe to all property observables mentioned
            for match in PLACEHOLDER_RE.finditer(format_str):
                placeholder = match.group(1)
                # Direct property on value
                if not placeholder.startswith("#"):
                    prop_name = placeholder.split(".")[0]
                    prop_obs = getattr(value_wrapper, prop_name, None)
                    if isinstance(prop_obs, Observable):
                        prop_obs.on_change(on_change)  # pyright: ignore[reportUnknownMemberType]
                # Explicit #value.prop or #self.prop
                elif placeholder.startswith("#value.") or placeholder.startswith("#self."):
                    prop_name = placeholder.split(".", 1)[1].split(".")[0]
                    prop_obs = getattr(value_wrapper, prop_name, None)
                    if isinstance(prop_obs, Observable):
                        prop_obs.on_change(on_change)  # pyright: ignore[reportUnknownMemberType]

    def _connect_child_signals(
        self,
        widget: QWidget,
        key: K,
        key_wrapper: Observable[Any] | ObservableProxy[Any],
        value_wrapper: Observable[Any] | ObservableProxy[Any],
    ) -> None:
        """Connect child widget signals to parent handlers.

        Args:
            widget: The child widget instance.
            key: The dict key.
            key_wrapper: Observable or ObservableProxy wrapping the key.
            value_wrapper: Observable or ObservableProxy wrapping the value.
        """
        if not self._signal_connections or self._parent_widget is None:
            return

        for signal_name, handler_spec in self._signal_connections.items():
            # Get the signal from child widget
            signal = getattr(widget, signal_name, None)
            if signal is None:
                continue

            # Create handler that resolves placeholders at call time
            handler = self._create_signal_handler(handler_spec, key, key_wrapper, value_wrapper, widget)
            signal.connect(handler)

    def _create_signal_handler(
        self,
        spec: str | Callable[..., Any],
        key: K,
        key_wrapper: Observable[Any] | ObservableProxy[Any],
        value_wrapper: Observable[Any] | ObservableProxy[Any],
        widget: QWidget,
    ) -> Callable[..., Any]:
        """Create a handler that resolves placeholders at call time.

        Supports:
        - "method_name" → passes signal's args only (shorthand for method_name(#args))
        - "method_name()" → passes nothing
        - "method_name(#args)" → passes signal's args
        - "method_name(#value, #key, #args)" → passes value, key, then signal args

        Placeholders:
        - #value: The dict value
        - #key: The dict key
        - #widget: The child widget instance
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
            # Parse placeholders: "method_name(#value, #key, #args)"
            placeholders = [p.strip() for p in args_spec.split(",") if p.strip()]

        # Create the handler closure
        def handler(*signal_args: Any) -> Any:
            call_args: list[Any] = []
            for placeholder in placeholders:
                if placeholder == "#value":
                    # Get the value
                    if isinstance(value_wrapper, Observable):
                        call_args.append(value_wrapper.get())
                    else:
                        call_args.append(value_wrapper.unwrap())
                elif placeholder == "#key":
                    # Get the key
                    if isinstance(key_wrapper, Observable):
                        call_args.append(key_wrapper.get())
                    else:
                        call_args.append(key_wrapper.unwrap())
                elif placeholder == "#widget":
                    call_args.append(widget)
                elif placeholder == "#args":
                    # Spread signal args
                    call_args.extend(signal_args)
                else:
                    # Unknown placeholder - pass as-is (could be a literal)
                    call_args.append(placeholder)

            return parent_method(*call_args)

        return handler

    def _create_and_add_widget(self, key: K, value: V) -> None:
        """Create a widget for a key-value pair and add it to the layout."""
        key_wrapper = self._create_key_wrapper(key)
        value_wrapper = self._create_value_wrapper(value)
        widget = self._create_widget_for_entry()

        self._bind_widget_to_entry(widget, key, key_wrapper, value_wrapper)
        self._connect_child_signals(widget, key, key_wrapper, value_wrapper)

        # Store and add to layout
        self._entries[key] = (widget, key_wrapper, value_wrapper)
        self._key_order.append(key)
        self._layout.addWidget(widget)

    def _on_insert(self, key: K, value: V) -> None:
        """Handle new key insertion."""
        self._create_and_add_widget(key, value)
        if self._sort:
            self._rebuild_layout_order()

    def _on_remove(self, key: K, value: V) -> None:
        """Handle key removal."""
        if key in self._entries:
            widget, _, _ = self._entries.pop(key)
            self._key_order.remove(key)
            if key in self._layout_order:
                self._layout_order.remove(key)
            self._layout.removeWidget(widget)
            widget.deleteLater()

    def _on_replace(self, key: K, old_value: V, new_value: V) -> None:
        """Handle value replacement."""
        if key in self._entries:
            widget, key_wrapper, value_wrapper = self._entries[key]

            if isinstance(value_wrapper, Observable):
                # Primitives: just update the Observable
                value_wrapper.set(new_value)
            else:
                # Complex objects: remove old widget and create new one
                index = self._key_order.index(key)
                self._layout.removeWidget(widget)
                widget.deleteLater()

                new_value_wrapper = self._create_value_wrapper(new_value)
                new_widget = self._create_widget_for_entry()
                self._bind_widget_to_entry(new_widget, key, key_wrapper, new_value_wrapper)
                self._connect_child_signals(new_widget, key, key_wrapper, new_value_wrapper)

                self._entries[key] = (new_widget, key_wrapper, new_value_wrapper)
                self._layout.insertWidget(index, new_widget)

    def _on_clear(self, removed_items: dict[K, V]) -> None:
        """Handle dict clear."""
        # Remove all widgets
        for widget, _, _ in self._entries.values():
            self._layout.removeWidget(widget)
            widget.deleteLater()
        self._entries.clear()
        self._key_order.clear()
        self._layout_order.clear()

    def widget_for_key(self, key: K) -> QWidget | None:
        """Get the widget for a specific key."""
        entry = self._entries.get(key)
        return entry[0] if entry else None

    def widget_count(self) -> int:
        """Get the number of widgets."""
        return len(self._entries)

    # List-like interface for iteration
    def __getitem__(self, key: K) -> QWidget:
        """Get widget for key (dict-like access)."""
        entry = self._entries.get(key)
        if entry is None:
            raise KeyError(key)
        return entry[0]

    def __len__(self) -> int:
        """Return number of widgets."""
        return len(self._entries)

    def __iter__(self):
        """Iterate over widgets in insertion order."""
        for key in self._key_order:
            yield self._entries[key][0]

    def keys(self) -> list[K]:
        """Return keys in insertion order."""
        return list(self._key_order)

    def items(self):
        """Iterate over (key, widget) pairs in insertion order."""
        for key in self._key_order:
            yield key, self._entries[key][0]
