# pyright: reportPrivateUsage=false, reportUnknownMemberType=false
"""Dialog - QDialog with QtPie declarative features."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Literal, cast, get_args, get_origin, overload, override

from observant import Observable
from qtpy.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QLayout,
    QPushButton,
    QWidget,
)

from .layout import GridPosition, LayoutType
from .mixins import QtPieComponentBase
from .new_field import NewField
from .new_fields import new_fields
from .signals import create_signal_expression_handler
from .state import QtPieState
from .utils.common import detect_required_bindings
from .utils.layouts import add_to_layout, create_layout
from .variable import Variable, _RequiredBindingDescriptor, _VariableDescriptor
from .widget import IconType

# =============================================================================
# ShowDialog Descriptor - Allows both class method and instance method behavior
# =============================================================================


class _ShowDialogDescriptor[T]:
    """Descriptor that makes show_dialog work as both class method and instance method.

    When called on class: MyDialog.show_dialog() → creates instance and shows
    When called on instance: dialog.show_dialog() → shows the existing instance
    """

    @overload
    def __get__(self, obj: None, objtype: type[Dialog[T]]) -> Callable[..., DialogResult[T]]: ...

    @overload
    def __get__(self, obj: Dialog[T], objtype: type[Dialog[T]] | None) -> Callable[..., DialogResult[T]]: ...

    def __get__(
        self,
        obj: Dialog[T] | None,
        objtype: type[Dialog[T]] | None = None,
    ) -> Callable[..., DialogResult[T]]:
        """Return a callable that shows the dialog.

        Args:
            obj: Instance if called on instance, None if called on class.
            objtype: The class.

        Returns:
            Callable that shows the dialog and returns DialogResult.
        """
        if obj is None:
            # Called on class: MyDialog.show_dialog()
            def class_show_dialog(
                record: T | None = None,
                *,
                parent: QWidget | None = None,
                **kwargs: Any,
            ) -> DialogResult[T]:
                assert objtype is not None
                instance = objtype(**kwargs)  # Forward kwargs to constructor
                if record is not None and hasattr(instance, "record"):
                    instance.record = record  # type: ignore[assignment]
                if parent is not None:
                    instance.setParent(parent)
                return instance._show_dialog()

            return class_show_dialog
        else:
            # Called on instance: dialog.show_dialog()
            def instance_show_dialog() -> DialogResult[T]:
                return obj._show_dialog()

            return instance_show_dialog


# Button type literal for autocomplete support
DialogButtonType = Literal["ok", "cancel", "yes", "no", "save", "discard", "apply", "close", "help", "reset"]

# Map button types to Qt StandardButton
_BUTTON_TYPE_TO_STANDARD: dict[str, QDialogButtonBox.StandardButton] = {
    "ok": QDialogButtonBox.StandardButton.Ok,
    "cancel": QDialogButtonBox.StandardButton.Cancel,
    "yes": QDialogButtonBox.StandardButton.Yes,
    "no": QDialogButtonBox.StandardButton.No,
    "save": QDialogButtonBox.StandardButton.Save,
    "discard": QDialogButtonBox.StandardButton.Discard,
    "apply": QDialogButtonBox.StandardButton.Apply,
    "close": QDialogButtonBox.StandardButton.Close,
    "help": QDialogButtonBox.StandardButton.Help,
    "reset": QDialogButtonBox.StandardButton.Reset,
}

# Map button types to default labels
_BUTTON_TYPE_TO_LABEL: dict[str, str] = {
    "ok": "OK",
    "cancel": "Cancel",
    "yes": "Yes",
    "no": "No",
    "save": "Save",
    "discard": "Discard",
    "apply": "Apply",
    "close": "Close",
    "help": "Help",
    "reset": "Reset",
}

# Map button types to Qt ButtonRole
_BUTTON_TYPE_TO_ROLE: dict[str, QDialogButtonBox.ButtonRole] = {
    "ok": QDialogButtonBox.ButtonRole.AcceptRole,
    "cancel": QDialogButtonBox.ButtonRole.RejectRole,
    "yes": QDialogButtonBox.ButtonRole.YesRole,
    "no": QDialogButtonBox.ButtonRole.NoRole,
    "save": QDialogButtonBox.ButtonRole.AcceptRole,
    "discard": QDialogButtonBox.ButtonRole.DestructiveRole,
    "apply": QDialogButtonBox.ButtonRole.ApplyRole,
    "close": QDialogButtonBox.ButtonRole.RejectRole,
    "help": QDialogButtonBox.ButtonRole.HelpRole,
    "reset": QDialogButtonBox.ButtonRole.ResetRole,
}

# Positive buttons that auto-bind to is_valid by default
_POSITIVE_BUTTON_TYPES = {"ok", "save", "yes", "apply"}


def _normalize_button_name(name: str) -> str:
    """Normalize a button field name to a button type.

    Strips leading underscores so both 'ok' and '_ok' map to 'ok'.
    """
    return name.lstrip("_")


@dataclass
class ButtonInfo:
    """Information about a clicked dialog button."""

    name: str  # Button type: "ok", "cancel", "save", etc.
    text: str  # Actual display label
    role: QDialogButtonBox.ButtonRole


@dataclass
class DialogResult[T = None]:
    """Result returned from show_dialog()."""

    accepted: bool
    button: ButtonInfo | None  # None if closed via X or Escape
    record: T | None  # For Dialog[T]

    @property
    def rejected(self) -> bool:
        """Convenience: True if dialog was rejected."""
        return not self.accepted

    def __bool__(self) -> bool:
        """True if dialog was accepted (OK, Yes, Save, etc.), False if rejected (Cancel, No, X, Escape, etc.)."""
        return self.accepted


class DialogButton:
    """Marker class for dialog buttons.

    Used as a type annotation in @dialog classes to define buttons.
    The field name determines the button type (ok, cancel, save, etc.).

    Examples:
        @dialog
        class MyDialog(Dialog):
            ok: DialogButton  # Bare annotation - uses default "OK" label
            cancel: DialogButton = new("Nope")  # Custom label
            save: DialogButton = new("Save Changes", enabled="{is_valid}")
    """

    pass


@dataclass
class DialogButtonConfig:
    """Configuration for a DialogButton field."""

    name: str  # Field name (e.g., '_ok' or 'ok')
    button_type: str  # Normalized button type (e.g., 'ok') - used for Qt lookup
    label: str | None = None  # Custom label (None = use default)
    enabled: str | None = None  # Binding expression for enabled state
    visible: str | None = None  # Binding expression for visibility
    clicked: str | Callable[..., Any] | None = None  # Signal handler


@dataclass
class DialogConfig:
    """Configuration for @dialog decorator."""

    init_wrapped: bool = False
    auto_bind: bool = True
    widget_props: dict[str, Any] = field(default_factory=lambda: {})
    object_name: str | None = None
    css_classes: list[str] = field(default_factory=lambda: [])
    fields: dict[str, NewField] = field(default_factory=lambda: {})
    variable_names: list[str] = field(default_factory=lambda: [])
    layout: LayoutType = "vertical"
    margins: int | tuple[int, int, int, int] | None = None
    size: tuple[int, int] | None = None
    icon: IconType = None
    record_type: type[Any] | None = None
    record_default: Any | None = None
    required_bindings: set[str] = field(default_factory=lambda: set[str]())
    signal_connections: dict[str, str] = field(default_factory=lambda: {})
    # Dialog-specific: button configurations
    button_configs: list[DialogButtonConfig] = field(default_factory=lambda: [])
    # Whether an explicit DialogButtons/QDialogButtonBox field exists
    has_explicit_button_box: bool = False


class Dialog[T = None](QDialog, QtPieComponentBase):
    """QDialog with QtPie declarative features.

    Similar to Widget/Window but for dialogs. Automatically:
    - Collects DialogButton fields and creates a QDialogButtonBox
    - Processes new() fields for layout
    - Supports Widget[T] style record binding
    - Provides show_dialog() method returning DialogResult

    Example:
        @dialog(title="Edit Person")
        class PersonDialog(Dialog[Person]):
            name: QLineEdit = new(label="Name:")
            age: QSpinBox = new(label="Age:")

            ok: DialogButton = new("Save", enabled="{is_valid}")
            cancel: DialogButton

        # Usage:
        result = PersonDialog.show_dialog(some_person)
        if result.accepted:
            save(result.record)
    """

    _qtpie_config: DialogConfig
    _qtpie: QtPieState
    _clicked_button: ButtonInfo | None = None
    _button_box: QDialogButtonBox | None = None
    _buttons: dict[str, QPushButton]  # Map button type to QPushButton

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        cls._qtpie_config = DialogConfig()

        # Extract T from Dialog[T] if present
        for base in getattr(cls, "__orig_bases__", ()):
            origin = get_origin(base)
            if origin is Dialog:
                args = get_args(base)
                if args:
                    cls._qtpie_config.record_type = args[0]
                break

        # Check if user declared 'record' explicitly
        has_explicit_record = "record" in cls.__dict__

        # Collect NewField instances and DialogButton fields
        _collect_dialog_fields(cls)

        # Detect bare Variable[T] annotations as required bindings
        _detect_required_bindings_for_dialog(cls)

        # Auto-new bare annotations (non-Variable types)
        # DialogButton fields are already marked in config.fields by _collect_dialog_fields
        from .widget_base import _auto_new_bare_annotations

        _auto_new_bare_annotations(cls)

        # Remove DialogButton fields from config.fields BEFORE new_fields runs
        # so new_fields doesn't try to instantiate them as widgets
        button_field_names = {bc.name for bc in cls._qtpie_config.button_configs}
        for name in button_field_names:
            cls._qtpie_config.fields.pop(name, None)
            # Also remove from class __dict__ so new_fields doesn't see them
            if name in cls.__dict__ and isinstance(getattr(cls, name, None), NewField):
                delattr(cls, name)

        # Apply new_fields to handle Variable and QWidget instantiation
        new_fields(cls)

        # Collect variable names (after new_fields converts NewField → _VariableDescriptor)
        for name, value in list(cls.__dict__.items()):
            if isinstance(value, _VariableDescriptor):
                cls._qtpie_config.variable_names.append(name)

        # Auto-create record descriptor if Dialog[T] but no explicit record
        if cls._qtpie_config.record_type is not None and not has_explicit_record:
            from .widget import _RecordDescriptor

            cls.record = _RecordDescriptor(cls._qtpie_config.record_type)  # type: ignore[assignment]

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Check that @dialog decorator was applied."""
        if not self._qtpie_config.init_wrapped:
            raise TypeError(f"{type(self).__name__} must be decorated with @dialog")
        super().__init__(*args, **kwargs)

    if TYPE_CHECKING:
        # Lie to pyright: say record returns T for field autocomplete
        @property
        def record(self) -> T: ...
        @record.setter
        def record(self, value: T) -> None: ...

        @property
        def record_value(self) -> T:
            """Get the raw record value, unwrapped from the ObservableProxy."""
            ...

    if not TYPE_CHECKING:

        def __getattr__(self, name: str) -> Any:
            """Handle attribute access for special cases."""
            if name == "record":
                raise TypeError(f"{type(self).__name__} has no record type. Use Dialog[YourModel] to enable record access.")
            if name == "record_value":
                if hasattr(self, "_qtpie") and self._qtpie._record is not None:
                    return self._qtpie._record.value
                raise AttributeError(f"{type(self).__name__} has no record type. Use Dialog[YourModel] to enable record_value access.")
            raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")

    # -------------------------------------------------------------------------
    # Lifecycle Hooks
    # -------------------------------------------------------------------------

    def on_accept(self) -> bool:
        """Hook called before accepting the dialog.

        Return False to prevent the dialog from closing.
        Default implementation returns True (allow accept).

        Example:
            def on_accept(self) -> bool:
                if not self.is_valid.get():
                    return False  # Prevent closing
                return True
        """
        return True

    def on_reject(self) -> bool:
        """Hook called before rejecting the dialog.

        Return False to prevent the dialog from closing.
        Default implementation returns True (allow reject).

        Example:
            def on_reject(self) -> bool:
                if self.is_dirty.get():
                    return self.confirm_discard()
                return True
        """
        return True

    # -------------------------------------------------------------------------
    # Override accept/reject to call hooks
    # -------------------------------------------------------------------------

    @override
    def accept(self) -> None:
        """Override to call on_accept hook before accepting."""
        if self.on_accept():
            super().accept()

    @override
    def reject(self) -> None:
        """Override to call on_reject hook before rejecting."""
        if self.on_reject():
            super().reject()

    # -------------------------------------------------------------------------
    # show_dialog() - Works as both class method and instance method
    # -------------------------------------------------------------------------

    # Descriptor allows both:
    #   MyDialog.show_dialog()     -> creates instance, shows it
    #   dialog.show_dialog()       -> shows existing instance
    show_dialog: _ShowDialogDescriptor[T] = _ShowDialogDescriptor()

    def _show_dialog(self) -> DialogResult[T]:
        """Internal method that actually executes the dialog.

        Tests can override this to avoid blocking exec().
        """
        result_code = QDialog.DialogCode(self.exec())
        return self._build_result(result_code)

    def _build_result(self, result_code: QDialog.DialogCode) -> DialogResult[T]:
        """Build DialogResult from exec() return code.

        This is a separate method so tests can call it directly.
        """
        accepted = result_code == QDialog.DialogCode.Accepted

        # Get record if available
        record: T | None = None
        if hasattr(self, "_qtpie") and self._qtpie._record is not None:
            record = cast(T, self._qtpie._record.value)

        return DialogResult(
            accepted=accepted,
            button=self._clicked_button,
            record=record,
        )

    def _simulate_button_click(self, button_type: str) -> None:
        """Simulate a button click (for testing).

        Sets _clicked_button as if the user clicked that button.
        """
        self._clicked_button = self._get_button_info(button_type)

    def _get_button_info(self, button_type: str) -> ButtonInfo | None:
        """Get ButtonInfo for a button type."""
        if button_type not in _BUTTON_TYPE_TO_ROLE:
            return None

        # Get the actual button to find its label
        btn = self._buttons.get(button_type)
        if btn is not None:
            label = btn.text()
        else:
            label = _BUTTON_TYPE_TO_LABEL.get(button_type, button_type)

        return ButtonInfo(
            name=button_type,
            text=label,
            role=_BUTTON_TYPE_TO_ROLE[button_type],
        )

    def _get_button(self, button_type: str) -> QPushButton | None:
        """Get the QPushButton for a button type (for testing)."""
        return self._buttons.get(button_type)


