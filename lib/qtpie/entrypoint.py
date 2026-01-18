"""The @entrypoint decorator for declarative app entry points."""

import asyncio
import signal
import tempfile
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, cast, overload

import qasync  # type: ignore[import-untyped]
from qtpy.QtCore import QFile, QIODeviceBase, QTextStream, QTimer
from qtpy.QtWidgets import QApplication, QWidget

from qtpie.styles.color_scheme import ColorScheme, set_color_scheme
from qtpie.styles.watcher import QssWatcher, ScssWatcher

# Import App and run_app lazily to avoid circular imports
_App: type | None = None
_run_app_fn: Callable[..., int] | None = None


def _get_app_class() -> type:
    """Lazily import App class to avoid circular imports."""
    global _App
    if _App is None:
        from qtpie.app import App

        _App = App
    return _App


def _get_run_app_fn() -> Callable[..., int]:
    """Lazily import run_app function to avoid circular imports."""
    global _run_app_fn
    if _run_app_fn is None:
        from qtpie.app import run_app

        _run_app_fn = run_app
    return _run_app_fn


@dataclass(frozen=True)
class EntryConfig:
    """Configuration stored by @entrypoint decorator."""

    dark_mode: bool = False
    light_mode: bool = False
    title: str | None = None
    size: tuple[int, int] | None = None
    stylesheet: str | None = None
    watch_stylesheet: bool = False
    scss_search_paths: tuple[str, ...] = field(default_factory=tuple)
    scss_output: str | None = None  # Output path for compiled SCSS -> QSS
    window: type[QWidget] | None = None
    # Translation support
    translations: str | tuple[str, ...] | None = None
    language: str = "en"
    watch_translations: bool = False
    # Theme support
    themes: str | None = None  # Path to themes directory
    theme: str | None = None  # Initial theme name
    watch_themes: bool = False  # Hot-reload themes
    themes_output: str | None = None  # Output path for compiled theme SCSS


# Attribute name for storing entry config
ENTRY_CONFIG_ATTR = "_qtpie_entry_config"


def _is_main_module(target: Any) -> bool:
    """Check if target's module is __main__."""
    return getattr(target, "__module__", None) == "__main__"


def _should_auto_run(target: Any) -> bool:
    """Check if we should auto-run the entry point."""
    return _is_main_module(target) and QApplication.instance() is None


def _load_qrc_stylesheet(qrc_path: str) -> str:
    """Load stylesheet content from a QRC resource path."""
    qrc_file = QFile(qrc_path)
    if qrc_file.open(QIODeviceBase.OpenModeFlag.ReadOnly | QIODeviceBase.OpenModeFlag.Text):
        stream = QTextStream(qrc_file)
        content = stream.readAll()
        qrc_file.close()
        return content
    return ""


def _compile_scss_to_string(scss_path: str, search_paths: list[str]) -> str:
    """Compile SCSS file to a QSS string."""
    from scss import Compiler  # type: ignore[import-untyped]

    scss_file = Path(scss_path)
    if not scss_file.exists():
        return ""

    compiler = Compiler(search_path=search_paths)
    return cast(str, compiler.compile(str(scss_file)))  # pyright: ignore[reportUnknownMemberType]


def _apply_stylesheet(app: QApplication, config: EntryConfig) -> QssWatcher | ScssWatcher | None:
    """
    Apply stylesheet to the application based on config.

    Supports:
    - QRC paths (e.g., ":/styles/app.qss") - loads from Qt resources
    - QSS files (e.g., "styles.qss") - loads from filesystem
    - SCSS files (e.g., "styles.scss") - compiles and applies

    If watch_stylesheet=True and not a QRC path, sets up hot-reloading.

    Returns a watcher if watch_stylesheet=True, otherwise None.
    """
    if not config.stylesheet:
        return None

    stylesheet_path = config.stylesheet
    is_qrc = stylesheet_path.startswith(":/")
    is_scss = stylesheet_path.endswith(".scss")

    # Determine search paths for SCSS
    if config.scss_search_paths:
        search_paths = list(config.scss_search_paths)
    elif is_scss:
        # Auto-add the SCSS file's parent folder
        search_paths = [str(Path(stylesheet_path).parent)]
    else:
        search_paths = []

    if config.watch_stylesheet and not is_qrc:
        # Set up a watcher - it will handle initial load too
        if is_scss:
            # Use configured output path or create a temp file
            if config.scss_output:
                qss_path = config.scss_output
            else:
                temp_dir = Path(tempfile.gettempdir()) / "qtpie_scss"
                temp_dir.mkdir(exist_ok=True)
                qss_path = str(temp_dir / f"{Path(stylesheet_path).stem}.qss")
            return ScssWatcher(app, stylesheet_path, qss_path, search_paths or None)
        else:
            # QSS file
            return QssWatcher(app, stylesheet_path)

    # One-shot load (no watching)
    if is_qrc:
        content = _load_qrc_stylesheet(stylesheet_path)
    elif is_scss:
        content = _compile_scss_to_string(stylesheet_path, search_paths)
    else:
        # Regular QSS file
        qss_file = Path(stylesheet_path)
        content = qss_file.read_text() if qss_file.exists() else ""

    if content:
        app.setStyleSheet(content)

    return None


