# pyright: reportPrivateUsage=false
# pyright: reportUnknownMemberType=false
"""App class - a QApplication subclass with lifecycle hooks and qasync support."""

import asyncio
import signal
import sys
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, NoReturn, overload

import qasync  # type: ignore[import-untyped]
from observant import Observable
from qtpy.QtCore import QTimer
from qtpy.QtGui import QIcon, QPixmap
from qtpy.QtWidgets import (
    QApplication,
    QDockWidget,
    QLayout,
    QMainWindow,
    QMenu,
    QStyle,
    QSystemTrayIcon,
    QWidget,
)

from qtpie.layout import GridPosition, LayoutType
from qtpie.new_field import NewField
from qtpie.signals import create_signal_expression_handler
from qtpie.styles.color_scheme import ColorScheme, apply_deferred_color_scheme, set_color_scheme
from qtpie.styles.loader import load_stylesheet as _load_stylesheet
from qtpie.utils.layouts import add_to_layout, create_layout, resolve_icon
from qtpie.widget import _validate_layout_params


@dataclass
class AppConfig:
    """Configuration for @app decorator."""

    init_wrapped: bool = False
    auto_bind: bool = True
    widget_props: dict[str, Any] = field(default_factory=lambda: {})
    object_name: str | None = None
    css_classes: list[str] = field(default_factory=lambda: [])
    # Track fields for signal connections and handling
    fields: dict[str, NewField] = field(default_factory=lambda: {})
    variable_names: list[str] = field(default_factory=lambda: [])
    # Dock fields - field names that are Dock[T] types
    dock_fields: list[str] = field(default_factory=lambda: [])
    variable_dock_fields: list[str] = field(default_factory=lambda: [])
    # Dock area corner assignments
    corners: dict[str, str] | None = None
    # Dock locked binding
    docks_locked: str | None = None

    # Layout configuration for auto-Window's central widget
    layout: LayoutType = "vertical"
    margins: int | tuple[int, int, int, int] | None = None

    # Feature toggles
    window: bool = True  # Auto-create Window for QWidget/QMenu fields
    system_tray: bool | None = None  # None=auto (only if QActions/system_tray field), True=force, False=never
    show: bool = True  # Auto-show window in run()
    minimize_to_tray: bool = True  # If True, closing window hides to tray instead of quitting

    # Icon settings (str path, QIcon, QPixmap, or QStyle.StandardPixmap)
    icon: str | QIcon | QPixmap | QStyle.StandardPixmap | None = None  # Sets BOTH window_icon AND tray_icon (fallback)
    window_icon: str | QIcon | QPixmap | QStyle.StandardPixmap | None = None  # Window icon only (overrides icon=)
    tray_icon: str | QIcon | QPixmap | QStyle.StandardPixmap | None = None  # Tray icon only (overrides icon=)

    # Record type from App[T]
    record_type: type[Any] | None = None
    # Initial record value from @app(record=...)
    record_default: Any | None = None
    # Required bindings - bare Variable[T] fields that must be provided
    required_bindings: set[str] = field(default_factory=lambda: set[str]())

    # For AppBase: track if we're in a real QApplication context
    is_qapplication: bool = False


def run_app(app: QApplication) -> int:
    """
    Run a QApplication with qasync event loop.

    This is a standalone helper that can be used with any QApplication,
    not just the App class. It sets up qasync and runs until the app quits.

    Args:
        app: The QApplication instance to run.

    Returns:
        The application exit code (always 0 currently).

    Example:
        from qtpy.QtWidgets import QApplication, QLabel

        app = QApplication([])
        label = QLabel("Hello")
        label.show()
        run_app(app)  # Blocks until app quits
    """
    loop = qasync.QEventLoop(app)
    asyncio.set_event_loop(loop)

    quit_event = asyncio.Event()
    app.aboutToQuit.connect(quit_event.set)

    # Handle CTRL-C gracefully
    def handle_sigint(*_: object) -> None:
        app.quit()

    signal.signal(signal.SIGINT, handle_sigint)

    # Timer to let Python process signals (Qt blocks them otherwise)
    signal_timer = QTimer()
    signal_timer.timeout.connect(lambda: None)  # Just let Python run
    signal_timer.start(100)

    with loop:
        loop.run_until_complete(quit_event.wait())  # pyright: ignore[reportUnknownMemberType]

    return 0


# Forward declaration for type hints - actual class defined below
# This is needed because _collect_fields_for_app is called in AppBase.__init_subclass__
# before the App class is fully defined


def _collect_fields_for_app(cls: type) -> None:
    """Collect NewField instances from class before they're processed."""
    from qtpie.variable import _VariableDescriptor

    config: AppConfig = cls._qtpie_config  # type: ignore[attr-defined]
    for name in getattr(cls, "__annotations__", {}):
        value = getattr(cls, name, None)
        if isinstance(value, NewField):
            config.fields[name] = value  # pyright: ignore[reportUnknownMemberType]
            # Track dock fields separately (after __set_name__ has run, is_dock is set)
            if value.is_dock:
                config.dock_fields.append(name)
        # Check for Variable[T, Dock[W]] descriptors
        elif isinstance(value, _VariableDescriptor) and value.dock_info is not None:
            config.variable_dock_fields.append(name)


def _detect_required_bindings_for_app(cls: type) -> None:
    """Detect bare Variable[T] annotations as required bindings for App."""
    from qtpie.utils.common import detect_required_bindings
    from qtpie.variable import Variable, _RequiredBindingDescriptor

    detect_required_bindings(cls, "_qtpie_config", Variable, _RequiredBindingDescriptor)