def _collect_dialog_fields(cls: type[Dialog[Any]]) -> None:
    """Collect NewField instances and DialogButton fields from class."""
    config = cls._qtpie_config
    annotations = getattr(cls, "__annotations__", {})

    for name in annotations:
        annotation = annotations[name]
        value = getattr(cls, name, None)

        # Check for DialogButton annotation
        if annotation is DialogButton or (hasattr(annotation, "__origin__") and getattr(annotation, "__origin__", None) is DialogButton):
            # Validate button type (normalize to strip leading underscores)
            button_type = _normalize_button_name(name)
            if button_type not in _BUTTON_TYPE_TO_STANDARD:
                raise TypeError(f"Invalid DialogButton field name '{name}'. Must be one of: {', '.join(_BUTTON_TYPE_TO_STANDARD.keys())} (underscore prefix allowed)")

            # Extract configuration from NewField if present
            label: str | None = None
            enabled: str | None = None
            visible: str | None = None
            clicked: str | Callable[..., Any] | None = None

            if isinstance(value, NewField):
                # Get custom label from positional args
                if value.args:
                    label = str(value.args[0])
                # Get bindings from kwargs
                enabled = value.kwargs.get("enabled")
                visible = value.kwargs.get("visible")
                clicked = value.kwargs.get("clicked")
                # Mark as processed so _auto_new_bare_annotations skips it
                # but DON'T add to config.fields - we don't want new_fields to instantiate it
                config.fields[name] = value  # Mark in fields to skip auto-new
            else:
                # Bare annotation - set a placeholder NewField so _auto_new_bare_annotations skips it
                # We don't need to actually create a widget, just prevent auto-new
                placeholder = NewField()
                setattr(cls, name, placeholder)
                config.fields[name] = placeholder  # Mark as processed

            config.button_configs.append(
                DialogButtonConfig(
                    name=name,
                    button_type=button_type,
                    label=label,
                    enabled=enabled,
                    visible=visible,
                    clicked=clicked,
                )
            )

        elif isinstance(value, NewField):
            config.fields[name] = value

            # Check if it's an explicit button box
            field_type = value.field_type
            if field_type is not None:
                try:
                    if issubclass(field_type, (QDialogButtonBox, DialogButtons)):
                        config.has_explicit_button_box = True
                except TypeError:
                    # field_type is not a class (e.g., a generic alias)
                    pass


