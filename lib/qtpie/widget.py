# pyright: reportPrivateUsage=false, reportUnknownMemberType=false
"""Widget - QWidget container with automatic layout."""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, Any, cast, get_args, get_origin, overload

from observant import Observable, ObservableDict, ObservableList, ObservableProxy, ObservableSet
from qtpy.QtWidgets import (
    QLayout,
    QSpacerItem,
    QWidget,
)

from .layout import GridPosition, LayoutType
from .mixins import QtPieComponentBase
from .new_field import NewField
from .new_fields import new_fields
from .qtpie_config import _QtPieConfig
from .signals import create_signal_expression_handler
from .state import QtPieState
from .utils.common import detect_required_bindings
from .utils.layouts import IconType, add_to_layout, create_layout, resolve_icon
from .variable import NO_DEFAULT, RecordVariable, Variable, _create_observable_for_type, _RequiredBindingDescriptor, _VariableDescriptor
from .widget_base import WidgetBase

# Re-export for backwards compatibility (window.py imports from here)
_resolve_icon = resolve_icon


class _RecordDescriptor[T]:
    """Descriptor for auto-created record on Widget[T].

    This is used when the user doesn't explicitly declare `record: Variable[T] = new(...)`.
    It lazily creates the record Variable on first access.
    """

    def __init__(self, record_type: type[T]) -> None:
        self._record_type = record_type

    def __get__(self, obj: Widget[T] | None, objtype: type | None = None) -> RecordVariable[T]:
        if obj is None:
            return self  # type: ignore[return-value]

        if not hasattr(obj, "_qtpie"):
            obj._qtpie = QtPieState(obj)

        state = obj._qtpie
        if state._record is None:
            from observant import ObservableProxy

            try:
                wrapper = _create_observable_for_type(self._record_type, NO_DEFAULT)
            except ValueError:
                # Type requires constructor args - create proxy with None target
                # User must set it in __setup__ or later
                wrapper = ObservableProxy[T](None)  # type: ignore[arg-type]
            record_var = RecordVariable(cast(ObservableProxy[T], wrapper))
            state._record = record_var
            state.register_variable("record", record_var)
            # Subscribe record to widget-level aggregation if active
            state._subscribe_record_to_widget_dirty()
            state._subscribe_record_to_widget_valid()

        return state._record  # type: ignore[return-value]

    def __set__(self, obj: Widget[T], value: T | RecordVariable[T] | Variable[T]) -> None:
        if not hasattr(obj, "_qtpie"):
            obj._qtpie = QtPieState(obj)

        if isinstance(value, RecordVariable):
            obj._qtpie._record = value
            obj._qtpie.register_variable("record", value)  # type: ignore[arg-type]
        elif isinstance(value, Variable):
            # Variable binding (from parent's Variable via bind=)
            # The child shares the parent's Observable, so wrap it in a RecordVariable
            # No need to subscribe - changes to the parent's Observable are automatically
            # reflected because we share the same Observable instance.
            from observant import ObservableProxy

            # Get the parent's Observable (which may be Observable or ObservableProxy)
            parent_obs = value.observable  # pyright: ignore[reportUnknownVariableType]

            # If it's an ObservableProxy, wrap it in RecordVariable directly
            # If it's a plain Observable, we need to get/wrap its value
            if isinstance(parent_obs, ObservableProxy):
                record_var: RecordVariable[T] = RecordVariable(parent_obs)  # type: ignore[arg-type]
                obj._qtpie._record = record_var
                obj._qtpie.register_variable("record", record_var)
                # Apply model bindings now that record is set (the target may have data already)
                target = object.__getattribute__(parent_obs, "_target")  # pyright: ignore[reportUnknownArgumentType]
                if target is not None:
                    config = getattr(type(obj), "_qtpie_config", None)
                    if config is not None:
                        _create_list_widget_fields(obj, config)
                        _apply_model_bindings_for_record(obj, config)
                else:
                    # Target is None - subscribe to changes so we can apply bindings later
                    def on_proxy_target_set(_: Any = None, child_obj: Widget[T] = obj, proxy: ObservableProxy[T] = parent_obs) -> None:  # type: ignore[assignment]
                        target = object.__getattribute__(proxy, "_target")
                        if target is not None:
                            config = getattr(type(child_obj), "_qtpie_config", None)
                            if config is not None:
                                _create_list_widget_fields(child_obj, config)
                                _apply_model_bindings_for_record(child_obj, config)
                                _propagate_record_to_tab_children(child_obj, config)
                                _propagate_model_bindings_to_children(child_obj, config)

                    parent_obs.on_change(on_proxy_target_set)
            else:
                # Plain Observable[T | None] - wrap current value in ObservableProxy
                current_value = value.value  # pyright: ignore[reportUnknownVariableType]
                if current_value is not None:
                    wrapper = ObservableProxy(current_value)  # pyright: ignore[reportUnknownVariableType, reportUnknownArgumentType]
                    record_var = RecordVariable(wrapper)  # pyright: ignore[reportUnknownArgumentType]
                    obj._qtpie._record = record_var
                    obj._qtpie.register_variable("record", record_var)
                    # Apply model bindings now that record is set with data
                    config = getattr(type(obj), "_qtpie_config", None)
                    if config is not None:
                        _create_list_widget_fields(obj, config)
                        _apply_model_bindings_for_record(obj, config)
                else:
                    # Value is None - create empty proxy, subscribe for future updates
                    wrapper = ObservableProxy[T](None)  # type: ignore[arg-type]
                    record_var = RecordVariable(wrapper)
                    obj._qtpie._record = record_var
                    obj._qtpie.register_variable("record", record_var)

                    # Subscribe to parent for when value becomes non-None
                    def on_parent_value_set(_: Any = None) -> None:
                        new_val = value.value  # pyright: ignore[reportUnknownVariableType]
                        if new_val is not None:
                            obj._qtpie._record.observable.replace_target(new_val)  # pyright: ignore[reportOptionalMemberAccess, reportAttributeAccessIssue]
                            # Recreate list widget fields and model bindings now that record has data
                            config = getattr(type(obj), "_qtpie_config", None)
                            if config is not None:
                                _create_list_widget_fields(obj, config)
                                _apply_model_bindings_for_record(obj, config)
                                _propagate_record_to_tab_children(obj, config)

                    parent_obs.on_change(on_parent_value_set)
        else:
            # Setting a value - reuse existing proxy to preserve subscriptions
            from observant import ObservableProxy

            existing_record = obj._qtpie._record
            if existing_record is not None:
                # Use replace_target to update the existing proxy in-place.
                # This preserves all subscriptions set up by bindings.
                existing_record.observable.replace_target(value)  # pyright: ignore[reportAttributeAccessIssue]
            else:
                # First time - create new proxy
                wrapper = ObservableProxy(value)
                record_var = RecordVariable(wrapper)
                obj._qtpie._record = record_var
                obj._qtpie.register_variable("record", record_var)

            # Create list widget fields now that record has data
            config = getattr(type(obj), "_qtpie_config", None)
            if config is not None:
                _create_list_widget_fields(obj, config)
                _apply_model_bindings_for_record(obj, config)

        # Subscribe record to widget-level aggregation if active
        obj._qtpie._subscribe_record_to_widget_dirty()
        obj._qtpie._subscribe_record_to_widget_valid()

        # Propagate record to any child tab widgets
        config = getattr(type(obj), "_qtpie_config", None)
        if config is not None:
            _propagate_record_to_tab_children(obj, config)