def _load_translations(app: QApplication, config: EntryConfig) -> Any:
    """Load translations and optionally set up hot-reload watcher.

    Returns the watcher if watch_translations=True, otherwise None.
    """
    if config.translations is None:
        return None

    from qtpie.translations import load_translations_from_yaml, set_language, watch_translations

    # Set language
    set_language(config.language)

    # Load translation YAML files
    if isinstance(config.translations, str):
        paths: list[str | Path] = [config.translations]
    else:
        paths = list(config.translations)

    load_translations_from_yaml(paths)

    # Set up hot-reload if requested
    if config.watch_translations:
        # Convert to Path objects for watcher
        path_objects = [Path(p) for p in paths]
        return watch_translations(path_objects, config.language, parent=app)

    return None


def _load_themes(app: QApplication, config: EntryConfig) -> Any:
    """Load themes and optionally set up hot-reload watcher.

    If themes= is specified, the theme system takes precedence over
    dark_mode/light_mode and stylesheet= parameters.

    Returns the ThemeWatcher if watch_themes=True, otherwise None.
    """
    if config.themes is None:
        return None

    from qtpie.styles.theme_runtime import init_themes

    return init_themes(
        themes_dir=config.themes,
        app=app,
        initial_theme=config.theme,
        watch=config.watch_themes,
        output_dir=config.themes_output,
    )


def _run_entrypoint(target: Any, config: EntryConfig) -> None:
    """Execute the entry point."""
    App = _get_app_class()
    run_app_fn = _get_run_app_fn()

    # Determine what kind of target we have
    is_function = callable(target) and not isinstance(target, type)
    is_class = isinstance(target, type)
    is_app_subclass = is_class and issubclass(target, QApplication)

    window: QWidget | None = None
    app: QApplication

    # Keep watchers alive for duration of app
    _watcher: QssWatcher | ScssWatcher | None = None
    _translation_watcher: Any = None
    _theme_watcher: Any = None

    def create_default_app() -> QApplication:
        """Create app with dark/light mode from config."""
        app_kwargs: dict[str, Any] = {}
        # Don't set dark/light mode if themes are being used
        # (themes will set color scheme based on selected theme)
        if config.themes is None:
            if config.dark_mode:
                app_kwargs["dark_mode"] = True
            if config.light_mode:
                app_kwargs["light_mode"] = True
        return App(**app_kwargs)

    def setup_app(application: QApplication) -> None:
        """Apply translations, themes, and stylesheet to app."""
        nonlocal _translation_watcher, _watcher, _theme_watcher
        _translation_watcher = _load_translations(application, config)

        # Themes take precedence over stylesheet
        if config.themes is not None:
            _theme_watcher = _load_themes(application, config)
        else:
            _watcher = _apply_stylesheet(application, config)

    if is_app_subclass:
        # Target is an App or QApplication subclass
        app = cast(QApplication, target())
        # Apply color scheme from config to the app
        if config.dark_mode:
            set_color_scheme(ColorScheme.Dark, app)
        elif config.light_mode:
            set_color_scheme(ColorScheme.Light, app)
        setup_app(app)

    elif is_function:
        func = cast(Callable[..., Any], target)

        if asyncio.iscoroutinefunction(func):
            # Async function - need app for event loop first
            app = create_default_app()
            setup_app(app)

            loop = qasync.QEventLoop(app)
            asyncio.set_event_loop(loop)

            # Handle CTRL-C gracefully
            def handle_sigint(*_: object) -> None:
                app.quit()

            signal.signal(signal.SIGINT, handle_sigint)

            # Timer to let Python process signals
            signal_timer = QTimer()
            signal_timer.timeout.connect(lambda: None)
            signal_timer.start(100)

            with loop:
                result: Any = loop.run_until_complete(func())  # pyright: ignore[reportUnknownMemberType,reportUnknownVariableType]
                if isinstance(result, QWidget):
                    window = result
                # Now continue with the event loop
                quit_event = asyncio.Event()
                app.aboutToQuit.connect(quit_event.set)
                if window is not None:
                    _apply_window_config(window, config)
                    window.show()
                loop.run_until_complete(quit_event.wait())  # pyright: ignore[reportUnknownMemberType]
            return
        else:
            # Sync function - call it first to check if it returns an app
            result = func()

            if isinstance(result, QApplication):
                # Function returned an app - use it directly
                app = result
                # Apply color scheme from config to the returned app
                if config.dark_mode:
                    set_color_scheme(ColorScheme.Dark, app)
                elif config.light_mode:
                    set_color_scheme(ColorScheme.Light, app)
            else:
                # Create default app
                app = create_default_app()
                if isinstance(result, QWidget):
                    window = result

            setup_app(app)

    else:
        # Widget class
        app = create_default_app()
        setup_app(app)

        if is_class:
            widget_cls = cast(type[QWidget], target)
            window = widget_cls()

    # Handle window= parameter
    if config.window is not None and window is None:
        window = config.window()

    # Apply config to window
    if window is not None:
        _apply_window_config(window, config)
        window.show()

    # Run the app - use app.run() if it exists (for App subclasses with auto-show)
    # otherwise use the standalone helper
    run_method = getattr(app, "run", None)
    if run_method is not None and callable(run_method):
        run_method()
    else:
        run_app_fn(app)


