"""Binding registry for mapping widget types to their bindable properties."""

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from qtpy.QtCore import QObject
from qtpy.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDateEdit,
    QDateTimeEdit,
    QDial,
    QDoubleSpinBox,
    QFontComboBox,
    QKeySequenceEdit,
    QLabel,
    QLineEdit,
    QListWidget,
    QPlainTextEdit,
    QProgressBar,
    QRadioButton,
    QSlider,
    QSpinBox,
    QTextEdit,
    QTimeEdit,
)


@dataclass(frozen=True)
class BindingKey:
    """Key for looking up bindings in the registry."""

    widget_type: type[QObject]
    property_name: str


@dataclass
class BindingAdapter[TWidget: QObject, TValue]:
    """Adapter for binding a widget property to an observable."""

    getter: Callable[[TWidget], TValue] | None = None
    setter: Callable[[TWidget, TValue], None] | None = None
    signal_name: str | None = None


class BindingRegistry:
    """Registry of widget property bindings."""

    def __init__(self) -> None:
        self._bindings: dict[BindingKey, BindingAdapter[Any, Any]] = {}
        self._default_props: dict[type[QObject], str] = {}

    def add(self, key: BindingKey, adapter: BindingAdapter[Any, Any]) -> None:
        """Add a binding adapter to the registry."""
        self._bindings[key] = adapter

    def set_default_prop(self, widget_type: type[QObject], prop: str) -> None:
        """Set the default property for a widget type."""
        self._default_props[widget_type] = prop

    def get_default_prop(self, widget: QObject) -> str:
        """Get the default property for a widget, checking MRO."""
        for cls in type(widget).mro():
            if cls in self._default_props:
                return self._default_props[cls]
        return "text"  # fallback

    def get(self, widget: QObject, property_name: str) -> BindingAdapter[Any, Any] | None:
        """Get a binding adapter for a widget and property, checking MRO."""
        for cls in type(widget).mro():
            key = BindingKey(cls, property_name)
            if key in self._bindings:
                return self._bindings[key]
        return None


# Global registry instance
_binding_registry: BindingRegistry | None = None


def get_binding_registry() -> BindingRegistry:
    """Get the global binding registry, creating it if needed."""
    global _binding_registry
    if _binding_registry is None:
        _binding_registry = BindingRegistry()
        _register_default_bindings(_binding_registry)
    return _binding_registry


def register_binding[TWidget: QObject, TValue](
    widget_type: type[TWidget],
    property_name: str,
    *,
    getter: Callable[[TWidget], TValue] | None = None,
    setter: Callable[[TWidget, TValue], None] | None = None,
    signal: str | None = None,
    default: bool = False,
) -> None:
    """
    Register a binding adapter for a widget type and property.

    Args:
        widget_type: The Qt widget class (e.g., QLineEdit, QSpinBox)
        property_name: The property name to bind (e.g., "text", "value")
        getter: Function to get the current value from the widget
        setter: Function to set a value on the widget
        signal: Signal name that fires when the property changes
        default: If True, this property becomes the default for this widget type

    Example:
        register_binding(
            QSpinBox,
            "value",
            getter=lambda w: w.value(),
            setter=lambda w, v: w.setValue(int(v)),
            signal="valueChanged",
            default=True,
        )
    """
    registry = get_binding_registry()
    key = BindingKey(widget_type, property_name)

    adapter: BindingAdapter[TWidget, TValue] = BindingAdapter(
        getter=getter,
        setter=setter,
        signal_name=signal,
    )

    registry.add(key, adapter)

    if default:
        registry.set_default_prop(widget_type, property_name)


