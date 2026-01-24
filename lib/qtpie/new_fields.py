"""new_fields - Decorator that processes new() fields."""

import logging
from typing import Any, get_origin

from .new_field import NewField
from .utils.type_checks import is_model_widget
from .variable import AnyObservable, RecordVariable, Variable

logger = logging.getLogger("qtpie.new_fields")

# Default property mapping for common widget types
# Used to determine which property to set for positional Translatable args
_DEFAULT_TEXT_PROPS: dict[str, str] = {
    "QLabel": "text",
    "QPushButton": "text",
    "QCheckBox": "text",
    "QRadioButton": "text",
    "QToolButton": "text",
    "QGroupBox": "title",
    "QMenu": "title",
    "QLineEdit": "text",
    "QAction": "text",
    "QAbstractButton": "text",
}


def _get_default_prop(widget: Any) -> str | None:
    """Get the default text property name for a widget type."""
    for cls_name, prop in _DEFAULT_TEXT_PROPS.items():
        # Check if the widget's class name or parent class matches
        for cls in type(widget).__mro__:
            if cls.__name__ == cls_name:
                return prop
    return None


def _setup_app_inheritance_properties(app: Any, cls: type[Any]) -> None:
    """Set icon and title on QApplication so child widgets can inherit them.

    Called right after QApplication.__init__ but before child widgets are created.
    """
    from qtpy.QtWidgets import QApplication

    if not isinstance(app, QApplication):
        return

    config = getattr(cls, "_qtpie_config", None)
    if config is None:
        return

    # Set icon on QApplication for inheritance
    from .utils.layouts import resolve_icon

    window_icon = getattr(config, "window_icon", None)
    icon = getattr(config, "icon", None)
    resolved_icon = resolve_icon(window_icon) or resolve_icon(icon)
    if resolved_icon:
        app.setWindowIcon(resolved_icon)

    # Set title as property for inheritance (QApplication doesn't have windowTitle)
    widget_props = getattr(config, "widget_props", {})
    window_title = widget_props.get("windowTitle")
    if window_title:
        app.setProperty("qtpie_window_title", window_title)


