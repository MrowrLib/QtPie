"""ActionRepeater - Manages repeated QActions bound to list items in menus."""

import re
from collections.abc import Callable
from typing import Any

from observant import Observable, ObservableList, ObservableProxy
from qtpy.QtGui import QAction
from qtpy.QtWidgets import QMenu

# Regex to find placeholders like {#self}, {#index}, {name}, {age}
_PLACEHOLDER_RE = re.compile(r"\{(#?\w+(?:\.\w+)*)\}")


def _is_primitive_type(t: type | None) -> bool:
    """Check if type is a primitive."""
    return t in (str, int, float, bool, type(None))


class ActionRepeater[T]:
    """Manages repeated QActions bound to list items in a menu.

    Creates one QAction per list item. Uses granular callbacks (on_insert,
    on_remove, on_replace, on_clear) to efficiently sync the action list
    with the underlying ObservableList.

    Usage:
        # In a Menu with @newmenu decorator
        window_actions: list[QAction] = new(bind="_windows")
    """

    def __init__(
        self,
        menu: QMenu,
        observable_list: ObservableList[T],
        item_type: type | None,
        format_expr: str | Callable[[T], str] = "{#self}",
        triggered_handler: str | Callable[..., Any] | None = None,
        anchor_action: QAction | None = None,
    ) -> None:
        """Initialize the action repeater.

        Args:
            menu: The menu to add actions to.
            observable_list: The ObservableList to sync with.
            item_type: The type of items in the list (e.g., str, WindowInfo).
            format_expr: Format expression for action text (default "{#self}").
            triggered_handler: Method name or callable to connect to triggered signal.
            anchor_action: Action to insert before (for maintaining position with other items).
        """
        self._menu = menu
        self._obs_list = observable_list
        self._item_type = item_type
        self._format_expr: str | Callable[[T], str] = format_expr
        self._triggered_handler = triggered_handler
        self._anchor_action = anchor_action
        self._is_primitive = _is_primitive_type(item_type)

        # Track: (action, item_wrapper, index_holder)
        # item_wrapper is Observable[T] for primitives, ObservableProxy[T] for objects
        # index_holder is [int] so closures can access updated index
        self._items: list[tuple[QAction, Observable[Any] | ObservableProxy[Any], list[int]]] = []

        # Create initial actions for existing items
        for i, item in enumerate(observable_list):
            self._create_and_add_action(i, item)

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

    def _format_action_text(
        self,
        wrapper: Observable[Any] | ObservableProxy[Any],
        index_holder: list[int],
    ) -> str:
        """Compute the action text from the format expression."""
        format_expr = self._format_expr

        # Case: Callable formatter
        if callable(format_expr):
            if isinstance(wrapper, Observable):
                item = wrapper.get()
            else:
                item = wrapper.unwrap()
            return format_expr(item)

        # Case: Format string
        result = format_expr

        for match in _PLACEHOLDER_RE.finditer(format_expr):
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
                # Nested property on item: #self.name -> item.name
                prop_path = placeholder[6:]  # Remove "#self."
                if isinstance(wrapper, Observable):
                    value = self._resolve_property(wrapper.get(), prop_path)
                else:
                    value = self._resolve_property(wrapper, prop_path)
            elif isinstance(wrapper, ObservableProxy):
                # Property access on object
                value = self._resolve_property(wrapper, placeholder)
            else:
                value = f"<unknown:{placeholder}>"

            result = result.replace(full_match, str(value), 1)  # pyright: ignore[reportUnknownArgumentType]

        return result

    def _resolve_property(self, obj: Any, path: str) -> Any:
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

    def _create_action_for_item(
        self,
        wrapper: Observable[Any] | ObservableProxy[Any],
        index_holder: list[int],
    ) -> QAction:
        """Create a new action instance for an item."""
        text = self._format_action_text(wrapper, index_holder)
        action = QAction(text, self._menu)

        # Connect triggered handler
        if self._triggered_handler is not None:
            # Get the item for the handler
            def make_handler(
                w: Observable[Any] | ObservableProxy[Any],
            ) -> Callable[[], None]:
                def handler() -> None:
                    if isinstance(w, Observable):
                        item = w.get()
                    else:
                        item = w.unwrap()
                    if isinstance(self._triggered_handler, str):
                        method = getattr(self._menu, self._triggered_handler, None)
                        if method is not None:
                            method(item)
                    elif callable(self._triggered_handler):
                        self._triggered_handler(item)  # pyright: ignore[reportUnknownArgumentType]

                return handler

            action.triggered.connect(make_handler(wrapper))

        # Subscribe to wrapper changes to update text
        def on_change(_: Any, a: QAction = action, w: Observable[Any] | ObservableProxy[Any] = wrapper, i: list[int] = index_holder) -> None:
            a.setText(self._format_action_text(w, i))

        if isinstance(wrapper, Observable):
            wrapper.on_change(on_change)
        else:
            wrapper.on_change(lambda: on_change(None))

        return action

    def _get_insert_position(self, index: int) -> QAction | None:
        """Get the action to insert before, maintaining proper position."""
        if index < len(self._items):
            # Insert before existing action at this index
            return self._items[index][0]
        elif self._anchor_action is not None:
            # Insert before anchor
            return self._anchor_action
        else:
            # Append at end
            return None

    def _create_and_add_action(self, index: int, item: T) -> None:
        """Create an action for an item and add it to the menu."""
        wrapper = self._create_item_wrapper(item)
        index_holder = [index]
        action = self._create_action_for_item(wrapper, index_holder)

        # Insert at correct position
        before_action = self._get_insert_position(index)
        if before_action is not None:
            self._menu.insertAction(before_action, action)
        else:
            self._menu.addAction(action)

        self._items.insert(index, (action, wrapper, index_holder))

        # Update indices for items after this one
        for i in range(index + 1, len(self._items)):
            self._items[i][2][0] = i

    def _on_insert(self, index: int, item: T) -> None:
        """Handle item insertion."""
        self._create_and_add_action(index, item)

    def _on_remove(self, index: int, item: T) -> None:
        """Handle item removal."""
        if index < len(self._items):
            action, _, _ = self._items.pop(index)
            self._menu.removeAction(action)

            # Update indices for remaining items
            for i in range(index, len(self._items)):
                self._items[i][2][0] = i

    def _on_replace(self, index: int, old_item: T, new_item: T) -> None:
        """Handle item replacement."""
        if index < len(self._items):
            action, wrapper, index_holder = self._items[index]

            if isinstance(wrapper, Observable):
                # Primitives: just update the Observable (text updates via callback)
                wrapper.set(new_item)
            else:
                # Complex objects: remove old action and create new one
                self._menu.removeAction(action)

                new_wrapper = self._create_item_wrapper(new_item)
                new_action = self._create_action_for_item(new_wrapper, index_holder)

                # Insert at the same position
                before_action = self._get_insert_position(index + 1)
                if before_action is not None:
                    self._menu.insertAction(before_action, new_action)
                else:
                    self._menu.addAction(new_action)

                self._items[index] = (new_action, new_wrapper, index_holder)

    def _on_clear(self, removed_items: list[T]) -> None:
        """Handle list clear."""
        for action, _, _ in self._items:
            self._menu.removeAction(action)
        self._items.clear()

    def action_at(self, index: int) -> QAction | None:
        """Get the action at a specific index."""
        if 0 <= index < len(self._items):
            return self._items[index][0]
        return None

    def action_count(self) -> int:
        """Get the number of actions."""
        return len(self._items)

    # List-like interface
    def __getitem__(self, index: int) -> QAction:
        """Get action at index."""
        if index < 0:
            index = len(self._items) + index
        if 0 <= index < len(self._items):
            return self._items[index][0]
        raise IndexError(f"index {index} out of range")

    def __len__(self) -> int:
        """Return number of actions."""
        return len(self._items)

    def __iter__(self):
        """Iterate over actions."""
        for action, _, _ in self._items:
            yield action