def _detect_required_bindings_for_dialog(cls: type[Dialog[Any]]) -> None:
    """Detect bare Variable[T] annotations as required bindings."""
    detect_required_bindings(cls, "_qtpie_config", Variable, _RequiredBindingDescriptor)


@overload
def dialog[D: Dialog[Any]](cls: type[D]) -> type[D]: ...


@overload
def dialog[D: Dialog[Any]](
    cls: None = None,
    *,
    title: str | None = None,
    icon: IconType = None,
    layout: LayoutType = "vertical",
    margins: int | tuple[int, int, int, int] | None = None,
    size: tuple[int, int] | None = None,
    auto_bind: bool = True,
    name: str | None = None,
    classes: list[str] | None = None,
    record: Any | None = None,
    **kwargs: Any,
) -> Callable[[type[D]], type[D]]: ...


def dialog[D: Dialog[Any]](
    cls: type[D] | None = None,
    *,
    title: str | None = None,
    icon: IconType = None,
    layout: LayoutType = "vertical",
    margins: int | tuple[int, int, int, int] | None = None,
    size: tuple[int, int] | None = None,
    auto_bind: bool = True,
    name: str | None = None,
    classes: list[str] | None = None,
    record: Any | None = None,
    stylesheet: str | None = None,
    **kwargs: Any,
) -> type[D] | Callable[[type[D]], type[D]]:
    """Decorator for Dialog classes.

    Usage:
        @dialog
        class MyDialog(Dialog):
            ok: DialogButton
            cancel: DialogButton

        @dialog(title="Edit Person")
        class PersonDialog(Dialog[Person]):
            name: QLineEdit = new(label="Name:")
            ok: DialogButton = new("Save", enabled="{is_valid}")
            cancel: DialogButton

    Args:
        title: Dialog window title. Can be reactive: title="{_title}".
        icon: Window icon. Can be a path string, QIcon, or QPixmap.
        layout: "vertical" | "horizontal" | "form" | "grid" | None
        margins: Layout margins. int applies to all sides.
        auto_bind: If True (default), enable auto-binding for Variables.
        name: Set the dialog's objectName.
        classes: List of CSS classes to apply.
        record: Initial record value for Dialog[T].
        stylesheet: Shorthand for styleSheet.
        **kwargs: Extra properties applied via setXXX() methods.
    """
    if title is not None:
        kwargs["windowTitle"] = title
    if stylesheet is not None:
        kwargs["styleSheet"] = stylesheet

    def decorator(target: type[D]) -> type[D]:
        from qtpie.utils.common import is_signal_on_type

        config = target._qtpie_config

        # Extract signal connections from kwargs
        signal_connections: dict[str, str] = {}
        widget_props: dict[str, Any] = {}
        for key, value in kwargs.items():
            if is_signal_on_type(key, target) and isinstance(value, str):
                signal_connections[key] = value
            else:
                widget_props[key] = value

        config.layout = layout
        config.margins = margins
        config.size = size
        config.icon = icon
        config.auto_bind = auto_bind
        config.record_default = record
        config.widget_props = widget_props
        config.object_name = name
        config.css_classes = classes or []
        config.signal_connections = signal_connections

        # Wrap __init__
        _wrap_init_for_dialog(target)

        return target

    if cls is not None:
        return decorator(cls)

    return decorator  # type: ignore[return-value]


