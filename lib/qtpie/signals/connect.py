"""Shared signal connection logic for QtPie modules."""

from collections.abc import Callable
from typing import Any

from qtpie.utils import is_signal


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
                target = getattr(context, handler, None)
                if target is None:
                    raise AttributeError(f"{type(context).__name__} has no method or signal '{handler}' for signal connection {item_name}.{signal_name}=\"{handler}\"")

                if is_signal(target):
                    # Target is a Signal - connect signal-to-signal
                    signal.connect(target)
                elif callable(target):
                    # Target is a method
                    signal.connect(target)
                else:
                    raise AttributeError(f'{type(context).__name__}.{handler} is not callable or a Signal for signal connection {item_name}.{signal_name}="{handler}"')
        elif callable(handler):
            # Direct callable (lambda, function, etc.)
            signal.connect(handler)


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
