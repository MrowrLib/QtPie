"""menu - Declarative menu system with Variable bindings."""

# pyright: reportPrivateUsage=false
# pyright: reportUnknownMemberType=false
# pyright: reportUnknownVariableType=false
# pyright: reportUnknownArgumentType=false
# pyright: reportUnknownLambdaType=false
# pyright: reportUnnecessaryCast=false
# pyright: reportUnnecessaryIsInstance=false
# pyright: reportArgumentType=false

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, cast, get_args, get_origin, overload

from observant import Observable, ObservableDict, ObservableList, ObservableProxy
from qtpy.QtWidgets import QMenu

from .new_field import NewField
from .new_fields import new_fields
from .signals import create_signal_expression_handler
from .state import QtPieState
from .utils.common import detect_required_bindings
from .variable import (
    RecordVariable,
    Variable,
    _RequiredBindingDescriptor,  # pyright: ignore[reportPrivateUsage]
)

# =============================================================================
# Marker Classes
# =============================================================================


class Separator:
    """Marker class for menu separators.

    Usage:
        ____: Separator  # Bare annotation creates separator
    """

    pass


class Section:
    """Marker class for menu sections.

    Usage:
        ___recent___: Section  # Text derived from name ("Recent")
        ___files___: Section = new("Recent Files")  # Explicit text
        ___dynamic___: Section = new(bind="_section_title")  # Reactive
    """

    pass


# =============================================================================
# Record Descriptor for Menu[T]
# =============================================================================


class _MenuRecordDescriptor[T]:
    """Descriptor for auto-created record on Menu[T].

    Lazily creates the record Variable on first access.
    """

    def __init__(self, record_type: type[T]) -> None:
        self._record_type = record_type

    def __get__(self, obj: "Menu[T] | None", objtype: type | None = None) -> RecordVariable[T]:  # noqa: UP037
        if obj is None:
            return self  # type: ignore[return-value]

        if not hasattr(obj, "_qtpie"):
            obj._qtpie = QtPieState(obj)

        state = obj._qtpie
        if state._record is None:
            try:
                # Try to create instance with no args
                instance = self._record_type()
                wrapper: ObservableProxy[T] = ObservableProxy(instance)
            except TypeError:
                # Type requires constructor args - create proxy with None target
                wrapper = ObservableProxy[T](None)  # type: ignore[arg-type]
            record_var: RecordVariable[T] = RecordVariable(wrapper)
            state._record = record_var
            state.register_variable("record", record_var)

        return state._record  # type: ignore[return-value]

    def __set__(self, obj: "Menu[T]", value: T | RecordVariable[T]) -> None:  # noqa: UP037
        if not hasattr(obj, "_qtpie"):
            obj._qtpie = QtPieState(obj)

        if isinstance(value, RecordVariable):
            obj._qtpie._record = value
            obj._qtpie.register_variable("record", value)  # type: ignore[arg-type]
        else:
            # Setting a value - create a new ObservableProxy with the value
            wrapper: ObservableProxy[T] = ObservableProxy(value)
            record_var: RecordVariable[T] = RecordVariable(wrapper)
            obj._qtpie._record = record_var
            obj._qtpie.register_variable("record", record_var)


# =============================================================================
# Menu Configuration
# =============================================================================


@dataclass
class MenuConfig:
    """Configuration for @menu decorator."""

    init_wrapped: bool = False
    auto_bind: bool = True  # Enable auto-binding for Variables
    text: str | None = None  # Menu title (e.g., "&File")
    object_name: str | None = None
    css_classes: list[str] = field(default_factory=lambda: list[str]())
    # Widget props from decorator (for reactive props like title="{_var}")
    widget_props: dict[str, Any] = field(default_factory=lambda: dict[str, Any]())
    # Track fields for action handling
    fields: dict[str, NewField] = field(default_factory=lambda: dict[str, NewField]())
    variable_names: list[str] = field(default_factory=lambda: list[str]())
    # Required bindings - bare Variable[T] fields
    required_bindings: set[str] = field(default_factory=lambda: set[str]())
    # Record type from Menu[T]
    record_type: type[Any] | None = None
    # Initial record value from @menu(record=...)
    record_default: Any | None = None
    # Ordered list of items (actions, separators, sections) by field name
    item_order: list[str] = field(default_factory=lambda: list[str]())
    # Signal connections from decorator: {signal_name: handler_name}
    signal_connections: dict[str, str] = field(default_factory=lambda: dict[str, str]())