def _wrap_init_for_dialog(cls: type[Dialog[Any]]) -> None:
    """Wrap __init__ to create layout, add widgets, create button box, and call __setup__."""
    if cls._qtpie_config.init_wrapped:
        return

    original_init = cls.__init__
    config = cls._qtpie_config

    def wrapped_init(self: Dialog[Any], *args: Any, **kwargs: Any) -> None:
        # Extract _qtpie_bindings before passing kwargs to original init
        _qtpie_bindings = kwargs.pop("_qtpie_bindings", None)

        # Extract Variable kwargs (match against variable_names and required_bindings)
        variable_kwargs: dict[str, Any] = {}
        all_variable_names = set(config.variable_names) | config.required_bindings
        for var_name in all_variable_names:
            if var_name in kwargs:
                variable_kwargs[var_name] = kwargs.pop(var_name)

        # Set translation context
        from qtpie.translations import set_translation_context

        set_translation_context(type(self).__name__)

        # Initialize QtPieState early so Variables have somewhere to register
        if not hasattr(self, "_qtpie"):
            self._qtpie = QtPieState(self)

        # Apply parent variable bindings BEFORE original_init runs
        if _qtpie_bindings is not None:
            parent, bindings = _qtpie_bindings
            from .new_fields import _apply_variable_bindings_direct

            _apply_variable_bindings_direct(parent, self, bindings)

        # Apply constructor variable kwargs
        if variable_kwargs:
            from .new_fields import apply_variable_kwargs

            apply_variable_kwargs(self, variable_kwargs)

        # Call original __init__
        original_init(self, *args, **kwargs)

        # Initialize buttons dict
        self._buttons = {}

        # Create list widget fields
        from .widget import _create_list_widget_fields

        _create_list_widget_fields(self, config)  # type: ignore[arg-type]

        # Apply widget properties
        from .bindings import is_format_string
        from .translations.translatable import Translatable
        from .utils.layouts import apply_object_name_and_classes, apply_widget_props

        def skip_reactive_or_translatable(prop_name: str, value: Any) -> bool:
            if isinstance(value, str) and is_format_string(value):
                return True
            if isinstance(value, Translatable):
                return True
            return False

        apply_widget_props(self, config.widget_props, skip_filter=skip_reactive_or_translatable)

        # Apply objectName and CSS classes
        apply_object_name_and_classes(
            self,
            config.object_name,
            config.css_classes,
            default_name=type(self).__name__,
        )

        # Apply initial size
        if config.size is not None:
            self.resize(*config.size)

        # Apply icon (inherit from active window if not specified)
        # - None: inherit from active window
        # - False: explicitly no icon (opt-out)
        # - other: use specified icon
        if config.icon is False:
            pass  # Explicit opt-out, no icon
        elif config.icon is not None:
            from .utils.layouts import resolve_icon

            resolved_icon = resolve_icon(config.icon)
            if resolved_icon is not None:
                self.setWindowIcon(resolved_icon)
        else:
            # Try to inherit icon from active window
            from qtpy.QtWidgets import QApplication

            active_window = QApplication.activeWindow()
            if active_window is not None:
                parent_icon = active_window.windowIcon()
                if not parent_icon.isNull():
                    self.setWindowIcon(parent_icon)

        # Set up layout if configured
        if config.layout is not None:
            qt_layout = create_layout(config.layout)
            if qt_layout is not None:
                self.setLayout(qt_layout)

                # Apply margins
                from .utils.layouts import apply_layout_margins

                apply_layout_margins(qt_layout, config.margins)

                # Track nested layouts
                nested_layouts: dict[str, QLayout] = {}

                # First pass: Create nested layouts
                for name in getattr(cls, "__annotations__", {}):
                    # Skip DialogButton fields
                    if any(bc.name == name for bc in config.button_configs):
                        continue
                    if name in config.fields:
                        field = config.fields[name]
                        if field.is_nested_layout:
                            layout_instance = field.field_type(*field.args, **field.kwargs)  # type: ignore[misc]
                            setattr(self, name, layout_instance)
                            nested_layouts[name] = layout_instance

                # Second pass: Add widgets to layout (excluding DialogButton fields)
                from qtpie.layout import Stretch

                from .widget import (
                    _add_layout_to_nested_layout,
                    _add_spacer_to_layout,
                    _add_stretch_to_layout,
                    _add_widget_to_nested_layout,
                    _create_spacer_item,
                    _get_target_layout,
                    _validate_layout_params,
                )

                for name in getattr(cls, "__annotations__", {}):
                    # Skip DialogButton fields - they go in button box at end
                    if any(bc.name == name for bc in config.button_configs):
                        continue

                    annotation = getattr(cls, "__annotations__", {}).get(name)

                    # Handle bare Stretch annotation
                    if annotation is Stretch and name not in config.fields:
                        _add_stretch_to_layout(qt_layout, 1)
                        continue

                    if name in config.fields:
                        field = config.fields[name]
                        if field.exclude_from_layout:
                            continue

                        # Handle nested layouts
                        if field.is_nested_layout:
                            layout_instance = nested_layouts.get(name)
                            if layout_instance is not None:
                                target = _get_target_layout(qt_layout, nested_layouts, field.target_layout)
                                if target is not None:
                                    _add_layout_to_nested_layout(target, layout_instance, field.grid, name)
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
                            label: str | None = None
                            label_translatable: Any = None
                            grid: GridPosition | None = None

                            if isinstance(field.label, Translatable):
                                label = field.label.resolve()
                                label_translatable = field.label
                            else:
                                label = field.label
                            grid = field.grid

                            if field.target_layout is None:
                                _validate_layout_params(name, config.layout, label, grid)
                                _add_to_layout(target, widget_instance, config.layout, label, grid, label_translatable)
                            else:
                                _add_widget_to_nested_layout(target, widget_instance, label, grid, name)

                    # Check if it's a Variable with a widget
                    elif name in config.variable_names:
                        var = getattr(self, name, None)
                        if isinstance(var, Variable) and var.widget is not None:
                            descriptor = getattr(cls, name, None)
                            var_label: str | None = None
                            var_label_translatable: Any = None
                            grid: GridPosition | None = None
                            target_layout_name: str | None = None
                            is_format_label = False
                            raw_label: Any = None
                            if isinstance(descriptor, _VariableDescriptor):
                                if descriptor.exclude_from_layout:
                                    continue
                                raw_label = descriptor.label
                                if isinstance(raw_label, Translatable):
                                    var_label = raw_label.resolve()
                                    var_label_translatable = raw_label
                                elif isinstance(raw_label, str) and "{" in raw_label and "}" in raw_label:
                                    # Format string label like "{kind}" - use placeholder, will be set by binding
                                    # Use space (not empty string) so Qt creates the QLabel widget
                                    var_label = " "  # Placeholder - binding sets initial value immediately
                                    is_format_label = True
                                else:
                                    var_label = raw_label
                                grid = descriptor.grid  # type: ignore[assignment]
                                target_layout_name = descriptor.target_layout

                            target = _get_target_layout(qt_layout, nested_layouts, target_layout_name)
                            if target is None:
                                continue

                            if target_layout_name is None:
                                _validate_layout_params(name, config.layout, var_label, grid)
                                _add_to_layout(target, var.widget, config.layout, var_label, grid, var_label_translatable)

                                # Apply format binding to form label if it was a format string
                                if is_format_label and config.layout == "form" and isinstance(raw_label, str):
                                    from qtpy.QtWidgets import QFormLayout

                                    from .bindings import create_format_binding

                                    form_layout = cast(QFormLayout, target)
                                    label_widget = form_layout.labelForField(var.widget)
                                    if label_widget is not None:  # pyright: ignore[reportUnnecessaryComparison] - Qt returns None for spanningWidget
                                        create_format_binding(self, raw_label, label_widget.setText)  # type: ignore[union-attr]
                            else:
                                _add_widget_to_nested_layout(target, var.widget, var_label, grid, name)

                # Create button box at END of layout (if not explicit)
                if not config.has_explicit_button_box and config.button_configs:
                    button_box = _create_button_box(self, config)
                    self._button_box = button_box
                    qt_layout.addWidget(button_box)

        # Ensure QtPieState exists
        if not hasattr(self, "_qtpie"):
            self._qtpie = QtPieState(self)

        # Register validators
        from .widget import _register_validators

        _register_validators(self, config)  # type: ignore[arg-type]

        # Set initial record value if provided
        if config.record_default is not None and hasattr(self, "record"):
            self.record = config.record_default

        # Call __setup__ hook
        setup_method = getattr(self, "__setup__", None)
        if setup_method is not None:
            setup_method()

        # Apply bindings
        from .bindings.apply import apply_auto_bindings, apply_property_bindings, apply_reactive_widget_props, pre_create_selection_variables
        from .bindings.expression import create_expression_binding

        pre_create_selection_variables(self, config)
        apply_auto_bindings(self, config)
        apply_property_bindings(self, config, create_expression_binding_fn=create_expression_binding)
        apply_reactive_widget_props(self, config)

        # Apply button bindings (enabled, visible)
        _apply_button_bindings(self, config)

        # Connect signals for fields
        from qtpie.signals import connect_field_focus_handlers, connect_field_signals

        connect_field_signals(self, config.fields, _create_dialog_signal_expression_handler)
        connect_field_focus_handlers(self, config.fields)

        # Connect signals from decorator
        _connect_decorator_signals(self, config)

        # Enable hooks
        self._qtpie.enable_dirty_hook()
        self._qtpie.enable_valid_hook()

    cls.__init__ = wrapped_init  # type: ignore[method-assign]
    cls._qtpie_config.init_wrapped = True


