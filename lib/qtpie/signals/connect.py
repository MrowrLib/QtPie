"""Shared signal connection logic for QtPie modules."""

from collections.abc import Callable
from typing import Any, override

from qtpy.QtCore import QEvent, QObject

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


class _WidgetEventFilter(QObject):
    """Event filter that intercepts various Qt events and calls handlers.

    Only installed if at least one handler is set. Uses direct attribute checks
    for performance - no dict lookups in the hot path.
    """

    def __init__(self, parent: QObject) -> None:
        super().__init__(parent)
        # Focus events
        self.on_focus: Callable[[], None] | None = None
        self.on_blur: Callable[[], None] | None = None
        # Mouse events
        self.on_mouse_enter: Callable[[], None] | None = None
        self.on_mouse_leave: Callable[[], None] | None = None
        self.on_mouse_press: Callable[[QEvent], None] | None = None
        self.on_mouse_release: Callable[[QEvent], None] | None = None
        self.on_mouse_double_click: Callable[[QEvent], None] | None = None
        self.on_mouse_move: Callable[[QEvent], None] | None = None
        self.on_wheel: Callable[[QEvent], None] | None = None
        # Keyboard events
        self.on_key_press: Callable[[QEvent], None] | None = None
        self.on_key_release: Callable[[QEvent], None] | None = None
        # Widget events
        self.on_show: Callable[[], None] | None = None
        self.on_hide: Callable[[], None] | None = None
        self.on_close: Callable[[QEvent], None] | None = None
        self.on_resize: Callable[[QEvent], None] | None = None
        self.on_move: Callable[[QEvent], None] | None = None
        # Drag & drop events
        self.on_drag_enter: Callable[[QEvent], None] | None = None
        self.on_drag_leave: Callable[[], None] | None = None
        self.on_drag_move: Callable[[QEvent], None] | None = None
        self.on_drop: Callable[[QEvent], None] | None = None

    @override
    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        t = event.type()

        # Focus events (no event data needed)
        if t == QEvent.Type.FocusIn and self.on_focus:
            self.on_focus()
        elif t == QEvent.Type.FocusOut and self.on_blur:
            self.on_blur()

        # Mouse events
        elif t == QEvent.Type.Enter and self.on_mouse_enter:
            self.on_mouse_enter()
        elif t == QEvent.Type.Leave and self.on_mouse_leave:
            self.on_mouse_leave()
        elif t == QEvent.Type.MouseButtonPress and self.on_mouse_press:
            self.on_mouse_press(event)
        elif t == QEvent.Type.MouseButtonRelease and self.on_mouse_release:
            self.on_mouse_release(event)
        elif t == QEvent.Type.MouseButtonDblClick and self.on_mouse_double_click:
            self.on_mouse_double_click(event)
        elif t == QEvent.Type.MouseMove and self.on_mouse_move:
            self.on_mouse_move(event)
        elif t == QEvent.Type.Wheel and self.on_wheel:
            self.on_wheel(event)

        # Keyboard events
        elif t == QEvent.Type.KeyPress and self.on_key_press:
            self.on_key_press(event)
        elif t == QEvent.Type.KeyRelease and self.on_key_release:
            self.on_key_release(event)

        # Widget events
        elif t == QEvent.Type.Show and self.on_show:
            self.on_show()
        elif t == QEvent.Type.Hide and self.on_hide:
            self.on_hide()
        elif t == QEvent.Type.Close and self.on_close:
            self.on_close(event)
        elif t == QEvent.Type.Resize and self.on_resize:
            self.on_resize(event)
        elif t == QEvent.Type.Move and self.on_move:
            self.on_move(event)

        # Drag & drop events
        elif t == QEvent.Type.DragEnter and self.on_drag_enter:
            self.on_drag_enter(event)
        elif t == QEvent.Type.DragLeave and self.on_drag_leave:
            self.on_drag_leave()
        elif t == QEvent.Type.DragMove and self.on_drag_move:
            self.on_drag_move(event)
        elif t == QEvent.Type.Drop and self.on_drop:
            self.on_drop(event)

        return False  # Don't block the event