# =============================================================================
# Menu Base Class
# =============================================================================


class Menu[T = None](QMenu):
    """QMenu with QtPie declarative features.

    Supports:
    - Variable bindings (required and optional)
    - Declarative QAction fields
    - Separators and Sections
    - Dynamic action lists
    - Record type (Menu[T])
    """

    _qtpie_config: MenuConfig
    _qtpie: QtPieState

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)

        # Each subclass gets its own config
        cls._qtpie_config = MenuConfig()

        # Extract T from Menu[T] if present
        for base in getattr(cls, "__orig_bases__", ()):
            origin = get_origin(base)
            if origin is Menu:
                args = get_args(base)
                if args:
                    cls._qtpie_config.record_type = args[0]
                break

        # Collect NewField instances and track item order
        _collect_menu_fields(cls)

        # Detect bare Variable[T] annotations as required bindings
        _detect_required_bindings_for_menu(cls)

        # Apply new_fields to handle Variable and QAction instantiation
        new_fields(cls)

        # Collect variable names (after new_fields processes them)
        from .variable import _VariableDescriptor  # pyright: ignore[reportPrivateUsage]

        for name, value in list(cls.__dict__.items()):
            if isinstance(value, _VariableDescriptor):
                cls._qtpie_config.variable_names.append(name)

        # If Menu[T] has a record_type, create a record descriptor
        # Check if user explicitly declared a record field
        has_explicit_record = "record" in cls.__dict__
        if cls._qtpie_config.record_type is not None and not has_explicit_record:
            cls.record = _MenuRecordDescriptor(cls._qtpie_config.record_type)  # type: ignore[assignment]

    if TYPE_CHECKING:
        # Lie to pyright: say record returns T for field autocomplete
        # Runtime: _MenuRecordDescriptor returns RecordVariable which forwards via __getattr__
        @property
        def record(self) -> T: ...
        @record.setter
        def record(self, value: T) -> None: ...

    def _refresh_parent_bindings(self) -> None:
        """Refresh bindings that depend on #parent.

        Called by Window after adding menu to menubar to set up parent-dependent
        bindings that couldn't be established during menu creation.
        """
        # Get config
        config = getattr(self.__class__, "_qtpie_config", None)
        if config is None:
            return

        # Re-apply action property bindings now that parent is set
        _apply_action_property_bindings(self, config)

    def build[W](self, cls: type[W], /, *args: Any, **kwargs: Any) -> W:
        """Build an instance at runtime with new()-like signal and property wiring.

        This is the runtime equivalent of new(). Use it when you need to create
        widget instances dynamically (not at class definition time).

        Args:
            cls: The class to instantiate.
            *args: Positional arguments passed to the constructor.
            **kwargs: Keyword arguments. Signal names (e.g., triggered="handler")
                      are extracted and connected to methods on this Menu.

        Returns:
            The created instance with signals connected and properties applied.

        Supported (see create_instance for full details):
            - Signal connections: triggered="method_name" or triggered=lambda: ...
            - Widget props: enabled=False, toolTip="...", etc.
            - name=, classes=, bind=, visible=, enabled=, ref(), t()
            - Variable bindings for child widgets with required bindings (bare Variable[T])

        NOT supported (only work with new() at class definition time):
            - list/dict repeaters, label=, grid=, stretch=, layout hints

        Example:
            def add_recent_file(self, path: str) -> None:
                action = self.build(QAction, path, triggered="open_recent")
                self.addAction(action)
        """
        from qtpie.create import create_instance

        return create_instance(self, cls, *args, **kwargs)

    # -------------------------------------------------------------------------
    # Validation
    # -------------------------------------------------------------------------

    def add_validator(self, field: str, name: str, validator: Callable[[Any], None | str | list[str]]) -> None:
        """Add a named validator to a field."""
        if not hasattr(self, "_qtpie"):
            self._qtpie = QtPieState(self)
        self._qtpie.add_validator(field, name, validator)

    def remove_validator(self, field: str, name: str) -> None:
        """Remove a named validator from a field."""
        if not hasattr(self, "_qtpie"):
            self._qtpie = QtPieState(self)
        self._qtpie.remove_validator(field, name)

    @property
    def is_valid(self) -> Observable[bool]:
        """Check if all fields are valid. Returns Observable[bool] for reactive bindings."""
        if not hasattr(self, "_qtpie"):
            self._qtpie = QtPieState(self)
        return self._qtpie.widget_is_valid

    @property
    def validation_errors(self) -> dict[str, dict[str, list[str]]]:
        """Errors: {field: {validator: [errors]}}."""
        if not hasattr(self, "_qtpie"):
            return {}
        return self._qtpie.validation_errors

    @property
    def validation_error_messages(self) -> Observable[list[str]]:
        """Flat list of all error messages. Returns Observable[list[str]] for reactive bindings."""
        if not hasattr(self, "_qtpie"):
            self._qtpie = QtPieState(self)
        return self._qtpie.validation_error_messages

    # -------------------------------------------------------------------------
    # Signal Resolution
    # -------------------------------------------------------------------------

    def signal(self, name: str) -> Any:
        """Get a signal by name, searching up the parent hierarchy.

        First checks this menu, then walks up parent() chain, then QApplication.

        Args:
            name: The signal name (e.g., "on_reload_window")

        Returns:
            The signal if found

        Raises:
            AttributeError: If signal not found in hierarchy

        Example:
            self.signal("on_reload_window").emit()
        """
        from .utils.common import is_signal, resolve_signal_from_hierarchy

        # First check on self
        target = getattr(self, name, None)
        if target is not None and is_signal(target):
            return target

        # Search up hierarchy
        target = resolve_signal_from_hierarchy(self, name)
        if target is not None and is_signal(target):
            return target

        raise AttributeError(f"Signal '{name}' not found on {type(self).__name__} or in parent hierarchy")

    def emit_signal(self, name: str, *args: Any, **kwargs: Any) -> None:
        """Emit a signal by name, searching up the parent hierarchy.

        Convenience method that combines signal() lookup with emit().

        Args:
            name: The signal name (e.g., "on_reload_window")
            *args: Arguments to pass to signal.emit()
            **kwargs: Keyword arguments to pass to signal.emit()

        Raises:
            AttributeError: If signal not found in hierarchy

        Example:
            self.emit_signal("on_reload_window")
        """
        sig = self.signal(name)
        sig.emit(*args, **kwargs)

    def var(self, name: str) -> Any:
        """Resolve a variable by name from the binding context.

        Searches in this order:
        1. This menu (with and without underscore prefix)
        2. Parent widget hierarchy (walking up parent() chain)
        3. QApplication.instance() for app-level Variables

        Args:
            name: The variable name to resolve (e.g., "count" or "_count").

        Returns:
            The resolved value (unwrapped from Variable if applicable).

        Raises:
            AttributeError: If variable not found in context or parent hierarchy.

        Example:
            count = self.var("count")  # Gets current value of _count Variable
            item = self.var("selected_item")  # May resolve from parent widget
        """
        from qtpie.bindings.expression import resolve_var

        return resolve_var(self, name)

    # -------------------------------------------------------------------------
    # Dirty Tracking
    # -------------------------------------------------------------------------

    @property
    def is_dirty(self) -> Observable[bool]:
        """Check if any field has changed. Returns Observable[bool] for reactive bindings."""
        if not hasattr(self, "_qtpie"):
            self._qtpie = QtPieState(self)
        return self._qtpie.widget_is_dirty

    def reset_dirty(self) -> None:
        """Mark all fields as clean (Variables and record)."""
        if not hasattr(self, "_qtpie"):
            return
        self._qtpie.reset_dirty()
        if self._qtpie._record is not None:
            self._qtpie._record.reset_dirty()

    @property
    def dirty_fields(self) -> set[str]:
        """Return set of field names that have changed."""
        if not hasattr(self, "_qtpie"):
            return set()
        return self._qtpie.dirty_fields

    # -------------------------------------------------------------------------
    # Lifecycle Hooks
    # -------------------------------------------------------------------------

    def on_dirty_changed(self, is_dirty: bool) -> None:
        """Called when dirty state transitions (clean→dirty or dirty→clean)."""
        pass

    def on_valid_changed(self, is_valid: bool) -> None:
        """Called when validity state transitions (valid→invalid or invalid→valid)."""
        pass