def _apply_window_config(window: QWidget, config: EntryConfig) -> None:
    """Apply configuration to the window."""
    if config.title is not None:
        window.setWindowTitle(config.title)
    if config.size is not None:
        window.resize(*config.size)


# Overload order matters: type[T] must come before Callable since classes are callable
@overload
def entrypoint[T](
    _target: type[T],
    *,
    dark_mode: bool = ...,
    light_mode: bool = ...,
    title: str | None = ...,
    size: tuple[int, int] | None = ...,
    stylesheet: str | None = ...,
    watch_stylesheet: bool = ...,
    scss_search_paths: list[str] | None = ...,
    scss_output: str | None = ...,
    window: type[QWidget] | None = ...,
    translations: str | list[str] | None = ...,
    language: str = ...,
    watch_translations: bool = ...,
    themes: str | None = ...,
    theme: str | None = ...,
    watch_themes: bool = ...,
    themes_output: str | None = ...,
) -> type[T]: ...


@overload
def entrypoint[T](
    _target: Callable[..., T],
    *,
    dark_mode: bool = ...,
    light_mode: bool = ...,
    title: str | None = ...,
    size: tuple[int, int] | None = ...,
    stylesheet: str | None = ...,
    watch_stylesheet: bool = ...,
    scss_search_paths: list[str] | None = ...,
    scss_output: str | None = ...,
    window: type[QWidget] | None = ...,
    translations: str | list[str] | None = ...,
    language: str = ...,
    watch_translations: bool = ...,
    themes: str | None = ...,
    theme: str | None = ...,
    watch_themes: bool = ...,
    themes_output: str | None = ...,
) -> Callable[..., T]: ...


@overload
def entrypoint[T](
    _target: None = None,
    *,
    dark_mode: bool = ...,
    light_mode: bool = ...,
    title: str | None = ...,
    size: tuple[int, int] | None = ...,
    stylesheet: str | None = ...,
    watch_stylesheet: bool = ...,
    scss_search_paths: list[str] | None = ...,
    scss_output: str | None = ...,
    window: type[QWidget] | None = ...,
    translations: str | list[str] | None = ...,
    language: str = ...,
    watch_translations: bool = ...,
    themes: str | None = ...,
    theme: str | None = ...,
    watch_themes: bool = ...,
    themes_output: str | None = ...,
) -> Callable[[Callable[..., T] | type[T]], Callable[..., T] | type[T]]: ...