def _register_default_bindings(registry: BindingRegistry) -> None:
    """Register default bindings for common Qt widgets."""

    # QLineEdit - text
    registry.add(
        BindingKey(QLineEdit, "text"),
        BindingAdapter(
            getter=lambda w: w.text(),
            setter=lambda w, v: w.setText(str(v) if v is not None else ""),
            signal_name="textChanged",
        ),
    )
    registry.set_default_prop(QLineEdit, "text")

    # QLineEdit - placeholderText (one-way, no signal)
    registry.add(
        BindingKey(QLineEdit, "placeholderText"),
        BindingAdapter(
            getter=lambda w: w.placeholderText(),
            setter=lambda w, v: w.setPlaceholderText(str(v) if v is not None else ""),
            signal_name=None,
        ),
    )

    # QLabel - text (one-way, no signal)
    registry.add(
        BindingKey(QLabel, "text"),
        BindingAdapter(
            getter=lambda w: w.text(),
            setter=lambda w, v: w.setText(str(v) if v is not None else ""),
            signal_name=None,
        ),
    )
    registry.set_default_prop(QLabel, "text")

    # QTextEdit - text
    registry.add(
        BindingKey(QTextEdit, "text"),
        BindingAdapter(
            getter=lambda w: w.toPlainText(),
            setter=lambda w, v: w.setPlainText(str(v) if v is not None else ""),
            signal_name="textChanged",
        ),
    )
    registry.set_default_prop(QTextEdit, "text")

    # QPlainTextEdit - text
    registry.add(
        BindingKey(QPlainTextEdit, "text"),
        BindingAdapter(
            getter=lambda w: w.toPlainText(),
            setter=lambda w, v: w.setPlainText(str(v) if v is not None else ""),
            signal_name="textChanged",
        ),
    )
    registry.set_default_prop(QPlainTextEdit, "text")

    # QSpinBox - value
    registry.add(
        BindingKey(QSpinBox, "value"),
        BindingAdapter(
            getter=lambda w: w.value(),
            setter=lambda w, v: w.setValue(int(v) if v is not None else 0),
            signal_name="valueChanged",
        ),
    )
    registry.set_default_prop(QSpinBox, "value")

    # QDoubleSpinBox - value
    registry.add(
        BindingKey(QDoubleSpinBox, "value"),
        BindingAdapter(
            getter=lambda w: w.value(),
            setter=lambda w, v: w.setValue(float(v) if v is not None else 0.0),
            signal_name="valueChanged",
        ),
    )
    registry.set_default_prop(QDoubleSpinBox, "value")

    # QCheckBox - checked
    registry.add(
        BindingKey(QCheckBox, "checked"),
        BindingAdapter(
            getter=lambda w: w.isChecked(),
            setter=lambda w, v: w.setChecked(bool(v) if v is not None else False),
            signal_name="checkStateChanged",
        ),
    )
    registry.set_default_prop(QCheckBox, "checked")

    # QRadioButton - checked
    registry.add(
        BindingKey(QRadioButton, "checked"),
        BindingAdapter(
            getter=lambda w: w.isChecked(),
            setter=lambda w, v: w.setChecked(bool(v) if v is not None else False),
            signal_name="toggled",
        ),
    )
    registry.set_default_prop(QRadioButton, "checked")

    # QComboBox - currentText
    registry.add(
        BindingKey(QComboBox, "currentText"),
        BindingAdapter(
            getter=lambda w: w.currentText(),
            setter=lambda w, v: w.setCurrentText(str(v) if v is not None else ""),
            signal_name="currentTextChanged",
        ),
    )
    registry.set_default_prop(QComboBox, "currentText")

    # QSlider - value
    registry.add(
        BindingKey(QSlider, "value"),
        BindingAdapter(
            getter=lambda w: w.value(),
            setter=lambda w, v: w.setValue(int(v) if v is not None else 0),
            signal_name="valueChanged",
        ),
    )
    registry.set_default_prop(QSlider, "value")

    # QDial - value
    registry.add(
        BindingKey(QDial, "value"),
        BindingAdapter(
            getter=lambda w: w.value(),
            setter=lambda w, v: w.setValue(int(v) if v is not None else 0),
            signal_name="valueChanged",
        ),
    )
    registry.set_default_prop(QDial, "value")

    # QProgressBar - value (one-way, no signal)
    registry.add(
        BindingKey(QProgressBar, "value"),
        BindingAdapter(
            getter=lambda w: w.value(),
            setter=lambda w, v: w.setValue(int(v) if v is not None else 0),
            signal_name=None,
        ),
    )
    registry.set_default_prop(QProgressBar, "value")

    # QDateEdit - date
    registry.add(
        BindingKey(QDateEdit, "date"),
        BindingAdapter(
            getter=lambda w: w.date(),
            setter=lambda w, v: w.setDate(v) if v is not None else None,
            signal_name="dateChanged",
        ),
    )
    registry.set_default_prop(QDateEdit, "date")

    # QTimeEdit - time
    registry.add(
        BindingKey(QTimeEdit, "time"),
        BindingAdapter(
            getter=lambda w: w.time(),
            setter=lambda w, v: w.setTime(v) if v is not None else None,
            signal_name="timeChanged",
        ),
    )
    registry.set_default_prop(QTimeEdit, "time")

    # QDateTimeEdit - dateTime
    registry.add(
        BindingKey(QDateTimeEdit, "dateTime"),
        BindingAdapter(
            getter=lambda w: w.dateTime(),
            setter=lambda w, v: w.setDateTime(v) if v is not None else None,
            signal_name="dateTimeChanged",
        ),
    )
    registry.set_default_prop(QDateTimeEdit, "dateTime")

    # QFontComboBox - currentFont
    registry.add(
        BindingKey(QFontComboBox, "currentFont"),
        BindingAdapter(
            getter=lambda w: w.currentFont(),
            setter=lambda w, v: w.setCurrentFont(v) if v is not None else None,
            signal_name="currentFontChanged",
        ),
    )
    registry.set_default_prop(QFontComboBox, "currentFont")

    # QKeySequenceEdit - keySequence
    registry.add(
        BindingKey(QKeySequenceEdit, "keySequence"),
        BindingAdapter(
            getter=lambda w: w.keySequence(),
            setter=lambda w, v: w.setKeySequence(v) if v is not None else None,
            signal_name="keySequenceChanged",
        ),
    )
    registry.set_default_prop(QKeySequenceEdit, "keySequence")

    # QListWidget - currentRow
    registry.add(
        BindingKey(QListWidget, "currentRow"),
        BindingAdapter(
            getter=lambda w: w.currentRow(),
            setter=lambda w, v: w.setCurrentRow(int(v) if v is not None else -1),
            signal_name="currentRowChanged",
        ),
    )
    registry.set_default_prop(QListWidget, "currentRow")