def _collect_menu_fields(cls: type[Menu[Any]]) -> None:
    """Collect NewField instances and track item order."""
    config = cls._qtpie_config  # pyright: ignore[reportPrivateUsage]
    annotations = getattr(cls, "__annotations__", {})

    for name in annotations:
        # Track order for all items (actions, separators, sections)
        config.item_order.append(name)

        # Store NewField instances
        value = getattr(cls, name, None)
        if isinstance(value, NewField):
            config.fields[name] = value


def _detect_required_bindings_for_menu(cls: type[Menu[Any]]) -> None:
    """Detect bare Variable[T] annotations as required bindings."""
    detect_required_bindings(cls, "_qtpie_config", Variable, _RequiredBindingDescriptor)


# =============================================================================
# @menu Decorator
# =============================================================================


@overload
def menu[M: Menu[Any]](cls: type[M]) -> type[M]: ...


@overload
def menu[M: Menu[Any]](
    cls: None = None,
    *,
    text: str | None = None,
    name: str | None = None,
    classes: list[str] | None = None,
    record: Any | None = None,
    **props: Any,
) -> Callable[[type[M]], type[M]]: ...


def menu[M: Menu[Any]](
    cls: type[M] | None = None,
    *,
    text: str | None = None,
    name: str | None = None,
    classes: list[str] | None = None,
    record: Any | None = None,
    **props: Any,
) -> type[M] | Callable[[type[M]], type[M]]:
    """Decorator for declarative menus.

    Usage:
        @menu
        class FileMenu(Menu):
            ...

        @menu(text="&File")
        class FileMenu(Menu):
            ...

        @menu(text="&File", on_menu_action="_on_menu_action")
        class FileMenu(Menu):
            on_menu_action = Signal()
            def _on_menu_action(self): ...
    """

    def decorator(target_cls: type[M]) -> type[M]:
        from qtpie.utils.common import is_signal_on_type

        config = target_cls._qtpie_config  # pyright: ignore[reportPrivateUsage]

        # Extract signal connections from props
        # Signal connections are props where the key is a Signal name on the class
        signal_connections: dict[str, str] = {}
        widget_props: dict[str, Any] = {}
        for key, value in props.items():
            if is_signal_on_type(key, target_cls) and isinstance(value, str):
                signal_connections[key] = value
            else:
                widget_props[key] = value

        # Store decorator options
        config.text = text
        config.object_name = name
        if classes:
            config.css_classes = classes
        if record is not None:
            config.record_default = record
        config.signal_connections = signal_connections

        # Wrap __init__ to set up menu
        _wrap_init_for_menu(target_cls, widget_props)

        return target_cls

    if cls is not None:
        return decorator(cls)

    return decorator


