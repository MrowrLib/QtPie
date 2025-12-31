"""The make() factory function for creating widget instances."""

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, cast

from qtpy.QtCore import QObject
from qtpy.QtWidgets import (
    QAbstractButton,
    QAction,
    QGroupBox,
    QLabel,
    QLineEdit,
    QMenu,
)

from qtpie.translations.translatable import Translatable, resolve_translatable

# Type alias for bind parameter - can be Translatable for translated format strings
BindSpec = str | dict[str, str] | Translatable | None

# Map widget types to property name for first positional string arg
_FIRST_ARG_PROPERTY: dict[type, str] = {
    QLabel: "text",
    QAbstractButton: "text",  # QPushButton, QCheckBox, QRadioButton, QToolButton
    QGroupBox: "title",
    QLineEdit: "text",
    QAction: "text",
    QMenu: "title",
}

# Metadata keys used to store info for the @widget decorator
SIGNALS_METADATA_KEY = "qtpie_signals"
FORM_LABEL_METADATA_KEY = "qtpie_form_label"
GRID_POSITION_METADATA_KEY = "qtpie_grid_position"
BIND_METADATA_KEY = "qtpie_bind"
MAKE_LATER_METADATA_KEY = "qtpie_make_later"
GET_APP_METADATA_KEY = "qtpie_get_app"
SELECTOR_METADATA_KEY = "qtpie_selector"

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


def make[T](
    cls: Callable[..., T],
    /,
    *args: Any,
    style: str | None = None,
    form_label: str | None = None,
    grid: GridTuple | None = None,
    bind: BindSpec = None,
    init: InitArgs | None = None,
    **kwargs: Any,
) -> T:
    """
    Create a widget instance as a dataclass field default.

    This provides a cleaner syntax than field(default_factory=lambda: ...).

    Args:
        cls: The widget class to instantiate.
        *args: Positional arguments passed to the constructor.
        style: CSS-like selector for objectName and classes.
               Examples: "#myid", ".primary", "#btn.primary.large"
        form_label: Label text for form layouts. When set, creates a labeled row.
        grid: Position in grid layout as (row, col) or (row, col, rowspan, colspan).
        bind: Data binding specification. Can be:
              - str: Path to bind to default widget property, e.g. "user.name"
              - dict: Map of widget properties to paths, e.g. {"text": "user.name", "enabled": "user.canEdit"}
              - Translatable: tr[] for translated format strings, e.g. bind=tr["Count: {count}"]
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

        # With style (objectName and/or classes)
        label: QLabel = make(QLabel, "Hello", style="#title")
        button: QPushButton = make(QPushButton, "Click", style=".primary")
        submit: QPushButton = make(QPushButton, "Submit", style="#submit.primary.large")

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

        # Translated format binding (hot-reloads with translation changes)
        count_label: QLabel = make(QLabel, bind=tr["Count: {count}"])

    Returns:
        At type-check time: T (the widget type)
        At runtime: a dataclass field with default_factory

    Note:
        The type lie (returning T but actually returning field()) is intentional
        to make the API ergonomic while maintaining type safety.
    """
    # Parse style= into selector info
    selector_info: SelectorInfo | None = None
    if style is not None:
        selector_info = parse_selector(style)

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

    is_qobject_class = isinstance(cls, type) and issubclass(cls, QObject)

    for key, value in kwargs.items():
        # Translatable is callable (for plurals) but is NOT a signal
        if isinstance(value, Translatable):
            widget_kwargs[key] = value
        elif is_qobject_class and (isinstance(value, str) or callable(value)):
            # Could be a signal connection - store for later verification
            potential_signals[key] = value
        else:
            # Regular property - pass to constructor
            widget_kwargs[key] = value

    # Merge init_kwargs into widget_kwargs (init takes precedence)
    widget_kwargs.update(init_kwargs)

    # Combine args with init_args
    combined_args = (*args, *init_args)

    # Track which kwargs have Translatable values for binding registration
    translatable_kwargs: dict[str, Translatable] = {k: v for k, v in widget_kwargs.items() if isinstance(v, Translatable)}

    # Track translatable positional args (index -> Translatable)
    translatable_args: dict[int, Translatable] = {i: arg for i, arg in enumerate(combined_args) if isinstance(arg, Translatable)}

    # Figure out property name for first positional arg (only for known widgets)
    first_arg_property: str | None = None
    if isinstance(cls, type):
        for widget_type, prop_name in _FIRST_ARG_PROPERTY.items():
            if issubclass(cls, widget_type):
                first_arg_property = prop_name
                break

    # Error if positional tr[] used on unknown widget type
    if 0 in translatable_args and first_arg_property is None:
        cls_name = getattr(cls, "__name__", str(cls))
        raise TypeError(f"tr[] as positional arg not supported for {cls_name}. Use keyword arg: make({cls_name}, text=tr[...]) or similar.")

    def factory_fn() -> T:
        # Resolve any Translatable markers in args and kwargs
        resolved_args: tuple[Any, ...] = tuple(resolve_translatable(arg) for arg in combined_args)
        resolved_kwargs: dict[str, Any] = {k: resolve_translatable(v) for k, v in widget_kwargs.items()}
        instance = cast(T, cls(*resolved_args, **resolved_kwargs))

        # Register translation bindings for hot-reload support
        if isinstance(instance, QObject):
            from qtpie.translations.store import register_binding

            # Register kwarg bindings (property name is explicit)
            for prop_name, translatable in translatable_kwargs.items():
                register_binding(
                    instance,
                    prop_name,
                    translatable.text,
                    translatable.disambiguation,
                )

            # Register positional arg bindings (first arg maps to known property)
            if first_arg_property and 0 in translatable_args:
                translatable = translatable_args[0]
                register_binding(
                    instance,
                    first_arg_property,
                    translatable.text,
                    translatable.disambiguation,
                )

        return instance

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


def get_app(**signals: str) -> Any:
    """
    Get the QApplication instance with optional signal connections.

    Use this to declaratively connect to app-level signals.

    Example:
        @widget()
        class MyWidget(QWidget):
            _app: QApplication = get_app(focusChanged="_on_focus_changed")

            def _on_focus_changed(self, old: QWidget, new: QWidget) -> None:
                ...

    The app instance is set during widget initialization and signals
    are connected to the specified methods.
    """
    return field(init=False, metadata={GET_APP_METADATA_KEY: signals})