class AppBase[T = None]:
    """
    Base class with declarative features for App.

    This class contains all the declarative logic (fields, dirty tracking,
    validation, lifecycle hooks) but does NOT inherit from QApplication.
    Use this for testing or when you need the declarative features without
    a QApplication.

    For actual applications, use App which inherits from both AppBase and QApplication.

    Features:
    - Declarative fields: Variables, QWidgets, QMenus, QActions
    - Auto-created Window for QWidget/QMenu fields
    - System tray support
    - Lifecycle hooks: __setup__()
    - Dirty tracking and validation

    Examples:
        # For testing (no QApplication needed):
        @app
        class MyAppBase(AppBase):
            _count: Variable[int] = new(0)
            _label: QLabel = new("Hello")

        app = MyAppBase()  # Works without QApplication!
        app._count.value = 5
        assert app.is_dirty.get() == True

        # For real apps, use App instead:
        @app
        class MyApp(App):
            ...
    """

    _qtpie_config: AppConfig

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        # Each subclass gets its own config
        cls._qtpie_config = AppConfig()

        # Check if this is a QApplication subclass
        cls._qtpie_config.is_qapplication = issubclass(cls, QApplication)

        # Extract T from AppBase[T] or App[T] if present
        from typing import TypeVar, get_args, get_origin

        for base in getattr(cls, "__orig_bases__", ()):
            origin = get_origin(base)
            if origin is AppBase or origin is App:
                args = get_args(base)
                # Only set record_type if T is a concrete type, not a TypeVar or None
                if args and args[0] is not type(None) and not isinstance(args[0], TypeVar):
                    cls._qtpie_config.record_type = args[0]
                break

        # Check if user declared 'record' explicitly
        has_explicit_record = "record" in cls.__dict__

        # Collect NewField instances before they're processed
        _collect_fields_for_app(cls)

        # Apply new_fields to handle Variable and QWidget instantiation
        from qtpie.new_fields import new_fields

        new_fields(cls)

        # Detect bare Variable[T] annotations (no = new())
        # These are required bindings - must be provided by parent or created for selection bindings
        _detect_required_bindings_for_app(cls)

        # Collect variable names (after new_fields converts NewField → _VariableDescriptor)
        from qtpie.variable import _VariableDescriptor

        for name, value in list(cls.__dict__.items()):
            if isinstance(value, _VariableDescriptor):
                cls._qtpie_config.variable_names.append(name)

        # Auto-create record descriptor if App[T] but no explicit record
        if cls._qtpie_config.record_type is not None and not has_explicit_record:
            from qtpie.widget import _RecordDescriptor

            cls.record = _RecordDescriptor(cls._qtpie_config.record_type)  # type: ignore[assignment]

    if TYPE_CHECKING:
        # Lie to pyright: say record returns T for field autocomplete
        @property
        def record(self) -> T: ...
        @record.setter
        def record(self, value: T) -> None: ...

    if not TYPE_CHECKING:
        # Runtime-only: provide better error messages for .record access
        # Hidden from pyright so it doesn't disable attribute checking
        def __getattr__(self, name: str) -> NoReturn:
            """Handle attribute access for special cases."""
            if name == "record":
                raise TypeError(f"{type(self).__name__} has no record type. Use AppBase[YourModel] or App[YourModel] to enable record access.")
            raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")

    # -------------------------------------------------------------------------
    # Dirty tracking properties
    # -------------------------------------------------------------------------

    @property
    def is_dirty(self) -> Observable[bool]:
        """Check if any Variable has changed from its clean state."""
        state = getattr(self, "_qtpie_state", None)
        if state is not None:
            return state.is_dirty
        # No state yet - return empty observable
        return Observable[bool](False, dirty_tracking=False, validation=False)

    @property
    def dirty_fields(self) -> set[str]:
        """Return set of field names that have changed."""
        state = getattr(self, "_qtpie_state", None)
        if state is not None:
            return state.dirty_fields
        return set()

    def reset_dirty(self) -> None:
        """Mark all Variables as clean."""
        state = getattr(self, "_qtpie_state", None)
        if state is not None:
            state.reset_dirty()
        # Also reset record dirty state (record is in _qtpie, not _qtpie_state)
        qtpie = getattr(self, "_qtpie", None)
        if qtpie is not None and qtpie._record is not None:
            qtpie._record.reset_dirty()

    # -------------------------------------------------------------------------
    # Validation properties
    # -------------------------------------------------------------------------

    @property
    def is_valid(self) -> Observable[bool]:
        """Check if all validators pass."""
        state = getattr(self, "_qtpie_state", None)
        if state is not None:
            return state.is_valid
        return Observable[bool](True, dirty_tracking=False, validation=False)

    @property
    def validation_errors(self) -> dict[str, dict[str, list[str]]]:
        """Return structured validation errors: {field: {validator: [errors]}}."""
        state = getattr(self, "_qtpie_state", None)
        if state is not None:
            return state.validation_errors
        return {}

    @property
    def validation_error_messages(self) -> list[str]:
        """Return flat list of all error messages."""
        state = getattr(self, "_qtpie_state", None)
        if state is not None:
            return state.validation_error_messages.get()
        return []

    def add_validator(
        self,
        field_name: str,
        validator_name: str,
        validator: Callable[[Any], str | None],
    ) -> None:
        """Add a named validator to a field."""
        state = getattr(self, "_qtpie_state", None)
        if state is not None:
            state.add_validator(field_name, validator_name, validator)

    def remove_validator(self, field_name: str, validator_name: str) -> None:
        """Remove a validator by name."""
        state = getattr(self, "_qtpie_state", None)
        if state is not None:
            state.remove_validator(field_name, validator_name)

    # -------------------------------------------------------------------------
    # Lifecycle hooks (override in subclass)
    # -------------------------------------------------------------------------

    def on_dirty_changed(self, is_dirty: bool) -> None:
        """Called when dirty state changes.

        Override this method to react to dirty state transitions.
        Only fires on actual state changes (True→False or False→True).

        Example::

            def on_dirty_changed(self, is_dirty: bool) -> None:
                self._save_btn.setEnabled(is_dirty)
        """

    def on_valid_changed(self, is_valid: bool) -> None:
        """Called when validation state changes.

        Override this method to react to validation state transitions.
        Only fires on actual state changes (True→False or False→True).

        Example::

            def on_valid_changed(self, is_valid: bool) -> None:
                self._submit_btn.setEnabled(is_valid)
        """

    def on_system_tray_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        """Called when system tray icon is activated.

        Override this method to customize tray activation behavior.
        Default behavior (double-click shows window) runs after this hook.

        Args:
            reason: The activation reason (DoubleClick, Trigger, Context, etc.)
        """

    def on_run(self) -> None:
        """Called when the application starts running.

        This hook is called after the event loop has started, making it safe
        to perform async operations or any initialization that requires
        a running event loop.

        Override this method to perform startup tasks.

        Example::

            @app
            class MyApp(App):
                def on_run(self) -> None:
                    print("App is now running!")
                    self.load_initial_data()
        """

    # -------------------------------------------------------------------------
    # Window control methods
    # -------------------------------------------------------------------------

    def show(self) -> None:
        """Show the auto-created window."""
        auto_window: QMainWindow | None = getattr(self, "_auto_window", None)
        if auto_window is not None:
            auto_window.show()

    def hide(self) -> None:
        """Hide the auto-created window."""
        auto_window: QMainWindow | None = getattr(self, "_auto_window", None)
        if auto_window is not None:
            auto_window.hide()

    @property
    def is_visible(self) -> bool:
        """Check if the auto-created window is visible."""
        auto_window: QMainWindow | None = getattr(self, "_auto_window", None)
        if auto_window is not None:
            return auto_window.isVisible()
        return False

    @property
    def window(self) -> QMainWindow | None:
        """Access the auto-created window, if any."""
        return getattr(self, "_auto_window", None)

    @property
    def tray_icon(self) -> QSystemTrayIcon | None:
        """Access the system tray icon, if any."""
        return getattr(self, "_tray_icon", None)

    def build[W](self, cls: type[W], /, *args: Any, **kwargs: Any) -> W:
        """Build an instance at runtime with new()-like signal and property wiring.

        This is the runtime equivalent of new(). Use it when you need to create
        widget instances dynamically (not at class definition time).

        Args:
            cls: The class to instantiate.
            *args: Positional arguments passed to the constructor.
            **kwargs: Keyword arguments. Signal names (e.g., clicked="handler")
                      are extracted and connected to methods on this App.

        Returns:
            The created instance with signals connected and properties applied.

        Example:
            def on_reload_window(self) -> None:
                self.main_window.close()
                self.main_window = self.build(ForcWindow, on_reload="on_reload")
                self.main_window.show()
        """
        from qtpie.create import create_instance

        return create_instance(self, cls, *args, **kwargs)

    def __init__(self) -> None:
        """Initialize AppBase with declarative features.

        This is a simple __init__ for the base class. When used with @app decorator,
        the wrapped __init__ handles all the declarative setup.
        """
        super().__init__()