def _wrap_init_for_menu(cls: type[Menu[Any]], props: dict[str, Any]) -> None:
    """Wrap __init__ to set up menu after construction."""
    config = cls._qtpie_config  # pyright: ignore[reportPrivateUsage]
    if config.init_wrapped:
        return

    original_init = cls.__init__

    def wrapped_init(self: Menu[Any], *args: Any, **kwargs: Any) -> None:
        from qtpy.QtGui import QAction

        from .bindings.apply import apply_auto_bindings, apply_property_bindings, apply_reactive_widget_props

        # Extract _qtpie_bindings before passing kwargs to original init
        _qtpie_bindings = kwargs.pop("_qtpie_bindings", None)

        nonlocal config

        # Apply parent variable bindings BEFORE original_init runs
        # This ensures required Variables exist before child widgets are created
        if _qtpie_bindings is not None:
            # Initialize QtPieState early so Variables have somewhere to register
            if not hasattr(self, "_qtpie"):
                self._qtpie = QtPieState(self)  # pyright: ignore[reportPrivateUsage]
            parent, bindings = _qtpie_bindings
            from .new_fields import _apply_variable_bindings_direct

            _apply_variable_bindings_direct(parent, self, bindings)

        # Call original __init__
        original_init(self, *args, **kwargs)

        # Initialize QtPie state (if not already done for bindings)
        if not hasattr(self, "_qtpie"):
            self._qtpie = QtPieState(self)  # pyright: ignore[reportPrivateUsage]

        # Set menu title
        menu_text = config.text
        if menu_text is None:
            # Derive from class name: FileMenu -> "File", EditMenu -> "Edit"
            class_name = cls.__name__
            if class_name.endswith("Menu"):
                menu_text = class_name[:-4]
            else:
                menu_text = class_name
        self.setTitle(menu_text)

        # Apply objectName and CSS classes
        from .utils.layouts import apply_object_name_and_classes, apply_widget_props

        apply_object_name_and_classes(
            self,
            config.object_name,
            config.css_classes,
            default_name=cls.__name__,
        )

        # Apply widget props from decorator
        apply_widget_props(self, props)

        # Add items (actions, separators, sections) in order
        for item_name in config.item_order:
            annotation = getattr(cls, "__annotations__", {}).get(item_name)

            # Check for Separator
            if annotation is Separator:
                self.addSeparator()
                continue

            # Check for Section
            if annotation is Section:
                section_text = _get_section_text(item_name, config.fields.get(item_name))
                self.addSection(section_text)
                continue

            # Check for list[QAction] - creates ActionRepeater
            if _is_action_list_type(annotation):
                field = config.fields.get(item_name)
                if field is not None:
                    repeater = _create_action_repeater(self, field, item_name, annotation)
                    if repeater is not None:
                        setattr(self, item_name, repeater)
                continue

            # Check for QAction
            item = getattr(self, item_name, None)
            if isinstance(item, QAction):
                self.addAction(item)
                field = config.fields.get(item_name)

                # Handle checked= binding for checkable actions
                if field:
                    checked_binding = field.property_bindings.get("checked") or field.kwargs.get("checked") or field.widget_props.get("checked")
                    if isinstance(checked_binding, str) and checked_binding.startswith("_"):
                        # Two-way binding to a Variable
                        _bind_action_checked(self, item, checked_binding)

                # Connect signals for this action
                if field and field.signal_connections:
                    from qtpie.signals import connect_item_signals

                    connect_item_signals(self, item, item_name, field.signal_connections, _create_menu_signal_expression_handler)

        # Set initial record if provided (record support will be added in C.8)
        if config.record_default is not None:
            if hasattr(self, "record"):
                self.record = config.record_default  # pyright: ignore[reportAttributeAccessIssue]

        # Call __setup__ hook (required bindings are now available)
        setup_method = getattr(self, "__setup__", None)
        if setup_method is not None:
            setup_method()

        # Apply bindings (after __setup__ so record is available)
        apply_auto_bindings(self, config)  # type: ignore[arg-type]
        apply_property_bindings(self, config)  # type: ignore[arg-type]
        apply_reactive_widget_props(self, config)  # type: ignore[arg-type]

        # Apply property bindings for QActions (not handled by apply_property_bindings)
        _apply_action_property_bindings(self, config)

        # Connect signals from decorator (e.g., @menu(on_menu_action="_on_menu_action"))
        _connect_decorator_signals(self, config)

        # Enable dirty/valid hooks
        state = self._qtpie  # pyright: ignore[reportPrivateUsage]
        state.enable_dirty_hook()
        state.enable_valid_hook()

    cls.__init__ = wrapped_init  # type: ignore[method-assign]
    config.init_wrapped = True