def new_fields[T](cls: type[T]) -> type[T]:
    """Decorator that processes NewField instances for non-Variable types.

    Variable[T] fields are handled automatically by NewField.__set_name__,
    which replaces the NewField with a Variable descriptor.

    This decorator handles non-Variable types by instantiating them in __init__.
    """
    # Check if already processed - use __dict__ to check THIS class only, not inherited
    # This is important because subclasses need their own NewField processing even if
    # parent class was already processed
    if cls.__dict__.get("__new_fields_processed__", False):
        return cls

    # Find all remaining NewField instances (non-Variable types)
    fields: dict[str, NewField] = {}
    for name, value in list(cls.__dict__.items()):
        if isinstance(value, NewField):
            fields[name] = value

    # If no NewField instances remain, nothing to do
    if not fields:
        cls.__new_fields_processed__ = True  # type: ignore[attr-defined]
        return cls

    # Wrap __init__ to instantiate non-Variable fields
    original_init = cls.__init__ if hasattr(cls, "__init__") else None

    # Check if this class is a QApplication subclass - needs to init QApp BEFORE widgets
    from qtpy.QtWidgets import QApplication

    is_qapp_subclass = issubclass(cls, QApplication)

    def new_init(self: Any, *args: Any, **kwargs: Any) -> None:
        from qtpie.translations.translatable import Translatable

        # For QApplication subclasses, MUST initialize QApplication BEFORE creating widgets
        # because Qt requires QApplication to exist before any QWidget can be created
        if is_qapp_subclass and original_init is not None:
            original_init(self, *args, **kwargs)

            # Set QApplication icon/title EARLY so child widgets can inherit them
            # (must happen AFTER original_init but BEFORE creating child widgets)
            _setup_app_inheritance_properties(self, cls)

        # Initialize record_default BEFORE processing child fields
        # This ensures child widgets can bind to parent.record
        config = getattr(cls, "_qtpie_config", None)
        if config is not None:
            record_default = getattr(config, "record_default", None)
            if record_default is not None and hasattr(self, "record"):
                self.record = record_default  # pyright: ignore[reportAttributeAccessIssue]

        # Track refs to resolve after all fields are created
        # Format: (field_name, instance, ref_kwarg_name, Ref)
        pending_refs: list[tuple[str, Any, str, Any]] = []

        # Instantiate non-Variable fields (skip list widgets - handled in widget.py)
        for fname, field in fields.items():
            origin = get_origin(field.field_type)
            if origin is not Variable and field.field_type is not Variable:
                # Skip list[QWidget] fields - they're created as WidgetRepeaters in widget.py
                if field.is_list_widget:
                    continue
                # Skip list[QAction] fields - they're created as ActionRepeaters in @menu
                if _is_action_list_type(field.field_type):
                    continue
                # Skip menu marker types (Separator, Section) - handled by @menu
                if _is_menu_marker_type(field.field_type):
                    continue
                # Skip Dock[T] fields - they're created by _create_dock_fields in window.py
                if field.is_dock:
                    continue
                # Skip layout items (Stretch, QSpacerItem, QLayout) - handled in _wrap_init_for_layout
                if field.is_stretch or field.is_spacer_item or field.is_nested_layout:
                    continue
                if field.field_type is not None:
                    # Resolve Translatable markers in args before construction
                    resolved_args = list(field.args)
                    for idx, translatable in field.translatable_args:
                        if idx < len(resolved_args):
                            resolved_args[idx] = translatable.resolve()

                    # Resolve Translatable markers in kwargs before construction
                    resolved_kwargs = dict(field.kwargs)
                    for key, translatable in field.translatable_kwargs.items():
                        if key in resolved_kwargs and isinstance(resolved_kwargs[key], Translatable):
                            resolved_kwargs[key] = translatable.resolve()

                    # Pass variable bindings via special kwarg so child can apply them
                    # BEFORE __setup__ runs (for deterministic timing)
                    # Build bindings dict, including bind -> record for Widget[T] children
                    bindings_dict = dict(field.variable_bindings)

                    # If this is a Widget[T] child with bind="xxx", convert to record="xxx"
                    # This handles both explicit bind="xxx" and auto-record-bind (bind="record")
                    if field.bind is not None and field.bind is not False:
                        child_config = getattr(field.field_type, "_qtpie_config", None)
                        if child_config is not None:
                            child_record_type = getattr(child_config, "record_type", None)
                            if child_record_type is not None and "record" not in bindings_dict:
                                bindings_dict["record"] = field.bind

                    # Pass parent reference to QtPie classes so they can find parent Variables
                    # during binding setup (only if field type has _qtpie_config - Widget, Window, Menu, Dialog, App)
                    if hasattr(field.field_type, "_qtpie_config"):
                        resolved_kwargs["_qtpie_bindings"] = (self, bindings_dict)

                    instance = field.field_type(*resolved_args, **resolved_kwargs)

                    # Resolve any #parent refs on the child now that we know the parent
                    _resolve_parent_refs(self, instance)

                    # Resolve any deferred bindings on the child (its grandchildren may have
                    # been waiting for the child's Variable bindings to be applied)
                    _resolve_deferred_bindings(instance)

                    # Apply pending auto-bindings on the child (deferred because required
                    # Variables weren't set up during child's __init__)
                    _apply_pending_bindings(instance)

                    # Apply objectName with priority: new(name=) > @widget(name=) > widget class name
                    from qtpy.QtWidgets import QWidget

                    if isinstance(instance, QWidget):
                        if field.object_name is not None:
                            # Explicit name= on new() takes top priority
                            # Check for reactive binding in object name
                            if "{" in field.object_name and "}" in field.object_name:
                                # Defer reactive object name application until after __init__ completes
                                _defer_reactive_object_name(self, instance, field.object_name)
                            else:
                                instance.setObjectName(field.object_name)
                        elif config is not None and config.object_name is not None:
                            # @widget(name=...) on parent class is next priority
                            instance.setObjectName(config.object_name)
                        else:
                            # Default to widget class name (e.g., "QPushButton", "QLabel")
                            instance.setObjectName(type(instance).__name__)

                        # Always set field property to attribute name (stripped)
                        from .styles import set_field_property

                        field_name = fname[1:] if fname.startswith("_") else fname
                        set_field_property(instance, field_name, refresh=False)

                        # Apply CSS classes if specified
                        if field.css_classes:
                            from .bindings.format_binding import is_format_string
                            from .styles import set_classes

                            # Check if any class has a reactive binding
                            has_reactive = any(is_format_string(c) for c in field.css_classes)
                            if has_reactive:
                                # Defer reactive class application until after __init__ completes
                                # to ensure widget base class is fully initialized
                                _defer_reactive_classes(self, instance, field.css_classes)
                            else:
                                set_classes(instance, field.css_classes)

                        # Apply initial size (width=/height=) via resize()
                        # Float values (0.0-1.0) are interpreted as percentage of window size.
                        if field.initial_width is not None or field.initial_height is not None:
                            init_w = field.initial_width
                            init_h = field.initial_height

                            # Check if we need to resolve fractional values
                            needs_window = (isinstance(init_w, float) and 0.0 < init_w < 1.0) or (isinstance(init_h, float) and 0.0 < init_h < 1.0)

                            if needs_window:
                                # Defer until window is available for fractional sizing
                                from qtpy.QtCore import QTimer

                                def apply_size(
                                    w: int | float | None = init_w,
                                    h: int | float | None = init_h,
                                    widget: QWidget = instance,
                                ) -> None:
                                    win = widget.window()
                                    if isinstance(w, float) and 0.0 < w < 1.0:
                                        w = int(win.width() * w)
                                    if isinstance(h, float) and 0.0 < h < 1.0:
                                        h = int(win.height() * h)
                                    final_w = int(w) if w is not None else widget.width()
                                    final_h = int(h) if h is not None else widget.height()
                                    widget.resize(final_w, final_h)

                                QTimer.singleShot(0, apply_size)
                            else:
                                # Absolute pixel values - apply immediately
                                w = int(init_w) if init_w is not None else instance.width()
                                h = int(init_h) if init_h is not None else instance.height()
                                instance.resize(w, h)

                        # Apply input validator (QLineEdit, QComboBox, etc.)
                        if field.validator is not None:
                            if hasattr(instance, "setValidator"):
                                from .input_validator import apply_validator

                                apply_validator(instance, field.validator)

                    # Apply widget props (windowTitle="X" → setWindowTitle("X")
                    # Also resolve Translatable markers in widget_props
                    for prop_name, value in field.widget_props.items():
                        # Resolve if it's a Translatable
                        if isinstance(value, Translatable):
                            value = value.resolve()

                        # Special handling for icon= - convert str/QPixmap/StandardPixmap to QIcon
                        if prop_name == "icon":
                            from .utils.layouts import resolve_icon

                            resolved_icon = resolve_icon(value)
                            if resolved_icon is not None and hasattr(instance, "setIcon"):
                                instance.setIcon(resolved_icon)  # pyright: ignore[reportUnknownMemberType, reportAttributeAccessIssue]
                            continue

                        setter_name = f"set{prop_name[0].upper()}{prop_name[1:]}"
                        setter = getattr(instance, setter_name, None)
                        if setter is not None and callable(setter):
                            setter(value)
                        # Special case: tooltip on QAction also sets statusTip
                        if prop_name == "toolTip":
                            from qtpy.QtGui import QAction

                            if isinstance(instance, QAction):
                                instance.setStatusTip(value)

                    # Register translation bindings for hot-reload
                    from qtpie.translations.store import register_binding

                    # Register bindings for positional args
                    for _idx, translatable in field.translatable_args:
                        default_prop = _get_default_prop(instance)
                        if default_prop:
                            register_binding(
                                instance,
                                default_prop,
                                translatable.text,
                                translatable.context,
                            )

                    # Register bindings for kwargs and widget_props
                    for prop_name, translatable in field.translatable_kwargs.items():
                        register_binding(
                            instance,
                            prop_name,
                            translatable.text,
                            translatable.context,
                        )

                    # Collect refs for deferred resolution
                    if field.ref_bindings:
                        for ref_kwarg, ref_obj in field.ref_bindings.items():
                            pending_refs.append((fname, instance, ref_kwarg, ref_obj))

                    # Defer bind= for plain QWidgets that use registry-based binding
                    # (e.g., QSplitter with bind="orientation")
                    # Skip: QtPie widgets, format strings, and model widgets (QComboBox, etc.)
                    if (
                        field.bind is not None
                        and field.bind is not False
                        and not hasattr(field.field_type, "_qtpie_config")
                        and isinstance(field.bind, str)
                        and "{" not in field.bind  # Not a format string
                        and not is_model_widget(field.field_type)  # Not QComboBox/QListView/etc.
                    ):
                        _defer_plain_widget_bind(self, instance, field.bind)

                    setattr(self, fname, instance)

        # Resolve refs now that all fields exist
        _resolve_refs(self, pending_refs)

        # Call original __init__ (skip for QApplication subclasses - already called above)
        if not is_qapp_subclass and original_init is not None:
            original_init(self, *args, **kwargs)

    cls.__init__ = new_init  # type: ignore[method-assign]
    cls.__new_fields_processed__ = True  # type: ignore[attr-defined]

    return cls