def _create_button_box(dialog: Dialog[Any], config: DialogConfig) -> QDialogButtonBox:
    """Create QDialogButtonBox from button configurations."""
    button_box = QDialogButtonBox()

    # Create a click handler factory outside the loop to satisfy ruff B023
    def make_click_handler(button_type: str) -> Callable[[], None]:
        def click_handler() -> None:
            dialog._clicked_button = dialog._get_button_info(button_type)

        return click_handler

    for btn_config in config.button_configs:
        # Get standard button using normalized button_type
        standard_btn = _BUTTON_TYPE_TO_STANDARD.get(btn_config.button_type)
        if standard_btn is None:
            continue

        # Add button to box - always returns QPushButton for StandardButton
        btn = button_box.addButton(standard_btn)

        # Set custom label if provided
        if btn_config.label is not None:
            btn.setText(btn_config.label)

        # Store reference by button_type (so _get_button("ok") works for both "ok" and "_ok" fields)
        dialog._buttons[btn_config.button_type] = btn

        # Connect clicked handler if provided
        if btn_config.clicked is not None:
            if isinstance(btn_config.clicked, str):
                user_handler = getattr(dialog, btn_config.clicked, None)
                if user_handler is not None and callable(user_handler):
                    btn.clicked.connect(user_handler)
            elif callable(btn_config.clicked):
                btn.clicked.connect(btn_config.clicked)

        # Track which button was clicked
        btn.clicked.connect(make_click_handler(btn_config.button_type))

    # Connect button box signals to dialog accept/reject
    button_box.accepted.connect(dialog.accept)
    button_box.rejected.connect(dialog.reject)

    return button_box


