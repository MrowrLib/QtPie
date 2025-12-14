"""The @widget decorator - transforms classes into Qt widgets with automatic layout."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import MISSING, dataclass, fields
from typing import (
    Any,
    Literal,
    cast,
    dataclass_transform,
    get_type_hints,
    overload,
)

from qtpy.QtWidgets import (
    QBoxLayout,
    QFormLayout,
    QGridLayout,
    QHBoxLayout,
    QLayout,
    QVBoxLayout,
    QWidget,
)

from qtpie.factories.make import (
    BIND_METADATA_KEY,
    BIND_PROP_METADATA_KEY,
    FORM_LABEL_METADATA_KEY,
    GRID_POSITION_METADATA_KEY,
    MAKE_LATER_METADATA_KEY,
    SIGNALS_METADATA_KEY,
    GridTuple,
)

LayoutType = Literal["vertical", "horizontal", "form", "grid", "none"]


@overload
@dataclass_transform()
def widget[T](
    _cls: type[T],
    *,
    name: str | None = ...,
    classes: list[str] | None = ...,
    layout: LayoutType = ...,
) -> type[T]: ...


@overload
@dataclass_transform()
def widget[T](
    _cls: None = None,
    *,
    name: str | None = ...,
    classes: list[str] | None = ...,
    layout: LayoutType = ...,
) -> Callable[[type[T]], type[T]]: ...


@dataclass_transform()
def widget[T](
    _cls: type[T] | None = None,
    *,
    name: str | None = None,
    classes: list[str] | None = None,
    layout: LayoutType = "vertical",
) -> Callable[[type[T]], type[T]] | type[T]:
    """
    Decorator that transforms a class into a Qt widget with automatic layout.

    Args:
        name: Object name for QSS styling (defaults to class name).
        classes: CSS-like classes for styling.
        layout: The layout type - "vertical", "horizontal", or "none".
                Defaults to "vertical".

    Example:
        @widget(name="MyEditor", classes=["card"], layout="vertical")
        class MyWidget(QWidget):
            label: QLabel = make(QLabel, "Hello")
            button: QPushButton = make(QPushButton, "Click", clicked="on_click")

            def setup(self) -> None:
                print("Widget initialized!")

            def on_click(self) -> None:
                print("Clicked!")
    """

    def decorator(cls: type[T]) -> type[T]:
        # Apply @dataclass to register fields
        cls = dataclass(cls)  # type: ignore[assignment]

        def new_init(self: QWidget, *args: object, **kwargs: object) -> None:
            # Initialize QWidget base class first
            QWidget.__init__(self)

            # Manually set dataclass fields (with default_factory support)
            for f in fields(cls):  # type: ignore[arg-type]
                if f.name in kwargs:
                    setattr(self, f.name, kwargs[f.name])
                elif f.default is not MISSING:
                    setattr(self, f.name, f.default)
                elif f.default_factory is not MISSING:  # type: ignore[arg-type]
                    setattr(self, f.name, f.default_factory())  # type: ignore[misc]

            # Connect signals from make() metadata
            for f in fields(cls):  # type: ignore[arg-type]
                potential_signals = f.metadata.get(SIGNALS_METADATA_KEY)
                if potential_signals:
                    widget_instance = getattr(self, f.name, None)
                    if widget_instance is not None:
                        _connect_signals(self, widget_instance, potential_signals)

            # Set object name
            if name:
                self.setObjectName(name)
            elif not self.objectName():
                # Auto-generate from class name
                object_name = cls.__name__
                # Strip "Widget" suffix if present
                if object_name.endswith("Widget"):
                    object_name = object_name[:-6]
                self.setObjectName(object_name)

            # Set CSS-like classes
            if classes:
                _set_classes(self, classes)

            # Set up layout
            _layout: QLayout | None = None
            _box_layout: QBoxLayout | None = None
            _form_layout: QFormLayout | None = None
            _grid_layout: QGridLayout | None = None

            if layout == "vertical":
                _box_layout = QVBoxLayout()
                _layout = _box_layout
            elif layout == "horizontal":
                _box_layout = QHBoxLayout()
                _layout = _box_layout
            elif layout == "form":
                _form_layout = QFormLayout()
                _layout = _form_layout
                # Add "form" class for styling
                prop_value = self.property("class")
                current_classes = cast(list[str], prop_value) if isinstance(prop_value, list) else []
                _set_classes(self, [*current_classes, "form"])
            elif layout == "grid":
                _grid_layout = QGridLayout()
                _layout = _grid_layout
            elif layout == "none":
                _layout = None

            if _layout is not None:
                self.setLayout(_layout)

                # Add child widgets to layout
                type_hints = get_type_hints(cls)
                for f in fields(cls):  # type: ignore[arg-type]
                    # Handle _stretch fields for box layouts
                    if f.name.startswith("_stretch"):
                        field_type = type_hints.get(f.name)
                        if isinstance(field_type, type) and issubclass(field_type, int) and _box_layout is not None:
                            stretch_value = getattr(self, f.name, 0)
                            _box_layout.addStretch(stretch_value)
                        continue

                    # Skip other private fields
                    if f.name.startswith("_"):
                        continue

                    field_type = type_hints.get(f.name)
                    if isinstance(field_type, type) and issubclass(field_type, QWidget):
                        widget_instance = getattr(self, f.name, None)
                        if isinstance(widget_instance, QWidget):
                            if _box_layout is not None:
                                _box_layout.addWidget(widget_instance)
                            elif _form_layout is not None:
                                form_label = f.metadata.get(FORM_LABEL_METADATA_KEY, "")
                                _form_layout.addRow(form_label, widget_instance)
                            elif _grid_layout is not None:
                                grid_pos: GridTuple | None = f.metadata.get(GRID_POSITION_METADATA_KEY)
                                if grid_pos is not None:
                                    row, col = grid_pos[0], grid_pos[1]
                                    rowspan = grid_pos[2] if len(grid_pos) > 2 else 1
                                    colspan = grid_pos[3] if len(grid_pos) > 3 else 1
                                    _grid_layout.addWidget(widget_instance, row, col, rowspan, colspan)

            # Call lifecycle hooks if they exist
            _call_if_exists(self, "setup")
            _call_if_exists(self, "setup_values")
            _call_if_exists(self, "setup_bindings")

            # Process ModelWidget if applicable (after setup, before bindings)
            _process_model_widget(self, cls)

            # Process data bindings after setup (user creates proxy in setup())
            _process_bindings(self, cls)

            # Process auto-bindings for ModelWidget (by field name)
            _process_model_widget_auto_bindings(self, cls)

            if self.layout() is not None:
                _call_if_exists(self, "setup_layout", self.layout())
            _call_if_exists(self, "setup_styles")
            _call_if_exists(self, "setup_events")
            _call_if_exists(self, "setup_signals")

        cls.__init__ = new_init  # type: ignore[method-assign]
        return cls

    if _cls is not None:
        return decorator(_cls)
    return decorator


def _connect_signals(
    parent: object,
    widget_instance: object,
    potential_signals: dict[str, str | Callable[..., Any]],
) -> None:
    """Connect signals from make() metadata to methods or callables."""
    for attr_name, handler in potential_signals.items():
        attr = getattr(widget_instance, attr_name, None)
        if attr is not None and hasattr(attr, "connect"):
            # It's a signal - connect it
            if isinstance(handler, str):
                # Look up method by name on parent
                method = getattr(parent, handler, None)
                if method is not None:
                    attr.connect(method)
            elif callable(handler):
                # Direct callable (lambda or function)
                attr.connect(handler)
        else:
            # Not a signal - it was a property, set it via setter
            setter_name = f"set{attr_name[0].upper()}{attr_name[1:]}"
            setter = getattr(widget_instance, setter_name, None)
            if setter is not None and callable(setter):
                setter(handler)


def _set_classes(widget: QWidget, class_list: list[str]) -> None:
    """Set CSS-like classes on a widget as a Qt property."""
    widget.setProperty("class", class_list)
    # Force style refresh
    widget.style().unpolish(widget)
    widget.style().polish(widget)


def _call_if_exists(obj: object, method_name: str, *args: object) -> None:
    """Call a method on obj if it exists and is callable."""
    method = getattr(obj, method_name, None)
    if method is not None and callable(method):
        method(*args)


def _process_bindings(widget: QWidget, cls: type[Any]) -> None:
    """Process data bindings from make() metadata."""
    # Import here to avoid circular import
    from qtpie.bindings import bind, get_binding_registry

    for f in fields(cls):  # type: ignore[arg-type]
        bind_path = f.metadata.get(BIND_METADATA_KEY)
        if bind_path is None:
            continue

        # Get the widget instance for this field
        widget_instance = getattr(widget, f.name, None)
        if widget_instance is None:
            continue

        # Parse the bind path: "proxy.name" or "proxy.address?.city"
        # First part is the field name on self that holds the proxy
        parts = bind_path.split(".", 1)
        if len(parts) < 2:
            # Invalid path - need at least "proxy.field"
            continue

        proxy_field_name = parts[0]
        observable_path = parts[1]

        # Get the proxy from self
        proxy = getattr(widget, proxy_field_name, None)
        if proxy is None:
            # Proxy not yet created - skip silently
            continue

        # Check if proxy has observable_for_path method (is ObservableProxy)
        if not hasattr(proxy, "observable_for_path"):
            continue

        # Get the observable for the path
        observable = proxy.observable_for_path(observable_path)

        # Get the property to bind to
        bind_prop = f.metadata.get(BIND_PROP_METADATA_KEY)
        if bind_prop is None:
            bind_prop = get_binding_registry().get_default_prop(widget_instance)

        # Create the binding
        bind(observable, widget_instance, bind_prop)


def _process_model_widget(widget: QWidget, cls: type[Any]) -> None:
    """Process ModelWidget initialization - create model and proxy."""
    # Import here to avoid circular import
    from qtpie.model_widget import get_model_type, is_model_widget_subclass

    if not is_model_widget_subclass(cls):
        return

    # Check if model field exists
    model_field = None
    for f in fields(cls):  # type: ignore[arg-type]
        if f.name == "model":
            model_field = f
            break

    model_instance = None

    if model_field is not None:
        # User defined a model field
        is_make_later = model_field.metadata.get(MAKE_LATER_METADATA_KEY, False)

        if is_make_later:
            # Check if user set it in setup()
            current_value = getattr(widget, "model", None)
            if current_value is None or not hasattr(widget, "model"):
                raise ValueError(
                    f"ModelWidget field 'model' was declared with make_later() but not set in setup(). Either set self.model in setup() or use make({cls.__name__}, ...) to provide a factory."
                )
            model_instance = current_value
        else:
            # User used make() - get the created instance
            model_instance = getattr(widget, "model", None)
    else:
        # No model field defined - auto-create T()
        model_type = get_model_type(cls)
        if model_type is None:
            raise ValueError(f"Cannot determine model type for {cls.__name__}. Ensure the class inherits from ModelWidget[YourModelType].")
        model_instance = model_type()
        widget.model = model_instance  # type: ignore[attr-defined]

    # Create proxy from model
    if model_instance is not None:
        from observant import ObservableProxy  # type: ignore[import-untyped]

        proxy = ObservableProxy(model_instance, sync=True)
        widget.proxy = proxy  # type: ignore[attr-defined]


def _process_model_widget_auto_bindings(widget: QWidget, cls: type[Any]) -> None:
    """Auto-bind widget fields to model properties by matching names."""
    # Import here to avoid circular import
    from qtpie.bindings import bind, get_binding_registry
    from qtpie.model_widget import is_model_widget_subclass

    if not is_model_widget_subclass(cls):
        return

    # Get proxy
    proxy = getattr(widget, "proxy", None)
    if proxy is None:
        return

    # Get model to check for attribute names
    model = getattr(widget, "model", None)
    if model is None:
        return

    # Get type hints for field types
    type_hints = get_type_hints(cls)

    for f in fields(cls):  # type: ignore[arg-type]
        # Skip private fields
        if f.name.startswith("_"):
            continue

        # Skip model and proxy fields
        if f.name in ("model", "proxy"):
            continue

        # Skip fields that already have explicit bind=
        if f.metadata.get(BIND_METADATA_KEY) is not None:
            continue

        # Check if this field name matches a model attribute
        if not hasattr(model, f.name):
            continue

        # Check if this is a QWidget field
        field_type = type_hints.get(f.name)
        if not isinstance(field_type, type) or not issubclass(field_type, QWidget):
            continue

        # Get the widget instance
        widget_instance = getattr(widget, f.name, None)
        if widget_instance is None:
            continue

        # Get the observable for this model property
        try:
            observable = proxy.observable_for_path(f.name)
        except Exception:
            # Property might not be observable
            continue

        # Get the default property for this widget type
        bind_prop = get_binding_registry().get_default_prop(widget_instance)

        # Create the binding
        try:
            bind(observable, widget_instance, bind_prop)
        except Exception:
            # Binding might fail for some widget types
            pass
