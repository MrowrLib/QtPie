"""The make() factory function for creating widget instances."""

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, cast, overload

from qtpy.QtCore import QObject

# Metadata keys used to store info for the @widget decorator
SIGNALS_METADATA_KEY = "qtpie_signals"
FORM_LABEL_METADATA_KEY = "qtpie_form_label"
GRID_POSITION_METADATA_KEY = "qtpie_grid_position"
BIND_METADATA_KEY = "qtpie_bind"
MAKE_LATER_METADATA_KEY = "qtpie_make_later"
SELECTOR_METADATA_KEY = "qtpie_selector"

# Type alias for grid position tuples
GridTuple = tuple[int, int] | tuple[int, int, int, int]


@dataclass
class SelectorInfo:
    """Parsed CSS selector info from make()."""

    object_name: str | None = None
    classes: list[str] | None = None


def parse_selector(selector: str) -> SelectorInfo:
    """Parse a CSS-like selector string into objectName and classes.

    Examples:
        "#hello" → SelectorInfo(object_name="hello", classes=None)
        ".primary" → SelectorInfo(object_name=None, classes=["primary"])
        "#btn.primary.large" → SelectorInfo(object_name="btn", classes=["primary", "large"])
        ".primary.large" → SelectorInfo(object_name=None, classes=["primary", "large"])
    """
    if not selector or (not selector.startswith("#") and not selector.startswith(".")):
        return SelectorInfo()

    object_name: str | None = None
    classes: list[str] = []

    # Split by . but keep track of # for objectName
    if selector.startswith("#"):
        # Has objectName
        rest = selector[1:]  # Remove leading #
        parts = rest.split(".")
        object_name = parts[0] if parts[0] else None
        classes = [p for p in parts[1:] if p]
    else:
        # Starts with . - only classes
        parts = selector.split(".")
        classes = [p for p in parts if p]

    return SelectorInfo(
        object_name=object_name,
        classes=classes if classes else None,
    )


@overload
def make[T](
    __selector: str,
    __class_type: Callable[..., T],
    *args: Any,
    form_label: str | None = None,
    grid: GridTuple | None = None,
    bind: str | dict[str, str] | None = None,
    **kwargs: Any,
) -> T: ...


@overload
def make[T](
    __class_type: Callable[..., T],
    *args: Any,
    form_label: str | None = None,
    grid: GridTuple | None = None,
    bind: str | dict[str, str] | None = None,
    **kwargs: Any,
) -> T: ...