class App[T = None](AppBase[T], QApplication):
    """
    A QApplication subclass with declarative features and qasync integration.

    This class combines AppBase (declarative features) with QApplication.

    Features:
    - Declarative fields: Variables, QWidgets, QMenus, QActions
    - Auto-created Window for QWidget/QMenu fields
    - System tray support
    - Lifecycle hooks: __setup__()
    - Dark/light mode support
    - Stylesheet loading
    - qasync event loop for async/await support

    Examples:
        # Simple usage (legacy - without @app decorator)
        app = App("My App", dark_mode=True)
        window = MyMainWindow()
        window.show()
        app.run()

        # Declarative usage with @app decorator
        @app
        class MyApp(App):
            _name: Variable[str] = new("")
            name_input: QLineEdit = new(bind="_name")
            save_btn: QPushButton = new("Save", clicked="on_save")

            def on_save(self) -> None:
                print(f"Saving: {self._name.value}")

        # With record type
        @app(title="Settings", record=Settings())
        class SettingsApp(App[Settings]):
            name: QLineEdit = new()  # Auto-binds to record.name
    """

    def __init__(
        self,
        name: str = "Application",
        *,
        version: str = "1.0.0",
        dark_mode: bool = False,
        light_mode: bool = False,
        argv: Sequence[str] | None = None,
    ) -> None:
        """
        Initialize the App.

        Args:
            name: Application name (sets QApplication.applicationName).
            version: Application version (sets QApplication.applicationVersion).
            dark_mode: Enable dark mode color scheme.
            light_mode: Enable light mode color scheme.
            argv: Command-line arguments. Defaults to sys.argv.
        """
        # Handle color scheme before QApplication init
        if dark_mode:
            set_color_scheme(ColorScheme.Dark)
        elif light_mode:
            set_color_scheme(ColorScheme.Light)

        # Initialize QApplication (skip AppBase.__init__ which does nothing useful here)
        if argv is None:
            argv = sys.argv
        QApplication.__init__(self, list(argv))

        # Set application metadata
        self.setApplicationName(name)
        self.setApplicationVersion(version)

        # Apply color scheme if app now exists
        if dark_mode:
            set_color_scheme(ColorScheme.Dark, self)
        elif light_mode:
            set_color_scheme(ColorScheme.Light, self)
        else:
            # Apply any pending color scheme set before app creation
            apply_deferred_color_scheme(self)

        # Call __setup__ hook (only if NOT using @app decorator - it handles this)
        if not self._qtpie_config.init_wrapped:
            setup_method = getattr(self, "__setup__", None)
            if setup_method is not None:
                setup_method()

    def load_stylesheet(
        self,
        path: str,
        *,
        qrc_path: str | None = None,
    ) -> None:
        """
        Load a stylesheet from a file path or QRC resource.

        Args:
            path: Path to a .qss or .scss file.
            qrc_path: Optional QRC resource path for fallback.
        """
        stylesheet = _load_stylesheet(qss_path=path, qrc_path=qrc_path)
        if stylesheet:
            self.setStyleSheet(stylesheet)

    def enable_dark_mode(self) -> None:
        """Enable dark mode color scheme."""
        set_color_scheme(ColorScheme.Dark, self)

    def enable_light_mode(self) -> None:
        """Enable light mode color scheme."""
        set_color_scheme(ColorScheme.Light, self)

    def run(self) -> int:
        """
        Run the application with qasync event loop.

        If the @app decorator was used with show=True (the default),
        the auto-created window will be shown before starting the event loop.

        This method blocks until the application exits.

        Returns:
            The application exit code.
        """
        # Auto-show window if show=True in config
        if self._qtpie_config.show:
            self.show()

        # Schedule on_run hook to be called after the event loop starts
        if type(self).on_run is not App.on_run:
            QTimer.singleShot(0, self.on_run)

        return run_app(self)

    async def run_async(self) -> int:
        """
        Run the application in an existing async context.

        Use this when you already have an async event loop running.

        Returns:
            The application exit code.
        """
        quit_event = asyncio.Event()
        self.aboutToQuit.connect(quit_event.set)
        await quit_event.wait()
        return 0


@overload
def app[A: AppBase[Any]](cls: type[A]) -> type[A]: ...


@overload
def app[A: AppBase[Any]](
    cls: None = None,
    *,
    # Feature toggles
    window: bool = True,
    system_tray: bool | None = None,
    show: bool = True,
    minimize_to_tray: bool = True,
    # Window settings
    title: str | None = None,
    layout: LayoutType = "vertical",
    margins: int | tuple[int, int, int, int] | None = None,
    # Icon settings
    icon: str | QIcon | QPixmap | QStyle.StandardPixmap | None = None,
    window_icon: str | QIcon | QPixmap | QStyle.StandardPixmap | None = None,
    tray_icon: str | QIcon | QPixmap | QStyle.StandardPixmap | None = None,
    # Standard settings
    auto_bind: bool = True,
    name: str | None = None,
    classes: list[str] | None = None,
    record: Any | None = None,
    # Dock settings
    corners: dict[str, str] | None = None,
    docksLocked: str | None = None,
    **kwargs: Any,
) -> Callable[[type[A]], type[A]]: ...


def app[A: AppBase[Any]](
    cls: type[A] | None = None,
    *,
    # Feature toggles
    window: bool = True,
    system_tray: bool | None = None,
    show: bool = True,
    minimize_to_tray: bool = True,
    # Window settings
    title: str | None = None,
    layout: LayoutType = "vertical",
    margins: int | tuple[int, int, int, int] | None = None,
    # Icon settings
    icon: str | QIcon | QPixmap | QStyle.StandardPixmap | None = None,
    window_icon: str | QIcon | QPixmap | QStyle.StandardPixmap | None = None,
    tray_icon: str | QIcon | QPixmap | QStyle.StandardPixmap | None = None,
    # Standard settings
    auto_bind: bool = True,
    name: str | None = None,
    classes: list[str] | None = None,
    record: Any | None = None,
    stylesheet: str | None = None,
    # Dock settings
    corners: dict[str, str] | None = None,
    docksLocked: str | None = None,
    **kwargs: Any,
) -> type[A] | Callable[[type[A]], type[A]]:
    """Decorator for App/AppBase classes with declarative features.

    Works with both AppBase (for testing) and App (for real applications).

    Usage:
        # For testing (no QApplication needed):
        @app
        class MyAppBase(AppBase):
            _count: Variable[int] = new(0)

        # For real apps:
        @app
        class MyApp(App):
            ...

        @app(title="My App", icon="app.png")
        class MyApp(App):
            _name: Variable[str] = new("")
            name_input: QLineEdit = new(bind="_name")
            file_menu: FileMenu = new()  # Auto-added to Window's menu bar

            system_tray: TrayMenu = new()  # Creates system tray with this menu

    Args:
        window: If True (default), auto-create Window for QWidget/QMenu fields.
        system_tray: If True (default), auto-create system tray.
        show: If True (default), auto-show window in run().
        title: Window title (also sets applicationName).
        layout: Layout for auto-Window's central widget.
        margins: Layout margins.
        icon: Shared icon for both window and tray.
        window_icon: Window icon (overrides icon=).
        tray_icon: Tray icon (overrides icon=).
        auto_bind: If True (default), enable auto-binding for Variables.
        name: Set the app's objectName.
        classes: List of CSS classes to apply.
        record: Initial record value for App[T]/AppBase[T].
        stylesheet: Shorthand for styleSheet.
        **kwargs: Extra properties.
    """
    if title is not None:
        kwargs["windowTitle"] = title
    if stylesheet is not None:
        kwargs["styleSheet"] = stylesheet

    def decorator(target: type[A]) -> type[A]:
        config = target._qtpie_config
        config.layout = layout
        config.margins = margins
        config.auto_bind = auto_bind
        config.record_default = record
        config.widget_props = kwargs
        config.object_name = name
        config.css_classes = classes or []
        config.window = window
        config.system_tray = system_tray
        config.show = show
        config.minimize_to_tray = minimize_to_tray
        config.icon = icon
        config.window_icon = window_icon
        config.tray_icon = tray_icon
        config.corners = corners
        config.docks_locked = docksLocked

        # Wrap __init__
        _wrap_init_for_app(target)

        return target

    if cls is not None:
        return decorator(cls)

    return decorator  # type: ignore[return-value]