def _connect_decorator_signals(menu: Menu[Any], config: MenuConfig) -> None:
    """Connect signals defined in @menu decorator kwargs.

    Example:
        @menu(text="&File", on_menu_action="_on_menu_action")
        class FileMenu(Menu):
            on_menu_action = Signal()
            def _on_menu_action(self): ...

    Args:
        menu: The Menu instance
        config: The MenuConfig containing signal_connections
    """
    from .utils.common import is_signal

    for signal_name, handler_name in config.signal_connections.items():
        signal = getattr(menu, signal_name, None)
        if signal is None:
            continue

        if not is_signal(signal):
            continue

        handler = getattr(menu, handler_name, None)
        if handler is None:
            raise AttributeError(f"Handler '{handler_name}' not found on {type(menu).__name__} for signal '{signal_name}'")

        if callable(handler):
            signal.connect(handler)


def _get_section_text(name: str, field: NewField | None) -> str:
    """Get section text from field name or explicit new() value.

    Name format: ___text___ -> "Text"
    """
    # Check for explicit text in new()
    if field is not None:
        if field.args:
            return str(field.args[0])
        if "text" in field.kwargs:
            return str(field.kwargs["text"])

    # Extract from name: ___recent___ -> "Recent"
    stripped = name.strip("_")
    if stripped:
        # Convert snake_case to Title Case
        return stripped.replace("_", " ").title()

    return ""