def _apply_button_bindings(dialog: Dialog[Any], config: DialogConfig) -> None:
    """Apply enabled/visible bindings to buttons."""
    from .bindings.expression import create_expression_binding

    for btn_config in config.button_configs:
        btn = dialog._buttons.get(btn_config.button_type)
        if btn is None:
            continue

        # Apply enabled binding
        enabled_expr = btn_config.enabled
        if enabled_expr is None and btn_config.button_type in _POSITIVE_BUTTON_TYPES:
            # Auto-bind positive buttons to is_valid
            enabled_expr = "{is_valid}"

        if enabled_expr is not None:
            if enabled_expr.startswith("{") and enabled_expr.endswith("}"):

                def make_enabled_handler(button: QPushButton) -> Callable[[Any], None]:
                    def handler(value: Any) -> None:
                        button.setEnabled(bool(value))

                    return handler

                create_expression_binding(dialog, enabled_expr, make_enabled_handler(btn))
            else:
                # Simple variable reference
                from .variable import _get_variable_observable

                obs = _get_variable_observable(dialog, enabled_expr)
                if obs is not None:

                    def make_obs_handler(button: QPushButton, observable: Observable[Any]) -> None:
                        def on_change(value: Any) -> None:
                            button.setEnabled(bool(value))

                        observable.on_change(on_change)
                        on_change(observable.get())

                    make_obs_handler(btn, obs)

        # Apply visible binding
        if btn_config.visible is not None:
            if btn_config.visible.startswith("{") and btn_config.visible.endswith("}"):

                def make_visible_handler(button: QPushButton) -> Callable[[Any], None]:
                    def handler(value: Any) -> None:
                        button.setVisible(bool(value))

                    return handler

                create_expression_binding(dialog, btn_config.visible, make_visible_handler(btn))
            else:
                from .variable import _get_variable_observable

                obs = _get_variable_observable(dialog, btn_config.visible)
                if obs is not None:

                    def make_vis_handler(button: QPushButton, observable: Observable[Any]) -> None:
                        def on_change(value: Any) -> None:
                            button.setVisible(bool(value))

                        observable.on_change(on_change)
                        on_change(observable.get())

                    make_vis_handler(btn, obs)


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


