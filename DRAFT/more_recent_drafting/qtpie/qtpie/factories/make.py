from dataclasses import field
from typing import Any, Callable, TypeVar

T = TypeVar("T", covariant=True)

BIND_METADATA_KEY = "qtpie_bind"
BIND_PROP_METADATA_KEY = "qtpie_bind_prop"
SIGNALS_METADATA_KEY = "qtpie_signals"


def make(
    class_type: Callable[..., T],
    *args: Any,
    bind: str | None = None,
    bind_prop: str | None = None,
    **kwargs: Any,
) -> T:
    """
    Creates a factory for any object that can be used as a dataclass field default.

    This provides a cleaner syntax for object creation in dataclasses compared to
    using field(default_factory=lambda: ...) directly.

    Usage:
        # For widgets:
        central_widget: QLabel = make(QLabel, "Hello World")
        my_button: QPushButton = make(QPushButton, "Click me")

        # With model binding (uses widget's default property):
        txt_name: QLineEdit = make(QLineEdit, bind="name")  # uses "text"
        slider_age: QSlider = make(QSlider, bind="age")     # uses "value"

        # Override the property if needed:
        custom: MyWidget = make(MyWidget, bind="foo", bind_prop="custom_prop")

        # Connect signals to methods by name:
        btn: QPushButton = make(QPushButton, "Click", clicked="on_button_clicked")

        # Connect multiple signals:
        slider: QSlider = make(QSlider, valueChanged="on_value", sliderReleased="on_done")

        # Connect with lambdas for simple cases:
        btn: QPushButton = make(QPushButton, clicked=lambda: print("clicked!"))

    Signal connections are detected by checking if the value is a string (method name)
    or callable. At runtime, the widget decorator verifies the attribute is actually
    a signal with a .connect() method.

    Returns an object of type T for type checking, but at runtime returns a dataclass field.

    This type lie is intentional to make the API more ergonomic while maintaining type safety.
    """
    # Separate potential signal kwargs from widget property kwargs
    # If value is a string or callable, assume it might be a signal connection
    # The widget decorator will verify at runtime if it's actually a signal
    potential_signals: dict[str, str | Callable[..., Any]] = {}
    widget_kwargs: dict[str, Any] = {}

    for key, value in kwargs.items():
        if isinstance(value, str) or callable(value):
            # Could be a signal connection - store separately
            # Will be verified at widget init time
            potential_signals[key] = value
        else:
            widget_kwargs[key] = value

    factory_fn: Callable[[], T] = lambda: class_type(*args, **widget_kwargs)  # noqa: E731
    metadata: dict[str, Any] = {}

    if bind is not None:
        metadata[BIND_METADATA_KEY] = bind
        if bind_prop is not None:
            metadata[BIND_PROP_METADATA_KEY] = bind_prop

    if potential_signals:
        metadata[SIGNALS_METADATA_KEY] = potential_signals

    return field(default_factory=factory_fn, metadata=metadata)
