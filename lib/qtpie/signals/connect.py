"""Shared signal connection logic for QtPie modules."""

from collections.abc import Callable
from typing import Any

from qtpie.utils import is_signal
from qtpie.utils.common import resolve_signal_from_hierarchy


def connect_item_signals(
    context: Any,
    item: Any,
    item_name: str,
    signal_connections: dict[str, Any],
    create_expression_handler: Callable[[Any, str], Callable[..., Any]],
) -> None:
    """Connect signals for a single item (widget or action).

    Args:
        context: The context object (Widget, Window, App, or Menu instance).
        item: The item (widget or action) whose signals to connect.
        item_name: Name of the item (for error messages).
        signal_connections: Dict of signal_name -> handler from NewField.
        create_expression_handler: Factory for creating expression handlers.
    """
    from qtpie.bindings import is_format_string

    for signal_name, handler in signal_connections.items():
        signal = getattr(item, signal_name, None)
        if signal is None:
            continue

        if isinstance(handler, str):
            # Check if it's an expression (format string with {})
            if is_format_string(handler):
                # Expression handler - create a wrapper that evaluates the expression
                expr_handler = create_expression_handler(context, handler)
                signal.connect(expr_handler)
            else:
                # Simple string handler - could be method name or signal name
                # First check on context itself
                target = getattr(context, handler, None)

                if target is not None:
                    # Found on context - connect directly
                    if is_signal(target):
                        signal.connect(target)
                    elif callable(target):
                        signal.connect(target)
                    else:
                        raise AttributeError(f'{type(context).__name__}.{handler} is not callable or a Signal for signal connection {item_name}.{signal_name}="{handler}"')
                else:
                    # Not found on context - use lazy resolution wrapper
                    # This defers hierarchy lookup to emit time, when parent() is set
                    lazy_handler = create_lazy_hierarchy_handler(context, handler, item_name, signal_name)
                    signal.connect(lazy_handler)
        elif callable(handler):
            # Direct callable (lambda, function, etc.)
            signal.connect(handler)


def create_lazy_hierarchy_handler(
    context: Any,
    handler_name: str,
    item_name: str,
    signal_name: str,
) -> Callable[..., None]:
    """Create a wrapper that resolves the handler from hierarchy at emit time.

    This allows signal connections like clicked="on_parent_action" to work
    even when the widget isn't parented yet at connection time. The handler
    is looked up lazily when the signal is actually emitted.
    """

    def lazy_handler(*args: Any, **kwargs: Any) -> None:
        # First check on context (may have been added since connection time)
        target = getattr(context, handler_name, None)

        # If still not found, search up the parent hierarchy
        if target is None:
            target = resolve_signal_from_hierarchy(context, handler_name)

        if target is None:
            raise AttributeError(
                f"{type(context).__name__} has no method or signal '{handler_name}' for signal connection {item_name}.{signal_name}=\"{handler_name}\" (checked context and parent hierarchy)"
            )

        if is_signal(target):
            # Target is a Signal - emit it
            target.emit(*args, **kwargs)  # type: ignore[union-attr]
        elif callable(target):
            # Target is a method - call it
            target(*args, **kwargs)
        else:
            raise AttributeError(f'{type(context).__name__}.{handler_name} is not callable or a Signal for signal connection {item_name}.{signal_name}="{handler_name}"')

    return lazy_handler


def connect_field_signals(
    context: Any,
    fields: dict[str, Any],
    create_expression_handler: Callable[[Any, str], Callable[..., Any]],
) -> None:
    """Connect signals declared in new() to handlers.

    This is shared logic used by Widget, Window, App, and Menu.

    Args:
        context: The context object (Widget, Window, App, or Menu instance).
        fields: Dictionary of field_name -> NewField from config.fields.
        create_expression_handler: Factory for creating expression handlers,
            e.g., lambda ctx, expr: create_signal_expression_handler(ctx, expr, ["#widget"]).
    """
    for name, field in fields.items():
        if not field.signal_connections:
            continue

        instance = getattr(context, name, None)
        if instance is None:
            continue

        connect_item_signals(context, instance, name, field.signal_connections, create_expression_handler)