def _create_dialog_signal_expression_handler(dialog: Dialog[Any], expression: str) -> Callable[..., Any]:
    """Create a signal handler from an expression string."""
    return create_signal_expression_handler(dialog, expression, ["#dialog", "#widget", "#self"])


def _connect_decorator_signals(dialog: Dialog[Any], config: DialogConfig) -> None:
    """Connect signals defined in @dialog decorator kwargs."""
    from .utils.common import is_signal

    for signal_name, handler_name in config.signal_connections.items():
        signal = getattr(dialog, signal_name, None)
        if signal is None:
            continue

        if not is_signal(signal):
            continue

        handler = getattr(dialog, handler_name, None)
        if handler is None:
            raise AttributeError(f"Handler '{handler_name}' not found on {type(dialog).__name__} for signal '{signal_name}'")

        if callable(handler):
            signal.connect(handler)


# =============================================================================
# DialogButtons class and @buttons decorator
# =============================================================================


@dataclass
class DialogButtonsConfig:
    """Configuration for @buttons decorator."""

    init_wrapped: bool = False
    button_configs: list[DialogButtonConfig] = field(default_factory=lambda: [])
    variable_names: list[str] = field(default_factory=lambda: [])


class DialogButtons(QDialogButtonBox):
    """QDialogButtonBox with QtPie features.

    Used for custom button box positioning in dialogs.

    Example:
        @buttons
        class MyButtons(DialogButtons):
            ok: DialogButton = new("Save")
            cancel: DialogButton

        @dialog
        class MyDialog(Dialog):
            header: QLabel = new("Header")
            buttons: MyButtons = new()  # Positioned HERE
            footer: QLabel = new("Footer")
    """

    _qtpie_buttons_config: DialogButtonsConfig
    _buttons: dict[str, QPushButton]

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        cls._qtpie_buttons_config = DialogButtonsConfig()

        # Collect DialogButton fields
        _collect_dialog_buttons_fields(cls)

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        if not self._qtpie_buttons_config.init_wrapped:
            raise TypeError(f"{type(self).__name__} must be decorated with @buttons")
        super().__init__(*args, **kwargs)

    def _get_button(self, button_type: str) -> QPushButton | None:
        """Get the QPushButton for a button type."""
        return self._buttons.get(button_type)


