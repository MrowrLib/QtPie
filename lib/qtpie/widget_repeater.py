"""WidgetRepeater - Container that manages repeated widgets bound to list items."""

from __future__ import annotations

import re
from collections.abc import Callable
from typing import Any

from observant import Observable, ObservableList, ObservableProxy
from PySide6.QtWidgets import QHBoxLayout, QVBoxLayout, QWidget

from .bindings import bind
from .variable import Variable

# Regex to find placeholders like {#self}, {#index}, {name}, {age}, {#self.age}
_PLACEHOLDER_RE = re.compile(r"\{(#?\w+(?:\.\w+)*)\}")


def _is_primitive_type(t: type | None) -> bool:
    """Check if type is a primitive."""
    return t in (str, int, float, bool, type(None))


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
        layout_type: str = "vertical",
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
            layout_type: "vertical" or "horizontal".
        """
        super().__init__()

        self._obs_list = observable_list
        self._item_type = item_type
        self._widget_type = widget_type
        self._widget_args = widget_args
        self._widget_kwargs = widget_kwargs or {}
        self._widget_props = widget_props or {}
        self._bind_expr: str | Callable[[T], str] = bind_expr
        self._is_primitive = _is_primitive_type(item_type)

        # Track: (widget, item_wrapper, index_holder)
        # item_wrapper is Observable[T] for primitives, ObservableProxy[T] for objects
        # index_holder is [int] so closures can access updated index
        self._items: list[tuple[QWidget, Observable[Any] | ObservableProxy[Any], list[int]]] = []

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

        # Subscribe to granular callbacks
        observable_list.on_insert(self._on_insert)
        observable_list.on_remove(self._on_remove)
        observable_list.on_replace(self._on_replace)
        observable_list.on_clear(self._on_clear)

    def _create_item_wrapper(self, item: T) -> Observable[Any] | ObservableProxy[Any]:
        """Create the appropriate wrapper for an item."""
        if self._is_primitive:
            return Observable(item)
        else:
            return ObservableProxy(item)

    def _create_widget_for_item(self) -> QWidget:
        """Create a new widget instance."""
        widget = self._widget_type(*self._widget_args, **self._widget_kwargs)
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
        placeholders = _PLACEHOLDER_RE.findall(bind_expr)

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
            for match in _PLACEHOLDER_RE.finditer(format_str):
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
                        value = self._resolve_nested_property(wrapper.get(), prop_path)
                    else:
                        value = self._resolve_nested_property(wrapper, prop_path)
                elif isinstance(wrapper, ObservableProxy):
                    # Property access on object (may be nested like breed.name)
                    value = self._resolve_nested_property(wrapper, placeholder)
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
            for match in _PLACEHOLDER_RE.finditer(format_str):
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

    def _create_and_add_widget(self, index: int, item: T) -> None:
        """Create a widget for an item and add it to the layout."""
        wrapper = self._create_item_wrapper(item)
        widget = self._create_widget_for_item()
        index_holder = [index]

        self._bind_widget_to_item(widget, wrapper, index_holder)

        # Insert at correct position
        self._items.insert(index, (widget, wrapper, index_holder))
        self._layout.insertWidget(index, widget)

        # Update indices for items after this one
        for i in range(index + 1, len(self._items)):
            self._items[i][2][0] = i

    def _on_insert(self, index: int, item: T) -> None:
        """Handle item insertion."""
        self._create_and_add_widget(index, item)

    def _on_remove(self, index: int, item: T) -> None:
        """Handle item removal."""
        if index < len(self._items):
            widget, _, _ = self._items.pop(index)
            self._layout.removeWidget(widget)
            widget.deleteLater()

            # Update indices for remaining items
            for i in range(index, len(self._items)):
                self._items[i][2][0] = i

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

                self._items[index] = (new_widget, new_wrapper, index_holder)
                self._layout.insertWidget(index, new_widget)

    def _on_clear(self, removed_items: list[T]) -> None:
        """Handle list clear."""
        # Remove all widgets
        for widget, _, _ in self._items:
            self._layout.removeWidget(widget)
            widget.deleteLater()
        self._items.clear()

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