def _defer_plain_widget_bind(context: Any, widget: Any, bind_expr: str) -> None:
    """Defer bind= application for plain QWidgets until after __init__ completes.

    This is needed because resolve_binding_source walks the parent hierarchy,
    which requires the widget's base class __init__ to have completed.
    """
    from qtpy.QtCore import QTimer

    def apply_later() -> None:
        _apply_plain_widget_bind(context, widget, bind_expr)

    QTimer.singleShot(0, apply_later)


def _apply_plain_widget_bind(context: Any, widget: Any, bind_expr: str) -> None:
    """Apply bind= for plain QWidgets (non-QtPie widgets like QSplitter).

    Uses the binding registry to find the default property for the widget type
    and sets up a one-way binding from the parent's Variable.
    """
    from observant import Observable

    from .bindings.path import resolve_binding_source
    from .bindings.registry import get_binding_registry
    from .variable import Variable

    # Get the registry and find the default property for this widget type
    registry = get_binding_registry()
    property_name = registry.get_default_prop(widget)

    # Get the adapter for this widget/property
    adapter = registry.get(widget, property_name)
    if adapter is None or adapter.setter is None:
        return

    setter = adapter.setter

    # Resolve the source Variable/Observable
    source = resolve_binding_source(context, bind_expr)  # type: ignore[arg-type]
    if source is None:
        return

    if isinstance(source, Variable):
        setter(widget, source.value)  # pyright: ignore[reportUnknownMemberType]
        source.on_change(lambda v: setter(widget, v))  # pyright: ignore[reportUnknownLambdaType]
    elif isinstance(source, Observable):
        setter(widget, source.get())
        source.on_change(lambda v: setter(widget, v))  # pyright: ignore[reportUnknownLambdaType]


def _apply_variable_bindings_direct(parent: Any, child: Any, bindings: dict[str, Any]) -> None:  # pyright: ignore[reportUnusedFunction] - imported dynamically in widget/window/menu __init__
    """Wire up variable bindings between parent and child widgets.

    For each binding in bindings dict:
    - Direct variable reference (e.g., count="_my_count") -> share Observable (two-way)
    - Expression binding (e.g., enabled="{len(_items) > 0}") -> computed (one-way)
    - Literal value (e.g., label_text="Hello") -> set as default value

    Args:
        parent: The parent widget instance
        child: The child widget instance
        bindings: Dict mapping child variable names to binding values
    """
    for child_var_name, binding_value in bindings.items():
        # Determine binding type
        if isinstance(binding_value, str):
            if "{" in binding_value and "}" in binding_value:
                # Expression binding - computed one-way (A.6)
                _apply_expression_binding(parent, child, child_var_name, binding_value)
            elif _is_variable_reference(parent, binding_value):
                # Direct variable reference - two-way binding
                _apply_direct_binding(parent, child, child_var_name, binding_value)
            else:
                # Literal string value (A.7)
                _apply_literal_binding(child, child_var_name, binding_value)
        else:
            # Literal non-string value (int, bool, etc.) (A.7)
            _apply_literal_binding(child, child_var_name, binding_value)


def _is_variable_reference(parent: Any, value: str) -> bool:
    """Check if value is a reference to a Variable or RecordVariable on parent.

    Returns True if value is a simple identifier that matches a Variable/RecordVariable on parent,
    or if it's a required binding on the parent class (may not be populated yet),
    or if it's a path through the parent's record (for Widget[T] parents).
    """
    # Must be a valid Python identifier (or dot-separated path like "auth.type")
    parts = value.replace("?.", ".").split(".")
    if not all(p.isidentifier() for p in parts):
        return False

    # Check if parent has this as a Variable or RecordVariable (already populated)
    parent_attr = getattr(parent, value, None)
    if isinstance(parent_attr, (Variable, RecordVariable)):
        return True

    # Check if parent class has this as a required binding (may not be populated yet)
    parent_class = type(parent)  # pyright: ignore[reportUnknownVariableType]
    config = getattr(parent_class, "_qtpie_config", None)  # pyright: ignore[reportUnknownArgumentType]
    if config is not None:
        required: set[str] = getattr(config, "required_bindings", set())
        if value in required:
            return True

        # Check if this is a path through the parent's record (for Widget[T])
        record_type = getattr(config, "record_type", None)
        if record_type is not None:
            # The parent is a Widget[T], check if value is a field on its record
            first_part = parts[0]
            if hasattr(record_type, "__annotations__"):
                annotations = record_type.__annotations__
                if first_part in annotations:
                    return True

    return False