def _wrap_init_for_app(cls: type[AppBase[Any]]) -> None:
    """Wrap __init__ to set up declarative features."""
    if cls._qtpie_config.init_wrapped:
        return

    original_init = cls.__init__
    config = cls._qtpie_config

    def wrapped_init(self: AppBase[Any], *args: Any, **kwargs: Any) -> None:
        # Call original __init__
        original_init(self, *args, **kwargs)

        # Initialize state for dirty tracking and validation
        from qtpie.state import QtPieStateBase

        state = QtPieStateBase(self)
        self._qtpie_state = state  # type: ignore[attr-defined]

        # Register Variables in state
        for var_name in config.variable_names:
            var = getattr(self, var_name, None)
            if var is not None:
                state.variables[var_name] = var

        # Set objectName (only for QApplication subclasses)
        if config.is_qapplication:
            if config.object_name is not None:
                self.setObjectName(config.object_name)  # type: ignore[attr-defined]
            else:
                self.setObjectName(type(self).__name__)  # type: ignore[attr-defined]

        # Apply widget_props (style="Fusion" -> setStyle("Fusion"), etc.)
        _apply_app_widget_props(self, config)

        # Connect signals for fields
        from qtpie.signals import connect_field_signals

        connect_field_signals(self, config.fields, _create_app_signal_expression_handler)

        # Set initial record value if provided via @app(record=...)
        # new_fields may have already set this (so child widgets can bind to parent.record)
        # Only set if _qtpie doesn't exist yet (indicating new_fields didn't set it)
        if config.record_default is not None and config.record_type is not None:
            # Check _qtpie WITHOUT triggering the record descriptor
            # (hasattr(self, "record") would trigger lazy creation!)
            qtpie = getattr(self, "_qtpie", None)
            if qtpie is None or qtpie._record is None:  # pyright: ignore[reportPrivateUsage, reportUnknownMemberType]
                self.record = config.record_default

        # Call __setup__ hook (before bindings, so record can be initialized)
        setup_method = getattr(self, "__setup__", None)
        if setup_method is not None:
            setup_method()

        # Apply bindings for widget fields
        from qtpie.bindings.apply import apply_auto_bindings, apply_property_bindings, pre_create_selection_variables
        from qtpie.bindings.expression import create_expression_binding

        # Pre-create Variables for selection bindings (bare Variable[T] without new())
        pre_create_selection_variables(self, config)  # type: ignore[arg-type]

        # Property bindings (visible=, enabled=)
        apply_property_bindings(self, config, create_expression_binding_fn=create_expression_binding)  # type: ignore[arg-type]

        # Apply property bindings for QActions (not handled by apply_property_bindings which only does QWidgets)
        _apply_action_property_bindings_for_app(self, config)

        # Auto bindings (bind="{_name}", etc.)
        apply_auto_bindings(self, config)  # type: ignore[arg-type]

        # Handle list widget fields (list[QLabel] bound to Variable[list[...]])
        for name, field_info in config.fields.items():
            if field_info.is_list_widget:
                _apply_list_binding_for_app(self, name, field_info)

        # Create auto-Window if we have widget/menu fields and window=True
        if config.window:
            _create_auto_window(self, config, cls)

        # Set up system tray (None=auto-detect, True=force, False=never)
        if config.system_tray is not False:
            _setup_system_tray(self, config)

        # Set up dirty/valid change hooks
        _setup_state_hooks(self, state)

    cls.__init__ = wrapped_init  # type: ignore[method-assign]
    cls._qtpie_config.init_wrapped = True


def _create_app_signal_expression_handler(app: AppBase[Any], expression: str) -> Callable[..., Any]:
    """Create a signal handler from an expression string like "{my_signal(123)}"."""
    return create_signal_expression_handler(app, expression, ["#app", "#self"])


def _apply_app_widget_props(app: AppBase[Any], config: AppConfig) -> None:
    """Apply widget properties from @app decorator kwargs.

    For each prop like style="Fusion", calls app.setStyle("Fusion").
    Reactive props (with {}) are skipped here.
    CSS classes are applied to the auto-created window, not the app itself.
    """
    from qtpie.bindings import is_format_string
    from qtpie.utils.layouts import apply_widget_props

    # Apply widget properties, skipping reactive ones
    def skip_reactive(prop_name: str, value: Any) -> bool:
        return isinstance(value, str) and is_format_string(value)

    apply_widget_props(app, config.widget_props, skip_filter=skip_reactive)


def _create_auto_window(app: AppBase[Any], config: AppConfig, cls: type[AppBase[Any]]) -> None:
    """Create an auto-Window for QWidget/QMenu fields.

    Categorizes fields and creates a QMainWindow with:
    - QMenu fields added to menuBar
    - QWidget/Variable[T,W] fields added to central widget layout

    Works with both AppBase (for testing) and App (real applications).
    """
    from qtpie.variable import Variable

    # Check if this is a real QApplication for applicationName() access
    qapp = app if isinstance(app, QApplication) else None

    # Categorize fields
    menu_fields: list[tuple[str, QMenu]] = []
    widget_fields: list[tuple[str, QWidget]] = []
    system_tray_menu: QMenu | None = None

    for name in getattr(cls, "__annotations__", {}):
        instance = getattr(app, name, None)

        # Check for system_tray field (with or without underscore prefix)
        if name in ("system_tray", "_system_tray") and isinstance(instance, QMenu):
            system_tray_menu = instance
            continue

        # QMenu -> menu bar (not system_tray)
        if isinstance(instance, QMenu):
            menu_fields.append((name, instance))
            continue

        # QWidget -> central widget (but not QMainWindow - those are top-level)
        if isinstance(instance, QWidget) and not isinstance(instance, QMainWindow):
            widget_fields.append((name, instance))
            continue

        # Variable[T, W] -> central widget (its .widget)
        if isinstance(instance, Variable) and instance.widget is not None:
            widget_fields.append((name, instance.widget))
            continue

    # Store system_tray_menu for later use in system tray setup
    if system_tray_menu is not None:
        app._system_tray_menu = system_tray_menu  # type: ignore[attr-defined]

    # Check if we have dock fields
    has_docks = bool(config.dock_fields) or bool(config.variable_dock_fields)

    # Check if we have layout items (nested layouts, stretch, spacers)
    has_layout_items = any(field.is_nested_layout or field.is_stretch or field.is_spacer_item for field in config.fields.values())

    # Only create window if there are fields to display
    if not menu_fields and not widget_fields and not has_docks and not has_layout_items:
        return

    # Create the auto-Window
    window = QMainWindow()

    # Apply object name and CSS classes to window
    from qtpie.utils.layouts import apply_object_name_and_classes

    apply_object_name_and_classes(
        window,
        object_name=config.object_name,  # From name= parameter
        css_classes=config.css_classes,
        default_name=type(app).__name__,
    )

    # Set window title from config
    window_title = config.widget_props.get("windowTitle")
    if window_title:
        window.setWindowTitle(window_title)
    elif qapp is not None:
        window.setWindowTitle(qapp.applicationName())
    else:
        # For AppBase testing, use class name as title
        window.setWindowTitle(type(app).__name__)

    # Set window icon
    resolved_icon = resolve_icon(config.window_icon) or resolve_icon(config.icon)
    if resolved_icon:
        window.setWindowIcon(resolved_icon)

    # Add menus to menu bar
    for _name, menu in menu_fields:
        window.menuBar().addMenu(menu)
        # Store reference to parent window for #parent bindings
        menu._parent_window = window  # type: ignore[attr-defined]

    # Create central widget with layout if we have widget fields or layout items
    if config.layout is not None:
        from qtpie.variable import _VariableDescriptor
        from qtpie.widget import _add_layout_to_nested_layout, _add_spacer_to_layout, _add_stretch_to_layout, _add_widget_to_nested_layout, _create_spacer_item, _get_target_layout

        central = QWidget()
        qt_layout = create_layout(config.layout)

        if qt_layout is not None:
            central.setLayout(qt_layout)

            # Apply margins
            from qtpie.utils.layouts import apply_layout_margins

            apply_layout_margins(qt_layout, config.margins)

            # Track nested layouts by field name for later reference
            nested_layouts: dict[str, QLayout] = {}

            # First pass: Create and add nested layouts
            for name in getattr(cls, "__annotations__", {}):
                if name in config.fields:
                    field = config.fields[name]
                    if field.is_nested_layout:
                        # Create the nested layout instance
                        layout_instance = field.field_type(*field.args, **field.kwargs)  # type: ignore[misc]
                        setattr(app, name, layout_instance)
                        nested_layouts[name] = layout_instance

                        # Add to target layout (default or another nested layout)
                        target = _get_target_layout(qt_layout, nested_layouts, field.target_layout)
                        if target is not None and not field.exclude_from_layout:
                            _add_layout_to_nested_layout(target, layout_instance, field.grid, name)

            # Second pass: Add child widgets, Variables, Stretch, and QSpacerItem to layouts
            for name in getattr(cls, "__annotations__", {}):
                # Skip system_tray field
                if name in ("system_tray", "_system_tray"):
                    continue

                if name in config.fields:
                    field = config.fields[name]
                    if field.exclude_from_layout:
                        continue

                    # Skip nested layouts (already handled in first pass)
                    if field.is_nested_layout:
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
                        setattr(app, name, spacer)
                        _add_spacer_to_layout(target, spacer, field.grid)
                        continue

                    # Handle regular QWidget (skip QMenu, already handled above)
                    widget_instance = getattr(app, name, None)
                    if widget_instance is not None and isinstance(widget_instance, QWidget) and not isinstance(widget_instance, QMenu):
                        label: str | None = None
                        grid: GridPosition | None = None

                        label = field.label
                        grid = field.grid

                        # For default layout: validate and use decorator's layout type
                        # For nested layout: detect actual layout type and use appropriate add method
                        if field.target_layout is None:
                            _validate_layout_params(name, config.layout, label, grid)
                            _add_to_layout_for_app(target, widget_instance, config.layout, label, grid)
                        else:
                            _add_widget_to_nested_layout(target, widget_instance, label, grid, name)

                # Check if it's a Variable with a widget
                elif name in config.variable_names:
                    var = getattr(app, name, None)
                    if isinstance(var, Variable) and var.widget is not None:
                        # Get label/grid/exclude_from_layout/target_layout from the descriptor
                        descriptor = getattr(cls, name, None)
                        var_label: str | None = None
                        grid: GridPosition | None = None
                        target_layout_name: str | None = None
                        if isinstance(descriptor, _VariableDescriptor):
                            if descriptor.exclude_from_layout:
                                continue
                            var_label = descriptor.label
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
                            _add_to_layout_for_app(target, var.widget, config.layout, var_label, grid)
                        else:
                            _add_widget_to_nested_layout(target, var.widget, var_label, grid, name)

        window.setCentralWidget(central)

    # Create dock widgets
    if has_docks:
        _create_docks_for_app(app, window, config, cls)

    # Store the auto-Window on the app
    app._auto_window = window  # type: ignore[attr-defined]

    # Set up minimize-to-tray behavior if enabled
    # This will be finalized after system tray is set up
    app._qtpie_minimize_to_tray = config.minimize_to_tray  # type: ignore[attr-defined]


