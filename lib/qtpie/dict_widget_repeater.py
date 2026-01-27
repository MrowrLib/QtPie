"""DictWidgetRepeater - Container that manages repeated widgets bound to dict entries."""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from observant import Observable, ObservableDict, ObservableProxy
from qtpy.QtWidgets import QWidget

from .bindings import bind
from .repeaters.utils import (
    bind_callable_format,
    bind_computed_format,
    connect_child_signals,
    create_item_wrapper,
    create_styled_widget,
    dispose_widget_proxies,
    rebind_child_widgets,
    resolve_sort,
    setup_repeater_layout,
)
from .utils.common import PLACEHOLDER_RE, is_primitive_type
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
        field_name: str | None = None,
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
            object_name: objectName to set on each created widget (None = use class name).
            css_classes: CSS classes to apply to each created widget.
            signal_connections: Signal connections from child widget to parent handlers.
                e.g., {"on_delete": "remove_item(#key)"} connects child.on_delete
                to parent.remove_item with the dict key.
            parent_widget: The parent Widget instance for resolving handler methods.
            field_name: Field/attribute name to set as 'field' property on each widget.
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
        self._sort: bool | Callable[[K], Any] | None = resolve_sort(sort, parent_widget)
        self._is_key_primitive = is_primitive_type(key_type)
        self._is_value_primitive = is_primitive_type(value_type)
        self._object_name = object_name
        self._css_classes = css_classes or []
        self._signal_connections = signal_connections or {}
        self._parent_widget = parent_widget
        self._field_name = field_name

        # Track: key -> (widget, key_wrapper, value_wrapper)
        # key_wrapper is Observable[K] for primitives, ObservableProxy[K] for objects
        # value_wrapper is Observable[V] for primitives, ObservableProxy[V] for objects
        self._entries: dict[K, tuple[QWidget, Observable[Any] | ObservableProxy[Any], Observable[Any] | ObservableProxy[Any]]] = {}
        # Maintain insertion order for layout
        self._key_order: list[K] = []
        # Track layout ordering for sorted display
        self._layout_order: list[K] = []  # Keys in display order

        # Setup layout
        self._layout = setup_repeater_layout(self, layout_type)

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

    def _create_key_wrapper(self, key: K) -> Observable[Any] | ObservableProxy[Any]:
        """Create the appropriate wrapper for a key."""
        return create_item_wrapper(key, self._key_type)

    def _create_value_wrapper(self, value: V) -> Observable[Any] | ObservableProxy[Any]:
        """Create the appropriate wrapper for a value."""
        return create_item_wrapper(value, self._value_type)

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
        return create_styled_widget(
            self._widget_type,
            self._widget_args,
            self._widget_kwargs,
            self._object_name,
            self._css_classes,
            self._widget_props,
            self._field_name,
        )

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
            # DictWidgetRepeater callable takes (key, value), wrap to single-arg
            def make_dict_formatter(
                kw: Observable[Any] | ObservableProxy[Any],
                vw: Observable[Any] | ObservableProxy[Any],
                f: Callable[[Any, Any], str],
            ) -> Callable[[Any], str]:
                def formatter(_: Any) -> str:
                    k = kw.get() if isinstance(kw, Observable) else kw.unwrap()
                    v = vw.get() if isinstance(vw, Observable) else vw.unwrap()
                    return f(k, v)

                return formatter

            bind_callable_format(widget, value_wrapper, make_dict_formatter(key_wrapper, value_wrapper, bind_expr))
            # Also subscribe to key changes
            if isinstance(key_wrapper, Observable):
                from .bindings.registry import get_binding_registry

                registry = get_binding_registry()
                adapter = registry.get(widget, registry.get_default_prop(widget))
                if adapter and adapter.setter:
                    setter = adapter.setter
                    key_wrapper.on_change(lambda _: setter(widget, make_dict_formatter(key_wrapper, value_wrapper, bind_expr)(None)))
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
        bind_computed_format(widget, value_wrapper, bind_expr, key_wrapper=key_wrapper)

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

    def _create_and_add_widget(self, key: K, value: V) -> None:
        """Create a widget for a key-value pair and add it to the layout."""
        key_wrapper = self._create_key_wrapper(key)
        value_wrapper = self._create_value_wrapper(value)
        widget = self._create_widget_for_entry()

        # If the widget is a Widget[T] with a record type, assign the value wrapper as its record
        # This ensures the widget and the repeater share the same ObservableProxy
        widget_config = getattr(type(widget), "_qtpie_config", None)
        if widget_config is not None and getattr(widget_config, "record_type", None) is not None:
            from .bindings.apply import apply_auto_bindings
            from .variable import RecordVariable

            if isinstance(value_wrapper, ObservableProxy):
                record_var: RecordVariable[Any] = RecordVariable(value_wrapper)
                widget.record = record_var  # type: ignore[union-attr]
            else:
                # Primitive type - just set the value directly
                widget.record = value  # type: ignore[union-attr]

            # Re-apply auto-bindings now that record is populated
            apply_auto_bindings(widget, widget_config)  # type: ignore[arg-type]

            # Also re-apply bindings on child Widget[T] instances that bind to parent's record
            rebind_child_widgets(widget)

        self._bind_widget_to_entry(widget, key, key_wrapper, value_wrapper)
        connect_child_signals(widget, value_wrapper, self._signal_connections, self._parent_widget, key_wrapper=key_wrapper)

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
            widget, key_wrapper, value_wrapper = self._entries.pop(key)
            self._key_order.remove(key)
            if key in self._layout_order:
                self._layout_order.remove(key)

            # Dispose proxies before deleting widget
            dispose_widget_proxies(widget)
            if isinstance(key_wrapper, ObservableProxy):
                key_wrapper.dispose()
            if isinstance(value_wrapper, ObservableProxy):
                value_wrapper.dispose()

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
                connect_child_signals(new_widget, new_value_wrapper, self._signal_connections, self._parent_widget, key_wrapper=key_wrapper)

                self._entries[key] = (new_widget, key_wrapper, new_value_wrapper)
                self._layout.insertWidget(index, new_widget)

    def _on_clear(self, removed_items: dict[K, V]) -> None:
        """Handle dict clear."""
        # Remove all widgets
        for widget, key_wrapper, value_wrapper in self._entries.values():
            # Dispose proxies before deleting widget
            dispose_widget_proxies(widget)
            if isinstance(key_wrapper, ObservableProxy):
                key_wrapper.dispose()
            if isinstance(value_wrapper, ObservableProxy):
                value_wrapper.dispose()
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

    @property
    def widgets(self) -> list[QWidget]:
        """Get all widgets as a list (in insertion order)."""
        return [self._entries[key][0] for key in self._key_order]

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