def _apply_direct_binding(parent: Any, child: Any, child_var_name: str, parent_var_name: str) -> None:
    """Create two-way binding between parent Variable/RecordVariable and child.

    The child's Variable will share the parent's Observable, so changes
    to either side are reflected on both.

    If the parent's Variable doesn't exist yet (it's a required binding that
    will be populated later), we store a deferred binding to be resolved after
    the parent's bindings are applied.

    Also handles paths through the parent's record (for Widget[T] parents),
    e.g., binding "auth" to a child when parent.record.auth exists.
    """
    from observant import Observable, ObservableProxy

    logger.debug(
        "_apply_direct_binding: parent=%s, child=%s, child_var_name=%r, parent_var_name=%r",
        type(parent).__name__,
        type(child).__name__,
        child_var_name,
        parent_var_name,
    )

    # Try to get the parent's Variable/RecordVariable
    parent_var: Variable[Any] | RecordVariable[Any] | Observable[Any] | None = None
    try:
        parent_var = getattr(parent, parent_var_name)
    except AttributeError:
        pass

    logger.debug("  parent_var = %s (type=%s)", parent_var, type(parent_var).__name__ if parent_var else None)

    if parent_var is not None:
        # Check for RecordVariable first (specialized type for records)
        if isinstance(parent_var, RecordVariable):
            # Share the ObservableProxy - create a RecordVariable for the child
            logger.debug("  -> parent_var is RecordVariable, sharing proxy")
            child_record_var: RecordVariable[Any] = RecordVariable(parent_var.observable)  # pyright: ignore[reportUnknownMemberType, reportUnknownArgumentType]
            setattr(child, child_var_name, child_record_var)
            return

        if isinstance(parent_var, (Variable, Observable)):  # pyright: ignore[reportUnnecessaryIsInstance]
            # Parent has the Variable - share its Observable
            logger.debug("  -> parent_var is Variable/Observable, sharing observable")
            parent_observable: AnyObservable[Any]
            if isinstance(parent_var, Variable):
                parent_observable = parent_var.observable
            else:
                parent_observable = parent_var

            # Create a Variable for the child that shares the parent's Observable
            child_var: Variable[Any] = Variable(parent_observable)
            setattr(child, child_var_name, child_var)
            return

    # Check if this is a required binding that will be populated later
    parent_class = type(parent)  # pyright: ignore[reportUnknownVariableType]
    config = getattr(parent_class, "_qtpie_config", None)  # pyright: ignore[reportUnknownArgumentType]
    if config is not None:
        required: set[str] = getattr(config, "required_bindings", set())
        if parent_var_name in required:
            # Store deferred binding to be resolved later
            logger.debug("  -> required binding not yet populated, deferring")
            _store_deferred_binding(parent, child, child_var_name, parent_var_name)
            return

        # Check if this is a path through the parent's record (for Widget[T])
        record_type = getattr(config, "record_type", None)
        if record_type is not None:
            logger.debug("  -> parent is Widget[%s], checking record path", record_type.__name__ if hasattr(record_type, "__name__") else record_type)
            # Parent is a Widget[T], try to resolve path through its record
            parts = parent_var_name.replace("?.", ".").split(".")
            first_part = parts[0]
            if hasattr(record_type, "__annotations__"):
                annotations = record_type.__annotations__
                if first_part in annotations:
                    logger.debug("  -> %r is a field on record_type", first_part)
                    # This is a record field path - get the ObservableProxy for it
                    try:
                        record = parent.record
                        proxy = record.observable
                        logger.debug("  -> parent.record.observable = %s (id=%d)", proxy, id(proxy))
                        # Get the observable for this path
                        field_proxy = proxy.observable_for_path(parent_var_name)
                        logger.debug("  -> field_proxy = %s (type=%s)", field_proxy, type(field_proxy).__name__)
                        if isinstance(field_proxy, ObservableProxy):
                            # Share the ObservableProxy with the child's record
                            logger.debug("  -> field_proxy is ObservableProxy, creating RecordVariable for child")
                            child_record_var = RecordVariable(field_proxy)  # pyright: ignore[reportUnknownArgumentType]
                            setattr(child, child_var_name, child_record_var)
                            logger.debug("  -> setattr(child, %r, child_record_var) done", child_var_name)

                            # Register child for field binding updates when parent's record changes.
                            # This is needed because when a new record is set on the parent,
                            # replace_target is called on the parent's proxy, but the child
                            # needs its nested field proxy updated too.
                            field_children: list[tuple[Any, str, str]]
                            if not hasattr(parent, "_qtpie_field_bound_children"):
                                field_children = []
                                parent._qtpie_field_bound_children = field_children  # pyright: ignore[reportAttributeAccessIssue]
                            else:
                                field_children = parent._qtpie_field_bound_children  # pyright: ignore[reportAttributeAccessIssue]
                            field_children.append((child, child_var_name, parent_var_name))
                            logger.debug("  -> registered child for field binding updates")
                            return
                        # Field observable exists but value is None (e.g., auth: Auth | None = None)
                        # Defer the binding - it will be resolved when the parent's record is set
                        logger.debug("  -> field_proxy is not ObservableProxy, deferring")
                        _store_deferred_binding(parent, child, child_var_name, parent_var_name)
                        return
                    except (AttributeError, ValueError) as e:
                        # Record not set up yet or path invalid - defer
                        logger.debug("  -> exception accessing record: %s", e)
                        _store_deferred_binding(parent, child, child_var_name, parent_var_name)
                        return

    # Not found and not a required binding
    raise AttributeError(f"Cannot bind '{child_var_name}' to '{parent_var_name}': '{parent_var_name}' not found on {type(parent).__name__}")


def _store_deferred_binding(parent: Any, child: Any, child_var_name: str, parent_var_name: str) -> None:
    """Store a deferred binding to be resolved after parent's bindings are applied."""
    deferred_list: list[tuple[Any, str, str]]
    if not hasattr(parent, "_qtpie_deferred_bindings"):
        deferred_list = []
        parent._qtpie_deferred_bindings = deferred_list
    else:
        deferred_list = parent._qtpie_deferred_bindings
    deferred_list.append((child, child_var_name, parent_var_name))


def _apply_pending_bindings(instance: Any) -> None:
    """Apply pending auto-bindings on the instance.

    If the instance has `_qtpie_pending_auto_bindings = True`, it means the child widget
    deferred its binding application because required Variables weren't set up during init.
    Now that the parent has applied variable bindings, we can apply those bindings.

    This function can be called multiple times safely - it checks whether required
    bindings are actually satisfied before applying.
    """
    if not getattr(instance, "_qtpie_pending_auto_bindings", False):
        return

    # Get the child's config
    instance_type = type(instance)  # pyright: ignore[reportUnknownVariableType]
    child_config = getattr(instance_type, "_qtpie_config", None)  # pyright: ignore[reportUnknownArgumentType]
    if child_config is None:
        return

    # Check if all required bindings are now satisfied
    required: set[str] = getattr(child_config, "required_bindings", set())
    for name in required:
        if not hasattr(instance, name):
            # Still missing required bindings - keep the flag and return
            return

    # Import the binding functions from shared module
    from .bindings.apply import apply_auto_bindings, apply_property_bindings, apply_reactive_widget_props
    from .bindings.expression import create_expression_binding

    # Apply the deferred bindings
    apply_auto_bindings(instance, child_config)
    apply_property_bindings(instance, child_config, create_expression_binding_fn=create_expression_binding)
    apply_reactive_widget_props(instance, child_config)

    # Resolve deferred refs now that required bindings are set
    _resolve_deferred_refs(instance)

    # Clear the flag - all bindings applied successfully
    del instance._qtpie_pending_auto_bindings


