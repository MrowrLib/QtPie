"""The @widget decorator - transforms classes into Qt widgets with automatic layout."""

import ast
import string
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
    QSizePolicy,
    QSpacerItem,
    QVBoxLayout,
    QWidget,
)

from qtpie.decorators._async_wrap import wrap_async_methods
from qtpie.factories.make import (
    BIND_METADATA_KEY,
    FORM_LABEL_METADATA_KEY,
    GET_APP_METADATA_KEY,
    GRID_POSITION_METADATA_KEY,
    MAKE_LATER_METADATA_KEY,
    SELECTOR_METADATA_KEY,
    SIGNALS_METADATA_KEY,
    GridTuple,
    SelectorInfo,
)
from qtpie.factories.spacer import SPACER_METADATA_KEY, SpacerConfig
from qtpie.state import get_state_observable, get_state_proxy, is_state_descriptor
from qtpie.translations.translatable import Translatable, set_translation_context

LayoutType = Literal["vertical", "horizontal", "form", "grid", "none"]


# Metadata key for storing undo config on the class
UNDO_CONFIG_METADATA_KEY = "_qtpie_undo_config"


def _is_excluded_field(field_name: str) -> bool:
    """Check if a field should be excluded from layout and auto-binding.

    Fields that start AND end with underscore (`_foo_`) are excluded.
    This provides a convention for fields that exist but opt out of magic.
    """
    return field_name.startswith("_") and field_name.endswith("_")


def _get_bind_name(field_name: str) -> str | None:
    """Get the name to use for auto-binding.

    - Excluded fields (`_foo_`): return None (no auto-bind)
    - Single underscore (`_foo`): return `foo` (strip leading underscore)
    - No underscore (`foo`): return `foo`
    """
    if _is_excluded_field(field_name):
        return None
    if field_name.startswith("_"):
        return field_name[1:]
    return field_name


def _should_add_to_layout(field_name: str) -> bool:
    """Check if a field should be added to the layout.

    - Excluded fields (`_foo_`): False
    - Single underscore (`_foo`): True
    - No underscore (`foo`): True
    """
    return not _is_excluded_field(field_name)


@overload
@dataclass_transform()
def widget[T](
    _cls: type[T],
    *,
    name: str | None = ...,
    classes: list[str] | None = ...,
    layout: LayoutType = ...,
    margins: int | tuple[int, int, int, int] | None = ...,
    auto_bind: bool = ...,
    undo: bool = ...,
    undo_max: int | None = ...,
    undo_debounce_ms: int | None = ...,
) -> type[T]: ...


@overload
@dataclass_transform()
def widget[T](
    _cls: None = None,
    *,
    name: str | None = ...,
    classes: list[str] | None = ...,
    layout: LayoutType = ...,
    margins: int | tuple[int, int, int, int] | None = ...,
    auto_bind: bool = ...,
    undo: bool = ...,
    undo_max: int | None = ...,
    undo_debounce_ms: int | None = ...,
) -> Callable[[type[T]], type[T]]: ...