def _bind_action_checked(menu: Menu[Any], action: Any, var_name: str) -> None:
    """Create two-way binding between action's checked state and a Variable.

    Args:
        menu: The menu containing the Variable
        action: The QAction to bind
        var_name: Name of the Variable (e.g., "_word_wrap")
    """
    from qtpy.QtGui import QAction

    if not isinstance(action, QAction):
        return

    # Get the Variable
    var = getattr(menu, var_name, None)
    if var is None or not isinstance(var, Variable):
        return

    # Set initial checked state from Variable
    action.setChecked(bool(var.value))

    # Variable -> Action: when Variable changes, update action
    def on_var_change(new_value: bool) -> None:
        if action.isChecked() != new_value:
            action.setChecked(new_value)

    var.observable.on_change(on_var_change)

    # Action -> Variable: when action toggled, update Variable
    def on_action_toggled(checked: bool) -> None:
        if var.value != checked:
            var.value = checked

    action.toggled.connect(on_action_toggled)


def _create_menu_signal_expression_handler(menu: Menu[Any], expression: str) -> Callable[[Any], Any]:
    """Create a signal handler from an expression string like "{my_signal(123)}"."""
    return create_signal_expression_handler(menu, expression, ["#menu", "#self"])


def _is_action_list_type(annotation: Any) -> bool:
    """Check if annotation is list[QAction]."""
    from qtpy.QtGui import QAction

    origin = get_origin(annotation)
    if origin is not list:
        return False

    type_args = get_args(annotation)
    if not type_args:
        return False

    return type_args[0] is QAction


def _create_action_repeater(
    menu: Menu[Any],
    field: NewField,
    item_name: str,
    annotation: Any,
) -> Any:
    """Create an ActionRepeater for a list[QAction] field.

    Args:
        menu: The menu instance
        field: The NewField containing bind=, format=, triggered=
        item_name: The field name
        annotation: The type annotation (list[QAction])

    Returns:
        ActionRepeater instance or None if no bind= specified
    """
    from observant import ObservableList

    from .action_repeater import ActionRepeater

    # Get bind= from field (should be a Variable name)
    bind_target = field.bind
    if bind_target is None:
        return None

    # Resolve the Variable
    var = getattr(menu, bind_target, None)
    if var is None:
        return None

    # Get the ObservableList from the Variable
    # For Variable[list[T]], the observable IS the ObservableList directly
    obs_list: ObservableList[Any] | None = None
    if hasattr(var, "observable"):
        obs = var.observable
        if isinstance(obs, ObservableList):
            obs_list = obs

    if obs_list is None:
        return None

    # Get format= from field
    format_expr = field.list_format or "{#self}"

    # Get triggered= handler from signal_connections
    triggered_handler = field.signal_connections.get("triggered")

    # Get item type from the Variable's inner type
    # For Variable[list[str]], we want to get str
    item_type: type | None = None
    if hasattr(var, "_inner_type"):
        inner = var._inner_type  # pyright: ignore[reportAttributeAccessIssue]
        # inner would be list[str] for Variable[list[str]]
        inner_origin = get_origin(inner)
        if inner_origin is list:
            inner_args = get_args(inner)
            if inner_args:
                item_type = inner_args[0]

    # Create the ActionRepeater
    repeater: ActionRepeater[Any] = ActionRepeater(
        menu=menu,
        observable_list=obs_list,
        item_type=item_type,
        format_expr=format_expr,
        triggered_handler=triggered_handler,
    )

    return repeater


