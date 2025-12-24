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
FORWARD_REF_METADATA_KEY = "qtpie_forward_ref"

# Type alias for grid position tuples
GridTuple = tuple[int, int] | tuple[int, int, int, int]

# Type alias for init parameter
InitArgs = list[Any] | dict[str, Any] | tuple[list[Any], dict[str, Any]]


@dataclass
class SelectorInfo:
    """Parsed CSS selector info from make()."""

    object_name: str | None = None
    classes: list[str] | None = None


def is_selector(s: str) -> bool:
    """Check if string is a CSS selector (starts with # or .)."""
    return s.startswith("#") or s.startswith(".")


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
    init: InitArgs | None = None,
    **kwargs: Any,
) -> T: ...


@overload
def make[T](
    __class_type: Callable[..., T],
    *args: Any,
    form_label: str | None = None,
    grid: GridTuple | None = None,
    bind: str | dict[str, str] | None = None,
    init: InitArgs | None = None,
    **kwargs: Any,
) -> T: ...


@overload
def make(
    *,
    class_name: str,
    form_label: str | None = None,
    grid: GridTuple | None = None,
    bind: str | dict[str, str] | None = None,
    init: InitArgs | None = None,
    **kwargs: Any,
) -> Any: ...


def make[T](
    __selector_or_class: str | Callable[..., T] | None = None,
    __class_type_or_first_arg: Callable[..., T] | Any = None,
    *args: Any,
    class_name: str | None = None,
    form_label: str | None = None,
    grid: GridTuple | None = None,
    bind: str | dict[str, str] | None = None,
    init: InitArgs | None = None,
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
        class_name: Forward reference class name (string). Use with init= for args.
        form_label: Label text for form layouts. When set, creates a labeled row.
        grid: Position in grid layout as (row, col) or (row, col, rowspan, colspan).
        bind: Data binding specification. Can be:
              - str: Path to bind to default widget property, e.g. "user.name"
              - dict: Map of widget properties to paths, e.g. {"text": "user.name", "enabled": "user.canEdit"}
        init: Explicit constructor arguments (use when kwargs conflict with signals).
              - list: Positional args, e.g. init=[1, 2, 3]
              - dict: Keyword args, e.g. init={"name": "value"}
              - tuple[list, dict]: Both, e.g. init=([1, 2], {"name": "value"})
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

        # Forward reference (for circular imports)
        child: "ChildWidget" = make(class_name="ChildWidget", init=["arg1"])

        # With signal connections (string = method name)
        button: QPushButton = make(QPushButton, "Click", clicked="on_click")

        # With signal connections (callable)
        button: QPushButton = make(QPushButton, clicked=lambda: print("clicked!"))

        # Explicit constructor args (when kwarg names conflict with signals)
        widget: MyWidget = make(MyWidget, init={"clicked": "not_a_signal"})

        # Form layout with label
        name: QLineEdit = make(QLineEdit, form_label="Full Name")

        # Grid layout with position
        btn: QPushButton = make(QPushButton, "7", grid=(1, 0))
        display: QLineEdit = make(QLineEdit, grid=(0, 0, 1, 4))  # spans 4 cols

        # Data binding
        name_edit: QLineEdit = make(QLineEdit, bind="user.name")

    Returns:
        At type-check time: T (the widget type)
        At runtime: a dataclass field with default_factory

    Note:
        The type lie (returning T but actually returning field()) is intentional
        to make the API ergonomic while maintaining type safety.
    """
    # Handle overloaded signature
    selector_info: SelectorInfo | None = None
    forward_ref: str | None = None
    class_type: Callable[..., T] | None = None
    actual_args: tuple[Any, ...]

    # Check for class_name keyword arg (forward reference)
    if class_name is not None:
        forward_ref = class_name
        class_type = None
        actual_args = ()  # Use init= for constructor args
    elif isinstance(__selector_or_class, str):
        # First arg is a string - must be a CSS selector
        if is_selector(__selector_or_class):
            selector_info = parse_selector(__selector_or_class)
            class_type = cast(Callable[..., T], __class_type_or_first_arg)
            actual_args = args
        else:
            raise ValueError(f"Invalid selector: {__selector_or_class!r}. Selectors must start with # or . (e.g., '#id', '.class'). For forward references, use class_name='ClassName'.")
    elif __selector_or_class is not None:
        # First arg is the class type - this is the normal case: make(QLabel, ...)
        class_type = __selector_or_class
        if __class_type_or_first_arg is not None:
            actual_args = (__class_type_or_first_arg, *args)
        else:
            actual_args = args
    else:
        raise ValueError("make() requires a class type, selector, or class_name='...'.")

    # Parse init parameter into args and kwargs
    init_args: list[Any] = []
    init_kwargs: dict[str, Any] = {}
    if init is not None:
        if isinstance(init, list):
            init_args = init
        elif isinstance(init, dict):
            init_kwargs = init
        else:
            # Must be tuple[list, dict]
            init_args, init_kwargs = init

    # Separate potential signal kwargs from widget property kwargs
    # Only do signal detection for QObject subclasses (widgets, actions, etc.)
    potential_signals: dict[str, str | Callable[..., Any]] = {}
    widget_kwargs: dict[str, Any] = {}

    is_qobject_class = class_type is not None and isinstance(class_type, type) and issubclass(class_type, QObject)

    for key, value in kwargs.items():
        if is_qobject_class and (isinstance(value, str) or callable(value)):
            # Could be a signal connection - store for later verification
            potential_signals[key] = value
        else:
            # Regular property - pass to constructor
            widget_kwargs[key] = value

    # Merge init_kwargs into widget_kwargs (init takes precedence)
    widget_kwargs.update(init_kwargs)

    # Combine actual_args with init_args (actual_args first, then init_args)
    combined_args = (*actual_args, *init_args)

    def factory_fn() -> T:
        if forward_ref is not None:
            # Resolve forward reference at runtime
            import inspect

            # Look up in the caller's module globals
            frame = inspect.currentframe()
            if frame is not None:
                frame = frame.f_back
            while frame is not None:
                if forward_ref in frame.f_globals:
                    resolved_class = frame.f_globals[forward_ref]
                    return cast(T, resolved_class(*combined_args, **widget_kwargs))
                frame = frame.f_back
            raise NameError(f"Forward reference {forward_ref!r} could not be resolved")
        else:
            assert class_type is not None
            return cast(T, class_type(*combined_args, **widget_kwargs))

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
    if forward_ref is not None:
        metadata[FORWARD_REF_METADATA_KEY] = forward_ref

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