def _resolve_event_handler(
    context: Any,
    handler: str | Callable[..., Any],
    item_name: str,
    event_name: str,
    pass_event: bool = False,
) -> Callable[..., None]:
    """Resolve an event handler to a callable.

    Supports the same patterns as signal handlers:
    - Direct callable (lambda, function)
    - Method name on context
    - Method/signal name on parent hierarchy
    - Expression strings with {}

    Args:
        context: The context object (Widget, Window, App instance).
        handler: The handler (string name, callable, or expression).
        item_name: Name of the widget (for error messages).
        event_name: Name of the event (for error messages).
        pass_event: If True, the handler receives the event object.
    """
    from qtpie.bindings import is_format_string
    from qtpie.signals.expression_handler import create_signal_expression_handler

    if callable(handler) and not isinstance(handler, str):
        return handler  # type: ignore[return-value]

    # handler is str at this point
    if is_format_string(handler):
        # Expression handler
        return create_signal_expression_handler(context, handler, ["#widget"])

    # Try to find on context first
    target = getattr(context, handler, None)
    if target is not None:
        if is_signal(target):
            return lambda *args, t=target: t.emit()  # type: ignore[misc]
        elif callable(target):
            return target  # type: ignore[return-value]
        else:
            raise AttributeError(f'{type(context).__name__}.{handler} is not callable or a Signal for {event_name}="{handler}"')

    # Use lazy resolution for hierarchy lookup
    def lazy_event_handler(*args: Any, handler_name: str = handler) -> None:
        resolved: Any = getattr(context, handler_name, None)
        if resolved is None:
            resolved = resolve_signal_from_hierarchy(context, handler_name)

        if resolved is None:
            raise AttributeError(f"{type(context).__name__} has no method or signal '{handler_name}' for {item_name}.{event_name}=\"{handler_name}\"")

        if is_signal(resolved):
            resolved.emit()
        elif callable(resolved):
            # Pass event if handler accepts it, otherwise call without args
            if pass_event and args:
                resolved(args[0])
            else:
                resolved()
        else:
            raise AttributeError(f'{type(context).__name__}.{handler_name} is not callable or a Signal for {event_name}="{handler_name}"')

    return lazy_event_handler


# Event name -> (NewField attribute, passes event to handler)
_EVENT_MAPPINGS: dict[str, tuple[str, bool]] = {
    # Focus (no event data)
    "onFocus": ("on_focus", False),
    "onBlur": ("on_blur", False),
    # Mouse
    "onMouseEnter": ("on_mouse_enter", False),
    "onMouseLeave": ("on_mouse_leave", False),
    "onMousePress": ("on_mouse_press", True),
    "onMouseRelease": ("on_mouse_release", True),
    "onMouseDoubleClick": ("on_mouse_double_click", True),
    "onMouseMove": ("on_mouse_move", True),
    "onWheel": ("on_wheel", True),
    # Keyboard
    "onKeyPress": ("on_key_press", True),
    "onKeyRelease": ("on_key_release", True),
    # Widget
    "onShow": ("on_show", False),
    "onHide": ("on_hide", False),
    "onClose": ("on_close", True),
    "onResize": ("on_resize", True),
    "onMove": ("on_move", True),
    # Drag & drop
    "onDragEnter": ("on_drag_enter", True),
    "onDragLeave": ("on_drag_leave", False),
    "onDragMove": ("on_drag_move", True),
    "onDrop": ("on_drop", True),
}


def connect_event_handlers(
    context: Any,
    widget: QObject,
    widget_name: str,
    event_handlers: dict[str, str | Callable[..., Any]],
) -> None:
    """Install event filter for event handlers on a widget.

    Args:
        context: The context object (Widget, Window, App instance).
        widget: The widget to install the event filter on.
        widget_name: Name of the widget (for error messages).
        event_handlers: Dict of event_name -> handler from NewField.
    """
    if not event_handlers:
        return

    event_filter = _WidgetEventFilter(widget)

    for event_name, handler in event_handlers.items():
        if event_name not in _EVENT_MAPPINGS:
            continue

        attr_name, pass_event = _EVENT_MAPPINGS[event_name]
        resolved = _resolve_event_handler(context, handler, widget_name, event_name, pass_event)
        setattr(event_filter, attr_name, resolved)

        # Enable mouse tracking if onMouseMove is used
        # Without this, MouseMove events only fire when a button is pressed
        if event_name == "onMouseMove":
            set_mouse_tracking = getattr(widget, "setMouseTracking", None)
            if set_mouse_tracking is not None:
                set_mouse_tracking(True)

    widget.installEventFilter(event_filter)


def connect_field_event_handlers(
    context: Any,
    fields: dict[str, Any],
) -> None:
    """Connect event handlers declared in new() to widgets.

    Args:
        context: The context object (Widget, Window, App instance).
        fields: Dictionary of field_name -> NewField from config.fields.
    """
    for name, field in fields.items():
        if not field.event_handlers:
            continue

        instance = getattr(context, name, None)
        if instance is None:
            continue

        connect_event_handlers(context, instance, name, field.event_handlers)
