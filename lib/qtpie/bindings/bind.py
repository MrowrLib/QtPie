"""bind() - Connect Variables to widget properties."""

from typing import Any

from observant import Observable, ObservableProxy
from qtpy.QtCore import QObject

from ..variable import Variable
from .registry import get_binding_registry


def is_widget_with_record(widget: QObject) -> bool:
    """Check if widget is a Widget[T] subclass with record support."""
    # Check for our Widget class by looking for the QtPie markers
    widget_type: Any = type(widget)
    return hasattr(widget_type, "_qtpie_config") and hasattr(widget_type._qtpie_config, "record_type") and widget_type._qtpie_config.record_type is not None


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
        # Special case: Widget[T] subclass - bind via .record with shared proxy
        if is_widget_with_record(widget):
            self._bind_to_widget_record(widget)
            return

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

        # Set initial value from Variable
        adapter.setter(widget, self._variable.value)

        # Subscribe to Variable changes → update widget
        # Observable.on_change passes value, others don't - handle both
        observable = self._variable.observable
        if isinstance(observable, Observable):

            def on_observable_change(value: Any) -> None:
                assert adapter.setter is not None
                adapter.setter(widget, value)

            observable.on_change(on_observable_change)
        else:

            def on_wrapper_change() -> None:
                assert adapter.setter is not None
                adapter.setter(widget, self._variable.value)

            observable.on_change(on_wrapper_change)

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

    def _bind_to_widget_record(self, widget: QObject) -> None:
        """Bind to a Widget[T] subclass via its .record property.

        This shares the ObservableProxy between the Variable and the Widget,
        so changes made via either path are visible to both.
        """
        # Get the underlying observable from our Variable
        observable = self._variable.observable

        # For Widget[T], we need to share our ObservableProxy with the widget's record
        if isinstance(observable, ObservableProxy):
            # Import here to avoid circular imports
            from ..qt_pie_state import QtPieState
            from ..repeaters.utils import rebind_child_widgets
            from ..variable import RecordVariable
            from .apply import apply_auto_bindings

            # Get or create the widget's QtPieState
            if not hasattr(widget, "_qtpie"):
                widget._qtpie = QtPieState(widget)  # type: ignore[arg-type, attr-defined]

            # Create a RecordVariable that wraps our same ObservableProxy
            # This shares the proxy so both sides see the same data
            record_var = RecordVariable(observable)
            widget._qtpie._record = record_var  # type: ignore[attr-defined, union-attr]
            widget._qtpie.register_variable("record", record_var)  # type: ignore[union-attr]
            # Subscribe record to widget-level aggregation if active
            widget._qtpie._subscribe_record_to_widget_dirty()  # type: ignore[union-attr]
            widget._qtpie._subscribe_record_to_widget_valid()  # type: ignore[union-attr]

            # Re-apply auto-bindings now that record is populated
            # This is needed because the widget's __init__ ran before we set up the record
            config = type(widget)._qtpie_config  # type: ignore[attr-defined]
            apply_auto_bindings(widget, config)  # type: ignore[arg-type]

            # Also rebind child Widget[T] widgets (e.g., tabs created via tabs=)
            # These children may have been created before the parent's record was set
            rebind_child_widgets(widget)  # type: ignore[arg-type]
        else:
            # For primitives or other types, just set the value directly
            # The widget will create its own proxy when accessed
            widget.record = self._variable.value  # type: ignore[attr-defined]


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