def _collect_dialog_buttons_fields(cls: type[DialogButtons]) -> None:
    """Collect DialogButton fields from a DialogButtons class."""
    config = cls._qtpie_buttons_config
    annotations = getattr(cls, "__annotations__", {})

    for name in annotations:
        annotation = annotations[name]
        value = getattr(cls, name, None)

        if annotation is DialogButton:
            # Validate button type (normalize to strip leading underscores)
            button_type = _normalize_button_name(name)
            if button_type not in _BUTTON_TYPE_TO_STANDARD:
                raise TypeError(f"Invalid DialogButton field name '{name}'. Must be one of: {', '.join(_BUTTON_TYPE_TO_STANDARD.keys())} (underscore prefix allowed)")

            label: str | None = None
            enabled: str | None = None
            visible: str | None = None
            clicked: str | Callable[..., Any] | None = None

            if isinstance(value, NewField):
                if value.args:
                    label = str(value.args[0])
                enabled = value.kwargs.get("enabled")
                visible = value.kwargs.get("visible")
                clicked = value.kwargs.get("clicked")

            config.button_configs.append(
                DialogButtonConfig(
                    name=name,
                    button_type=button_type,
                    label=label,
                    enabled=enabled,
                    visible=visible,
                    clicked=clicked,
                )
            )


@overload
def buttons[B: DialogButtons](cls: type[B]) -> type[B]: ...


@overload
def buttons[B: DialogButtons](
    cls: None = None,
) -> Callable[[type[B]], type[B]]: ...


def buttons[B: DialogButtons](
    cls: type[B] | None = None,
) -> type[B] | Callable[[type[B]], type[B]]:
    """Decorator for DialogButtons classes.

    Usage:
        @buttons
        class MyButtons(DialogButtons):
            ok: DialogButton = new("Save")
            cancel: DialogButton
    """

    def decorator(target: type[B]) -> type[B]:
        _wrap_init_for_dialog_buttons(target)
        return target

    if cls is not None:
        return decorator(cls)

    return decorator  # type: ignore[return-value]


def _wrap_init_for_dialog_buttons(cls: type[DialogButtons]) -> None:
    """Wrap __init__ to create buttons."""
    if cls._qtpie_buttons_config.init_wrapped:
        return

    original_init = cls.__init__
    config = cls._qtpie_buttons_config

    def wrapped_init(self: DialogButtons, *args: Any, **kwargs: Any) -> None:
        original_init(self, *args, **kwargs)
        self._buttons = {}

        # Create buttons
        for btn_config in config.button_configs:
            standard_btn = _BUTTON_TYPE_TO_STANDARD.get(btn_config.button_type)
            if standard_btn is None:
                continue

            btn = self.addButton(standard_btn)

            if btn_config.label is not None:
                btn.setText(btn_config.label)

            self._buttons[btn_config.button_type] = btn

            # Connect clicked handler
            if btn_config.clicked is not None:
                if isinstance(btn_config.clicked, str):
                    handler = getattr(self, btn_config.clicked, None)
                    if handler is not None and callable(handler):
                        btn.clicked.connect(handler)
                elif callable(btn_config.clicked):
                    btn.clicked.connect(btn_config.clicked)

    cls.__init__ = wrapped_init  # type: ignore[method-assign]
    cls._qtpie_buttons_config.init_wrapped = True