def _resolve_deferred_bindings(widget: Any) -> None:
    """Resolve any deferred bindings on the widget.

    Called after a widget's own Variable bindings are applied, so its children
    can now access the newly-bound Variables.

    If a parent variable still doesn't exist (because the parent itself has
    unresolved required bindings), those bindings are kept deferred for later
    resolution when the parent's binding is eventually resolved.

    Also handles record paths (e.g., "auth" -> widget.record.auth) for Widget[T].
    """
    from observant import Observable, ObservableProxy

    logger.debug("_resolve_deferred_bindings: widget=%s", type(widget).__name__)

    deferred: list[tuple[Any, str, str]] | None = getattr(widget, "_qtpie_deferred_bindings", None)
    if not deferred:
        # Still need to check expression bindings even if no regular deferred bindings
        logger.debug("  -> no _qtpie_deferred_bindings")
        _resolve_deferred_expression_bindings(widget)
        return
    logger.debug("  -> found %d deferred bindings", len(deferred))

    # Track which bindings couldn't be resolved yet
    still_deferred: list[tuple[Any, str, str]] = []

    for child, child_var_name, parent_var_name in deferred:
        # Check if the parent's Variable exists now
        parent_var = getattr(widget, parent_var_name, None)

        # If not found directly, try record path (for Widget[T])
        if parent_var is None:
            config = getattr(type(widget), "_qtpie_config", None)  # pyright: ignore[reportUnknownArgumentType]
            if config is not None:
                record_type = getattr(config, "record_type", None)
                if record_type is not None:
                    # Check if this is a record field path
                    parts = parent_var_name.replace("?.", ".").split(".")
                    first_part = parts[0]
                    if hasattr(record_type, "__annotations__"):
                        annotations = record_type.__annotations__
                        if first_part in annotations:
                            # Try to resolve through record
                            try:
                                record = widget.record
                                proxy = record.observable
                                field_proxy = proxy.observable_for_path(parent_var_name)
                                if isinstance(field_proxy, ObservableProxy):
                                    # For record binding to child Widget[T], share the proxy
                                    child_record_var: RecordVariable[Any] = RecordVariable(field_proxy)  # pyright: ignore[reportUnknownArgumentType]
                                    setattr(child, child_var_name, child_record_var)

                                    # Register child for field binding updates when parent's
                                    # record changes (e.g., user clicks different request)
                                    field_bound_children: list[tuple[Any, str, str]]
                                    if not hasattr(widget, "_qtpie_field_bound_children"):
                                        field_bound_children = []
                                        widget._qtpie_field_bound_children = field_bound_children  # pyright: ignore[reportAttributeAccessIssue]
                                    else:
                                        field_bound_children = widget._qtpie_field_bound_children  # pyright: ignore[reportAttributeAccessIssue]
                                    field_bound_children.append((child, child_var_name, parent_var_name))
                                    logger.debug("  -> registered child for field binding updates (deferred)")

                                    # Re-apply auto-bindings on child now that its record is set
                                    # This is needed because format bindings were set up with no record
                                    child_config = getattr(type(child), "_qtpie_config", None)  # pyright: ignore[reportUnknownArgumentType]
                                    if child_config is not None:
                                        from .bindings.apply import apply_auto_bindings
                                        from .bindings.expression import create_expression_binding

                                        apply_auto_bindings(child, child_config, create_expression_binding_fn=create_expression_binding)

                                    # Recursively resolve any deferred bindings on the child
                                    _resolve_deferred_bindings(child)
                                    _apply_pending_bindings(child)
                                    continue
                            except (AttributeError, ValueError):
                                pass  # Fall through to still_deferred

        if parent_var is None:
            # Parent variable still doesn't exist (parent has unresolved required binding)
            # Keep this binding deferred for later resolution
            still_deferred.append((child, child_var_name, parent_var_name))
            continue

        parent_observable: AnyObservable[Any]
        if isinstance(parent_var, Variable):
            parent_observable = parent_var.observable  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]
        elif isinstance(parent_var, Observable):
            parent_observable = parent_var  # pyright: ignore[reportUnknownVariableType]
        else:
            raise TypeError(f"Deferred binding failed: expected Variable or Observable, got {type(parent_var).__name__}")

        # Check if the child already has a Variable (e.g., optional with default)
        existing_var = getattr(child, child_var_name, None)
        if existing_var is not None and isinstance(existing_var, Variable):
            # Child has an existing Variable (optional with default)
            # We need to sync it with the parent's Observable, NOT replace it
            # because format bindings are already subscribed to the existing Observable
            child_obs: AnyObservable[Any] = existing_var.observable  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]

            # Initial sync: set child's Observable to parent's value
            if isinstance(child_obs, Observable) and isinstance(parent_observable, Observable):
                child_obs.set(parent_observable.get())

                # Two-way binding: parent <-> child Observables
                # When parent changes, update child
                def on_parent_change(v: Any, child_obs: Observable[Any] = child_obs) -> None:
                    child_obs.set(v)

                parent_observable.on_change(on_parent_change)

                # When child changes, update parent
                def on_child_change(v: Any, parent_obs: Observable[Any] = parent_observable) -> None:
                    parent_obs.set(v)

                child_obs.on_change(on_child_change)
            else:
                # For non-Observable wrappers (ObservableList, etc.), just replace
                object.__setattr__(existing_var, "_wrapper", parent_observable)  # pyright: ignore[reportUnknownArgumentType]
        else:
            # Create new Variable sharing the parent's Observable
            child_var: Variable[Any] = Variable(parent_observable)
            setattr(child, child_var_name, child_var)

        # Recursively resolve any deferred bindings on the child
        _resolve_deferred_bindings(child)

        # Re-apply pending bindings on the child now that its Variable is set
        # This is needed because _apply_pending_bindings may have run earlier
        # when the child's required Variables weren't yet populated
        _apply_pending_bindings(child)

    # Update the deferred list - keep only those that couldn't be resolved
    if still_deferred:
        widget._qtpie_deferred_bindings = still_deferred
    else:
        if hasattr(widget, "_qtpie_deferred_bindings"):
            del widget._qtpie_deferred_bindings

    # Also resolve any deferred expression bindings
    _resolve_deferred_expression_bindings(widget)


def _resolve_deferred_expression_bindings(widget: Any) -> None:
    """Resolve any deferred expression bindings on the widget.

    Expression bindings can be deferred if they reference required variables
    that don't exist yet. This function is called after direct bindings are
    resolved, so the required variables should now be available.
    """
    deferred: list[tuple[Any, str, str]] | None = getattr(widget, "_qtpie_deferred_expression_bindings", None)
    if not deferred:
        return

    # Clear the list before attempting resolution
    # _apply_expression_binding may add back to it if still deferred
    del widget._qtpie_deferred_expression_bindings

    for child, child_var_name, expression in deferred:
        # Try to apply the expression binding
        # _apply_expression_binding will check if variables exist and may re-defer
        _apply_expression_binding(widget, child, child_var_name, expression)

        # After creating the child's Variable, apply any pending bindings on the child
        # (the child may have deferred its format bindings waiting for this Variable)
        _apply_pending_bindings(child)