def _add_to_layout_for_app(
    layout: QLayout,
    widget_instance: QWidget,
    layout_type: LayoutType,
    label: str | None = None,
    grid: tuple[int, ...] | None = None,
) -> None:
    """Add a widget to the layout."""
    add_to_layout(layout, widget_instance, layout_type, label, grid)


def _setup_system_tray(app: AppBase[Any], config: AppConfig) -> None:
    """Set up system tray icon with menu.

    The system tray uses:
    - system_tray field (QMenu) if defined
    - QAction, Separator, Section fields are added to a lazily-created tray menu

    Behavior depends on config.system_tray:
    - None (default): auto-detect, only create if there are QActions or system_tray field
    - True: force create (with default menu for auto-window if no items)
    - False: never create (handled by caller, won't reach this function)

    Works with both AppBase (for testing) and App (real applications).
    When used with AppBase, tray is created without a parent.
    """
    from qtpy.QtGui import QAction

    from qtpie.menu import Section, Separator

    # Check if this is a real QApplication for parent assignment and quit action
    qapp = app if isinstance(app, QApplication) else None

    # Check if there's a system_tray menu stored from _create_auto_window
    tray_menu: QMenu | None = getattr(app, "_system_tray_menu", None)

    # Check if we have any tray-related fields (QAction, Separator, Section)
    annotations = getattr(type(app), "__annotations__", {})
    has_tray_items = False
    for name in annotations:
        annotation = annotations.get(name)
        if annotation is QAction or annotation is Separator or annotation is Section:
            has_tray_items = True
            break
        # Also check if field instance is QAction
        instance = getattr(app, name, None)
        if isinstance(instance, QAction):
            has_tray_items = True
            break

    # If no system_tray field but we have an auto-window, create a default menu
    auto_window: QMainWindow | None = getattr(app, "_auto_window", None)

    # Decide whether to create the tray based on what content is available
    # tray_menu: explicit system_tray Menu field
    # has_tray_items: QAction/Separator/Section fields
    # auto_window: default show/hide/quit menu for window
    has_content = tray_menu is not None or has_tray_items or auto_window is not None

    if config.system_tray is True:
        # Force create - but still need something to show
        if not has_content:
            return
    else:
        # Auto-detect (system_tray=None): only create if there are tray items or menu
        # (not just because there's an auto_window - that's too implicit)
        if tray_menu is None and not has_tray_items:
            return

    # Resolve tray icon
    icon = resolve_icon(config.tray_icon) or resolve_icon(config.icon)
    if icon is None:
        # Use application icon as fallback (only available for QApplication)
        if qapp is not None:
            icon = qapp.windowIcon()
            if icon.isNull():
                # No explicit icon - use empty icon (system will show default)
                icon = QIcon()
        else:
            # For AppBase testing, create empty icon
            icon = QIcon()

    # Create system tray icon (parent to QApplication if available, None otherwise)
    tray = QSystemTrayIcon(icon, qapp)

    # Create or use the tray menu
    if tray_menu is None:
        tray_menu = QMenu()

        # Add items in declaration order (like Menu does)
        for name in annotations:
            annotation = annotations.get(name)

            # Check for Separator
            if annotation is Separator:
                tray_menu.addSeparator()
                continue

            # Check for Section
            if annotation is Section:
                section_text = _get_section_text_for_tray(name, config.fields.get(name))
                tray_menu.addSection(section_text)
                continue

            # Check for QAction
            instance = getattr(app, name, None)
            if isinstance(instance, QAction):
                tray_menu.addAction(instance)
                continue

    tray.setContextMenu(tray_menu)

    # Connect activation signals
    def on_tray_activated(reason: QSystemTrayIcon.ActivationReason) -> None:
        # Call hook if defined
        hook = getattr(app, "on_system_tray_activated", None)
        if hook is not None:
            hook(reason)
        # Default: double-click shows window
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick and auto_window is not None:
            auto_window.show()
            auto_window.raise_()
            auto_window.activateWindow()

    tray.activated.connect(on_tray_activated)

    # Store tray reference (accessible via .tray_icon property)
    app._tray_icon = tray  # type: ignore[attr-defined]

    # Set up minimize-to-tray on window close if enabled
    minimize_to_tray = getattr(app, "_qtpie_minimize_to_tray", True)
    if minimize_to_tray and auto_window is not None:
        _install_minimize_to_tray(auto_window)

    # Show tray
    tray.show()


def _install_minimize_to_tray(window: QMainWindow) -> None:
    """Install close event handler to hide window instead of closing.

    This makes closing the window hide it to the system tray instead of
    quitting the application.
    """
    from qtpy.QtCore import QEvent

    def close_event_handler(event: QEvent) -> None:
        # Hide window instead of closing
        window.hide()
        event.ignore()

    window.closeEvent = close_event_handler  # type: ignore[method-assign]


def _get_section_text_for_tray(name: str, field: NewField | None) -> str:
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


