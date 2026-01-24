"""WidgetRepeater - Container that manages repeated widgets bound to list items."""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from observant import Observable, ObservableList, ObservableProxy
from qtpy.QtWidgets import QWidget

from .bindings import bind
from .repeaters.utils import bind_callable_format, bind_computed_format, connect_child_signals, create_item_wrapper, create_styled_widget, rebind_child_widgets, resolve_sort, setup_repeater_layout
from .utils.common import PLACEHOLDER_RE, is_primitive_type
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
        field_name: str | None = None,
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
            object_name: objectName to set on each created widget (None = use class name).
            css_classes: CSS classes to apply to each created widget.
            signal_connections: Signal connections from child widget to parent handlers.
                e.g., {"on_delete": "remove_item(#index)"} connects child.on_delete
                to parent.remove_item with the item index.
            parent_widget: The parent Widget instance for resolving handler methods.
            field_name: Field/attribute name to set as 'field' property on each widget.
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
        self._sort: bool | Callable[[T], Any] | None = resolve_sort(sort, parent_widget)
        self._is_primitive = is_primitive_type(item_type)
        self._object_name = object_name
        self._css_classes = css_classes or []
        self._signal_connections = signal_connections or {}
        self._parent_widget = parent_widget
        self._field_name = field_name

        # Track: (widget, item_wrapper, index_holder)
        # item_wrapper is Observable[T] for primitives, ObservableProxy[T] for objects
        # index_holder is [int] so closures can access updated index
        self._items: list[tuple[QWidget, Observable[Any] | ObservableProxy[Any], list[int]]] = []

        # Track layout ordering for sorted display
        self._layout_indices: list[int] = []  # Maps layout position -> list index

        # Setup layout
        self._layout = setup_repeater_layout(self, layout_type)

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

    def _create_item_wrapper(self, item: T) -> Observable[Any] | ObservableProxy[Any]:
        """Create the appropriate wrapper for an item."""
        return create_item_wrapper(item, self._item_type)

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
        return create_styled_widget(
            self._widget_type,
            self._widget_args,
            self._widget_kwargs,
            self._object_name,
            self._css_classes,
            self._widget_props,
            self._field_name,
        )

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
            bind_callable_format(widget, wrapper, bind_expr)
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
                bind_computed_format(widget, wrapper, bind_expr, index_holder=index_holder)
            elif isinstance(wrapper, ObservableProxy):
                # Property on object - get Observable for that property
                prop_obs: Observable[Any] = getattr(wrapper, prop_name)
                var = Variable(prop_obs)
                bind(var).to(widget)
                # No need for sync - ObservableProxy auto-syncs to object
            else:
                # Primitive with property access doesn't make sense, fall back to format
                bind_computed_format(widget, wrapper, bind_expr, index_holder=index_holder)
            return

        # Case 3: Format string with multiple placeholders - one-way computed binding
        bind_computed_format(widget, wrapper, bind_expr, index_holder=index_holder)

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

    def _create_and_add_widget(self, index: int, item: T) -> None:
        """Create a widget for an item and add it to the layout."""
        wrapper = self._create_item_wrapper(item)
        widget = self._create_widget_for_item()
        index_holder = [index]

        # If the widget is a Widget[T] with a record type, assign the wrapper as its record
        # This ensures the widget and the repeater share the same ObservableProxy
        widget_config = getattr(type(widget), "_qtpie_config", None)
        if widget_config is not None and getattr(widget_config, "record_type", None) is not None:
            from .bindings.apply import apply_auto_bindings
            from .variable import RecordVariable

            if isinstance(wrapper, ObservableProxy):
                record_var: RecordVariable[Any] = RecordVariable(wrapper)
                widget.record = record_var  # type: ignore[union-attr]
            else:
                # Primitive type - just set the value directly
                widget.record = item  # type: ignore[union-attr]

            # Re-apply auto-bindings now that record is populated
            # This is needed because the widget's __init__ ran before we set up the record
            apply_auto_bindings(widget, widget_config)  # type: ignore[arg-type]

            # Also re-apply bindings on child Widget[T] instances that bind to parent's record
            rebind_child_widgets(widget)

        self._bind_widget_to_item(widget, wrapper, index_holder)
        connect_child_signals(widget, wrapper, self._signal_connections, self._parent_widget, index_holder=index_holder)

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
                connect_child_signals(new_widget, new_wrapper, self._signal_connections, self._parent_widget, index_holder=index_holder)

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

    @property
    def widgets(self) -> list[QWidget]:
        """Get all widgets as a list."""
        return [w for w, _, _ in self._items]

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
