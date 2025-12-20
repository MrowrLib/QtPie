"""Two-way binding between observables and Qt widgets."""

from typing import Any

from observant import IObservable
from qtpy.QtCore import QObject

from qtpie.bindings.registry import get_binding_registry


def bind(
    observable: IObservable[Any],
    widget: QObject,
    prop: str | None = None,
) -> None:
    """
    Bind an observable to a widget property with two-way sync.

    Args:
        observable: The observable to bind (from ObservableProxy)
        widget: The Qt widget to bind to
        prop: The widget property name. If None, uses the default for the widget type.

    Example:
        proxy = ObservableProxy(model, sync=True)
        name_obs = proxy.observable(str, "name")
        bind(name_obs, name_edit)  # Uses default "text" for QLineEdit
        bind(name_obs, name_edit, "text")  # Explicit property
    """
    registry = get_binding_registry()

    # Get property name (explicit or default)
    if prop is None:
        prop = registry.get_default_prop(widget)

    adapter = registry.get(widget, prop)
    if adapter is None:
        raise ValueError(f"No binding registered for {type(widget).__name__}.{prop}")

    # Lock to prevent infinite loops during sync
    lock = False

    def update_model(value: Any) -> None:
        """Update the observable when widget changes."""
        nonlocal lock
        if not lock:
            lock = True
            try:
                observable.set(value)
            finally:
                lock = False

    def update_widget(value: Any) -> None:
        """Update the widget when observable changes."""
        nonlocal lock
        if not lock and adapter.setter is not None:
            lock = True
            try:
                adapter.setter(widget, value)
            finally:
                lock = False

    # Widget → Model (if signal exists for two-way binding)
    if adapter.signal_name is not None and adapter.getter is not None:
        signal = getattr(widget, adapter.signal_name, None)
        if signal is not None:
            # Capture getter in closure
            getter = adapter.getter
            signal.connect(lambda *_args: update_model(getter(widget)))  # type: ignore[misc]

    # Model → Widget
    observable.on_change(update_widget)

    # Initial sync (model → widget)
    update_widget(observable.get())
