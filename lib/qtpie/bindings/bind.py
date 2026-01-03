"""bind() - Connect Variables to widget properties."""

from typing import Any

from PySide6.QtCore import QObject

from ..variable import Variable
from .registry import get_binding_registry


class Binding[T]:
    """Represents a pending binding from a Variable.

    Usage:
        bind(self._name).to(self._label)  # uses default property
        bind(self._name).to(self._label, "text")  # explicit property
    """

    def __init__(self, variable: Variable[T]) -> None:
        self._variable = variable

    def to(
        self,
        widget: QObject,
        property_name: str | None = None,
        *,
        two_way: bool = True,
    ) -> None:
        """Bind the Variable to a widget property.

        Args:
            widget: The Qt widget to bind to.
            property_name: Property name (e.g., "text", "value"). If None, uses the
                           widget's default property from the registry.
            two_way: If True and the property has a signal, changes to the widget
                     will update the Variable. Default True.
        """
        registry = get_binding_registry()

        # Get property name (use default if not specified)
        if property_name is None:
            property_name = registry.get_default_prop(widget)

        # Get the adapter for this widget/property
        adapter = registry.get(widget, property_name)
        if adapter is None:
            raise ValueError(f"No binding registered for {type(widget).__name__}.{property_name}")

        if adapter.setter is None:
            raise ValueError(f"Binding for {type(widget).__name__}.{property_name} has no setter")

        # Get the Observable from the Variable instance
        observable = self._variable.observable

        # Set initial value
        adapter.setter(widget, observable.get())

        # Subscribe to Variable changes → update widget
        def on_variable_change(value: Any) -> None:
            assert adapter.setter is not None
            adapter.setter(widget, value)

        observable.on_change(on_variable_change)

        # Two-way binding: widget changes → update Variable
        if two_way and adapter.signal_name is not None:
            signal = getattr(widget, adapter.signal_name, None)
            if signal is not None:
                # Prevent infinite loops: track if we're updating
                updating = {"active": False}

                def on_widget_change(*args: Any) -> None:
                    if updating["active"]:
                        return
                    if adapter.getter is not None:
                        updating["active"] = True
                        try:
                            self._variable.value = adapter.getter(widget)
                        finally:
                            updating["active"] = False

                signal.connect(on_widget_change)


def bind(variable: Variable[Any]) -> Binding[Any]:
    """Start a binding from a Variable to a widget property.

    Args:
        variable: The Variable instance to bind (e.g., self._name).

    Returns:
        A Binding object with a `.to()` method to complete the binding.

    Example:
        def __setup__(self):
            bind(self._name).to(self._label)  # uses default "text"
            bind(self._count).to(self._spinbox, "value")
    """
    return Binding(variable)