class Widget[T = None](QWidget, QtPieComponentBase):
    """QWidget container with automatic layout and QtPie features.

    Usage:
        @widget(layout="horizontal", margins=10)
        class MyWidget(Widget):
            _label: QLabel = new("Hello")
            _button: QPushButton = new("Click")

            def __setup__(self):
                self._button.clicked.connect(self._on_click)

    Or with defaults (vertical layout, no margins):
        @widget
        class MyWidget(Widget):
            _label: QLabel = new("Hello")

    With a record type (model binding):
        @widget
        class PersonEditor(Widget[Person]):
            _name: QLineEdit = new()

            def __setup__(self):
                # self.record is Variable[Person]
                self.record.observable.name.set("Alice")
    """

    # Class-level config
    _qtpie_config: _QtPieConfig
    # Instance-level state (set during __init__)
    _qtpie: QtPieState

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)

        # Create fresh config for this subclass
        cls._qtpie_config = _QtPieConfig()

        # Extract T from Widget[T] if present
        for base in getattr(cls, "__orig_bases__", ()):
            origin = get_origin(base)
            if origin is Widget:
                args = get_args(base)
                if args:
                    cls._qtpie_config.record_type = args[0]
                break

        # Check if user declared 'record' explicitly
        has_explicit_record = "record" in cls.__dict__

        # Collect fields and variable names
        for name, value in list(cls.__dict__.items()):
            if isinstance(value, NewField):
                cls._qtpie_config.fields[name] = value
            elif isinstance(value, _VariableDescriptor):
                cls._qtpie_config.variable_names.append(name)

        # Detect bare Variable[T] annotations (no = new())
        # These are required bindings - must be provided by parent
        _detect_required_bindings(cls)

        # Auto-new bare annotations (non-Variable types)
        from .widget_base import _auto_new_bare_annotations, _auto_record_bind_children

        _auto_new_bare_annotations(cls)

        # Apply @new_fields to handle non-Variable instantiation
        new_fields(cls)

        # Auto-record-bind: for child Widget[T] fields where T matches parent's T
        _auto_record_bind_children(cls)

        # Auto-create record descriptor if Widget[T] but no explicit record
        if cls._qtpie_config.record_type is not None and not has_explicit_record:
            # Create a descriptor that will lazily create the record
            cls.record = _RecordDescriptor(cls._qtpie_config.record_type)  # type: ignore[assignment]

    if TYPE_CHECKING:
        # Lie to pyright: say record returns T for field autocomplete
        # Runtime: _RecordDescriptor returns RecordVariable which forwards via __getattr__
        @property
        def record(self) -> T: ...
        @record.setter
        def record(self, value: T) -> None: ...

        @property
        def record_value(self) -> T:
            """Get the raw record value, unwrapped from the ObservableProxy.

            Use this when you need the actual object (e.g., for isinstance checks):
                if isinstance(self.record_value.auth, ApiKeyAuth):
                    ...
            """
            ...

    # -------------------------------------------------------------------------
    # Lifecycle Hooks
    # -------------------------------------------------------------------------

    async def on_close(self) -> None:
        """Async hook called when the widget is closing.

        Override this to perform async cleanup before the widget closes.
        The close event is automatically accepted after this completes.

        Example:
            @widget
            class MyWidget(Widget):
                @override
                async def on_close(self) -> None:
                    await self.save_data()
        """
        pass

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Check that @widget decorator was applied."""
        if not self._qtpie_config.init_wrapped:
            raise TypeError(f"{type(self).__name__} must be decorated with @widget. Add @widget above your class definition.")
        # This should never run - @widget replaces __init__
        super().__init__(*args, **kwargs)  # pragma: no cover

    if not TYPE_CHECKING:
        # Runtime-only: provide better error messages for .record access
        # Hidden from pyright so it doesn't disable attribute checking
        def __getattr__(self, name: str) -> Any:
            """Handle attribute access for special cases."""
            if name == "record":
                # Use AttributeError so hasattr() works correctly
                raise AttributeError(f"{type(self).__name__} has no record type. Use Widget[YourModel] to enable record access.")

            if name == "record_value":
                # Return unwrapped record value if available
                if hasattr(self, "_qtpie") and self._qtpie._record is not None:
                    return self._qtpie._record.value
                raise AttributeError(f"{type(self).__name__} has no record type. Use Widget[YourModel] to enable record_value access.")

            # Check if this is a descriptor that raised AttributeError (e.g., unresolved bare Variable)
            # If so, invoke the descriptor again to get the original error message
            from .variable import _RequiredBindingDescriptor

            cls = type(self)
            if name in cls.__dict__:
                attr = cls.__dict__[name]
                if isinstance(attr, _RequiredBindingDescriptor):
                    # Re-invoke the descriptor to get its error message
                    attr.__get__(self, cls)

            raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")


@overload
def widget[W: (Widget[Any] | WidgetBase[Any])](cls: type[W]) -> type[W]: ...


@overload
def widget[W: (Widget[Any] | WidgetBase[Any])](
    cls: None = None,
    *,
    layout: LayoutType = "vertical",
    margins: int | tuple[int, int, int, int] | None = None,
    auto_bind: bool = True,
    name: str | None = None,
    classes: list[str] | None = None,
    title: str | None = None,
    icon: IconType = None,
    size: tuple[int, int] | None = None,
    record: Any | None = None,
    **kwargs: Any,
) -> Callable[[type[W]], type[W]]: ...


def widget[W: (Widget[Any] | WidgetBase[Any])](
    cls: type[W] | None = None,
    *,
    layout: LayoutType = "vertical",
    margins: int | tuple[int, int, int, int] | None = None,
    auto_bind: bool = True,
    name: str | None = None,
    classes: list[str] | None = None,
    title: str | None = None,
    icon: IconType = None,
    size: tuple[int, int] | None = None,
    record: Any | None = None,
    stylesheet: str | None = None,
    **kwargs: Any,
) -> type[W] | Callable[[type[W]], type[W]]:
    """Decorator to configure Widget layout.

    Usage:
        @widget
        class MyWidget(Widget):
            ...

        @widget(layout="horizontal", margins=10)
        class MyWidget(Widget):
            ...

        @widget(name="my-widget", classes=["card", "primary"])
        class MyWidget(Widget):
            # Sets objectName and CSS classes
            ...

        @widget(auto_bind=False)
        class MyWidget(Widget[Person]):
            # No auto-binding, must use bind="field" explicitly
            ...

        @widget(title="My App", icon=":/icons/app.png")
        class MyWidget(Widget):
            # Extra kwargs become setXXX() calls on the widget
            ...

    Args:
        layout: "vertical" | "horizontal" | "form" | "grid" | None
                Default is "vertical". None disables auto-layout.
        margins: int | tuple[int, int, int, int] | None
                 Layout margins. int applies to all sides.
        auto_bind: If True (default), QWidget fields are automatically bound
                   to matching Variables or record fields.
        name: Set the widget's objectName.
        classes: List of CSS classes to apply to the widget.
        title: Shorthand for windowTitle.
        icon: Window icon. Accepts str path (file or Qt resource ":/..."),
              QIcon, QPixmap, or QStyle.StandardPixmap.
        stylesheet: Shorthand for styleSheet.
        **kwargs: Extra properties applied via setXXX() methods.
                  e.g., windowTitle="Foo" calls self.setWindowTitle("Foo")
    """
    # title is an alias for windowTitle
    if title is not None:
        kwargs["windowTitle"] = title
    # icon is stored raw and resolved at runtime (when Qt resources are available)
    # stylesheet is an alias for styleSheet
    if stylesheet is not None:
        kwargs["styleSheet"] = stylesheet

    def decorator(target: type[W]) -> type[W]:
        from qtpie.utils.common import is_signal_on_type

        # Extract signal connections from kwargs
        # Signal connections are kwargs where the key is a Signal name on the class
        signal_connections: dict[str, str] = {}
        widget_props: dict[str, Any] = {}
        for key, value in kwargs.items():
            if is_signal_on_type(key, target) and isinstance(value, str):
                signal_connections[key] = value
            else:
                widget_props[key] = value

        # Store layout config
        target._qtpie_config.layout = layout
        target._qtpie_config.margins = margins
        target._qtpie_config.auto_bind = auto_bind
        target._qtpie_config.record_default = record
        target._qtpie_config.widget_props = widget_props
        target._qtpie_config.object_name = name
        target._qtpie_config.css_classes = classes or []
        target._qtpie_config.icon = icon
        target._qtpie_config.size = size
        target._qtpie_config.signal_connections = signal_connections

        # Auto-wrap async methods (e.g., async def closeEvent)
        from qtpie.async_wrap import wrap_async_methods

        wrap_async_methods(target)

        # Wrap __init__ to set up layout
        _wrap_init_for_layout(target)

        return target

    if cls is not None:
        return decorator(cls)

    return decorator  # type: ignore[return-value]


def _wrap_init_for_layout(cls: type[Widget[Any]] | type[WidgetBase[Any]]) -> None:
    """Wrap __init__ to create layout, add child widgets, and call __setup__."""
    if cls._qtpie_config.init_wrapped:
        return

    original_init = cls.__init__

    # Capture config at decoration time
    config = cls._qtpie_config

    def wrapped_init(self: Any, *args: Any, **kwargs: Any) -> None:
        # Extract _qtpie_bindings before passing kwargs to original init
        _qtpie_bindings = kwargs.pop("_qtpie_bindings", None)

        # Set translation context to class name (used by t() markers)
        from qtpie.translations import set_translation_context

        set_translation_context(type(self).__name__)

        # Apply parent variable bindings BEFORE original_init runs
        # This ensures required Variables exist before child widgets are created
        if _qtpie_bindings is not None:
            # Initialize QtPieState early so Variables have somewhere to register
            if not hasattr(self, "_qtpie"):
                self._qtpie = QtPieState(self)
            parent, bindings = _qtpie_bindings
            from .new_fields import _apply_variable_bindings_direct

            _apply_variable_bindings_direct(parent, self, bindings)

        # Call original __init__ (which instantiates fields via new_fields)
        original_init(self, *args, **kwargs)

        # Create list widget fields (list[QWidget] = new(bind="..."))
        # This must happen before layout so they're included in the correct order
        _create_list_widget_fields(self, config)

        # Apply widget properties (windowTitle="X" → setWindowTitle("X"))
        _apply_widget_props(self, config)

        # Set up layout if configured
        if config.layout is not None:
            qt_layout = create_layout(config.layout)
            if qt_layout is not None:
                self.setLayout(qt_layout)

                # Apply margins
                from .utils.layouts import apply_layout_margins

                apply_layout_margins(qt_layout, config.margins)

                # Track nested layouts by field name for later reference
                nested_layouts: dict[str, QLayout] = {}

                # Track splitters by field name for later reference
                from qtpy.QtWidgets import QSplitter

                splitters: dict[str, QSplitter] = {}

                # First pass: Create nested layouts and splitters (so they exist before items reference them)
                # Don't ADD them yet - that happens in second pass to preserve field order
                for name in getattr(cls, "__annotations__", {}):
                    if name in config.fields:
                        field = config.fields[name]
                        if field.is_nested_layout:
                            # Create the nested layout instance (but don't add to layout yet - preserve order)
                            layout_instance = field.field_type(*field.args, **field.kwargs)  # type: ignore[misc]
                            setattr(self, name, layout_instance)
                            nested_layouts[name] = layout_instance

                        elif field.is_splitter:
                            # Create the splitter instance (but don't add to layout yet - preserve order)
                            splitter_instance = field.field_type(*field.args, **field.kwargs)  # type: ignore[misc]
                            setattr(self, name, splitter_instance)
                            splitters[name] = splitter_instance

                # Second pass: Add child widgets, Variables, Stretch, and QSpacerItem to layouts
                # Use __annotations__ to preserve order across all field types
                from qtpie.layout import Stretch

                for name in getattr(cls, "__annotations__", {}):
                    annotation = getattr(cls, "__annotations__", {}).get(name)

                    # Handle bare Stretch annotation (without = new())
                    if annotation is Stretch and name not in config.fields:
                        _add_stretch_to_layout(qt_layout, 1)  # Default factor
                        continue

                    if name in config.fields:
                        field = config.fields[name]
                        if field.exclude_from_layout:
                            continue

                        # Handle nested layouts - add to layout in order
                        if field.is_nested_layout:
                            layout_instance = nested_layouts.get(name)
                            if layout_instance is not None:
                                target = _get_target_layout(qt_layout, nested_layouts, field.target_layout)
                                if target is not None:
                                    _add_layout_to_nested_layout(target, layout_instance, field.grid, name)
                            continue

                        # Handle QSplitter - add to layout in order
                        if field.is_splitter:
                            splitter_instance = splitters.get(name)
                            if splitter_instance is not None:
                                target = _get_target_layout(qt_layout, nested_layouts, field.target_layout)
                                if target is not None:
                                    _add_to_layout(target, splitter_instance, config.layout, None, field.grid, None)
                            continue

                        # Check if widget should go to a splitter instead of layout
                        target_splitter = _get_target_splitter(splitters, field.target_splitter)
                        if target_splitter is not None:
                            # Add to splitter, not layout
                            widget_instance = getattr(self, name, None)
                            if widget_instance is not None and isinstance(widget_instance, QWidget):
                                target_splitter.addWidget(widget_instance)
                            continue

                        # Determine target layout
                        target = _get_target_layout(qt_layout, nested_layouts, field.target_layout)
                        if target is None:
                            continue

                        # Handle Stretch
                        if field.is_stretch:
                            _add_stretch_to_layout(target, field.stretch_factor)
                            continue

                        # Handle QSpacerItem
                        if field.is_spacer_item:
                            spacer = _create_spacer_item(field)
                            setattr(self, name, spacer)
                            _add_spacer_to_layout(target, spacer, field.grid)
                            continue

                        # Handle regular QWidget
                        widget_instance = getattr(self, name, None)
                        if widget_instance is not None and isinstance(widget_instance, QWidget):
                            # Resolve Translatable labels (keep original for retranslation)
                            from qtpie.translations.translatable import Translatable

                            label_translatable = field.label if isinstance(field.label, Translatable) else None
                            label = field.label.resolve() if isinstance(field.label, Translatable) else field.label

                            # For default layout: validate and use decorator's layout type
                            # For nested layout: detect actual layout type and use appropriate add method
                            if field.target_layout is None:
                                _validate_layout_params(name, config.layout, label, field.grid)
                                _add_to_layout(target, widget_instance, config.layout, label, field.grid, label_translatable)
                            else:
                                _add_widget_to_nested_layout(target, widget_instance, label, field.grid, name)

                    # Check if it's a Variable with a widget
                    elif name in config.variable_names:
                        var = getattr(self, name, None)
                        if isinstance(var, Variable) and var.widget is not None:
                            # Get label/grid/exclude_from_layout/target_layout from the descriptor
                            descriptor: Any = getattr(cls, name, None)
                            var_label: str | None = None
                            var_label_translatable: Any = None
                            grid: GridPosition | None = None
                            target_layout_name: str | None = None
                            if isinstance(descriptor, _VariableDescriptor):
                                if descriptor.exclude_from_layout:
                                    continue
                                # Resolve Translatable labels (keep original for retranslation)
                                from qtpie.translations.translatable import Translatable

                                raw_label = descriptor.label
                                if isinstance(raw_label, Translatable):
                                    var_label = raw_label.resolve()
                                    var_label_translatable = raw_label
                                else:
                                    var_label = raw_label
                                grid = descriptor.grid  # type: ignore[assignment]
                                target_layout_name = descriptor.target_layout

                            # Determine target layout
                            target = _get_target_layout(qt_layout, nested_layouts, target_layout_name)
                            if target is None:
                                continue

                            # For default layout: validate and use decorator's layout type
                            # For nested layout: detect actual layout type and use appropriate add method
                            if target_layout_name is None:
                                _validate_layout_params(name, config.layout, var_label, grid)
                                _add_to_layout(target, var.widget, config.layout, var_label, grid, var_label_translatable)
                            else:
                                _add_widget_to_nested_layout(target, var.widget, var_label, grid, name)

        # Connect signals (clicked="on_clicked" or clicked=lambda: ...)
        _connect_signals(self, config)

        # Register validators from validate= parameter (before __setup__ so they're active)
        _register_validators(self, config)

        # Set initial record value if provided via @widget(record=...)
        if config.record_default is not None and hasattr(self, "record"):
            self.record = config.record_default

            # Propagate record to any child tab widgets that were created before record was set
            _propagate_record_to_tab_children(self, config)

        # Call __setup__ hook if defined (required bindings are now available)
        setup_method = getattr(self, "__setup__", None)
        if setup_method is not None:
            setup_method()

        # Apply bindings (after __setup__ so record is available)
        from .bindings.apply import apply_auto_bindings, apply_property_bindings, apply_reactive_widget_props, pre_create_selection_variables
        from .bindings.expression import create_expression_binding

        # Pre-create Variables for selection bindings (bare Variable[T] without new())
        pre_create_selection_variables(self, config)

        apply_auto_bindings(self, config)

        # Apply property bindings (visible="_is_visible", enabled="{_count > 0}", etc.)
        apply_property_bindings(self, config, create_expression_binding_fn=create_expression_binding)

        # Apply reactive widget props from @widget decorator (windowTitle="{title}", etc.)
        apply_reactive_widget_props(self, config)

        # Enable on_dirty_changed and on_valid_changed hooks (subscribes to future Variable changes)
        state = getattr(self, "_qtpie", None)
        if not isinstance(state, QtPieState):
            state = QtPieState(self)
            self._qtpie = state  # type: ignore[assignment]
        state.enable_dirty_hook()
        state.enable_valid_hook()

    cls.__init__ = wrapped_init  # type: ignore[method-assign]
    cls._qtpie_config.init_wrapped = True


def _validate_layout_params(
    field_name: str,
    layout_type: LayoutType,
    label: str | None,
    grid: GridPosition | None,
) -> None:
    """Validate that required layout params are provided.

    Raises:
        TypeError: If form layout is used without label=, or grid layout without grid=.
    """
    if layout_type == "form" and label is None:
        raise TypeError(f"Field '{field_name}' requires label= for form layout. Use: new(..., label=\"Field Label\")")
    if layout_type == "grid" and grid is None:
        raise TypeError(f"Field '{field_name}' requires grid= for grid layout. Use: new(..., grid=(row, col)) or new(..., grid=(row, col, rowspan, colspan))")


def _add_to_layout(
    layout: QLayout,
    widget_instance: QWidget,
    layout_type: LayoutType,
    label: str | None = None,
    grid: GridPosition | None = None,
    label_translatable: Any | None = None,
) -> None:
    """Add a widget to the layout."""
    add_to_layout(layout, widget_instance, layout_type, label, grid, label_translatable)


def _get_target_layout(
    default_layout: QLayout,
    nested_layouts: dict[str, QLayout],
    target_name: str | None,
) -> QLayout | None:
    """Get the target layout for adding items.

    Args:
        default_layout: The widget's default layout.
        nested_layouts: Dictionary of nested layouts by field name.
        target_name: Name of the target layout (or None for default).

    Returns:
        The target QLayout, or None if target not found.
    """
    if target_name is None:
        return default_layout
    return nested_layouts.get(target_name)


def _get_target_splitter(
    splitters: dict[str, Any],
    target_name: str | None,
) -> Any | None:
    """Get the target splitter for adding widgets.

    Args:
        splitters: Dictionary of splitters by field name.
        target_name: Name of the target splitter (or None for no splitter).

    Returns:
        The target QSplitter, or None if no splitter target.
    """
    if target_name is None:
        return None
    return splitters.get(target_name)


def _add_stretch_to_layout(layout: QLayout, factor: int = 1) -> None:
    """Add stretch to a layout.

    Only works for QBoxLayout (QVBoxLayout, QHBoxLayout).
    For other layout types, this is a no-op.
    """
    from qtpy.QtWidgets import QBoxLayout

    if isinstance(layout, QBoxLayout):
        layout.addStretch(factor)


def _create_spacer_item(field: NewField) -> QSpacerItem:
    """Create a QSpacerItem from field configuration."""
    return QSpacerItem(*field.args, **field.kwargs)


def _add_spacer_to_layout(layout: QLayout, spacer: QSpacerItem, grid: GridPosition | None = None) -> None:
    """Add a spacer item to a layout.

    Works for QBoxLayout and QGridLayout.
    """
    from qtpy.QtWidgets import QBoxLayout, QGridLayout

    if isinstance(layout, QBoxLayout):
        layout.addSpacerItem(spacer)
    elif isinstance(layout, QGridLayout):
        if grid is not None:
            row, col = grid[0], grid[1]
            rowspan = grid[2] if len(grid) > 2 else 1
            colspan = grid[3] if len(grid) > 3 else 1
            layout.addItem(spacer, row, col, rowspan, colspan)
        else:
            layout.addItem(spacer)


def _add_widget_to_nested_layout(
    layout: QLayout,
    widget: QWidget,
    label: str | None = None,
    grid: GridPosition | None = None,
    field_name: str = "",
) -> None:
    """Add a widget to a nested layout, respecting grid=/label= based on layout type.

    Unlike _add_to_layout which uses the decorator's layout type, this detects
    the actual QLayout subclass and uses the appropriate add method.

    Raises:
        TypeError: If QGridLayout and grid= not provided, or QFormLayout and label= not provided.
    """
    from qtpy.QtWidgets import QBoxLayout, QFormLayout, QGridLayout

    if isinstance(layout, QGridLayout):
        if grid is None:
            raise TypeError(f"Field '{field_name}' requires grid= for grid layout. Use: new(..., grid=(row, col)) or new(..., grid=(row, col, rowspan, colspan))")
        row, col = grid[0], grid[1]
        rowspan = grid[2] if len(grid) > 2 else 1
        colspan = grid[3] if len(grid) > 3 else 1
        layout.addWidget(widget, row, col, rowspan, colspan)
    elif isinstance(layout, QFormLayout):
        if label is None:
            raise TypeError(f"Field '{field_name}' requires label= for form layout. Use: new(..., label=\"Field Label\")")
        layout.addRow(label, widget)
    elif isinstance(layout, QBoxLayout):
        layout.addWidget(widget)
    else:
        # Fallback for other layout types
        layout.addWidget(widget)  # type: ignore[union-attr]


def _add_layout_to_nested_layout(
    parent_layout: QLayout,
    child_layout: QLayout,
    grid: GridPosition | None = None,
    field_name: str = "",
) -> None:
    """Add a nested layout to a parent layout, respecting grid= for grid layouts.

    Raises:
        TypeError: If parent is QGridLayout and grid= is not provided.
    """
    from qtpy.QtWidgets import QBoxLayout, QFormLayout, QGridLayout

    if isinstance(parent_layout, QGridLayout):
        if grid is None:
            raise TypeError(f"Field '{field_name}' requires grid= for grid layout. Use: new(..., grid=(row, col)) or new(..., grid=(row, col, rowspan, colspan))")
        row, col = grid[0], grid[1]
        rowspan = grid[2] if len(grid) > 2 else 1
        colspan = grid[3] if len(grid) > 3 else 1
        parent_layout.addLayout(child_layout, row, col, rowspan, colspan)
    elif isinstance(parent_layout, QFormLayout):
        # QFormLayout.addRow can take a layout
        parent_layout.addRow(child_layout)
    elif isinstance(parent_layout, QBoxLayout):
        parent_layout.addLayout(child_layout)
    else:
        # Fallback
        parent_layout.addLayout(child_layout)  # type: ignore[union-attr]


def _apply_widget_props(widget: Widget[Any], config: _QtPieConfig) -> None:
    """Apply widget properties from @widget decorator kwargs.

    For each prop like windowTitle="X", calls widget.setWindowTitle("X").
    Also applies name and classes from the decorator.

    Reactive props (with {}) are skipped here and applied later by _apply_reactive_widget_props.
    """
    from .bindings import is_format_string
    from .utils.layouts import apply_object_name_and_classes, apply_widget_props

    # Apply objectName and CSS classes
    apply_object_name_and_classes(
        widget,
        config.object_name,
        config.css_classes,
        default_name=type(widget).__name__,
    )

    # Apply icon at runtime (when Qt resources are available)
    if config.icon is not None:
        resolved_icon = resolve_icon(config.icon)
        if resolved_icon is not None:
            widget.setWindowIcon(resolved_icon)

    # Apply initial size
    if config.size is not None:
        widget.resize(*config.size)

    # Apply widget properties, skipping reactive ones
    def skip_reactive(prop_name: str, value: Any) -> bool:
        return isinstance(value, str) and is_format_string(value)

    apply_widget_props(widget, config.widget_props, skip_filter=skip_reactive, strict=True)


def _register_validators(widget: Widget[Any], config: _QtPieConfig) -> None:  # pyright: ignore[reportUnknownArgumentType]
    """Register validators defined via validate= parameter on Variables.

    Supports multiple formats:
    - validate="method_name" → single string method
    - validate=callable → single callable
    - validate=["method1", "method2"] → list of method names
    - validate=[callable1, callable2] → list of callables
    - validate=[("custom_name", "method")] → tuple with explicit validator name
    - validate=[("custom_name", callable)] → tuple with explicit name and callable
    """
    from .variable import Variable, _VariableDescriptor

    cls = type(widget)

    for name in config.variable_names:
        # Get the descriptor to access validators list
        descriptor = getattr(cls, name, None)
        if not isinstance(descriptor, _VariableDescriptor):
            continue

        if not descriptor.validators:
            continue

        # Access the Variable instance to register validators
        var = getattr(widget, name, None)
        if not isinstance(var, Variable):
            continue

        # Normalize validators to a list
        raw_validators: Any = descriptor.validators
        validators_list: list[Any] = cast(list[Any], raw_validators) if isinstance(raw_validators, list) else [raw_validators]

        for spec in validators_list:
            validator_name: str
            validator_fn: Callable[..., Any]

            if isinstance(spec, tuple) and len(spec) == 2:  # pyright: ignore[reportUnknownArgumentType]
                # ("name", "method") or ("name", callable)
                name_part = str(spec[0])  # pyright: ignore[reportUnknownArgumentType]
                fn_part = cast(Any, spec[1])
                if isinstance(fn_part, str):
                    fn = getattr(widget, fn_part, None)
                    if fn is None or not callable(fn):
                        raise AttributeError(f"Validator method '{fn_part}' not found on {cls.__name__}")
                    validator_name = name_part
                    validator_fn = fn
                elif callable(fn_part):  # pyright: ignore[reportUnknownArgumentType]
                    validator_name = name_part
                    validator_fn = fn_part
                else:
                    raise TypeError(f"Invalid validator spec: {spec}")
            elif isinstance(spec, str):
                # "method_name" → name defaults to method name
                validator_name = spec
                fn = getattr(widget, spec, None)
                if fn is None or not callable(fn):
                    raise AttributeError(f"Validator method '{spec}' not found on {cls.__name__}")
                validator_fn = fn
            elif callable(spec):  # pyright: ignore[reportUnknownArgumentType]
                # callable → name from __name__ attribute
                validator_name = getattr(spec, "__name__", str(spec))
                validator_fn = spec
            else:
                raise TypeError(f"Invalid validator spec: {spec}")

            var.add_validator(validator_name, validator_fn)  # pyright: ignore[reportUnknownMemberType]


def _propagate_record_to_tab_children(widget: Widget[Any], config: _QtPieConfig) -> None:
    """Propagate record to child tab widgets after record is set.

    When a Widget[T] contains a QTabWidget with tabs=[], the tab content widgets
    are created before the parent's record is set. This function re-propagates
    the record to child tab widgets that have matching record types.
    """
    from qtpy.QtWidgets import QTabWidget

    from .bindings.tab_binding import _propagate_record_to_child

    for name in config.fields:
        field_value = getattr(widget, name, None)
        if isinstance(field_value, QTabWidget):
            # Iterate over all tabs and propagate record
            for i in range(field_value.count()):
                child_widget = field_value.widget(i)
                _propagate_record_to_child(widget, child_widget)


def _propagate_model_bindings_to_children(widget: Widget[Any], config: _QtPieConfig) -> None:
    """Apply model bindings to child Widget[T] instances after parent's record is set.

    When a Widget[T] contains bare annotation Widget[T] children (same T), those children
    share the parent's ObservableProxy. When the parent's record target changes, we need
    to apply model bindings on children because they couldn't resolve bind sources at init time.
    """
    from qtpy.QtWidgets import QWidget

    # Get parent's record type
    parent_record_type = getattr(config, "record_type", None)
    if parent_record_type is None:
        return

    for name, field in config.fields.items():
        # Check if this is a Widget[T] field (same T as parent)
        child_cls = field.field_type
        if child_cls is None:
            continue

        child_config = getattr(child_cls, "_qtpie_config", None)
        if child_config is None:
            continue

        child_record_type = getattr(child_config, "record_type", None)
        if child_record_type is None or child_record_type != parent_record_type:
            continue

        # Get the child instance
        child_widget = getattr(widget, name, None)
        if child_widget is None or not isinstance(child_widget, QWidget):
            continue

        # Apply model bindings on the child (and recurse into its children)
        _apply_model_bindings_for_record(child_widget, child_config)  # type: ignore[arg-type]
        _propagate_model_bindings_to_children(child_widget, child_config)  # type: ignore[arg-type]


def _create_list_widget_fields(widget: Widget[Any], config: _QtPieConfig) -> None:
    """Create WidgetRepeater/SetWidgetRepeater instances for list[QWidget]/set[QWidget] fields.

    For each field with annotation like `list[QLabel]` or `set[QLabel]` and `bind="some_path"`,
    resolves the bind path to get the source collection and creates an appropriate repeater.

    The source can be:
    - Variable[list[T]/set[T]] → uses its ObservableList/ObservableSet (reactive)
    - ObservableList/ObservableSet directly → uses it (reactive)
    - Observable[list/set] → wraps value in ObservableList/ObservableSet (one-time)
    - Plain list/set → wraps in ObservableList/ObservableSet (one-time)
    """
    from observant import Observable, ObservableDict, ObservableList, ObservableSet

    from .bindings import resolve_binding_source
    from .set_widget_repeater import SetWidgetRepeater
    from .variable import Variable
    from .widget_repeater import WidgetRepeater

    for name, field in config.fields.items():
        if not field.is_list_widget:
            continue

        # Skip if already processed (repeater already set)
        existing = getattr(widget, name, None)
        if existing is not None and hasattr(existing, "widget_count"):
            continue

        # Compute objectName with priority: new(name=) > @widget(name=) > field name (stripped)
        if field.object_name is not None:
            computed_object_name = field.object_name
        elif config.object_name is not None:
            computed_object_name = config.object_name
        else:
            computed_object_name = name[1:] if name.startswith("_") else name

        # list_widget_type is always set when is_list_widget is True
        assert field.list_widget_type is not None

        if field.bind is None:
            raise ValueError(f"list[{field.list_widget_type.__name__}] field '{name}' requires bind='...'")

        # Resolve the bind path to get the source
        source = resolve_binding_source(widget, field.bind)

        # Convert source to ObservableList
        obs_list: ObservableList[Any]
        item_type: type | None = None

        # If source is None, check if it's a plain list/dict attribute
        if source is None:
            # Try to get raw attribute (handles plain list/dict fields)
            bind_path = field.bind.lstrip("_")
            raw_attr = None

            # Helper to check if value is a real data value (not a descriptor/NewField)
            def is_real_value(val: Any) -> bool:
                from .new_field import NewField

                return val is not None and not isinstance(val, NewField)

            if hasattr(widget, bind_path):
                val = getattr(widget, bind_path)
                if is_real_value(val):
                    raw_attr = val
            if raw_attr is None and hasattr(widget, f"_{bind_path}"):
                val = getattr(widget, f"_{bind_path}")
                if is_real_value(val):
                    raw_attr = val

            # If still not found and widget has a record, check the record
            got_from_record = False
            if raw_attr is None and config.record_type is not None:
                try:
                    record_proxy = widget.record
                    # Get the underlying target object from the proxy
                    target = object.__getattribute__(record_proxy.observable, "_target")
                    if target is not None and hasattr(target, bind_path):
                        raw_attr = getattr(target, bind_path)
                        got_from_record = True
                    elif target is None:
                        # Record not yet available (e.g., tab content before propagation)
                        # Mark as pending - will be processed when record is set
                        if not hasattr(widget, "_qtpie_pending_list_fields"):
                            widget._qtpie_pending_list_fields = []  # type: ignore[attr-defined]
                        widget._qtpie_pending_list_fields.append(name)  # type: ignore[attr-defined]

                        # Subscribe to record changes so we process pending fields when record is set
                        def make_record_subscription(
                            w: Widget[Any],
                            field_name: str,
                            cfg: _QtPieConfig,
                            proxy: Any,
                        ) -> None:
                            def on_record_change() -> None:
                                pending = getattr(w, "_qtpie_pending_list_fields", [])
                                if field_name in pending:
                                    _create_list_widget_fields(w, cfg)

                            proxy.on_change(on_record_change)

                        make_record_subscription(widget, name, config, record_proxy.observable)
                        continue
                except (AttributeError, TypeError):
                    pass

            # If we got the attr from record but it's None, defer until it has a value
            if got_from_record and raw_attr is None:
                if not hasattr(widget, "_qtpie_pending_list_fields"):
                    widget._qtpie_pending_list_fields = []  # type: ignore[attr-defined]
                widget._qtpie_pending_list_fields.append(name)  # type: ignore[attr-defined]
                continue

            if isinstance(raw_attr, list):
                # Wrap plain list in ObservableList
                obs_list = ObservableList(cast(list[Any], raw_attr))
                setattr(widget, field.bind, obs_list)  # Replace with observable version
                # Skip to repeater creation
                plain_bind_expr: Any = field.list_format if field.list_format is not None else "{#self}"
                repeater = WidgetRepeater(
                    observable_list=obs_list,
                    item_type=item_type,
                    widget_type=field.list_widget_type,
                    widget_args=field.args,
                    widget_kwargs=field.kwargs,
                    widget_props=field.widget_props,
                    bind_expr=plain_bind_expr,
                    sort=field.sort,
                    object_name=computed_object_name,
                    css_classes=field.css_classes,
                    signal_connections=field.signal_connections,
                    parent_widget=widget,
                )
                setattr(widget, name, repeater)
                _add_repeater_to_layout(widget, repeater, name, field)
                continue
            elif isinstance(raw_attr, dict):
                from .dict_widget_repeater import DictWidgetRepeater

                obs_dict: ObservableDict[Any, Any] = ObservableDict(cast(dict[Any, Any], raw_attr))
                setattr(widget, field.bind, obs_dict)
                bind_expr_dict: Any = field.list_format if field.list_format is not None else "{#key} = {#value}"
                dict_repeater: DictWidgetRepeater[Any, Any] = DictWidgetRepeater(
                    observable_dict=obs_dict,
                    key_type=None,
                    value_type=None,
                    widget_type=field.list_widget_type,
                    widget_args=field.args,
                    widget_kwargs=field.kwargs,
                    widget_props=field.widget_props,
                    bind_expr=bind_expr_dict,
                    sort=field.sort,
                    object_name=computed_object_name,
                    css_classes=field.css_classes,
                    signal_connections=field.signal_connections,
                    parent_widget=widget,
                )
                setattr(widget, name, dict_repeater)
                _add_repeater_to_layout(widget, dict_repeater, name, field)
                continue
            else:
                raise ValueError(f"Could not resolve bind path '{field.bind}' for field '{name}'")

        # Get the underlying observable from Variable or use source directly
        wrapper: Any = None
        if isinstance(source, Variable):
            wrapper = source.observable
        else:
            wrapper = source

        # For nested paths like "workspace.collections", we also need to subscribe to the ROOT Variable
        # so that when workspace changes from None to a real object, we re-sync
        root_variable: Variable[Any] | None = None
        bind_path_normalized = field.bind.replace("?.", ".")
        if "." in bind_path_normalized:
            root_name = bind_path_normalized.split(".")[0]
            root_attr: Any = getattr(widget, root_name, None)
            if root_attr is not None and isinstance(root_attr, Variable):
                root_variable = cast(Variable[Any], root_attr)

        # Handle ObservableDict -> DictWidgetRepeater
        if isinstance(wrapper, ObservableDict):
            from .dict_widget_repeater import DictWidgetRepeater

            # Determine bind expression: use format= if provided, else "{#key} = {#value}"
            bind_expr_dict: Any = field.list_format if field.list_format is not None else "{#key} = {#value}"

            dict_repeater: DictWidgetRepeater[Any, Any] = DictWidgetRepeater(
                observable_dict=wrapper,  # pyright: ignore[reportUnknownArgumentType]
                key_type=None,  # Could extract from type hints if needed
                value_type=None,
                widget_type=field.list_widget_type,  # pyright: ignore[reportArgumentType]
                widget_args=field.args,
                widget_kwargs=field.kwargs,
                widget_props=field.widget_props,
                bind_expr=bind_expr_dict,
                sort=field.sort,
                object_name=computed_object_name,
                css_classes=field.css_classes,
                signal_connections=field.signal_connections,
                parent_widget=widget,
            )
            setattr(widget, name, dict_repeater)
            _add_repeater_to_layout(widget, dict_repeater, name, field)
            continue

        # Handle ObservableList -> WidgetRepeater
        obs_list: ObservableList[Any]
        if isinstance(wrapper, ObservableList):
            obs_list = wrapper  # pyright: ignore[reportUnknownVariableType]
        elif isinstance(wrapper, Observable):
            # Observable containing a list or dict - create synced repeater
            val: Any = wrapper.get()  # pyright: ignore[reportUnknownVariableType]
            if isinstance(val, list):
                obs_list = ObservableList(cast(list[Any], val))
            elif isinstance(val, dict):
                # Observable wrapping a dict - create DictWidgetRepeater
                from .dict_widget_repeater import DictWidgetRepeater

                obs_dict: ObservableDict[Any, Any] = ObservableDict(cast(dict[Any, Any], val))
                bind_expr_dict: Any = field.list_format if field.list_format is not None else "{#key} = {#value}"
                dict_repeater: DictWidgetRepeater[Any, Any] = DictWidgetRepeater(
                    observable_dict=obs_dict,
                    key_type=None,
                    value_type=None,
                    widget_type=field.list_widget_type,
                    widget_args=field.args,
                    widget_kwargs=field.kwargs,
                    widget_props=field.widget_props,
                    bind_expr=bind_expr_dict,
                    sort=field.sort,
                    object_name=computed_object_name,
                    css_classes=field.css_classes,
                    signal_connections=field.signal_connections,
                    parent_widget=widget,
                )
                setattr(widget, name, dict_repeater)
                _add_repeater_to_layout(widget, dict_repeater, name, field)

                # Sync: when Observable changes, update ObservableDict
                def make_dict_sync(obs: Observable[Any], target_dict: ObservableDict[Any, Any]) -> None:
                    def on_source_change(new_val: Any) -> None:
                        if isinstance(new_val, dict):
                            target_dict.clear()
                            target_dict.update(cast(dict[Any, Any], new_val))
                        elif new_val is None:
                            target_dict.clear()

                    obs.on_change(on_source_change)

                make_dict_sync(wrapper, obs_dict)  # pyright: ignore[reportUnknownArgumentType]
                continue
            elif val is None:
                # Initial value is None - defer until value becomes available
                # Mark as pending - will be processed when value is set
                if not hasattr(widget, "_qtpie_pending_list_fields"):
                    widget._qtpie_pending_list_fields = []  # type: ignore[attr-defined]
                widget._qtpie_pending_list_fields.append(name)  # type: ignore[attr-defined]

                # Subscribe to be notified when value changes
                def make_deferred_setup(
                    obs: Observable[Any],
                    w: Widget[Any],
                    field_name: str,
                    cfg: _QtPieConfig,
                ) -> None:
                    def on_value_available(new_val: Any) -> None:
                        if new_val is not None:
                            # Value is now available, process the field
                            pending = getattr(w, "_qtpie_pending_list_fields", [])
                            if field_name in pending:
                                _create_list_widget_fields(w, cfg)
                                # Remove from pending
                                if hasattr(w, "_qtpie_pending_list_fields"):
                                    w._qtpie_pending_list_fields = [  # type: ignore[attr-defined]
                                        f
                                        for f in w._qtpie_pending_list_fields  # pyright: ignore[reportUnknownVariableType, reportAttributeAccessIssue]
                                        if f != field_name  # type: ignore[attr-defined]
                                    ]

                    obs.on_change(on_value_available)

                make_deferred_setup(wrapper, widget, name, config)  # pyright: ignore[reportUnknownArgumentType]
                continue
            else:
                raise TypeError(f"bind='{field.bind}' resolved to Observable[{type(val).__name__}], expected list or dict")  # pyright: ignore[reportUnknownArgumentType]

            # Sync: when Observable changes, update ObservableList
            def make_sync(obs: Observable[Any], target: ObservableList[Any]) -> None:
                def on_source_change(new_val: Any) -> None:
                    if isinstance(new_val, list):
                        target.clear()
                        target.extend(cast(list[Any], new_val))
                    elif new_val is None:
                        target.clear()

                obs.on_change(on_source_change)

            make_sync(wrapper, obs_list)  # pyright: ignore[reportUnknownArgumentType]

            # For nested paths, also subscribe to ROOT Variable to re-sync when it changes
            # BUT only if the nested path is on the VALUE (not on the Variable itself)
            if root_variable is not None:
                nested_path = ".".join(bind_path_normalized.split(".")[1:])
                first_nested = nested_path.split(".")[0] if nested_path else ""

                # Skip if nested path is a Variable property (e.g., validation_error_messages)
                # Those are already properly subscribed via resolve_binding_source
                is_variable_property = hasattr(root_variable, first_nested) and not first_nested.startswith("_")

                if not is_variable_property:

                    def make_root_sync(root_var: Variable[Any], target: ObservableList[Any], path: str) -> None:
                        def on_root_change(*_: Any) -> None:
                            root_val = root_var.value
                            if root_val is None:
                                target.clear()
                                return
                            # Traverse nested path
                            nested_val: Any = root_val
                            for part in path.split("."):
                                if nested_val is None:
                                    break
                                nested_val = getattr(nested_val, part, None)
                            if isinstance(nested_val, list):
                                target.clear()
                                target.extend(cast(list[Any], nested_val))
                            elif nested_val is None:
                                target.clear()

                        root_var.observable.on_change(on_root_change)

                    make_root_sync(root_variable, obs_list, nested_path)
        elif isinstance(wrapper, ObservableProxy):
            # ObservableProxy - need to handle nested path like "workspace.collections"
            # Start with empty list, sync when root object changes
            obs_list = ObservableList[Any]()

            # Get the nested path (e.g., "collections" from "workspace.collections")
            bind_path = field.bind.replace("?.", ".")
            parts = bind_path.split(".")
            nested_path = ".".join(parts[1:]) if len(parts) > 1 else None

            def make_proxy_sync(proxy: ObservableProxy[Any], target: ObservableList[Any], path: str | None) -> None:
                def on_proxy_change() -> None:
                    root_val = proxy.unwrap()
                    if root_val is None:
                        target.clear()
                        return
                    # Get nested value
                    if path:
                        nested_val = root_val
                        for part in path.split("."):
                            if nested_val is None:
                                break
                            nested_val = getattr(nested_val, part, None)
                    else:
                        nested_val = root_val
                    if isinstance(nested_val, list):
                        target.clear()
                        target.extend(cast(list[Any], nested_val))
                    elif nested_val is None:
                        target.clear()

                proxy.on_change(on_proxy_change)
                # Also trigger initial sync
                on_proxy_change()

            make_proxy_sync(wrapper, obs_list, nested_path)  # pyright: ignore[reportUnknownArgumentType]
        else:
            raise TypeError(f"bind='{field.bind}' resolved to {type(wrapper).__name__}, expected Variable[list[...]], Variable[dict[...]], ObservableList, or ObservableDict")

        # Determine bind expression: use format= if provided, else "{#self}"
        bind_expr: str | Callable[[Any], str] = field.list_format if field.list_format is not None else "{#self}"

        # Create WidgetRepeater
        repeater = WidgetRepeater(
            observable_list=obs_list,
            item_type=item_type,  # Could extract from source type hints if needed
            widget_type=field.list_widget_type,
            widget_args=field.args,
            widget_kwargs=field.kwargs,
            widget_props=field.widget_props,
            bind_expr=bind_expr,
            sort=field.sort,
            object_name=computed_object_name,
            css_classes=field.css_classes,
            signal_connections=field.signal_connections,
            parent_widget=widget,
        )

        # Store the repeater on the widget
        setattr(widget, name, repeater)
        _add_repeater_to_layout(widget, repeater, name, field)

    # Handle set[QWidget] fields
    for name, field in config.fields.items():
        if not field.is_set_widget:
            continue

        # Compute objectName with priority: new(name=) > @widget(name=) > field name (stripped)
        if field.object_name is not None:
            computed_object_name = field.object_name
        elif config.object_name is not None:
            computed_object_name = config.object_name
        else:
            computed_object_name = name[1:] if name.startswith("_") else name

        # set_widget_type is always set when is_set_widget is True
        assert field.set_widget_type is not None

        if field.bind is None:
            raise ValueError(f"set[{field.set_widget_type.__name__}] field '{name}' requires bind='...'")

        # Resolve the bind path to get the source
        source = resolve_binding_source(widget, field.bind)

        # Convert source to ObservableSet
        obs_set: ObservableSet[Any]
        item_type: type | None = None

        # If source is None, check if it's a plain set attribute
        if source is None:
            # Try to get raw attribute (handles plain set fields)
            bind_path = field.bind.lstrip("_")
            raw_attr = None
            if hasattr(widget, bind_path):
                raw_attr = getattr(widget, bind_path)
            elif hasattr(widget, f"_{bind_path}"):
                raw_attr = getattr(widget, f"_{bind_path}")

            if isinstance(raw_attr, set):
                # Wrap plain set in ObservableSet
                obs_set = ObservableSet(cast(set[Any], raw_attr))
                setattr(widget, field.bind, obs_set)  # Replace with observable version
                # Skip to repeater creation
                plain_bind_expr: Any = field.set_format if field.set_format is not None else "{#self}"
                set_repeater = SetWidgetRepeater(
                    observable_set=obs_set,
                    item_type=item_type,
                    widget_type=field.set_widget_type,
                    widget_args=field.args,
                    widget_kwargs=field.kwargs,
                    widget_props=field.widget_props,
                    bind_expr=plain_bind_expr,
                    sort=field.sort,
                    object_name=computed_object_name,
                    css_classes=field.css_classes,
                    signal_connections=field.signal_connections,
                    parent_widget=widget,
                )
                setattr(widget, name, set_repeater)
                _add_repeater_to_layout(widget, set_repeater, name, field)
                continue
            else:
                raise ValueError(f"Could not resolve bind path '{field.bind}' for field '{name}'")

        # Get the underlying observable from Variable or use source directly
        wrapper: Any = None
        if isinstance(source, Variable):
            wrapper = source.observable
        else:
            wrapper = source

        # Handle ObservableSet -> SetWidgetRepeater
        if isinstance(wrapper, ObservableSet):
            # Determine bind expression: use format= if provided, else "{#self}"
            set_bind_expr: Any = field.set_format if field.set_format is not None else "{#self}"

            set_repeater: SetWidgetRepeater[Any] = SetWidgetRepeater(
                observable_set=wrapper,  # pyright: ignore[reportUnknownArgumentType]
                item_type=None,  # Could extract from type hints if needed
                widget_type=field.set_widget_type,
                widget_args=field.args,
                widget_kwargs=field.kwargs,
                widget_props=field.widget_props,
                bind_expr=set_bind_expr,
                sort=field.sort,
                object_name=computed_object_name,
                css_classes=field.css_classes,
                signal_connections=field.signal_connections,
                parent_widget=widget,
            )
            setattr(widget, name, set_repeater)
            _add_repeater_to_layout(widget, set_repeater, name, field)
            continue

        # Handle Observable containing a set - create synced ObservableSet
        if isinstance(wrapper, Observable):
            val: Any = wrapper.get()  # pyright: ignore[reportUnknownVariableType]
            if isinstance(val, set):
                obs_set = ObservableSet(cast(set[Any], val))

                # Sync: when Observable changes, update ObservableSet
                def make_set_sync(obs: Observable[Any], target: ObservableSet[Any]) -> None:
                    def on_source_change(new_val: Any) -> None:
                        if isinstance(new_val, set):
                            target.clear()
                            target.update(cast(set[Any], new_val))

                    obs.on_change(on_source_change)

                make_set_sync(wrapper, obs_set)  # pyright: ignore[reportUnknownArgumentType]

                # Determine bind expression
                set_bind_expr = field.set_format if field.set_format is not None else "{#self}"

                set_repeater = SetWidgetRepeater(
                    observable_set=obs_set,
                    item_type=item_type,
                    widget_type=field.set_widget_type,
                    widget_args=field.args,
                    widget_kwargs=field.kwargs,
                    widget_props=field.widget_props,
                    bind_expr=set_bind_expr,
                    sort=field.sort,
                    object_name=computed_object_name,
                    css_classes=field.css_classes,
                    signal_connections=field.signal_connections,
                    parent_widget=widget,
                )
                setattr(widget, name, set_repeater)
                _add_repeater_to_layout(widget, set_repeater, name, field)
                continue
            else:
                raise TypeError(f"bind='{field.bind}' resolved to Observable[{type(val).__name__}], expected set")  # pyright: ignore[reportUnknownArgumentType]
        else:
            raise TypeError(f"bind='{field.bind}' resolved to {type(wrapper).__name__}, expected Variable[set[...]] or ObservableSet")


def _connect_signals(widget: Widget[Any], config: _QtPieConfig) -> None:
    """Connect signals declared in new() to handlers."""
    from qtpie.signals import connect_field_signals

    connect_field_signals(widget, config.fields, _create_signal_expression_handler)

    # Connect signals from decorator (e.g., @widget(on_reload="_on_reload"))
    _connect_decorator_signals(widget, config)


def _connect_decorator_signals(widget: Widget[Any], config: _QtPieConfig) -> None:
    """Connect signals declared in @widget decorator.

    For example: @widget(on_reload="_on_reload") connects widget.on_reload to widget._on_reload.
    """
    for signal_name, handler_name in config.signal_connections.items():
        signal = getattr(widget, signal_name, None)
        if signal is None:
            continue

        handler = getattr(widget, handler_name, None)
        if handler is None:
            raise AttributeError(f"{type(widget).__name__} has no method '{handler_name}' for signal connection @widget({signal_name}=\"{handler_name}\")")

        if callable(handler):
            signal.connect(handler)
        else:
            raise AttributeError(f'{type(widget).__name__}.{handler_name} is not callable for signal connection @widget({signal_name}="{handler_name}")')


def _create_signal_expression_handler(widget: Widget[Any], expression: str) -> Callable[..., Any]:
    """Create a signal handler from an expression string like "{my_signal(123)}"."""
    return create_signal_expression_handler(widget, expression, ["#widget", "#self"])


def _detect_required_bindings(cls: type[Widget[Any]]) -> None:
    """Detect bare Variable[T] annotations as required bindings."""
    detect_required_bindings(cls, "_qtpie_config", Variable, _RequiredBindingDescriptor)


def _apply_model_bindings_for_record(widget: Widget[Any], config: _QtPieConfig) -> None:
    """Apply model bindings for QTableView/QListView/etc when record is set.

    Called when the record is set after initial widget creation. Model bindings
    may have failed during init because record was None - retry them now.
    """
    from qtpy.QtWidgets import QComboBox, QListView, QTableView, QTreeView

    from .bindings.model_binding import apply_model_binding
    from .bindings.path import resolve_binding_source

    def is_table_view(w: QWidget) -> bool:
        return isinstance(w, QTableView)

    def is_tree_view(w: QWidget) -> bool:
        return isinstance(w, QTreeView)

    def resolve_or_create_variable(host: QWidget, name: str, item_type: type | None) -> Variable[Any]:
        # Check if variable already exists on host
        existing = getattr(host, name, None)
        if isinstance(existing, Variable):
            return existing  # pyright: ignore[reportReturnType, reportUnknownVariableType]
        # Create new variable
        from observant import Observable

        var: Variable[Any] = Variable(Observable(None))  # pyright: ignore[reportArgumentType]
        setattr(host, name, var)
        return var

    for name, field in config.fields.items():
        if field.bind is None:
            continue

        widget_instance = getattr(widget, name, None)
        if widget_instance is None:
            continue

        # Check if this is a model widget that needs binding
        if not isinstance(widget_instance, (QComboBox, QListView, QTableView, QTreeView)):
            continue

        # Check if model is already set
        existing_model = widget_instance.model() if hasattr(widget_instance, "model") else None
        if existing_model is not None:
            continue

        # Try to resolve the binding source
        source = resolve_binding_source(widget, field.bind)
        if source is None:
            continue

        # Apply the model binding
        apply_model_binding(
            widget,
            widget_instance,
            source,
            field.bind,
            field,
            is_table_view_fn=is_table_view,
            is_tree_view_fn=is_tree_view,
            resolve_or_create_variable_fn=resolve_or_create_variable,
        )


def _add_repeater_to_layout(widget: Widget[Any], repeater: QWidget, field_name: str, field: NewField) -> None:
    """Add a repeater widget to the parent widget's layout.

    Called when creating list/dict/set widget repeaters after the layout is already built.
    Adds the repeater at the correct position based on field order in class annotations.
    """
    # App doesn't have a layout - it's a QApplication, not a QWidget
    if not hasattr(widget, "layout") or not callable(getattr(widget, "layout", None)):
        return

    layout = widget.layout()
    if layout is None:
        return

    # Find the correct insertion position based on field order
    # Get the class annotations to determine where this field should appear
    cls = type(widget)
    annotations = list(getattr(cls, "__annotations__", {}).keys())

    if field_name not in annotations:
        # Field not in annotations, just append
        layout.addWidget(repeater)
        return

    field_index = annotations.index(field_name)

    # Find the widget that should come AFTER this field in the layout
    # by looking at fields that come after this one in annotations
    insert_before_widget: QWidget | None = None
    for i in range(field_index + 1, len(annotations)):
        next_field_name = annotations[i]
        next_widget = getattr(widget, next_field_name, None)
        if isinstance(next_widget, QWidget) and next_widget.parent() is widget:
            # Found a widget that should come after our repeater
            # Find its position in the layout
            for j in range(layout.count()):
                item = layout.itemAt(j)
                if item is not None and item.widget() is next_widget:
                    insert_before_widget = next_widget
                    break
            if insert_before_widget is not None:
                break

    if insert_before_widget is not None:
        # Insert before the next widget
        from qtpy.QtWidgets import QBoxLayout

        if isinstance(layout, QBoxLayout):
            for j in range(layout.count()):
                item = layout.itemAt(j)
                if item.widget() is insert_before_widget:
                    layout.insertWidget(j, repeater)
                    return

    # Fallback: just add at end
    layout.addWidget(repeater)