def _apply_action_property_bindings_for_app(app: AppBase[Any], config: AppConfig) -> None:
    """Apply property bindings like enabled="_can_quit" to QAction fields.

    This handles QAction property bindings which aren't handled by the regular
    apply_property_bindings (which only handles QWidgets).
    """
    from qtpy.QtGui import QAction

    from qtpie.bindings import is_format_string, resolve_binding_source
    from qtpie.bindings.expression import create_expression_binding
    from qtpie.variable import Variable

    for field_name, field_info in config.fields.items():
        if not field_info.property_bindings:
            continue

        action = getattr(app, field_name, None)
        if action is None or not isinstance(action, QAction):
            continue

        for prop_name, bind_expr in field_info.property_bindings.items():
            # Get the setter for this property
            setter_name = f"set{prop_name[0].upper()}{prop_name[1:]}"
            setter = getattr(action, setter_name, None)
            if setter is None or not callable(setter):
                continue

            # Wrap setter for type compatibility
            def make_setter(s: Callable[..., Any]) -> Callable[[Any], None]:
                def setter_fn(val: Any) -> None:
                    s(val)

                return setter_fn

            typed_setter = make_setter(setter)

            if is_format_string(bind_expr):
                # Expression binding like "{_count > 0}"
                create_expression_binding(app, bind_expr, typed_setter)
            else:
                # Simple variable reference like "_can_quit"
                source = resolve_binding_source(app, bind_expr)  # type: ignore[arg-type]
                if source is None:
                    continue

                if isinstance(source, Variable):
                    # Set initial value and subscribe
                    typed_setter(source.value)  # pyright: ignore[reportUnknownMemberType]
                    source.on_change(typed_setter)


def _apply_list_binding_for_app(app: AppBase[Any], name: str, field: NewField) -> None:
    """Apply list binding for list[QWidget] fields."""
    from observant import ObservableDict, ObservableList

    from qtpie.bindings import resolve_binding_source
    from qtpie.dict_widget_repeater import DictWidgetRepeater
    from qtpie.variable import Variable
    from qtpie.widget_repeater import WidgetRepeater

    if field.bind is None:
        return

    bind_path = field.bind if isinstance(field.bind, str) else field.bind.resolve()  # type: ignore[union-attr]

    # Resolve the source variable
    source = resolve_binding_source(app, bind_path)  # type: ignore[arg-type]
    if source is None or not isinstance(source, Variable):
        return

    # Get the widget type from field
    widget_type = field.list_widget_type
    if widget_type is None:
        return

    # Get the underlying observable from Variable
    wrapper = source._wrapper  # pyright: ignore[reportPrivateUsage]

    # Handle dict bindings
    if isinstance(wrapper, ObservableDict):
        # Dict binding with #key and #value
        bind_expr: str | Callable[[Any], str] = field.list_format if field.list_format is not None else "{#key} = {#value}"

        dict_repeater: DictWidgetRepeater[Any, Any] = DictWidgetRepeater(
            observable_dict=wrapper,
            key_type=None,
            value_type=None,
            widget_type=widget_type,
            widget_args=field.args,
            widget_kwargs=field.kwargs,
            widget_props=field.widget_props,
            bind_expr=bind_expr,  # type: ignore[arg-type]
            sort=field.sort,
            object_name=field.object_name or name,
            css_classes=field.css_classes,
            signal_connections=field.signal_connections,
            parent_widget=app,  # type: ignore[arg-type]
        )
        setattr(app, name, dict_repeater)
        return

    # Handle list bindings
    if not isinstance(wrapper, ObservableList):
        return

    # Get format string if provided (stored as list_format in NewField)
    list_bind_expr: str | Callable[[Any], str] = field.list_format if field.list_format is not None else "{#self}"

    # Create and store the repeater
    repeater: WidgetRepeater[Any] = WidgetRepeater(
        observable_list=wrapper,
        item_type=None,  # Could extract from type hints if needed
        widget_type=widget_type,
        widget_args=field.args,
        widget_kwargs=field.kwargs,
        widget_props=field.widget_props,
        bind_expr=list_bind_expr,
        sort=field.sort,
        object_name=field.object_name or name,
        css_classes=field.css_classes,
        signal_connections=field.signal_connections,
        parent_widget=app,  # type: ignore[arg-type]
    )
    setattr(app, name, repeater)


def _setup_state_hooks(app: AppBase[Any], state: Any) -> None:
    """Set up dirty and valid change hooks."""
    # Track previous values for edge detection
    # Sync with current state (after __setup__ ran and added validators)
    was_dirty = state.is_dirty.get()
    was_valid = state.is_valid.get()

    def on_dirty_update(is_dirty: bool) -> None:
        nonlocal was_dirty
        if is_dirty != was_dirty:
            was_dirty = is_dirty
            # Check if hook is overridden
            if type(app).on_dirty_changed is not AppBase.on_dirty_changed:
                app.on_dirty_changed(is_dirty)

    def on_valid_update(is_valid: bool) -> None:
        nonlocal was_valid
        if is_valid != was_valid:
            was_valid = is_valid
            # Check if hook is overridden
            if type(app).on_valid_changed is not AppBase.on_valid_changed:
                app.on_valid_changed(is_valid)

    # Subscribe to state changes (if there are Variables or record)
    # For App, record is in _qtpie (via _RecordDescriptor) not _qtpie_state
    qtpie = getattr(app, "_qtpie", None)
    record = qtpie._record if qtpie is not None else None

    if state.variables or record is not None:
        state.is_dirty.on_change(on_dirty_update)
        state.is_valid.on_change(on_valid_update)

    # Subscribe record's is_dirty to state's aggregated is_dirty (for App)
    if record is not None:

        def update_dirty_from_record(_: Any = None) -> None:
            # Recompute: any Variable dirty OR record dirty
            current = state._compute_is_dirty()
            if record is not None:
                current = current or record.is_dirty.get()
            state._aggregated_is_dirty.set(current)

        record.is_dirty.on_change(update_dirty_from_record)
        # Initial sync
        update_dirty_from_record()


def _create_docks_for_app(
    app: AppBase[Any],
    window: QMainWindow,
    config: AppConfig,
    cls: type[AppBase[Any]],
) -> None:
    """Create Dock[T] fields for the app's auto-window.

    This function handles dock creation for AppBase, adapting the logic from
    Window's _create_dock_fields to work with AppBase's auto-created QMainWindow.
    """
    # Apply corner assignments
    if config.corners:
        _apply_corner_assignments_for_app(window, config.corners)

    # First, create regular Dock[T] fields
    if config.dock_fields:
        _create_dock_fields_for_app(app, window, config)

    # Then, create Variable[T, Dock[W]] fields
    if config.variable_dock_fields:
        _create_variable_dock_fields_for_app(app, window, config, cls)

    # Set up docks locked binding
    if config.docks_locked:
        _setup_docks_locked_binding_for_app(app, window, config.docks_locked)