def _apply_expression_binding(parent: Any, child: Any, child_var_name: str, expression: str) -> None:
    """Create one-way computed binding from expression to child Variable.

    The expression is evaluated with parent's context, and the result
    is set on the child's Variable. Updates when any referenced Variable changes.

    Special case: If the expression is a simple reference to a Variable or RecordVariable
    (like "{record}" or "{_my_var}"), we share the underlying Observable for two-way binding.

    If the expression references variables that don't exist yet (required bindings
    on the parent that haven't been populated), this binding is deferred.
    """
    from observant import Observable, ObservableDict, ObservableList, ObservableProxy, ObservableSet

    # Extract the expression from {expr}
    expr = expression.strip()
    if expr.startswith("{") and expr.endswith("}"):
        expr = expr[1:-1].strip()

    # Special case: simple variable reference like "{record}" or "{_my_var}"
    # In this case, share the Observable directly for two-way binding
    if expr.isidentifier():
        parent_attr = getattr(parent, expr, None)
        if parent_attr is None:
            # Try with underscore prefix
            parent_attr = getattr(parent, f"_{expr}", None)

        if parent_attr is not None:
            # Check if it's a Variable or RecordVariable - share the Observable
            if isinstance(parent_attr, Variable):
                child_var: Variable[Any] = Variable(parent_attr.observable)  # pyright: ignore[reportUnknownMemberType, reportUnknownArgumentType]
                setattr(child, child_var_name, child_var)
                return
            if isinstance(parent_attr, RecordVariable):
                # Share the ObservableProxy - create a RecordVariable for the child
                child_record_var: RecordVariable[Any] = RecordVariable(parent_attr.observable)  # pyright: ignore[reportUnknownMemberType, reportUnknownArgumentType]
                setattr(child, child_var_name, child_record_var)
                return

    # Extract variable names from the expression
    # Simple approach: find all identifiers that might be Variables
    import re

    # Find potential variable names (identifiers, possibly with underscore prefix)
    potential_vars = set(re.findall(r"\b_?[a-zA-Z_][a-zA-Z0-9_]*\b", expr))

    # Check if any referenced variable is a required binding that doesn't exist yet
    parent_class = type(parent)  # pyright: ignore[reportUnknownVariableType]
    parent_config = getattr(parent_class, "_qtpie_config", None)  # pyright: ignore[reportUnknownArgumentType]
    parent_required: set[str] = set()
    if parent_config is not None:
        parent_required = getattr(parent_config, "required_bindings", set())

    for var_name in potential_vars:
        # Check both with and without underscore prefix
        for check_name in [var_name, f"_{var_name}"]:
            if check_name in parent_required:
                # This is a required binding
                if not hasattr(parent, check_name) or getattr(parent, check_name, None) is None:
                    # The required binding hasn't been populated yet - defer this expression binding
                    deferred: list[tuple[Any, str, str]] = getattr(parent, "_qtpie_deferred_expression_bindings", [])
                    deferred.append((child, child_var_name, expression))
                    parent._qtpie_deferred_expression_bindings = deferred
                    return  # Don't apply now, will be applied later

    # Filter to only those that exist on parent
    # Track both Observable (takes value arg) and others (no arg)
    observables: list[Observable[Any]] = []
    observable_collections: list[ObservableList[Any] | ObservableDict[Any, Any] | ObservableSet[Any] | ObservableProxy[Any]] = []
    for var_name in potential_vars:
        parent_attr = getattr(parent, var_name, None)
        if parent_attr is None:
            # Try with underscore prefix
            parent_attr = getattr(parent, f"_{var_name}", None)
        if isinstance(parent_attr, Variable):
            obs: AnyObservable[Any] = parent_attr.observable  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]
            if isinstance(obs, Observable):
                observables.append(obs)  # pyright: ignore[reportUnknownArgumentType]
            else:
                # ObservableList, ObservableDict, or ObservableProxy have on_change with different signature (no args)
                observable_collections.append(obs)
        elif isinstance(parent_attr, RecordVariable):
            # RecordVariable wraps ObservableProxy
            observable_collections.append(parent_attr.observable)  # pyright: ignore[reportUnknownMemberType, reportUnknownArgumentType]
        elif isinstance(parent_attr, Observable):
            observables.append(parent_attr)  # pyright: ignore[reportUnknownArgumentType]

    def compute() -> Any:
        """Evaluate the expression with parent's context."""
        context: dict[str, Any] = {}

        for var_name in potential_vars:
            # Try with underscore prefix first, then without
            for attr_name in [f"_{var_name}", var_name]:
                if hasattr(parent, attr_name):
                    attr = getattr(parent, attr_name)
                    if isinstance(attr, Variable):
                        context[var_name] = attr.value  # pyright: ignore[reportUnknownMemberType]
                    elif isinstance(attr, RecordVariable):
                        context[var_name] = attr.value  # pyright: ignore[reportUnknownMemberType]
                    else:
                        context[var_name] = attr
                    break

        try:
            return eval(expr, {"__builtins__": __builtins__}, context)  # noqa: S307
        except Exception:
            return None

    # Create an Observable with the initial computed value
    initial_value = compute()
    child_observable: Observable[Any] = Observable(initial_value)

    # Create the child's Variable with this Observable
    child_var_computed: Variable[Any] = Variable(child_observable)

    # Assign to the child
    setattr(child, child_var_name, child_var_computed)

    # Subscribe to parent's Observables to update when they change
    def on_parent_change(_: Any) -> None:
        new_value = compute()
        child_observable.set(new_value)

    def on_collection_change() -> None:
        new_value = compute()
        child_observable.set(new_value)

    for obs in observables:
        obs.on_change(on_parent_change)

    for obs_coll in observable_collections:
        obs_coll.on_change(on_collection_change)


