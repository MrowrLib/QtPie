"""Shared signal connection logic for QtPie modules."""

from collections.abc import Callable
from typing import Any, override

from qtpy.QtCore import QEvent, QObject, Qt

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

    Event Consumption:
        Handlers can return True to consume the event (stop propagation).
        This is useful when a child widget handles an event and doesn't want
        it to bubble up to parent widgets.

        Example:
            def on_enter_key(self) -> bool:
                self.do_something()
                return True  # Consume the event, don't propagate to parent
    """

    def __init__(self, parent: QObject) -> None:
        super().__init__(parent)
        # All handlers use Callable[..., bool | None] because they accept optional event
        # and return optional bool for event consumption
        # Focus events
        self.on_focus: Callable[..., bool | None] | None = None
        self.on_blur: Callable[..., bool | None] | None = None
        # Mouse events
        self.on_mouse_enter: Callable[..., bool | None] | None = None
        self.on_mouse_leave: Callable[..., bool | None] | None = None
        self.on_mouse_press: Callable[..., bool | None] | None = None
        self.on_mouse_release: Callable[..., bool | None] | None = None
        self.on_mouse_double_click: Callable[..., bool | None] | None = None
        self.on_mouse_move: Callable[..., bool | None] | None = None
        self.on_wheel: Callable[..., bool | None] | None = None
        # Keyboard events
        self.on_key_press: Callable[..., bool | None] | None = None
        self.on_key_release: Callable[..., bool | None] | None = None
        self.on_enter_key: Callable[..., bool | None] | None = None
        self.on_delete_key: Callable[..., bool | None] | None = None
        # Widget events
        self.on_show: Callable[..., bool | None] | None = None
        self.on_hide: Callable[..., bool | None] | None = None
        self.on_close: Callable[..., bool | None] | None = None
        self.on_resize: Callable[..., bool | None] | None = None
        self.on_move: Callable[..., bool | None] | None = None
        # Drag & drop events
        self.on_drag_enter: Callable[..., bool | None] | None = None
        self.on_drag_leave: Callable[..., bool | None] | None = None
        self.on_drag_move: Callable[..., bool | None] | None = None
        self.on_drop: Callable[..., bool | None] | None = None

    @override
    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        t = event.type()
        consumed = False

        # Focus events (no event data needed)
        if t == QEvent.Type.FocusIn and self.on_focus:
            if self.on_focus() is True:
                consumed = True
        elif t == QEvent.Type.FocusOut and self.on_blur:
            if self.on_blur() is True:
                consumed = True

        # Mouse events
        elif t == QEvent.Type.Enter and self.on_mouse_enter:
            if self.on_mouse_enter() is True:
                consumed = True
        elif t == QEvent.Type.Leave and self.on_mouse_leave:
            if self.on_mouse_leave() is True:
                consumed = True
        elif t == QEvent.Type.MouseButtonPress and self.on_mouse_press:
            if self.on_mouse_press(event) is True:
                consumed = True
        elif t == QEvent.Type.MouseButtonRelease and self.on_mouse_release:
            if self.on_mouse_release(event) is True:
                consumed = True
        elif t == QEvent.Type.MouseButtonDblClick and self.on_mouse_double_click:
            if self.on_mouse_double_click(event) is True:
                consumed = True
        elif t == QEvent.Type.MouseMove and self.on_mouse_move:
            if self.on_mouse_move(event) is True:
                consumed = True
        elif t == QEvent.Type.Wheel and self.on_wheel:
            if self.on_wheel(event) is True:
                consumed = True

        # Keyboard events
        elif t == QEvent.Type.KeyPress:
            if self.on_key_press:
                if self.on_key_press(event) is True:
                    consumed = True
            # Specific key shortcuts (only if not already consumed by general handler)
            if not consumed:
                key = event.key()  # type: ignore[union-attr]
                if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter) and self.on_enter_key:
                    if self.on_enter_key(event) is True:
                        consumed = True
                elif key == Qt.Key.Key_Delete and self.on_delete_key:
                    if self.on_delete_key(event) is True:
                        consumed = True
        elif t == QEvent.Type.KeyRelease and self.on_key_release:
            if self.on_key_release(event) is True:
                consumed = True

        # Widget events
        elif t == QEvent.Type.Show and self.on_show:
            if self.on_show() is True:
                consumed = True
        elif t == QEvent.Type.Hide and self.on_hide:
            if self.on_hide() is True:
                consumed = True
        elif t == QEvent.Type.Close and self.on_close:
            if self.on_close(event) is True:
                consumed = True
        elif t == QEvent.Type.Resize and self.on_resize:
            if self.on_resize(event) is True:
                consumed = True
        elif t == QEvent.Type.Move and self.on_move:
            if self.on_move(event) is True:
                consumed = True

        # Drag & drop events
        elif t == QEvent.Type.DragEnter and self.on_drag_enter:
            if self.on_drag_enter(event) is True:
                consumed = True
        elif t == QEvent.Type.DragLeave and self.on_drag_leave:
            if self.on_drag_leave() is True:
                consumed = True
        elif t == QEvent.Type.DragMove and self.on_drag_move:
            if self.on_drag_move(event) is True:
                consumed = True
        elif t == QEvent.Type.Drop and self.on_drop:
            if self.on_drop(event) is True:
                consumed = True

        return consumed


def _handler_accepts_event(handler: Callable[..., Any]) -> bool:
    """Check if a handler function accepts an event parameter.

    Uses introspection to determine if the handler wants the QEvent passed to it.
    Handles both regular functions and bound methods.
    """
    import inspect

    try:
        sig = inspect.signature(handler)
        params = list(sig.parameters.values())
        # For bound methods, 'self' is not in the signature
        # For regular functions, count all parameters
        # Handler accepts event if it has at least one parameter (after self for methods)
        return len(params) >= 1
    except (ValueError, TypeError):
        # Can't inspect (e.g., built-in), assume no event parameter
        return False


def _wrap_handler_for_event_consumption(
    handler: Callable[..., Any],
    pass_event: bool,
) -> Callable[..., bool | None]:
    """Wrap a handler to support optional event parameter and return value capture.

    The wrapped handler:
    1. Checks if the original handler accepts an event parameter
    2. Calls the handler with or without the event based on its signature
    3. Returns True if the handler returned True (event consumed), else None

    Args:
        handler: The resolved callable to wrap.
        pass_event: If True, the event is available to pass (e.g., keyboard events).

    Returns:
        A wrapper that takes optional (event) and returns bool | None.
    """
    accepts_event = _handler_accepts_event(handler)

    def wrapper(event: QEvent | None = None) -> bool | None:
        if pass_event and accepts_event and event is not None:
            result = handler(event)
        else:
            result = handler()
        return True if result is True else None

    return wrapper


def _resolve_event_handler(
    context: Any,
    handler: str | Callable[..., Any],
    item_name: str,
    event_name: str,
    pass_event: bool = False,
) -> Callable[[QEvent], bool | None]:
    """Resolve an event handler to a callable.

    Supports the same patterns as signal handlers:
    - Direct callable (lambda, function)
    - Method name on context
    - Method/signal name on parent hierarchy
    - Expression strings with {}

    Event Consumption:
        Handlers can return True to consume the event and stop propagation.
        If a handler returns True, the event won't bubble up to parent widgets.

    Optional Event Parameter:
        Handlers can optionally accept the QEvent as their first parameter.
        The system uses introspection to detect this:
        - def on_enter_key(self): ...          # No event
        - def on_enter_key(self, event): ...   # Receives QKeyEvent

    Args:
        context: The context object (Widget, Window, App instance).
        handler: The handler (string name, callable, or expression).
        item_name: Name of the widget (for error messages).
        event_name: Name of the event (for error messages).
        pass_event: If True, the event is available to pass to the handler.

    Returns:
        A callable that takes (event) and returns bool | None.
    """
    from qtpie.bindings import is_format_string
    from qtpie.signals.expression_handler import create_signal_expression_handler

    if callable(handler) and not isinstance(handler, str):
        return _wrap_handler_for_event_consumption(handler, pass_event)

    # handler is str at this point
    if is_format_string(handler):
        # Expression handler - expressions don't support return values
        expr_handler = create_signal_expression_handler(context, handler, ["#widget"])
        return _wrap_handler_for_event_consumption(expr_handler, pass_event=False)

    # Try to find on context first
    target = getattr(context, handler, None)
    if target is not None:
        if is_signal(target):
            return lambda event, t=target: (t.emit(), None)[1]  # type: ignore[misc,return-value]
        elif callable(target):
            return _wrap_handler_for_event_consumption(target, pass_event)
        else:
            raise AttributeError(f'{type(context).__name__}.{handler} is not callable or a Signal for {event_name}="{handler}"')

    # Use lazy resolution for hierarchy lookup
    def lazy_event_handler(event: QEvent | None = None, handler_name: str = handler) -> bool | None:
        resolved: Any = getattr(context, handler_name, None)
        if resolved is None:
            resolved = resolve_signal_from_hierarchy(context, handler_name)

        if resolved is None:
            raise AttributeError(f"{type(context).__name__} has no method or signal '{handler_name}' for {item_name}.{event_name}=\"{handler_name}\"")

        if is_signal(resolved):
            resolved.emit()
            return None
        elif callable(resolved):
            # Check if handler accepts event parameter
            accepts_event = _handler_accepts_event(resolved)
            if pass_event and accepts_event and event is not None:
                result = resolved(event)
            else:
                result = resolved()
            return True if result is True else None
        else:
            raise AttributeError(f'{type(context).__name__}.{handler_name} is not callable or a Signal for {event_name}="{handler_name}"')

    return lazy_event_handler


# Event name -> (NewField attribute, event available to handler)
# If True, handlers can optionally accept the event as a parameter.
# The system uses introspection to detect if the handler wants the event.
_EVENT_MAPPINGS: dict[str, tuple[str, bool]] = {
    # Focus (no event data useful)
    "onFocus": ("on_focus", False),
    "onBlur": ("on_blur", False),
    # Mouse (event has position, button, modifiers)
    "onMouseEnter": ("on_mouse_enter", False),
    "onMouseLeave": ("on_mouse_leave", False),
    "onMousePress": ("on_mouse_press", True),
    "onMouseRelease": ("on_mouse_release", True),
    "onMouseDoubleClick": ("on_mouse_double_click", True),
    "onMouseMove": ("on_mouse_move", True),
    "onWheel": ("on_wheel", True),
    # Keyboard (event has key, modifiers, text)
    "onKeyPress": ("on_key_press", True),
    "onKeyRelease": ("on_key_release", True),
    "onEnterKey": ("on_enter_key", True),  # Event available for modifiers, etc.
    "onDeleteKey": ("on_delete_key", True),  # Event available for modifiers, etc.
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