def _create_dock_fields_for_app(
    app: AppBase[Any],
    window: QMainWindow,
    config: AppConfig,
) -> None:
    """Create Dock[T] fields for the app's auto-window."""
    from qtpie.dock import Dock, parse_dock_area

    # Build dependency graph for topological sort
    dock_info: dict[str, dict[str, Any]] = {}
    for name in config.dock_fields:
        field = config.fields.get(name)
        if field is None or not field.is_dock:
            continue

        deps: list[str] = []
        if field.dock_below:
            deps.append(field.dock_below)
        if field.dock_above:
            deps.append(field.dock_above)
        if field.dock_right_of:
            deps.append(field.dock_right_of)
        if field.dock_left_of:
            deps.append(field.dock_left_of)

        dock_info[name] = {"field": field, "deps": deps}

    # Topological sort
    processed: set[str] = set()
    ordered_names: list[str] = []

    def process(name: str) -> None:
        if name in processed:
            return
        info = dock_info.get(name)
        if info is None:
            return
        for dep in info["deps"]:
            process(dep)
        processed.add(name)
        ordered_names.append(name)

    for name in dock_info:
        process(name)

    # Track created docks
    created_docks: dict[str, Dock[Any]] = {}
    groups: dict[str, list[str]] = {}

    # Create all dock widgets
    for name in ordered_names:
        info = dock_info[name]
        fld: NewField = info["field"]

        content_type = fld.dock_content_type
        if content_type is None:
            continue

        # Create content widget
        content_widget = content_type(*fld.widget_args, **fld.widget_kwargs)

        # Create QDockWidget
        title = fld.dock_title or name
        dock_widget = QDockWidget(title, window)
        dock_widget.setWidget(content_widget)

        # Apply objectName
        if fld.object_name:
            dock_widget.setObjectName(fld.object_name)
        else:
            dock_widget.setObjectName(name)

        # Apply dock features
        _apply_dock_features_for_app(
            dock_widget,
            fld.dock_closable,
            fld.dock_floatable,
            fld.dock_movable,
            fld.dock_allowed_areas,
            fld.dock_vertical_title_bar,
        )

        # Create Dock wrapper
        dock = Dock(content_widget, dock_widget)
        created_docks[name] = dock
        setattr(app, name, dock)

        # Track group membership
        if fld.dock_group:
            if fld.dock_group not in groups:
                groups[fld.dock_group] = []
            groups[fld.dock_group].append(name)

        # Determine placement
        from qtpy.QtCore import Qt as QtCore

        if fld.dock_area:
            area = parse_dock_area(fld.dock_area)
            window.addDockWidget(area, dock_widget)
        elif fld.dock_below:
            ref_dock = created_docks.get(fld.dock_below)
            if ref_dock:
                window.splitDockWidget(ref_dock.dock_widget, dock_widget, QtCore.Orientation.Vertical)
        elif fld.dock_above:
            ref_dock = created_docks.get(fld.dock_above)
            if ref_dock:
                area = window.dockWidgetArea(ref_dock.dock_widget)
                window.addDockWidget(area, dock_widget)
                window.splitDockWidget(dock_widget, ref_dock.dock_widget, QtCore.Orientation.Vertical)
        elif fld.dock_right_of:
            ref_dock = created_docks.get(fld.dock_right_of)
            if ref_dock:
                window.splitDockWidget(ref_dock.dock_widget, dock_widget, QtCore.Orientation.Horizontal)
        elif fld.dock_left_of:
            ref_dock = created_docks.get(fld.dock_left_of)
            if ref_dock:
                area = window.dockWidgetArea(ref_dock.dock_widget)
                window.addDockWidget(area, dock_widget)
                window.splitDockWidget(dock_widget, ref_dock.dock_widget, QtCore.Orientation.Horizontal)

    # Handle group tabification
    for _group_name, dock_names in groups.items():
        if len(dock_names) < 2:
            continue

        anchor_name: str | None = None
        for name in dock_names:
            fld = dock_info[name]["field"]
            if fld.dock_area or fld.dock_below or fld.dock_above or fld.dock_right_of or fld.dock_left_of:
                anchor_name = name
                break

        if anchor_name is None:
            anchor_name = dock_names[0]
            anchor_dock = created_docks[anchor_name]
            window.addDockWidget(parse_dock_area("left"), anchor_dock.dock_widget)

        anchor_dock = created_docks[anchor_name]
        for name in dock_names:
            if name == anchor_name:
                continue
            dock = created_docks[name]
            fld = dock_info[name]["field"]
            if not (fld.dock_area or fld.dock_below or fld.dock_above or fld.dock_right_of or fld.dock_left_of):
                from qtpy.QtCore import Qt as QtCore

                area = window.dockWidgetArea(anchor_dock.dock_widget)
                if area == QtCore.DockWidgetArea.NoDockWidgetArea:
                    area = parse_dock_area("left")
                window.addDockWidget(area, dock.dock_widget)
            window.tabifyDockWidget(anchor_dock.dock_widget, dock.dock_widget)

        anchor_dock.dock_widget.raise_()

    # Set up bindings for dock fields
    _setup_dock_bindings_for_app(app, config, dock_info, created_docks, groups)


def _create_variable_dock_fields_for_app(
    app: AppBase[Any],
    window: QMainWindow,
    config: AppConfig,
    cls: type[AppBase[Any]],
) -> None:
    """Create Variable[T, Dock[W]] fields for the app's auto-window."""
    from qtpie.dock import Dock, parse_dock_area
    from qtpie.variable import Variable, _VariableDescriptor

    for name in config.variable_dock_fields:
        var: Variable[Any, Any] = getattr(app, name)
        if var.widget is None:
            continue

        descriptor = getattr(cls, name, None)
        if not isinstance(descriptor, _VariableDescriptor) or descriptor.dock_info is None:
            continue

        dock_info = descriptor.dock_info
        inner_widget = var.widget

        # Get title - use field name for initial title if title is a binding
        title_value = dock_info.get("dock_title")
        initial_title = name
        if title_value:
            # Check if it's a static title (no bindings)
            if "{" not in title_value and not title_value.startswith("_"):
                initial_title = title_value

        dock_widget = QDockWidget(initial_title, window)
        dock_widget.setWidget(inner_widget)

        object_name = dock_info.get("object_name")
        if object_name:
            dock_widget.setObjectName(object_name)
        else:
            dock_widget.setObjectName(name)

        _apply_dock_features_for_app(
            dock_widget,
            dock_info.get("dock_closable"),
            dock_info.get("dock_floatable"),
            dock_info.get("dock_movable"),
            dock_info.get("dock_allowed_areas"),
            dock_info.get("dock_vertical_title_bar"),
        )

        dock = Dock(inner_widget, dock_widget)
        var.widget = dock

        # Set up title binding if reactive
        if title_value:
            _setup_dock_title_binding_for_app(app, dock, title_value, name)

        dock_area = dock_info.get("dock_area")
        if dock_area:
            area = parse_dock_area(dock_area)
            window.addDockWidget(area, dock_widget)
        else:
            # Default to left if no area specified
            window.addDockWidget(parse_dock_area("left"), dock_widget)


def _apply_dock_features_for_app(
    dock_widget: QDockWidget,
    closable: bool | None,
    floatable: bool | None,
    movable: bool | None,
    allowed_areas: list[str] | None,
    vertical_title_bar: bool | None,
) -> None:
    """Apply dock widget features (closable, floatable, movable, etc.)."""
    from qtpy.QtCore import Qt as QtCore

    features = QDockWidget.DockWidgetFeature.DockWidgetClosable | QDockWidget.DockWidgetFeature.DockWidgetMovable | QDockWidget.DockWidgetFeature.DockWidgetFloatable

    if closable is False:
        features &= ~QDockWidget.DockWidgetFeature.DockWidgetClosable
    if floatable is False:
        features &= ~QDockWidget.DockWidgetFeature.DockWidgetFloatable
    if movable is False:
        features &= ~QDockWidget.DockWidgetFeature.DockWidgetMovable

    dock_widget.setFeatures(features)

    if allowed_areas is not None:
        areas = QtCore.DockWidgetArea(0)
        area_map = {
            "left": QtCore.DockWidgetArea.LeftDockWidgetArea,
            "right": QtCore.DockWidgetArea.RightDockWidgetArea,
            "top": QtCore.DockWidgetArea.TopDockWidgetArea,
            "bottom": QtCore.DockWidgetArea.BottomDockWidgetArea,
        }
        for area_name in allowed_areas:
            area_name_lower = area_name.lower()
            if area_name_lower in area_map:
                areas |= area_map[area_name_lower]
        dock_widget.setAllowedAreas(areas)

    if vertical_title_bar is True:
        dock_widget.setFeatures(dock_widget.features() | QDockWidget.DockWidgetFeature.DockWidgetVerticalTitleBar)


