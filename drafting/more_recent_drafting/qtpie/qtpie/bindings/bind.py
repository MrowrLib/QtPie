from __future__ import annotations

from typing import cast

from observant import IObservable, Observable
from PySide6.QtCore import QObject
from PySide6.QtWidgets import QWidget

from qtpie.bindings.registry import (
    BindingAdapter,
    Comparable,
    ComparableOrPrimitive,
    get_binding_registry,
)


def bind_fields_single[TValue: ComparableOrPrimitive](
    binding: tuple[QObject, str, IObservable[TValue]],
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


def bind[TValue: ComparableOrPrimitive](
    observable: IObservable[TValue], widget: QWidget, prop: str = "text"
) -> None:
    bind_fields_single((widget, prop, observable))


def bind_fields(bindings: list[tuple[QObject, str, Observable[Comparable]]]) -> None:
    for widget, prop, observable in bindings:
        adapter = get_binding_registry().get(widget, prop)
        if adapter is None:
            raise ValueError(
                f"No binding registered for {type(widget).__name__}.{prop}"
            )

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
