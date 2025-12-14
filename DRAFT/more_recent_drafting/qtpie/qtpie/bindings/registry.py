from __future__ import annotations

from dataclasses import dataclass
from typing import (
    Any,
    Callable,
    Generic,
    Optional,
    Protocol,
    TypeVar,
    runtime_checkable,
)

from PySide6.QtCore import QObject

H = TypeVar("H", contravariant=True)


@runtime_checkable
class SupportsLessThan(Protocol[H]):
    def __lt__(self, other: H) -> bool: ...


class Comparable(SupportsLessThan["Comparable"], Protocol):
    pass


ComparableOrPrimitive = Comparable | str | int | float | bool | None

TWidget = TypeVar("TWidget", bound=QObject)
TValue = TypeVar("TValue", bound=ComparableOrPrimitive)


@dataclass(frozen=True)
class BindingKey:
    widget_type: type[QObject]
    property_name: str


_binding_registry: Optional[BindingRegistry] = None


def get_binding_registry() -> BindingRegistry:
    global _binding_registry
    if _binding_registry is None:
        _binding_registry = BindingRegistry()
    return _binding_registry


@dataclass
class BindingAdapter(Generic[TWidget, TValue]):
    listen_to_change: Callable[[TWidget, Callable[[TValue], None]], None] | None = None
    apply_value: Callable[[TWidget, TValue], None] | None = None


class BindingRegistry:
    def __init__(self) -> None:
        self._bindings: dict[BindingKey, BindingAdapter[Any, Any]] = {}
        self._default_props: dict[type[QObject], str] = {}

    def add_binding(self, key: BindingKey, adapter: BindingAdapter[Any, Any]) -> None:
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

    def get(
        self, widget: QObject, property_name: str
    ) -> Optional[BindingAdapter[QObject, Comparable]]:
        for cls in type(widget).mro():
            key = BindingKey(cls, property_name)
            if key in self._bindings:
                return self._bindings[key]
        return None


def register_binding(
    widget_type: type[TWidget],
    property: str,
    *,
    signal: Optional[str] = None,
    getter: Optional[Callable[[TWidget], TValue]] = None,
    setter: Optional[Callable[[TWidget, TValue], None]] = None,
    value_type: type[TValue] = str,  # noqa: ARG001
    default: bool = False,
) -> None:
    """
    Register a binding adapter for a widget type and property.

    This allows the bind() function to automatically connect observables
    to widget properties.

    Args:
        widget_type: The Qt widget class (e.g., QLineEdit, QLabel)
        property: The property name to bind (e.g., "text", "value")
        signal: Optional signal name that fires when the property changes
                (e.g., "textChanged", "valueChanged")
        getter: Optional function to get the current value from the widget
        setter: Optional function to set a value on the widget
        value_type: The type of the value (default: str)
        default: If True, this property becomes the default for this widget type

    Example:
        # Register a binding for QSpinBox
        register_binding(
            QSpinBox,
            "value",
            setter=lambda w, v: w.setValue(int(v)),
            getter=lambda w: w.value(),
            signal="valueChanged",
            default=True,  # "value" is the default prop for QSpinBox
        )

        # Now you can use it with bind (no need to specify bind_prop):
        slider_count: QSpinBox = make(QSpinBox, bind="count")
    """
    key = BindingKey(widget_type, property)

    if default:
        get_binding_registry().set_default_prop(widget_type, property)

    listen_to_change: Optional[Callable[[TWidget, Callable[[TValue], None]], None]] = (
        None
    )

    if signal and not getter:

        def _connect_signal(
            widget: TWidget, callback: Callable[[TValue], None]
        ) -> None:
            signal_obj = getattr(widget, signal)
            signal_obj.connect(callback)

        listen_to_change = _connect_signal

    elif signal and getter:

        def _connect_signal(
            widget: TWidget, callback: Callable[[TValue], None]
        ) -> None:
            signal_obj = getattr(widget, signal)
            signal_obj.connect(lambda: callback(getter(widget)))

        listen_to_change = _connect_signal

    adapter = BindingAdapter(
        listen_to_change=listen_to_change,
        apply_value=setter,
    )

    get_binding_registry().add_binding(key, adapter)
