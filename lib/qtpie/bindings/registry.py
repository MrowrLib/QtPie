"""Binding registry for mapping widget types to their bindable properties."""

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from qtpy.QtCore import QObject
from qtpy.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QProgressBar,
    QRadioButton,
    QSlider,
    QSpinBox,
    QSplitter,
    QTextEdit,
    QWidget,
)


@dataclass(frozen=True)
class BindingKey:
    """Key for looking up bindings in the registry."""

    widget_type: type[QObject]
    property_name: str


@dataclass
class BindingAdapter[TWidget: QObject, TValue]:
    """Adapter for binding a widget property to a Variable.

    Attributes:
        getter: Function to get the current value from the widget.
        setter: Function to set a value on the widget.
        signal_name: Signal name that fires when the property changes (for two-way binding).
    """

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
    """Register a binding adapter for a widget type and property.

    Args:
        widget_type: The Qt widget class (e.g., QLineEdit, QSpinBox)
        property_name: The property name to bind (e.g., "text", "value")
        getter: Function to get the current value from the widget
        setter: Function to set a value on the widget
        signal: Signal name that fires when the property changes
        default: If True, this property becomes the default for this widget type
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
            setter=lambda w, v: w.setValue(int(v) if v not in (None, "") else 0),
            signal_name="valueChanged",
        ),
    )
    registry.set_default_prop(QSpinBox, "value")

    # QDoubleSpinBox - value
    registry.add(
        BindingKey(QDoubleSpinBox, "value"),
        BindingAdapter(
            getter=lambda w: w.value(),
            setter=lambda w, v: w.setValue(float(v) if v not in (None, "") else 0.0),
            signal_name="valueChanged",
        ),
    )
    registry.set_default_prop(QDoubleSpinBox, "value")

    # QCheckBox - checked
    def _parse_bool(v: Any) -> bool:
        """Parse a bool from various formats (bool, str, None)."""
        if v is None or v == "":
            return False
        if isinstance(v, bool):
            return v
        if isinstance(v, str):
            return v.lower() not in ("false", "0", "no", "")
        return bool(v)

    registry.add(
        BindingKey(QCheckBox, "checked"),
        BindingAdapter(
            getter=lambda w: w.isChecked(),
            setter=lambda w, v: w.setChecked(_parse_bool(v)),
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
            setter=lambda w, v: w.setValue(int(v) if v not in (None, "") else 0),
            signal_name="valueChanged",
        ),
    )
    registry.set_default_prop(QSlider, "value")

    # QProgressBar - value (one-way, no signal)
    registry.add(
        BindingKey(QProgressBar, "value"),
        BindingAdapter(
            getter=lambda w: w.value(),
            setter=lambda w, v: w.setValue(int(v) if v not in (None, "") else 0),
            signal_name=None,
        ),
    )
    registry.set_default_prop(QProgressBar, "value")

    # ============================================================
    # Common QWidget properties (inherited by all widgets)
    # ============================================================

    def _set_visible(w: QWidget, v: object) -> None:
        """Set widget visibility, also handling QFormLayout row visibility."""
        visible = bool(v) if v is not None else True

        # Find if widget is in a QFormLayout and use setRowVisible instead
        parent = w.parentWidget()
        if parent is not None:
            # Search all form layouts (including nested ones) for this widget
            for form_layout in parent.findChildren(QFormLayout):
                if form_layout.indexOf(w) != -1:
                    form_layout.setRowVisible(w, visible)
                    return
            # Also check the parent's default layout
            layout = parent.layout()
            if isinstance(layout, QFormLayout) and layout.indexOf(w) != -1:
                layout.setRowVisible(w, visible)
                return

        # Not in a form layout, just set widget visibility directly
        w.setVisible(visible)

    # QWidget - visible (one-way, no signal for visibility changes)
    registry.add(
        BindingKey(QWidget, "visible"),
        BindingAdapter(
            getter=lambda w: w.isVisible(),
            setter=_set_visible,
            signal_name=None,
        ),
    )

    # QWidget - enabled (one-way, no signal)
    registry.add(
        BindingKey(QWidget, "enabled"),
        BindingAdapter(
            getter=lambda w: w.isEnabled(),
            setter=lambda w, v: w.setEnabled(bool(v) if v is not None else True),
            signal_name=None,
        ),
    )

    # QWidget - styleSheet (one-way)
    registry.add(
        BindingKey(QWidget, "styleSheet"),
        BindingAdapter(
            getter=lambda w: w.styleSheet(),
            setter=lambda w, v: w.setStyleSheet(str(v) if v is not None else ""),
            signal_name=None,
        ),
    )

    # QWidget - toolTip (one-way)
    registry.add(
        BindingKey(QWidget, "toolTip"),
        BindingAdapter(
            getter=lambda w: w.toolTip(),
            setter=lambda w, v: w.setToolTip(str(v) if v is not None else ""),
            signal_name=None,
        ),
    )

    # QWidget - windowTitle (one-way)
    registry.add(
        BindingKey(QWidget, "windowTitle"),
        BindingAdapter(
            getter=lambda w: w.windowTitle(),
            setter=lambda w, v: w.setWindowTitle(str(v) if v is not None else ""),
            signal_name=None,
        ),
    )

    # QWidget - windowModified (one-way) - shows "document modified" indicator
    registry.add(
        BindingKey(QWidget, "windowModified"),
        BindingAdapter(
            getter=lambda w: w.isWindowModified(),
            setter=lambda w, v: w.setWindowModified(bool(v) if v is not None else False),
            signal_name=None,
        ),
    )

    # QWidget - acceptDrops (one-way)
    registry.add(
        BindingKey(QWidget, "acceptDrops"),
        BindingAdapter(
            getter=lambda w: w.acceptDrops(),
            setter=lambda w, v: w.setAcceptDrops(bool(v) if v is not None else False),
            signal_name=None,
        ),
    )

    # QWidget - updatesEnabled (one-way) - temporarily disable repainting for batch updates
    registry.add(
        BindingKey(QWidget, "updatesEnabled"),
        BindingAdapter(
            getter=lambda w: w.updatesEnabled(),
            setter=lambda w, v: w.setUpdatesEnabled(bool(v) if v is not None else True),
            signal_name=None,
        ),
    )

    # ============================================================
    # QSplitter
    # ============================================================

    # QSplitter - orientation (one-way)
    registry.add(
        BindingKey(QSplitter, "orientation"),
        BindingAdapter(
            getter=lambda w: w.orientation(),
            setter=lambda w, v: w.setOrientation(v) if v is not None else None,
            signal_name=None,
        ),
    )
    registry.set_default_prop(QSplitter, "orientation")