@dataclass_transform()
def widget[T](
    _cls: type[T] | None = None,
    *,
    name: str | None = None,
    classes: list[str] | None = None,
    layout: LayoutType = "vertical",
    margins: int | tuple[int, int, int, int] | None = None,
    auto_bind: bool = True,
    undo: bool = False,
    undo_max: int | None = None,
    undo_debounce_ms: int | None = None,
) -> Callable[[type[T]], type[T]] | type[T]:
    """
    Decorator that transforms a class into a Qt widget with automatic layout.

    Args:
        name: Object name for QSS styling (defaults to class name).
        classes: CSS-like classes for styling.
        layout: The layout type - "vertical", "horizontal", or "none".
                Defaults to "vertical".
        margins: Layout margins. Either an int (all sides) or tuple (left, top, right, bottom).
        auto_bind: If True (default), Widget[T] fields with names matching record
                   properties are automatically bound. Set to False to disable.
        undo: If True, enable undo/redo for Widget[T] record fields.
        undo_max: Maximum undo steps to store (default: unlimited).
        undo_debounce_ms: Debounce time for undo recording (useful for text input).

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
    # Store undo config for later use
    undo_config = {
        "undo": undo,
        "undo_max": undo_max,
        "undo_debounce_ms": undo_debounce_ms,
    }

    def decorator(cls: type[T]) -> type[T]:
        # Auto-wrap async methods (e.g., async def closeEvent)
        wrap_async_methods(cls)

        # Apply @dataclass to register fields
        cls = dataclass(cls)  # type: ignore[assignment]

        # Store undo config on class for _process_model_widget to use
        setattr(cls, UNDO_CONFIG_METADATA_KEY, undo_config)

        # Find the Qt base class to initialize (QFrame, QWidget, etc.)
        qt_base_class: type[QWidget] = QWidget
        for base in cls.__bases__:
            if issubclass(base, QWidget):
                qt_base_class = base
                break

        def new_init(self: QWidget, *args: object, **kwargs: object) -> None:
            # Initialize the Qt base class first (QFrame, QWidget, etc.)
            qt_base_class.__init__(self)

            # Set translation context for tr[] markers in make() factories
            set_translation_context(cls.__name__)

            # Manually set dataclass fields (with default_factory support)
            for f in fields(cls):  # type: ignore[arg-type]
                # Skip state() fields - they're handled by the descriptor
                if f.default is not MISSING and is_state_descriptor(f.default):
                    continue

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

            # Set objectName and classes for child widgets from selector or field name
            type_hints = get_type_hints(cls)
            for f in fields(cls):  # type: ignore[arg-type]
                field_type = type_hints.get(f.name)
                if isinstance(field_type, type) and issubclass(field_type, QWidget):
                    widget_instance = getattr(self, f.name, None)
                    if isinstance(widget_instance, QWidget):
                        selector: SelectorInfo | None = f.metadata.get(SELECTOR_METADATA_KEY)
                        if selector is not None and selector.object_name is not None:
                            widget_instance.setObjectName(selector.object_name)
                        else:
                            # Use field name as objectName (including any underscores)
                            widget_instance.setObjectName(f.name)
                        if selector is not None and selector.classes is not None:
                            _set_classes(widget_instance, selector.classes)

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

                # Apply margins if specified
                if margins is not None:
                    if isinstance(margins, int):
                        _layout.setContentsMargins(margins, margins, margins, margins)
                    else:
                        _layout.setContentsMargins(*margins)

                # Add child widgets to layout
                for f in fields(cls):  # type: ignore[arg-type]
                    # Fields like _foo_ (start AND end with _) are excluded from layout
                    if not _should_add_to_layout(f.name):
                        continue

                    # Handle spacer() fields
                    spacer_config: SpacerConfig | None = f.metadata.get(SPACER_METADATA_KEY)
                    if spacer_config is not None:
                        if _box_layout is not None:
                            spacer = _create_spacer(_box_layout, spacer_config, layout)
                            setattr(self, f.name, spacer)
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

            # Early lifecycle hook (before bindings)
            _call_if_exists(self, "configure")

            # Process Widget[T] record if applicable
            _process_record_widget(self, cls)

            # Process data bindings
            _process_bindings(self, cls)

            # Process auto-bindings for Widget[T] (by field name)
            if auto_bind:
                _process_record_widget_auto_bindings(self, cls)

            # Process get_app() fields
            _process_get_app_fields(self, cls)

            # Late lifecycle hook (after bindings)
            _call_if_exists(self, "setup")

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


def _is_format_string(bind_path: str) -> bool:
    """Check if bind path is a format string like 'Count: {count}'."""
    return "{" in bind_path and "}" in bind_path


def _extract_ast_names(expr: str) -> set[str]:
    """Extract all variable names from a Python expression using AST.

    Only returns top-level names (for 'dog.name', returns 'dog').

    Example: "count + 5" → {"count"}
    Example: "dog.name.upper()" → {"dog"}
    Example: "x + y * z" → {"x", "y", "z"}
    Example: "len(name)" → {"name"}
    """
    try:
        tree = ast.parse(expr, mode="eval")
    except SyntaxError:
        return set()

    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            names.add(node.id)
    return names


def _is_simple_name(expr: str) -> bool:
    """Check if expression is a simple name or dotted path (no operators/calls)."""
    # Simple name: "count" or "dog.name" or "dog?.name"
    normalized = expr.replace("?.", ".")
    return all(part.isidentifier() for part in normalized.split("."))


@dataclass
class _FormatField:
    """A parsed field from a format string."""

    expression: str  # The expression: "count", "count + 5", "name.upper()"
    format_spec: str  # Format spec: "", ".2f", etc.
    is_expression: bool  # True if it's more than a simple name/path


def _parse_format_fields(format_string: str) -> list[_FormatField]:
    """Extract fields from a format string using string.Formatter.

    Example: "Count: {count}" → [_FormatField("count", "", False)]
    Example: "{price * 1.1:.2f}" → [_FormatField("price * 1.1", ".2f", True)]
    Example: "{name.upper()}" → [_FormatField("name.upper()", "", True)]
    """
    formatter = string.Formatter()
    fields: list[_FormatField] = []
    for _, field_name, format_spec, _ in formatter.parse(format_string):
        if field_name is not None and field_name != "":
            is_expr = not _is_simple_name(field_name)
            fields.append(_FormatField(field_name, format_spec or "", is_expr))
    return fields


def _get_observables_for_field(widget: QWidget, field_path: str) -> list[Any]:
    """Get observables for a field path (simple or nested).

    Returns a list of observables to subscribe to. For nested paths,
    returns both the nested observable AND the top-level state observable
    (so we get notified when the whole object is replaced).

    Handles:
    - Simple state: "count" → [state observable]
    - Nested state: "dog.name" → [nested observable, top-level state observable]
    - Widget[T] record fields: "name" → [proxy observable for "name"]
    """
    from qtpie.widget_base import is_widget_subclass

    # Normalize optional chaining for splitting
    normalized = field_path.replace("?.", ".")
    parts = normalized.split(".", 1)
    first_segment = parts[0]
    has_nested = len(parts) > 1

    # Trigger lazy initialization
    try:
        _ = getattr(widget, first_segment)
    except AttributeError:
        pass  # Continue - might be a proxy field

    if not has_nested:
        # Try state field first
        obs = get_state_observable(widget, field_path)
        if obs is not None:
            return [obs]

        # Try Widget[T] record_observable_proxy field
        if is_widget_subclass(type(widget)):
            proxy = getattr(widget, "record_observable_proxy", None)
            if proxy is not None and hasattr(proxy, "observable_for_path"):
                try:
                    return [proxy.observable_for_path(field_path)]
                except Exception:
                    pass

        return []
    else:
        # Nested path
        result: list[Any] = []

        # Try state object first
        top_level_obs = get_state_observable(widget, first_segment)
        if top_level_obs:
            result.append(top_level_obs)

        state_proxy = get_state_proxy(widget, first_segment)
        if state_proxy is not None:
            nested_path = field_path.split(".", 1)[1] if "." in field_path else ""
            if nested_path:
                result.append(state_proxy.observable_for_path(nested_path))
            return result

        # Try Widget[T] record_observable_proxy for nested paths like "address.city"
        if is_widget_subclass(type(widget)):
            proxy = getattr(widget, "record_observable_proxy", None)
            if proxy is not None and hasattr(proxy, "observable_for_path"):
                try:
                    result.append(proxy.observable_for_path(field_path))
                except Exception:
                    pass

        return result


def _get_expression_variable_names(fields: list[_FormatField]) -> set[str]:
    """Extract all variable names/paths from format fields.

    For simple names like 'count' or 'dog.name', returns the full path.
    For expressions like 'count + 5', uses AST to find all root names.
    Filters out Python builtins.
    """
    # Common builtins that shouldn't be treated as widget attributes
    builtins = {
        "len",
        "str",
        "int",
        "float",
        "bool",
        "abs",
        "min",
        "max",
        "sum",
        "round",
        "sorted",
        "list",
        "dict",
        "set",
        "tuple",
        "range",
        "enumerate",
        "zip",
        "map",
        "filter",
        "any",
        "all",
        "True",
        "False",
        "None",
    }

    names: set[str] = set()
    for field in fields:
        if field.is_expression:
            # Use AST to extract names from expression
            expr_names = _extract_ast_names(field.expression)
            names.update(expr_names - builtins)
        else:
            # Simple name or dotted path - keep the full path for proper observable subscription
            normalized = field.expression.replace("?.", ".")
            root = normalized.split(".")[0]
            if root not in builtins:
                names.add(normalized)  # Add full path, not just root
    return names


def _process_format_binding(
    widget: QWidget,
    widget_instance: QWidget,
    format_string: str,
    bind_prop: str,
    translatable: Translatable | None = None,
) -> bool:
    """Process a format string binding like 'Count: {count}' or '{count + 5}'.

    Supports:
    - Simple names: {count}, {dog.name}
    - Expressions: {count + 5}, {name.upper()}, {x if x > 0 else 'none'}
    - Format specs: {price:.2f}, {price * 1.1:.2f}
    - self reference: {self.count + 5}
    - Widget[T] record fields: {name}, {age}
    - Translatable format strings with hot-reload support

    Args:
        widget: The parent widget containing the binding source
        widget_instance: The child widget to bind to
        format_string: The format string to use
        bind_prop: The property to bind on widget_instance
        translatable: Optional Translatable for hot-reload support

    Returns True if binding was successful, False otherwise.
    """
    from qtpie.bindings import get_binding_registry
    from qtpie.widget_base import is_widget_subclass

    fields = _parse_format_fields(format_string)
    if not fields:
        return False

    # Extract all variable names/paths we need to observe
    var_names = _get_expression_variable_names(fields)

    # Handle 'self' specially - we need to observe all state fields
    uses_self = "self" in var_names
    var_names.discard("self")

    # Get ROOT names for building eval context (e.g., "dog" from "dog.name")
    root_names: set[str] = set()
    for var_name in var_names:
        root = var_name.split(".")[0]
        root_names.add(root)

    # Collect all observables to subscribe to
    all_observables: list[Any] = []

    for var_name in var_names:
        obs_list = _get_observables_for_field(widget, var_name)
        if obs_list:
            all_observables.extend(obs_list)
        # If we can't find observables, still continue - might be a non-state attribute

    # If using 'self', subscribe to ALL state fields on the widget
    if uses_self:
        from qtpie.state import ReactiveDescriptor

        for name in dir(type(widget)):
            descriptor = getattr(type(widget), name, None)
            if isinstance(descriptor, ReactiveDescriptor):
                obs_list = _get_observables_for_field(widget, name)
                all_observables.extend(obs_list)

    # Get the adapter for one-way binding
    adapter = get_binding_registry().get(widget_instance, bind_prop)
    if adapter is None or adapter.setter is None:
        return False

    # Check if this is a Widget[T] with a record_observable_proxy
    widget_proxy = getattr(widget, "record_observable_proxy", None) if is_widget_subclass(type(widget)) else None

    # Use a mutable container for format_string so hot-reload can update it
    current_format: list[str] = [format_string]

    # Build the compute function
    def compute() -> str:
        # Build context with current values (use ROOT names for getattr)
        context: dict[str, Any] = {"self": widget}

        # Add all variable values to context using root names
        for root_name in root_names:
            # For Widget[T], prefer proxy fields over widget attributes
            # This allows {name} to mean record.name even when there's a QLineEdit named "name"
            if widget_proxy is not None:
                try:
                    context[root_name] = widget_proxy.observable(object, root_name).get()
                    continue  # Successfully got from proxy
                except Exception:
                    pass  # Not a proxy field, fall back to widget attribute

            # Fall back to widget attribute (for state fields or regular attributes)
            value = getattr(widget, root_name, None)
            # Skip QWidget children - they're child widgets, not format values
            if isinstance(value, QWidget):
                value = None
            context[root_name] = value

        # Process each field and build the result using current format string
        result_parts: list[str] = []

        formatter = string.Formatter()
        for literal_text, field_name, format_spec, _ in formatter.parse(current_format[0]):
            result_parts.append(literal_text)

            if field_name is not None and field_name != "":
                # Evaluate the expression
                try:
                    value = eval(field_name, {"__builtins__": __builtins__}, context)
                except Exception:
                    value = f"<error: {field_name}>"

                # Apply format spec if present
                if format_spec:
                    try:
                        value = format(value, format_spec)
                    except Exception:
                        value = str(value)
                else:
                    value = str(value)

                result_parts.append(value)

        return "".join(result_parts)

    # Set initial value
    setter = adapter.setter
    setter(widget_instance, compute())

    # Subscribe to ALL observables - when any changes, recompute
    def on_any_change(_: Any) -> None:
        setter(widget_instance, compute())

    for obs in all_observables:
        obs.on_change(on_any_change)

    # Register for translation hot-reload if this is a Translatable binding
    if translatable is not None:
        from qtpie.translations.store import register_format_binding

        def on_translation_change(new_format: str) -> None:
            # Update the format string and recompute
            current_format[0] = new_format
            setter(widget_instance, compute())

        register_format_binding(
            widget_instance,
            translatable.text,
            translatable.disambiguation,
            on_translation_change,
        )

    return True


def _process_single_binding(
    widget: QWidget,
    widget_instance: QWidget,
    bind_path: str,
    bind_prop: str,
    translatable: Translatable | None = None,
) -> None:
    """Process a single property binding.

    Supports multiple forms of bind paths:
    - Format string: bind="Count: {count}" → computed format binding
    - Translatable: bind=tr["Count: {count}"] → translated format binding with hot-reload
    - State field: bind="count" → binds to state(0) field on self
    - Short form: bind="name" or bind="address.city" → uses self.record_observable_proxy
    - Explicit form: bind="other_proxy.name" → uses self.other_proxy
    """
    from qtpie.bindings import bind

    # Check 0: Is this a format string binding?
    if _is_format_string(bind_path):
        if _process_format_binding(widget, widget_instance, bind_path, bind_prop, translatable):
            return
        # Fall through if format binding fails

    # Parse path for detection (normalize ?. to . just for splitting)
    normalized_for_split = bind_path.replace("?.", ".")
    parts = normalized_for_split.split(".", 1)
    first_segment = parts[0]
    has_nested_path = len(parts) > 1

    # Check 1: Is this a state field?
    # Access the field to trigger observable creation (lazy initialization)
    try:
        _ = getattr(widget, first_segment)
    except AttributeError:
        pass

    if not has_nested_path:
        # Simple state field: bind="count"
        state_observable = get_state_observable(widget, bind_path)
        if state_observable is not None:
            bind(state_observable, widget_instance, bind_prop)
            return
    else:
        # Check if first segment is a state field with nested path: bind="dog.name"
        state_proxy = get_state_proxy(widget, first_segment)
        if state_proxy is not None:
            # Get the nested path (everything after the first segment)
            nested_path = bind_path.split(".", 1)[1] if "." in bind_path else ""
            if nested_path:
                observable = state_proxy.observable_for_path(nested_path)
                bind(observable, widget_instance, bind_prop)
                return

    # Check 2: Is first segment an ObservableProxy field?
    potential_proxy = getattr(widget, first_segment, None)
    if potential_proxy is not None and hasattr(potential_proxy, "observable_for_path"):
        # Explicit path: first segment is a proxy field (e.g., "other_proxy.name")
        proxy_field_name = first_segment
        # Use original path with ?. intact, minus the first segment
        observable_path = bind_path.split(".", 1)[1] if "." in bind_path else ""
    else:
        # Short form: use default "record_observable_proxy" field (e.g., "name" or "address.city")
        proxy_field_name = "record_observable_proxy"
        observable_path = bind_path

    # Handle empty observable path (invalid - can't bind to proxy itself)
    if not observable_path:
        return

    # Get the proxy from self
    proxy = getattr(widget, proxy_field_name, None)
    if proxy is None:
        # Proxy not yet created - skip silently
        return

    # Check if proxy has observable_for_path method (is ObservableProxy)
    if not hasattr(proxy, "observable_for_path"):
        return

    # Get the observable for the path
    observable = proxy.observable_for_path(observable_path)

    # Create the binding
    bind(observable, widget_instance, bind_prop)


def _process_bindings(widget: QWidget, cls: type[Any]) -> None:
    """Process data bindings from make() metadata.

    Supports:
    - bind="path" → binds to default widget property
    - bind={"prop": "path", ...} → binds multiple properties
    - bind=tr["format"] → translated format binding with hot-reload
    """
    from qtpie.bindings import get_binding_registry
    from qtpie.translations.translatable import get_translation_context

    for f in fields(cls):  # type: ignore[arg-type]
        bind_spec = f.metadata.get(BIND_METADATA_KEY)
        if bind_spec is None:
            continue

        # Get the widget instance for this field
        widget_instance = getattr(widget, f.name, None)
        if widget_instance is None:
            continue

        if isinstance(bind_spec, dict):
            # Multiple bindings: {"text": "user.name", "enabled": "user.canEdit"}
            for prop_name, path in cast(dict[str, str], bind_spec).items():
                _process_single_binding(widget, widget_instance, path, prop_name)
        elif isinstance(bind_spec, Translatable):
            # Translated format binding: bind=tr["Count: {count}"]
            # Resolve the translation to get the format string
            context = get_translation_context()
            format_string = bind_spec.resolve(context)
            default_prop = get_binding_registry().get_default_prop(widget_instance)
            _process_single_binding(widget, widget_instance, format_string, default_prop, bind_spec)
        else:
            # Single binding to default property
            default_prop = get_binding_registry().get_default_prop(widget_instance)
            _process_single_binding(widget, widget_instance, cast(str, bind_spec), default_prop)


def _process_record_widget(widget: QWidget, cls: type[Any]) -> None:
    """Process Widget[T] initialization - create record and proxy if type param provided."""
    # Import here to avoid circular import
    from qtpie.widget_base import (
        get_model_type_from_widget,
        has_model_type_param,
        is_widget_subclass,
    )

    if not is_widget_subclass(cls):
        return

    # Only do record binding if type parameter was provided (Widget[Dog] vs Widget)
    if not has_model_type_param(cls):
        return

    # Check if record field exists
    record_field = None
    for f in fields(cls):  # type: ignore[arg-type]
        if f.name == "record":
            record_field = f
            break

    record_instance = None

    if record_field is not None:
        # User defined a record field
        is_make_later = record_field.metadata.get(MAKE_LATER_METADATA_KEY, False)

        if is_make_later:
            # Check if user set it in configure()
            current_value = getattr(widget, "record", None)
            if current_value is None or not hasattr(widget, "record"):
                raise ValueError(
                    f"Widget field 'record' was declared with make_later() but not set in configure(). Either set self.record in configure() or use make({cls.__name__}, ...) to provide a factory."
                )
            record_instance = current_value
        else:
            # User used make() - get the created instance
            record_instance = getattr(widget, "record", None)
    else:
        # No record field defined - auto-create T()
        record_type = get_model_type_from_widget(cls)
        if record_type is None:
            raise ValueError(f"Cannot determine record type for {cls.__name__}. Ensure the class inherits from Widget[YourRecordType].")
        record_instance = record_type()
        widget.record = record_instance  # type: ignore[attr-defined]

    # Create proxy from record
    if record_instance is not None:
        from observant import ObservableProxy

        # Get undo config from class metadata
        undo_config = getattr(cls, UNDO_CONFIG_METADATA_KEY, {})
        undo_enabled = undo_config.get("undo", False)
        undo_max = undo_config.get("undo_max")
        undo_debounce_ms = undo_config.get("undo_debounce_ms")

        proxy = ObservableProxy(record_instance, sync=True, undo=undo_enabled)
        widget.record_observable_proxy = proxy  # type: ignore[attr-defined]

        # Apply per-field undo config if specified
        if undo_enabled and (undo_max is not None or undo_debounce_ms is not None):
            # Get all field names from the record
            for f in fields(record_instance):  # type: ignore[arg-type]
                config_kwargs: dict[str, Any] = {"enabled": True}
                if undo_max is not None:
                    config_kwargs["undo_max"] = undo_max
                if undo_debounce_ms is not None:
                    config_kwargs["undo_debounce_ms"] = undo_debounce_ms
                proxy.set_undo_config(f.name, **config_kwargs)


def _process_record_widget_auto_bindings(widget: QWidget, cls: type[Any]) -> None:
    """Auto-bind widget fields to record properties by matching names."""
    # Import here to avoid circular import
    from qtpie.bindings import bind, get_binding_registry
    from qtpie.widget_base import has_model_type_param, is_widget_subclass

    if not is_widget_subclass(cls):
        return

    # Only do auto-binding if type parameter was provided
    if not has_model_type_param(cls):
        return

    # Get record_observable_proxy
    proxy = getattr(widget, "record_observable_proxy", None)
    if proxy is None:
        return

    # Get record to check for attribute names
    record = getattr(widget, "record", None)
    if record is None:
        return

    # Get type hints for field types
    type_hints = get_type_hints(cls)

    for f in fields(cls):  # type: ignore[arg-type]
        # Get the bind name (handles _foo -> foo, _foo_ -> None)
        bind_name = _get_bind_name(f.name)
        if bind_name is None:
            # Excluded fields (_foo_) don't auto-bind
            continue

        # Skip record and record_observable_proxy fields
        if f.name in ("record", "record_observable_proxy"):
            continue

        # Skip fields that already have explicit bind=
        if f.metadata.get(BIND_METADATA_KEY) is not None:
            continue

        # Check if the bind name matches a record attribute
        # For _name fields, we check for "name" on the record
        if not hasattr(record, bind_name):
            continue

        # Check if this is a QWidget field
        field_type = type_hints.get(f.name)
        if not isinstance(field_type, type) or not issubclass(field_type, QWidget):
            continue

        # Get the widget instance
        widget_instance = getattr(widget, f.name, None)
        if widget_instance is None:
            continue

        # Get the observable for this record property
        # Use bind_name (e.g., "name" for field "_name")
        try:
            observable = proxy.observable_for_path(bind_name)
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


def _process_get_app_fields(widget: QWidget, cls: type[Any]) -> None:
    """Process get_app() fields - set app instance and connect signals."""
    from qtpy.QtWidgets import QApplication

    for f in fields(cls):  # type: ignore[arg-type]
        app_signals: dict[str, str] | None = f.metadata.get(GET_APP_METADATA_KEY)
        if app_signals is None:
            continue

        # Get the app instance
        app = QApplication.instance()
        if app is None:
            continue

        # Set the field to the app instance
        setattr(widget, f.name, app)

        # Connect signals
        for signal_name, method_name in app_signals.items():
            signal = getattr(app, signal_name, None)
            if signal is None:
                continue
            method = getattr(widget, method_name, None)
            if method is None:
                continue
            signal.connect(method)


def _create_spacer(
    box_layout: QBoxLayout,
    config: SpacerConfig,
    layout_type: LayoutType,
) -> QSpacerItem:
    """Create a QSpacerItem and add it to a box layout.

    Args:
        box_layout: The box layout to add the spacer to.
        config: Stretch configuration with factor, min_size, max_size.
        layout_type: "vertical" or "horizontal" to determine direction.

    Returns:
        The created QSpacerItem (also stored on the widget instance).
    """
    is_vertical = layout_type == "vertical"

    # Determine size policies based on constraints
    if config.min_size > 0 and config.max_size > 0 and config.min_size == config.max_size:
        # Fixed size
        policy = QSizePolicy.Policy.Fixed
    elif config.max_size > 0:
        # Has max constraint
        policy = QSizePolicy.Policy.Maximum
    elif config.min_size > 0:
        # Has min constraint, can expand
        policy = QSizePolicy.Policy.Expanding
    else:
        # Default: expanding (same as addStretch)
        policy = QSizePolicy.Policy.Expanding

    # Create spacer with appropriate dimensions and policies
    if is_vertical:
        # Vertical layout: height matters, width is minimum
        width = 0
        height = config.min_size
        h_policy = QSizePolicy.Policy.Minimum
        v_policy = policy
    else:
        # Horizontal layout: width matters, height is minimum
        width = config.min_size
        height = 0
        h_policy = policy
        v_policy = QSizePolicy.Policy.Minimum

    spacer = QSpacerItem(width, height, h_policy, v_policy)
    box_layout.addSpacerItem(spacer)

    # Set stretch factor on the layout item (replicates addStretch behavior)
    if config.factor > 0:
        item_index = box_layout.count() - 1
        box_layout.setStretch(item_index, config.factor)

    return spacer
