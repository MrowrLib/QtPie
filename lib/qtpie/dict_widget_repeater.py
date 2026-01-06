"""DictWidgetRepeater - Container that manages repeated widgets bound to dict entries."""

from __future__ import annotations

import re
from collections.abc import Callable
from typing import Any

from observant import Observable, ObservableDict, ObservableProxy
from PySide6.QtWidgets import QHBoxLayout, QVBoxLayout, QWidget

from .bindings import bind
from .variable import Variable

# Regex to find placeholders like {#key}, {#value}, {#self}, {name}, {#key.name}
_PLACEHOLDER_RE = re.compile(r"\{(#?\w+(?:\.\w+)*)\}")


def _is_primitive_type(t: type | None) -> bool:
    """Check if type is a primitive."""
    return t in (str, int, float, bool, type(None))


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
        layout_type: str = "vertical",
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
            layout_type: "vertical" or "horizontal".
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
        self._is_key_primitive = _is_primitive_type(key_type)
        self._is_value_primitive = _is_primitive_type(value_type)

        # Track: key -> (widget, key_wrapper, value_wrapper)
        # key_wrapper is Observable[K] for primitives, ObservableProxy[K] for objects
        # value_wrapper is Observable[V] for primitives, ObservableProxy[V] for objects
        self._entries: dict[K, tuple[QWidget, Observable[Any] | ObservableProxy[Any], Observable[Any] | ObservableProxy[Any]]] = {}
        # Maintain insertion order for layout
        self._key_order: list[K] = []

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

        # Subscribe to granular callbacks
        observable_dict.on_insert(self._on_insert)
        observable_dict.on_remove(self._on_remove)
        observable_dict.on_replace(self._on_replace)
        observable_dict.on_clear(self._on_clear)

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

    def _create_widget_for_entry(self) -> QWidget:
        """Create a new widget instance."""
        widget = self._widget_type(*self._widget_args, **self._widget_kwargs)
        # Apply widget props (styleSheet="X" → setStyleSheet("X"))
        for prop_name, value in self._widget_props.items():
            setter_name = f"set{prop_name[0].upper()}{prop_name[1:]}"
            setter = getattr(widget, setter_name, None)
            if setter is not None and callable(setter):
                setter(value)
        return widget

    def _resolve_nested_property(self, obj: Any, path: str) -> Any:
        """Resolve a dotted property path like 'breed.name' on an object."""
        parts = path.split(".")
        current: Any = obj
        for part in parts:
            if isinstance(current, Observable):
                current = current.get()  # pyright: ignore[reportUnknownVariableType]
            if isinstance(current, ObservableProxy):
                prop_obs = getattr(current, part, None)  # pyright: ignore[reportUnknownArgumentType]
                if isinstance(prop_obs, Observable):
                    current = prop_obs.get()  # pyright: ignore[reportUnknownVariableType]
                else:
                    current = prop_obs  # pyright: ignore[reportUnknownVariableType]
            elif hasattr(current, part):  # pyright: ignore[reportUnknownArgumentType]
                current = getattr(current, part)  # pyright: ignore[reportUnknownArgumentType, reportUnknownVariableType]
            else:
                return f"<unknown:{path}>"
        if isinstance(current, Observable):
            current = current.get()  # pyright: ignore[reportUnknownVariableType]
        return current  # pyright: ignore[reportUnknownVariableType]

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
        placeholders = _PLACEHOLDER_RE.findall(bind_expr)

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
            for match in _PLACEHOLDER_RE.finditer(format_str):
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
                        resolved = self._resolve_nested_property(key_wrapper.get(), prop_path)
                    else:
                        resolved = self._resolve_nested_property(key_wrapper, prop_path)
                elif placeholder.startswith("#value.") or placeholder.startswith("#self."):
                    # Nested property on value: #value.age or #self.age -> value.age
                    prop_path = placeholder.split(".", 1)[1]
                    if isinstance(value_wrapper, Observable):
                        resolved = self._resolve_nested_property(value_wrapper.get(), prop_path)
                    else:
                        resolved = self._resolve_nested_property(value_wrapper, prop_path)
                elif isinstance(value_wrapper, ObservableProxy):
                    # Property access on value object (shorthand)
                    resolved = self._resolve_nested_property(value_wrapper, placeholder)
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
            for match in _PLACEHOLDER_RE.finditer(format_str):
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
            for match in _PLACEHOLDER_RE.finditer(format_str):
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

    def _create_and_add_widget(self, key: K, value: V) -> None:
        """Create a widget for a key-value pair and add it to the layout."""
        key_wrapper = self._create_key_wrapper(key)
        value_wrapper = self._create_value_wrapper(value)
        widget = self._create_widget_for_entry()

        self._bind_widget_to_entry(widget, key, key_wrapper, value_wrapper)

        # Store and add to layout
        self._entries[key] = (widget, key_wrapper, value_wrapper)
        self._key_order.append(key)
        self._layout.addWidget(widget)

    def _on_insert(self, key: K, value: V) -> None:
        """Handle new key insertion."""
        self._create_and_add_widget(key, value)

    def _on_remove(self, key: K, value: V) -> None:
        """Handle key removal."""
        if key in self._entries:
            widget, _, _ = self._entries.pop(key)
            self._key_order.remove(key)
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