def _create_menu_expression_binding(
    menu: Menu[Any],
    expression: str,
    setter: Callable[[Any], None],
) -> None:
    """Create a binding for an expression like "{record.can_undo}" or "{#parent._is_dirty}".

    Unlike format bindings which return strings, this returns the raw evaluated value.
    This is used for property bindings like enabled= that need boolean results.

    Special placeholders:
      - {#parent} - access the menu's parent (window or widget)
      - {#parent._is_dirty} - access parent's variable
    """
    from .bindings.format_binding import _BUILTINS, _extract_ast_names

    # Extract the expression from {expr}
    expr = expression.strip()
    if expr.startswith("{") and expr.endswith("}"):
        expr = expr[1:-1].strip()

    # Check for #parent usage
    uses_parent = "#parent" in expr

    # Extract variable names from the expression
    ast_names = _extract_ast_names(expr)
    var_names = ast_names - _BUILTINS

    # Collect all reactive objects to subscribe to
    observables: list[Observable[Any]] = []
    reactive_collections: list[ObservableList[Any] | ObservableDict[Any, Any] | ObservableProxy[Any]] = []

    def _resolve_menu_source(name: str) -> Observable[Any] | ObservableList[Any] | ObservableDict[Any, Any] | ObservableProxy[Any] | None:
        """Resolve a name to an Observable on the menu."""
        for attr_name in [name, f"_{name}"]:
            if hasattr(menu, attr_name):
                raw_attr: Any = getattr(menu, attr_name)
                if isinstance(raw_attr, Variable):
                    obs: Any = raw_attr.observable
                    if isinstance(obs, (Observable, ObservableList, ObservableDict, ObservableProxy)):
                        return obs  # type: ignore[return-value]
                elif isinstance(raw_attr, (Observable, ObservableList, ObservableDict, ObservableProxy)):
                    return raw_attr  # type: ignore[return-value]
        return None

    def _resolve_parent_source(path: str) -> Observable[Any] | ObservableList[Any] | ObservableDict[Any, Any] | ObservableProxy[Any] | None:
        """Resolve a path on the parent to an Observable."""
        # Get parent window (set by Window after adding to menubar)
        parent = getattr(menu, "_parent_window", None)
        if parent is None:
            return None
        for attr_name in [path, f"_{path}"]:
            if hasattr(parent, attr_name):
                raw_attr: Any = getattr(parent, attr_name)
                if isinstance(raw_attr, Variable):
                    obs: Any = raw_attr.observable
                    if isinstance(obs, (Observable, ObservableList, ObservableDict, ObservableProxy)):
                        return obs  # type: ignore[return-value]
                elif isinstance(raw_attr, (Observable, ObservableList, ObservableDict, ObservableProxy)):
                    return raw_attr  # type: ignore[return-value]
        return None

    for var_name in var_names:
        source = _resolve_menu_source(var_name)
        if source is not None:
            if isinstance(source, Observable):
                observables.append(cast(Observable[Any], source))
            elif isinstance(source, (ObservableList, ObservableDict, ObservableProxy)):
                reactive_collections.append(source)

    # Also check for nested paths like "record.can_undo"
    import re

    nested_patterns = re.findall(r"\b(\w+(?:\.\w+)+)(?:\s*\()?", expr)
    for path in nested_patterns:
        parts = path.split(".")
        obj: Any = menu
        for i, part in enumerate(parts):
            if not hasattr(obj, part):
                break

            # Special handling for RecordVariable - get the underlying proxy
            if isinstance(obj, RecordVariable):
                # Get the ObservableProxy from RecordVariable (use observable property for typing)
                proxy = obj.observable
                # Get the remaining path after "record"
                remaining_path = ".".join(parts[i:])
                nested_obs = proxy.observable_for_path(remaining_path)
                if isinstance(nested_obs, Observable):
                    if nested_obs not in observables:
                        observables.append(cast(Observable[Any], nested_obs))
                elif isinstance(nested_obs, (ObservableList, ObservableDict, ObservableProxy)):
                    if nested_obs not in reactive_collections:
                        reactive_collections.append(cast(ObservableList[Any] | ObservableDict[Any, Any] | ObservableProxy[Any], nested_obs))
                break

            obj = getattr(obj, part)
            if isinstance(obj, Observable):
                if obj not in observables:
                    observables.append(cast(Observable[Any], obj))
                break
            elif isinstance(obj, (ObservableList, ObservableDict, ObservableProxy)):
                if obj not in reactive_collections:
                    reactive_collections.append(cast(ObservableList[Any] | ObservableDict[Any, Any] | ObservableProxy[Any], obj))
                break

    # Handle #parent.path patterns
    if uses_parent:
        # Find patterns like #parent._is_dirty or #parent.some_var
        parent_patterns = re.findall(r"#parent\.(\w+)", expr)
        for parent_path in parent_patterns:
            source = _resolve_parent_source(parent_path)
            if source is not None:
                if isinstance(source, Observable):
                    if source not in observables:
                        observables.append(cast(Observable[Any], source))
                elif isinstance(source, (ObservableList, ObservableDict, ObservableProxy)):
                    if source not in reactive_collections:
                        reactive_collections.append(source)

    def compute() -> Any:
        # Build context with current values
        context: dict[str, Any] = {}

        # Add #parent support
        if uses_parent:
            # Get parent window (set by Window after adding to menubar)
            parent = getattr(menu, "_parent_window", None)
            if parent is None:
                # Parent not set yet - return False for boolean properties
                # This will be re-evaluated when parent variables change
                return False
            context["parent_ref"] = parent

        for var_name in var_names:
            for attr_name in [f"_{var_name}", var_name]:
                if hasattr(menu, attr_name):
                    raw_attr: Any = getattr(menu, attr_name)
                    if isinstance(raw_attr, Variable):
                        context[var_name] = raw_attr.value  # pyright: ignore[reportUnknownMemberType]
                    else:
                        context[var_name] = raw_attr
                    break

        # Replace #parent with parent_ref in expression
        eval_expr = expr.replace("#parent", "parent_ref")

        # Evaluate the expression
        try:
            value = eval(eval_expr, {"__builtins__": __builtins__}, context)  # noqa: S307
            # If the result is a Variable, unwrap it
            if isinstance(value, Variable):
                return value.value  # pyright: ignore[reportUnknownMemberType]
            return value
        except Exception:
            return False

    # Set initial value
    setter(compute())

    # Subscribe to ALL reactive objects
    def on_observable_change(_: Any) -> None:
        setter(compute())

    for obs in observables:
        obs.on_change(on_observable_change)

    def on_collection_change() -> None:
        setter(compute())

    for coll in reactive_collections:
        coll.on_change(on_collection_change)