def entrypoint(
    _target: Callable[..., Any] | type | None = None,
    *,
    dark_mode: bool = False,
    light_mode: bool = False,
    title: str | None = None,
    size: tuple[int, int] | None = None,
    stylesheet: str | None = None,
    watch_stylesheet: bool = False,
    scss_search_paths: list[str] | None = None,
    scss_output: str | None = None,
    window: type[QWidget] | None = None,
    translations: str | list[str] | None = None,
    language: str = "en",
    watch_translations: bool = False,
    themes: str | None = None,
    theme: str | None = None,
    watch_themes: bool = False,
    themes_output: str | None = None,
) -> Any:
    """
    Decorator that marks a function or class as the application entry point.

    When the decorated item's module is __main__ (i.e., the file is run directly),
    this decorator will automatically create an App, run the entry point, and
    start the event loop.

    When imported (module is not __main__), the decorator does nothing except
    store configuration, allowing the class/function to be used normally.

    Args:
        dark_mode: Enable dark mode color scheme.
        light_mode: Enable light mode color scheme.
        title: Window title to set.
        size: Window size as (width, height) tuple.
        stylesheet: Path to stylesheet. Can be:
            - QRC path (e.g., ":/styles/app.qss") - loads from Qt resources
            - QSS file (e.g., "styles.qss") - loads from filesystem
            - SCSS file (e.g., "styles.scss") - compiles and applies
        watch_stylesheet: If True, hot-reload stylesheet on file changes.
            Not applicable to QRC paths.
        scss_search_paths: Directories for SCSS @import resolution.
            If not provided, the SCSS file's parent folder is used.
        scss_output: Output path for compiled SCSS -> QSS file.
            If not provided, uses a temp directory. Only used with SCSS files.
        window: A widget class to instantiate as the main window.
        translations: Path or list of paths to translation YAML files.
        language: Language code to use (e.g., "en", "fr", "de"). Default is "en".
        watch_translations: If True, hot-reload translations on file changes.
        themes: Path to themes directory. Supports:
            - Filesystem paths (e.g., "./themes")
            - QRC paths (e.g., ":/themes") - QSS only, no watching
            Themes can be QSS files or SCSS folders. Takes precedence over
            stylesheet= and dark_mode=/light_mode= parameters.
        theme: Initial theme name to activate.
        watch_themes: If True, hot-reload theme files on changes.
            Not applicable to QRC paths.
        themes_output: Output directory for compiled theme SCSS -> QSS files.
            If not provided, uses a temp directory.

    Examples:
        # Simplest - function returning a widget
        @entrypoint
        def main():
            return QLabel("Hello World!")

        # With configuration
        @entrypoint(dark_mode=True, title="My App", size=(800, 600))
        def main():
            return MyWidget()

        # With stylesheet
        @entrypoint(stylesheet="styles.qss")
        def main():
            return MyWidget()

        # With SCSS and hot-reload
        @entrypoint(stylesheet="styles.scss", watch_stylesheet=True)
        def main():
            return MyWidget()

        # On a @widget class
        @entrypoint
        @widget
        class MyApp(QWidget):
            label: QLabel = new(QLabel, "Hello!")

        # Async function
        @entrypoint
        async def main():
            data = await fetch_data()
            return DataViewer(data)

        # App subclass with lifecycle hooks
        @entrypoint
        class MyApp(App):
            def __setup__(self):
                print("Setting up!")

        # With themes
        @entrypoint(themes="./themes", theme="dark", watch_themes=True)
        def main():
            return MyWidget()
    """
    config = EntryConfig(
        dark_mode=dark_mode,
        light_mode=light_mode,
        title=title,
        size=size,
        stylesheet=stylesheet,
        watch_stylesheet=watch_stylesheet,
        scss_search_paths=tuple(scss_search_paths) if scss_search_paths else (),
        scss_output=scss_output,
        window=window,
        translations=translations if isinstance(translations, str) else tuple(translations) if translations else None,
        language=language,
        watch_translations=watch_translations,
        themes=themes,
        theme=theme,
        watch_themes=watch_themes,
        themes_output=themes_output,
    )

    def decorator(target: Callable[..., Any] | type) -> Callable[..., Any] | type:
        # Store config on target
        setattr(target, ENTRY_CONFIG_ATTR, config)

        # Check if we should auto-run
        if _should_auto_run(target):
            _run_entrypoint(target, config)

        return target

    if _target is not None:
        # Called without parentheses: @entrypoint
        return decorator(_target)

    # Called with parentheses: @entrypoint(...)
    return decorator