def _setup_dock_bindings_for_app(
    app: AppBase[Any],
    config: AppConfig,
    dock_info: dict[str, dict[str, Any]],
    created_docks: dict[str, Any],
    groups: dict[str, list[str]],
) -> None:
    """Set up bindings for dock fields (visible=, floating=, title=, icon=, etc.)."""
    from qtpie.dock import Dock

    groups_with_binding: set[str] = set()

    for name in config.dock_fields:
        info = dock_info.get(name)
        if info is None:
            continue
        fld = info["field"]
        dock: Dock[Any] = created_docks[name]

        # title= binding (reactive title)
        if fld.dock_title:
            _setup_dock_title_binding_for_app(app, dock, fld.dock_title, name)

        # icon= binding (reactive icon)
        if fld.dock_icon:
            _setup_dock_icon_binding_for_app(app, dock, fld.dock_icon)

        # visible= binding
        if fld.dock_visible:
            _setup_dock_visible_binding_for_app(app, dock, fld.dock_visible)

        # floating= binding
        if fld.dock_floating:
            _setup_dock_floating_binding_for_app(app, dock, fld.dock_floating)

        # groupSelectedIndex= binding
        if fld.dock_group_selected_index and fld.dock_group:
            group_name = fld.dock_group
            if group_name not in groups_with_binding:
                groups_with_binding.add(group_name)
                group_dock_names = groups.get(group_name, [])
                if group_dock_names:
                    _setup_group_selected_index_binding_for_app(app, fld.dock_group_selected_index, group_dock_names, created_docks)


def _setup_dock_visible_binding_for_app(app: AppBase[Any], dock: Any, binding: str) -> None:
    """Set up two-way binding between Variable and dock visibility."""
    from qtpie.variable import _get_variable_observable

    observable = _get_variable_observable(app, binding)
    if observable is None:
        return

    dock_widget = dock.dock_widget

    def on_variable_change(visible: bool) -> None:
        if visible and dock_widget.isHidden():
            dock_widget.setVisible(True)
        elif not visible and not dock_widget.isHidden():
            dock_widget.setVisible(False)

    observable.on_change(on_variable_change)
    on_variable_change(observable.get())

    def on_visibility_change(visible: bool) -> None:
        if observable.get() != visible:
            observable.set(visible)

    dock_widget.visibilityChanged.connect(on_visibility_change)


def _setup_dock_floating_binding_for_app(app: AppBase[Any], dock: Any, binding: str) -> None:
    """Set up two-way binding between Variable and dock floating state."""
    from qtpie.variable import _get_variable_observable

    observable = _get_variable_observable(app, binding)
    if observable is None:
        return

    dock_widget = dock.dock_widget

    def on_variable_change(floating: bool) -> None:
        if dock_widget.isFloating() != floating:
            dock_widget.setFloating(floating)

    observable.on_change(on_variable_change)
    on_variable_change(observable.get())

    def on_floating_change(floating: bool) -> None:
        if observable.get() != floating:
            observable.set(floating)

    dock_widget.topLevelChanged.connect(on_floating_change)


def _setup_dock_title_binding_for_app(app: AppBase[Any], dock: Any, title: str, field_name: str) -> None:
    """Set up reactive binding for dock title."""
    dock_widget = dock.dock_widget

    # Check if it's an expression (contains {})
    if "{" in title:
        from qtpie.bindings import create_format_binding

        def set_title(value: Any) -> None:
            dock_widget.setWindowTitle(str(value))

        create_format_binding(app, title, set_title)
        return

    # Check if it's a variable reference (starts with _)
    if title.startswith("_"):
        from qtpie.variable import _get_variable_observable

        observable = _get_variable_observable(app, title)
        if observable is not None:

            def on_title_change(value: Any) -> None:
                dock_widget.setWindowTitle(str(value))

            observable.on_change(on_title_change)
            on_title_change(observable.get())
            return

    # Static value - already set during dock creation


def _setup_dock_icon_binding_for_app(app: AppBase[Any], dock: Any, icon: str) -> None:
    """Set up reactive binding for dock icon."""
    from qtpy.QtGui import QIcon, QPixmap

    dock_widget = dock.dock_widget

    def apply_icon(value: Any) -> None:
        if value is None or value == "":
            dock_widget.setWindowIcon(QIcon())
        elif isinstance(value, QIcon):
            dock_widget.setWindowIcon(value)
        elif isinstance(value, QPixmap):
            dock_widget.setWindowIcon(QIcon(value))
        else:
            dock_widget.setWindowIcon(QIcon(str(value)))

    # Check if it's an expression (contains {})
    if "{" in icon:
        from qtpie.bindings import create_format_binding

        create_format_binding(app, icon, apply_icon)
        return

    # Check if it's a variable reference (starts with _)
    if icon.startswith("_"):
        from qtpie.variable import _get_variable_observable

        observable = _get_variable_observable(app, icon)
        if observable is not None:
            observable.on_change(apply_icon)
            apply_icon(observable.get())
            return

    # Static value - set once
    apply_icon(icon)


def _setup_group_selected_index_binding_for_app(
    app: AppBase[Any],
    binding: str,
    group_dock_names: list[str],
    created_docks: dict[str, Any],
) -> None:
    """Set up two-way binding between Variable and tab bar current index for a dock group."""
    from qtpy.QtCore import QTimer
    from qtpy.QtWidgets import QTabBar

    from qtpie.variable import _get_variable_observable

    observable = _get_variable_observable(app, binding)
    if observable is None:
        return

    if not group_dock_names:
        return

    first_dock = created_docks.get(group_dock_names[0])
    if first_dock is None:
        return

    dock_widget = first_dock.dock_widget
    window = app.window

    if window is None:
        return

    def find_tab_bar_for_dock() -> QTabBar | None:
        for tab_bar in window.findChildren(QTabBar):
            for i in range(tab_bar.count()):
                if tab_bar.tabText(i) == dock_widget.windowTitle():
                    return tab_bar
        return None

    def setup_binding() -> None:
        tab_bar = find_tab_bar_for_dock()
        if tab_bar is None:
            return

        def on_variable_change(index: int) -> None:
            if 0 <= index < tab_bar.count() and tab_bar.currentIndex() != index:
                tab_bar.setCurrentIndex(index)

        observable.on_change(on_variable_change)
        on_variable_change(observable.get())

        def on_tab_change(index: int) -> None:
            if observable.get() != index:
                observable.set(index)

        tab_bar.currentChanged.connect(on_tab_change)

    QTimer.singleShot(0, setup_binding)


def _apply_corner_assignments_for_app(window: QMainWindow, corners: dict[str, str]) -> None:
    """Apply corner assignments for dock areas."""
    from qtpy.QtCore import Qt as QtCore

    corner_map = {
        "top_left": QtCore.Corner.TopLeftCorner,
        "top_right": QtCore.Corner.TopRightCorner,
        "bottom_left": QtCore.Corner.BottomLeftCorner,
        "bottom_right": QtCore.Corner.BottomRightCorner,
    }

    area_map = {
        "left": QtCore.DockWidgetArea.LeftDockWidgetArea,
        "right": QtCore.DockWidgetArea.RightDockWidgetArea,
        "top": QtCore.DockWidgetArea.TopDockWidgetArea,
        "bottom": QtCore.DockWidgetArea.BottomDockWidgetArea,
    }

    for corner_name, area_name in corners.items():
        corner_name_lower = corner_name.lower().replace("-", "_")
        area_name_lower = area_name.lower()

        if corner_name_lower in corner_map and area_name_lower in area_map:
            window.setCorner(corner_map[corner_name_lower], area_map[area_name_lower])


def _setup_docks_locked_binding_for_app(app: AppBase[Any], window: QMainWindow, binding: str) -> None:
    """Set up reactive binding for locking/unlocking all docks."""
    from qtpie.variable import _get_variable_observable

    observable = _get_variable_observable(app, binding)
    if observable is None:
        return

    original_features: dict[QDockWidget, QDockWidget.DockWidgetFeature] = {}

    def on_locked_change(locked: bool) -> None:
        for dock_widget in window.findChildren(QDockWidget):
            if locked:
                if dock_widget not in original_features:
                    original_features[dock_widget] = dock_widget.features()
                features = dock_widget.features()
                features &= ~QDockWidget.DockWidgetFeature.DockWidgetMovable
                features &= ~QDockWidget.DockWidgetFeature.DockWidgetFloatable
                dock_widget.setFeatures(features)
            else:
                if dock_widget in original_features:
                    dock_widget.setFeatures(original_features[dock_widget])

    observable.on_change(on_locked_change)
    on_locked_change(observable.get())