def make[T](
    __selector_or_class: str | Callable[..., T],
    __class_type_or_first_arg: Callable[..., T] | Any = None,
    *args: Any,
    form_label: str | None = None,
    grid: GridTuple | None = None,
    bind: str | dict[str, str] | None = None,
    **kwargs: Any,
) -> T:
    """
    Create a widget instance as a dataclass field default.

    This provides a cleaner syntax than field(default_factory=lambda: ...).

    Args:
        selector: Optional CSS-like selector for objectName and classes.
                  Examples: "#myid", ".primary", "#btn.primary.large"
        class_type: The widget class to instantiate.
        *args: Positional arguments passed to the constructor.
        form_label: Label text for form layouts. When set, creates a labeled row.
        grid: Position in grid layout as (row, col) or (row, col, rowspan, colspan).
        bind: Data binding specification. Can be:
              - str: Path to bind to default widget property, e.g. "user.name"
              - dict: Map of widget properties to paths, e.g. {"text": "user.name", "enabled": "user.canEdit"}
        **kwargs: Keyword arguments - if value is a string or callable,
                  it's treated as a potential signal connection. Otherwise,
                  it's passed to the constructor.

    Examples:
        # Basic widget creation
        label: QLabel = make(QLabel, "Hello World")

        # With CSS selector (objectName and/or classes)
        label: QLabel = make("#title", QLabel, "Hello")
        button: QPushButton = make(".primary", QPushButton, "Click")
        submit: QPushButton = make("#submit.primary.large", QPushButton, "Submit")

        # With properties
        edit: QLineEdit = make(QLineEdit, placeholderText="Enter name")

        # With signal connections (string = method name)
        button: QPushButton = make(QPushButton, "Click", clicked="on_click")

        # With signal connections (callable)
        button: QPushButton = make(QPushButton, clicked=lambda: print("clicked!"))

        # Form layout with label
        name: QLineEdit = make(QLineEdit, form_label="Full Name")

        # Grid layout with position
        btn: QPushButton = make(QPushButton, "7", grid=(1, 0))
        display: QLineEdit = make(QLineEdit, grid=(0, 0, 1, 4))  # spans 4 cols

        # Simple data binding (uses default widget property)
        name_edit: QLineEdit = make(QLineEdit, bind="user.name")
        age_spin: QSpinBox = make(QSpinBox, bind="user.age")

        # Multiple bindings to different properties
        name_edit: QLineEdit = make(QLineEdit, bind={
            "text": "user.name",
            "placeholderText": "user.namePlaceholder",
            "enabled": "user.canEdit",
        })

    Returns:
        At type-check time: T (the widget type)
        At runtime: a dataclass field with default_factory

    Note:
        The type lie (returning T but actually returning field()) is intentional
        to make the API ergonomic while maintaining type safety.
    """
    # Handle overloaded signature: detect if first arg is a selector string
    selector_info: SelectorInfo | None = None
    class_type: Callable[..., T]
    actual_args: tuple[Any, ...]

    if isinstance(__selector_or_class, str):
        # First arg is a selector string
        selector_info = parse_selector(__selector_or_class)
        class_type = cast(Callable[..., T], __class_type_or_first_arg)
        actual_args = args
    else:
        # First arg is the class type
        class_type = __selector_or_class
        if __class_type_or_first_arg is not None:
            actual_args = (__class_type_or_first_arg, *args)
        else:
            actual_args = args

    # Separate potential signal kwargs from widget property kwargs
    # Only do signal detection for QObject subclasses (widgets, actions, etc.)
    potential_signals: dict[str, str | Callable[..., Any]] = {}
    widget_kwargs: dict[str, Any] = {}

    is_qobject_class = isinstance(class_type, type) and issubclass(class_type, QObject)

    for key, value in kwargs.items():
        if is_qobject_class and (isinstance(value, str) or callable(value)):
            # Could be a signal connection - store for later verification
            potential_signals[key] = value
        else:
            # Regular property - pass to constructor
            widget_kwargs[key] = value

    def factory_fn() -> T:
        return cast(T, class_type(*actual_args, **widget_kwargs))

    metadata: dict[str, Any] = {}
    if potential_signals:
        metadata[SIGNALS_METADATA_KEY] = potential_signals
    if form_label is not None:
        metadata[FORM_LABEL_METADATA_KEY] = form_label
    if grid is not None:
        metadata[GRID_POSITION_METADATA_KEY] = grid
    if bind is not None:
        metadata[BIND_METADATA_KEY] = bind
    if selector_info is not None:
        metadata[SELECTOR_METADATA_KEY] = selector_info

    return field(default_factory=factory_fn, metadata=metadata if metadata else {})  # type: ignore[return-value]


def make_later() -> Any:
    """
    Declare a field that will be initialized later (in setup()).

    Use this for fields that need to reference other fields or self.

    Example:
        @widget()
        class MyWidget(QWidget):
            model: Dog = make(Dog)
            proxy: ObservableProxy[Dog] = make_later()  # initialized in setup()

            def setup(self) -> None:
                self.proxy = ObservableProxy(self.model, sync=True)

    For ModelWidget, if model is marked with make_later() but not set
    in setup(), an error will be raised.
    """
    return field(init=False, metadata={MAKE_LATER_METADATA_KEY: True})
