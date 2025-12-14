from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Generic, Optional, TypeVar, cast

from PySide6.QtCore import QObject
from PySide6.QtWidgets import QComboBox, QLabel, QLineEdit, QPlainTextEdit, QTextEdit, QWidget

from mrowr.observable import Comparable, ComparableOrPrimitive, Observable

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

    def add_binding(self, key: BindingKey, adapter: BindingAdapter[Any, Any]) -> None:
        self._bindings[key] = adapter

    def get(self, widget: QObject, property_name: str) -> Optional[BindingAdapter[QObject, Comparable]]:
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
    value_type: type[TValue] = str,
) -> None:
    key = BindingKey(widget_type, property)

    listen_to_change: Optional[Callable[[TWidget, Callable[[TValue], None]], None]] = None

    if signal and not getter:

        def _connect_signal(widget: TWidget, callback: Callable[[TValue], None]) -> None:
            signal_obj = getattr(widget, signal)
            signal_obj.connect(callback)

        listen_to_change = _connect_signal

    elif signal and getter:

        def _connect_signal(widget: TWidget, callback: Callable[[TValue], None]) -> None:
            signal_obj = getattr(widget, signal)
            signal_obj.connect(lambda: callback(getter(widget)))

        listen_to_change = _connect_signal

    adapter = BindingAdapter(
        listen_to_change=listen_to_change,
        apply_value=setter,
    )

    get_binding_registry().add_binding(key, adapter)


def bind_fields_single[TValue: ComparableOrPrimitive](
    binding: tuple[QObject, str, Observable[TValue]],
) -> None:
    widget, prop, observable = binding
    adapter_raw = get_binding_registry().get(widget, prop)
    if adapter_raw is None:
        raise ValueError(f"No binding registered for {type(widget).__name__}.{prop}")

    # Recast to get rid of Pylance whining
    adapter = cast(BindingAdapter[QObject, TValue], adapter_raw)

    lock = False

    def update_model(value: TValue) -> None:
        nonlocal lock
        if not lock:
            lock = True
            observable.set(value)
            lock = False

    def update_ui(value: TValue) -> None:
        if adapter.apply_value is not None:
            nonlocal lock
            if not lock:
                lock = True
                adapter.apply_value(widget, value)
                lock = False

    if adapter.listen_to_change:
        adapter.listen_to_change(widget, update_model)

    observable.on_change(update_ui)
    update_ui(observable.get())


def bind[TValue: ComparableOrPrimitive](observable: Observable[TValue], widget: QWidget, prop: str = "text") -> None:
    bind_fields_single((widget, prop, observable))


def bind_fields(bindings: list[tuple[QObject, str, Observable[Comparable]]]) -> None:
    for widget, prop, observable in bindings:
        adapter = get_binding_registry().get(widget, prop)
        if adapter is None:
            raise ValueError(f"No binding registered for {type(widget).__name__}.{prop}")

        lock = False

        def update_model(value: Comparable) -> None:
            nonlocal lock
            if not lock:
                lock = True
                observable.set(value)
                lock = False

        def update_ui(value: Comparable) -> None:
            if adapter and adapter.apply_value is not None:
                nonlocal lock
                if not lock:
                    lock = True
                    adapter.apply_value(widget, value)
                    lock = False

        if adapter.listen_to_change:
            adapter.listen_to_change(widget, update_model)

        observable.on_change(update_ui)
        update_ui(observable.get())


# Global registry instance


def register_default_bindings():
    # QTextEdit plainText
    register_binding(
        QTextEdit,
        "text",
        setter=lambda widget, value: widget.setPlainText(str(value)),
        getter=lambda widget: widget.toPlainText(),
        signal="textChanged",
    )

    # QPlainTextEdit plainText
    register_binding(
        QPlainTextEdit,
        "text",
        setter=lambda widget, value: widget.setPlainText(str(value)),
        getter=lambda widget: widget.toPlainText(),
        signal="textChanged",
    )

    # QLabel text
    register_binding(
        QLabel,
        "text",
        setter=lambda widget, value: widget.setText(str(value)),
    )

    # QLineEdit text
    register_binding(
        QLineEdit,
        "text",
        setter=lambda widget, value: widget.setText(str(value)),
        getter=lambda widget: widget.text(),
    )

    # QComboBox currentText
    register_binding(
        QComboBox,
        "text",
        setter=lambda widget, value: widget.setCurrentText(str(value)),
        getter=lambda widget: widget.currentText(),
        signal="currentTextChanged",
    )


register_default_bindings()