def _apply_action_property_bindings(menu: Menu[Any], config: MenuConfig) -> None:
    """Apply property bindings like enabled="{record.can_undo}" to QActions.

    This handles QAction property bindings which aren't handled by the regular
    apply_property_bindings (which only handles QWidgets).

    Note: Uses _create_menu_expression_binding instead of the shared version
    because menus need special #parent placeholder support.
    """
    from qtpy.QtGui import QAction

    from .bindings import is_format_string

    for field_name, field_info in config.fields.items():
        if not field_info.property_bindings:
            continue

        action = getattr(menu, field_name, None)
        if action is None or not isinstance(action, QAction):
            continue

        for prop_name, bind_expr in field_info.property_bindings.items():
            # Skip checked - it's handled separately with two-way binding
            if prop_name == "checked":
                continue

            # Get the setter for this property
            setter_name = f"set{prop_name[0].upper()}{prop_name[1:]}"
            setter = getattr(action, setter_name, None)
            if setter is None or not callable(setter):
                continue

            def make_setter(s: Any, a: QAction) -> Callable[[Any], None]:
                def setter_fn(val: Any) -> None:
                    s(val)

                return setter_fn

            prop_setter = make_setter(setter, action)

            if is_format_string(bind_expr):
                # Expression binding like {record.can_undo} - uses menu-specific version for #parent support
                _create_menu_expression_binding(menu, bind_expr, prop_setter)
            else:
                # Simple variable reference
                var = getattr(menu, bind_expr, None)
                if var is not None and hasattr(var, "observable"):
                    # Set initial value
                    prop_setter(var.value)
                    # Subscribe to changes
                    var.observable.on_change(lambda new_val, s=prop_setter: s(new_val))