def _apply_literal_binding(child: Any, child_var_name: str, value: Any) -> None:
    """Set a literal value as the child Variable's default.

    Unlike expression or variable bindings, this just sets the initial value
    and does not create any reactive connection.
    """
    from observant import Observable

    # Create an Observable with the literal value
    observable: Observable[Any] = Observable(value)

    # Create a Variable with the Observable
    child_var: Variable[Any] = Variable(observable)

    # Assign to the child - triggers descriptor's __set__
    setattr(child, child_var_name, child_var)


def apply_variable_kwargs(instance: Any, variable_kwargs: dict[str, Any]) -> None:
    """Apply constructor kwargs to Variables.

    This function handles three cases:
    - Static value (int, str, etc.) → set as initial value on the Variable
    - Observable → bind to it (share the Observable)
    - Variable → bind to its underlying Observable

    For bare Variables (required bindings), we create a new Variable directly
    since the descriptor would try to resolve from parent hierarchy.

    Args:
        instance: The widget/window/dialog/menu/app instance
        variable_kwargs: Dict mapping variable names to values
    """
    from observant import Observable

    # Import descriptor types for isinstance checks
    # These are internal types but we need them to distinguish bare vs initialized Variables
    from .variable import (
        _RequiredBindingDescriptor,  # pyright: ignore[reportPrivateUsage]
        _VariableDescriptor,  # pyright: ignore[reportPrivateUsage]
    )

    for var_name, value in variable_kwargs.items():
        if isinstance(value, Observable):
            # Share the Observable directly - create a Variable wrapping it
            shared_var: Variable[Any] = Variable(value)  # pyright: ignore[reportUnknownArgumentType]
            setattr(instance, var_name, shared_var)
        elif isinstance(value, Variable):
            # Share the underlying Observable from the other Variable
            shared_var = Variable(value.observable)  # pyright: ignore[reportUnknownArgumentType, reportUnknownMemberType]
            setattr(instance, var_name, shared_var)
        else:
            # Static value - need to handle bare Variables differently
            # Check if this is a _RequiredBindingDescriptor (bare Variable)
            cls_attr = getattr(type(instance), var_name, None)  # pyright: ignore[reportUnknownArgumentType]
            if isinstance(cls_attr, _RequiredBindingDescriptor):
                # For bare Variables, create a new Variable with the static value
                # (Can't use getattr because it would try to resolve from parent)
                wrapper: Observable[Any] = Observable(value)
                new_var: Variable[Any] = Variable(wrapper)  # pyright: ignore[reportUnknownArgumentType]
                setattr(instance, var_name, new_var)
            elif isinstance(cls_attr, _VariableDescriptor):
                # For Variables with = new(), access normally and set value
                var = getattr(instance, var_name)
                var.value = value  # pyright: ignore[reportUnknownMemberType]
            else:
                # Fallback - try normal access
                var = getattr(instance, var_name)
                var.value = value


def _is_menu_marker_type(field_type: type | None) -> bool:
    """Check if the field type is a menu marker (Separator, Section).

    These types are handled specially by @menu and shouldn't be instantiated
    by new_fields.
    """
    if field_type is None:
        return False

    # Import here to avoid circular import
    from .menu import Section, Separator

    return field_type is Separator or field_type is Section


def _is_action_list_type(field_type: type | None) -> bool:
    """Check if the field type is list[QAction].

    These types are handled specially by @menu as ActionRepeaters
    and shouldn't be instantiated by new_fields.
    """
    if field_type is None:
        return False

    from typing import get_args, get_origin

    from qtpy.QtGui import QAction

    origin = get_origin(field_type)
    if origin is not list:
        return False

    type_args = get_args(field_type)
    if not type_args:
        return False

    return type_args[0] is QAction


def _resolve_refs(widget: Any, pending_refs: list[tuple[str, Any, str, Any]]) -> None:
    """Resolve deferred ref bindings after all fields are created.

    Args:
        widget: The widget instance (self) where fields were created
        pending_refs: List of (field_name, instance, ref_kwarg_name, Ref) tuples
    """
    from .ref import Ref

    for field_name, instance, ref_kwarg, ref_obj in pending_refs:
        if not isinstance(ref_obj, Ref):
            continue

        # For #parent refs, the "parent" in this context is the widget creating
        # child widgets - but we're in that widget's __init__, so the parent
        # would need to be passed differently. For now, #parent refs in this
        # context don't make sense - they're for nested widget composition.
        # Store them for later resolution if needed.
        if ref_obj.is_parent_ref:
            # Store for later resolution when parent relationship is established
            _store_deferred_parent_ref(widget, instance, ref_kwarg, ref_obj)
            continue

        # Check if this ref depends on an unset required binding
        # If so, defer resolution until after bindings are applied
        if _ref_depends_on_unset_required_binding(widget, ref_obj):
            _store_deferred_ref(widget, instance, ref_kwarg, ref_obj)
            continue

        try:
            # Resolve the ref against the widget (sibling fields)
            resolved_value = ref_obj.resolve(widget)

            # Apply to the instance via setter
            setter_name = f"set{ref_kwarg[0].upper()}{ref_kwarg[1:]}"
            setter = getattr(instance, setter_name, None)
            if setter is not None and callable(setter):
                setter(resolved_value)
            else:
                raise AttributeError(f"Cannot apply ref('{ref_obj.name}'): {type(instance).__name__} has no '{setter_name}' method")
        except (AttributeError, ValueError) as e:
            raise type(e)(f"In field '{field_name}': {e}") from e


def _ref_depends_on_unset_required_binding(widget: Any, ref_obj: Any) -> bool:
    """Check if a ref depends on a required binding that hasn't been set yet."""
    from .ref import _extract_ast_names  # pyright: ignore[reportPrivateUsage]

    # Get the widget's required bindings
    widget_class = type(widget)  # pyright: ignore[reportUnknownVariableType]
    config = getattr(widget_class, "_qtpie_config", None)  # pyright: ignore[reportUnknownArgumentType]
    if config is None:
        return False

    required: set[str] = getattr(config, "required_bindings", set())
    if not required:
        return False

    # Extract names referenced in the ref
    names: set[str] = set()
    if ref_obj.is_expression:
        # For expression refs like "Dog name: {dog.name}", parse the format template
        # to extract expressions, then extract names from each expression
        from .bindings.format_binding import _parse_format_template  # pyright: ignore[reportPrivateUsage]

        parsed = _parse_format_template(ref_obj.name)
        for _literal, field in parsed:
            if field is not None:
                expr_names = _extract_ast_names(field.expression)
                names.update(expr_names)
    else:
        # For path refs like "dog.name", get the root name
        target = ref_obj.target_name
        names = {target.split(".")[0].split("?")[0]}

    # Check if any referenced name is an unset required binding
    for name in names:
        if name in required:
            # Check if it's actually set in _qtpie state
            qtpie = getattr(widget, "_qtpie", None)
            if qtpie is None:
                return True
            variables = getattr(qtpie, "variables", {})
            if name not in variables:
                return True

    return False


