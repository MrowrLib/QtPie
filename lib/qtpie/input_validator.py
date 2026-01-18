"""Input validator support for widgets with setValidator().

Creates QValidator instances from various input formats:
- Regex string: QRegularExpressionValidator
- Callable[[str], bool]: Simple predicate validator
- Callable[[str, int], QValidator.State]: Full control validator
- Method name string: Looked up on widget instance

Works with QLineEdit, QComboBox (editable), and any widget with setValidator().
"""

import inspect
from collections.abc import Callable
from typing import Any, override

from PySide6.QtCore import QEvent, QObject, QRegularExpression
from PySide6.QtGui import QKeyEvent, QRegularExpressionValidator, QValidator
from PySide6.QtWidgets import QWidget


class InputFilterEventFilter(QObject):
    """Event filter that blocks invalid character input.

    This is necessary because Qt's QValidator doesn't reliably block input
    when the field is already in an invalid state (e.g., setText() with invalid content).
    """

    def __init__(self, predicate: Callable[[str], bool], widget: QWidget) -> None:
        super().__init__(widget)
        self._predicate = predicate
        self._widget = widget

    @override
    def eventFilter(self, obj: QObject, event: QEvent) -> bool:  # pyright: ignore[reportIncompatibleMethodOverride]
        """Filter key press events to block invalid characters."""
        if event.type() == QEvent.Type.KeyPress and obj is self._widget:
            key_event = event
            if isinstance(key_event, QKeyEvent):
                text = key_event.text()
                # Only filter printable characters
                if text and text.isprintable():
                    # Check if this character alone would be valid
                    # (we check single char, not full text, to allow typing in invalid fields)
                    if not self._predicate(text):
                        # Block the character
                        return True
        return super().eventFilter(obj, event)


class PredicateValidator(QValidator):
    """Validator that wraps a simple predicate function.

    The predicate takes the text and returns True (valid) or False (invalid).
    """

    def __init__(self, predicate: Callable[[str], bool], parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._predicate = predicate

    @override
    def validate(self, text: str, pos: int) -> tuple[QValidator.State, str, int]:  # pyright: ignore[reportIncompatibleMethodOverride]
        """Validate the input text."""
        try:
            if self._predicate(text):
                return QValidator.State.Acceptable, text, pos
            return QValidator.State.Invalid, text, pos
        except Exception:
            return QValidator.State.Invalid, text, pos


class FullValidator(QValidator):
    """Validator that wraps a function returning QValidator.State.

    The function takes (text, pos) and returns a QValidator.State.
    """

    def __init__(self, validator_fn: Callable[[str, int], QValidator.State], parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._validator_fn = validator_fn

    @override
    def validate(self, text: str, pos: int) -> tuple[QValidator.State, str, int]:  # pyright: ignore[reportIncompatibleMethodOverride]
        """Validate the input text."""
        try:
            state = self._validator_fn(text, pos)
            return state, text, pos
        except Exception:
            return QValidator.State.Invalid, text, pos


class MethodValidator(QValidator):
    """Validator that calls a method on the widget's parent.

    Supports both simple predicate (bool return) and full validator (State return).
    """

    def __init__(self, widget: QWidget, method_name: str) -> None:
        super().__init__(widget)
        self._widget = widget
        self._method_name = method_name
        self._method: Callable[..., Any] | None = None
        self._is_full_validator: bool | None = None

    def _find_method(self) -> Callable[..., Any] | None:
        """Find the validator method on parent widgets."""
        if self._method is not None:
            return self._method

        # Search up the parent hierarchy for the method
        parent = self._widget.parent()
        while parent:
            method = getattr(parent, self._method_name, None)
            if method is not None and callable(method):
                self._method = method
                # Check if it's a full validator (takes pos) or simple predicate
                sig = inspect.signature(method)
                # Account for 'self' parameter - method bound to instance
                params = list(sig.parameters.values())
                self._is_full_validator = len(params) >= 2
                return method
            parent = parent.parent()
        return None

    @override
    def validate(self, text: str, pos: int) -> tuple[QValidator.State, str, int]:  # pyright: ignore[reportIncompatibleMethodOverride]
        """Validate the input text."""
        method = self._find_method()
        if method is None:
            # Method not found - allow everything
            return QValidator.State.Acceptable, text, pos

        try:
            if self._is_full_validator:
                result = method(text, pos)
                if isinstance(result, QValidator.State):
                    return result, text, pos
                # Maybe it returns bool despite having pos param
                return (QValidator.State.Acceptable if result else QValidator.State.Invalid), text, pos
            else:
                result = method(text)
                if isinstance(result, QValidator.State):
                    return result, text, pos
                return (QValidator.State.Acceptable if result else QValidator.State.Invalid), text, pos
        except Exception:
            return QValidator.State.Invalid, text, pos


def create_validator(
    validator_spec: str | Callable[..., Any],
    widget: QWidget,
) -> QValidator:
    """Create a QValidator from a validator specification.

    Args:
        validator_spec: One of:
            - str (regex pattern): Creates QRegularExpressionValidator
            - str (method name, no regex chars): Creates MethodValidator
            - Callable[[str], bool]: Creates PredicateValidator
            - Callable[[str, int], State]: Creates FullValidator
        widget: The widget to validate (must have setValidator)

    Returns:
        A QValidator instance
    """
    if isinstance(validator_spec, str):
        # Check if it looks like a regex or a method name
        # Method names are simple identifiers, regexes have special chars
        if _is_method_name(validator_spec):
            return MethodValidator(widget, validator_spec)
        else:
            # Treat as regex pattern
            regex = QRegularExpression(validator_spec)
            return QRegularExpressionValidator(regex, widget)
    elif callable(validator_spec):
        # Check signature to determine if it's a simple predicate or full validator
        sig = inspect.signature(validator_spec)
        params = list(sig.parameters.values())
        if len(params) >= 2:
            # Full validator: (text, pos) -> State
            return FullValidator(validator_spec, widget)
        else:
            # Simple predicate: (text) -> bool
            return PredicateValidator(validator_spec, widget)
    else:
        raise TypeError(f"Invalid validator type: {type(validator_spec)}")


def _is_method_name(s: str) -> bool:
    """Check if a string looks like a method name vs a regex pattern.

    Method names are valid Python identifiers.
    Regex patterns typically have special characters.
    """
    return s.isidentifier()


def apply_validator(widget: QWidget, validator_spec: str | Callable[..., Any]) -> None:
    """Apply a validator to a widget.

    Args:
        widget: The widget to validate (must have setValidator method)
        validator_spec: The validator specification (see create_validator)
    """
    validator = create_validator(validator_spec, widget)
    widget.setValidator(validator)  # type: ignore[union-attr]

    # For predicate validators, also install an event filter to block invalid
    # characters. This is necessary because Qt's QValidator doesn't reliably
    # block input when the field is already in an invalid state.
    if callable(validator_spec):
        sig = inspect.signature(validator_spec)
        params = list(sig.parameters.values())
        if len(params) < 2:  # Simple predicate
            event_filter = InputFilterEventFilter(validator_spec, widget)
            widget.installEventFilter(event_filter)
