"""Helper functions for selection bindings."""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from qtpy.QtWidgets import QWidget


def subscribe_to_root_variable_change(
    root_variable: Any,
    var_path: str | None,
    resolve_fn: Callable[..., Any] | None,
    host: QWidget,
    container: dict[str, Any],
    updating: dict[str, bool],
    key_prefix: str,
    widget_id: int,
    type_hint: type | None,
    on_value_resolved: Callable[[Any], None],
) -> None:
    """Subscribe to root variable changes for nested path re-resolution.

    When root_variable changes (e.g., workspace None -> Workspace), re-resolves
    var_path and calls on_value_resolved with the new value.

    This handles the common pattern where nested paths like "workspace?.selected_index"
    need to be re-resolved when the root Variable (workspace) changes from None to
    a real object.

    Args:
        root_variable: The root Variable to subscribe to
        var_path: The nested path to re-resolve (e.g., "workspace?.selected_index")
        resolve_fn: Function to resolve paths (resolve_or_create_variable_fn)
        host: The Widget/Window instance
        container: Mutable dict for tracking subscription state
        updating: Dict with "flag" key to prevent circular updates
        key_prefix: Unique prefix for subscription key (e.g., "combo_index")
        widget_id: id(widget) for unique key generation
        type_hint: Type hint for resolution (int, str, None, etc.)
        on_value_resolved: Callback receiving the resolved value (only called if not None)
    """
    if root_variable is None or var_path is None or resolve_fn is None:
        return

    from observant import Observable, ObservableList, ObservableProxy

    from qtpie.variable import Variable as VarType

    root_subscribed_key = f"{key_prefix}_root_subscribed_{widget_id}"
    if container.get(root_subscribed_key, False):
        return  # Already subscribed

    container[root_subscribed_key] = True

    def on_root_variable_change(*_args: Any) -> None:
        """Re-resolve var_path when root Variable changes."""
        if updating["flag"]:
            return

        new_source = resolve_fn(host, var_path, type_hint)
        if new_source is None:
            return

        # Extract value from Variable, Observable, ObservableProxy, or ObservableList
        new_value: Any = None  # pyright: ignore[reportUnknownVariableType]
        if isinstance(new_source, VarType):
            new_value = new_source.value  # pyright: ignore[reportUnknownMemberType,reportUnknownVariableType]
        elif isinstance(new_source, Observable):
            new_value = new_source.get()  # pyright: ignore[reportUnknownMemberType,reportUnknownVariableType]
        elif isinstance(new_source, ObservableProxy):
            new_value = new_source.unwrap()  # pyright: ignore[reportUnknownMemberType,reportUnknownVariableType]
        elif isinstance(new_source, ObservableList):
            new_value = list(new_source)  # pyright: ignore[reportUnknownArgumentType,reportUnknownVariableType]

        if new_value is not None:
            updating["flag"] = True
            try:
                on_value_resolved(new_value)
            finally:
                updating["flag"] = False

    root_variable.on_change(on_root_variable_change)  # pyright: ignore[reportUnknownMemberType]