def _store_deferred_ref(widget: Any, instance: Any, ref_kwarg: str, ref_obj: Any) -> None:
    """Store a ref for deferred resolution after required bindings are applied."""
    deferred: list[tuple[Any, str, Any]] = getattr(widget, "_qtpie_deferred_refs", [])
    deferred.append((instance, ref_kwarg, ref_obj))
    widget._qtpie_deferred_refs = deferred


def _resolve_deferred_refs(widget: Any) -> None:
    """Resolve refs that were deferred because they depended on required bindings."""
    deferred: list[tuple[Any, str, Any]] = getattr(widget, "_qtpie_deferred_refs", [])
    if not deferred:
        return

    for instance, ref_kwarg, ref_obj in deferred:
        try:
            # Resolve the ref against the widget
            resolved_value = ref_obj.resolve(widget)

            # Apply to the instance via setter
            setter_name = f"set{ref_kwarg[0].upper()}{ref_kwarg[1:]}"
            setter = getattr(instance, setter_name, None)
            if setter is not None and callable(setter):
                setter(resolved_value)
        except (AttributeError, ValueError) as e:
            # Log or handle error - ref resolution failed
            import warnings

            warnings.warn(f"Failed to resolve deferred ref: {e}", stacklevel=2)

    # Clear the deferred refs
    del widget._qtpie_deferred_refs


def _store_deferred_parent_ref(widget: Any, instance: Any, ref_kwarg: str, ref_obj: Any) -> None:
    """Store a #parent ref for later resolution.

    When a widget uses ref("#parent.something"), we can't resolve it during
    __init__ because the parent-child relationship isn't established yet.
    Store it on the containing widget (not the instance) to be resolved when
    that widget is created by its parent.

    Args:
        widget: The widget being initialized (self) - stores the deferred ref
        instance: The specific field instance that needs the setter called
        ref_kwarg: The kwarg name (determines the setter to call)
        ref_obj: The Ref object to resolve later
    """
    # Store on the widget (not instance) for later resolution
    # Format: (instance, ref_kwarg, ref_obj)
    deferred: list[tuple[Any, str, Any]] = getattr(widget, "_qtpie_deferred_parent_refs", [])
    deferred.append((instance, ref_kwarg, ref_obj))
    widget._qtpie_deferred_parent_refs = deferred


def _resolve_parent_refs(parent: Any, child: Any) -> None:
    """Resolve #parent refs on a child widget now that the parent is known.

    Called when a parent widget creates a child widget.
    At this point we know the parent-child relationship and can resolve #parent refs.

    Args:
        parent: The parent widget instance (provides the #parent attributes)
        child: The child widget instance that may have deferred #parent refs
    """
    from .ref import Ref

    deferred: list[tuple[Any, str, Any]] | None = getattr(child, "_qtpie_deferred_parent_refs", None)
    if not deferred:
        return

    for instance, ref_kwarg, ref_obj in deferred:
        if not isinstance(ref_obj, Ref):
            continue

        try:
            # Resolve against the parent (that's what #parent refers to)
            resolved_value = ref_obj.resolve(child, parent=parent)

            # Apply to the specific instance via setter
            setter_name = f"set{ref_kwarg[0].upper()}{ref_kwarg[1:]}"
            setter = getattr(instance, setter_name, None)
            if setter is not None and callable(setter):
                setter(resolved_value)
            else:
                raise AttributeError(f"Cannot apply ref('{ref_obj.name}'): {type(instance).__name__} has no '{setter_name}' method")
        except (AttributeError, ValueError) as e:
            raise type(e)(f"Resolving #parent ref: {e}") from e

    # Clean up
    del child._qtpie_deferred_parent_refs


def _defer_reactive_classes(context: Any, widget: Any, css_classes: list[str]) -> None:
    """Defer reactive class application until after __init__ completes.

    This is needed because create_format_binding may try to walk the parent hierarchy,
    which requires the widget's base class __init__ to have completed.
    """
    from qtpy.QtCore import QTimer

    def apply_later() -> None:
        _apply_reactive_classes(context, widget, css_classes)

    QTimer.singleShot(0, apply_later)


def _defer_reactive_object_name(context: Any, widget: Any, name_template: str) -> None:
    """Defer reactive object name application until after __init__ completes."""
    from qtpy.QtCore import QTimer

    from .bindings import create_format_binding

    def apply_later() -> None:
        create_format_binding(
            context,
            name_template,
            lambda v, inst=widget: inst.setObjectName(str(v) if v is not None else ""),
        )

    QTimer.singleShot(0, apply_later)


def _apply_reactive_classes(context: Any, widget: Any, css_classes: list[str]) -> None:
    """Apply CSS classes with reactive bindings.

    For each class that contains {expression}, create a binding that updates
    the class when the expression value changes.

    Args:
        context: The parent widget (provides variable context for bindings).
        widget: The widget to apply classes to.
        css_classes: List of CSS class names, some may contain {expression} bindings.
    """
    from qtpy.QtWidgets import QWidget

    from .bindings import create_format_binding
    from .bindings.format_binding import is_format_string
    from .styles import set_classes

    if not isinstance(widget, QWidget):
        return

    # Separate static and reactive classes
    static_classes: list[str] = []
    reactive_templates: list[str] = []

    for css_class in css_classes:
        if is_format_string(css_class):
            reactive_templates.append(css_class)
        else:
            static_classes.append(css_class)

    # Track current resolved values for reactive classes
    # Key = template, Value = current resolved class name
    resolved_reactive: dict[str, str] = {}

    def update_classes() -> None:
        """Rebuild and apply the full class list."""
        all_classes = static_classes + [v for v in resolved_reactive.values() if v]
        set_classes(widget, all_classes)

    # Create bindings for each reactive template
    for template in reactive_templates:
        # Initialize with empty string
        resolved_reactive[template] = ""

        def make_setter(tmpl: str) -> Any:
            def setter(value: Any) -> None:
                resolved_reactive[tmpl] = str(value) if value is not None else ""
                update_classes()

            return setter

        create_format_binding(context, template, make_setter(template))

    # If no reactive classes, just set static ones
    if not reactive_templates:
        set_classes(widget, static_classes)
