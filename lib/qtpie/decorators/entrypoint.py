"""The @entrypoint decorator for declarative app entry points."""

from __future__ import annotations

import asyncio
import tempfile
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, cast, overload

from qtpy.QtCore import QFile, QIODevice, QTextStream
from qtpy.QtWidgets import QApplication, QWidget

from qtpie.styles.watcher import QssWatcher, ScssWatcher
from qtpie.translations.watcher import TranslationWatcher

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
    window: type[QWidget] | None = None
    translations: str | None = None
    language: str | None = None  # None = use system locale
    watch_translations: bool = False


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
    if qrc_file.open(QIODevice.OpenModeFlag.ReadOnly | QIODevice.OpenModeFlag.Text):
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


def _get_system_language() -> str:
    """Get the system language code from Qt's locale detection."""
    from qtpy.QtCore import QLocale

    # QLocale.system().name() returns e.g. "fr_FR", "de_DE", "en_US"
    # Extract just the language part (first 2 chars)
    locale_name = QLocale.system().name()
    return locale_name.split("_")[0] if "_" in locale_name else locale_name


def _apply_translations(config: EntryConfig) -> TranslationWatcher | None:
    """
    Apply translations based on config.

    Supports:
    - Filesystem paths (Path or string)
    - QRC paths (e.g., ":/translations/app.yml")
    - .yml/.yaml files (YAML format, parsed into memory)
    - .qm files (Qt binary format, loaded via QTranslator)
    - Automatic system locale detection when language is not specified

    Returns a watcher if watch_translations=True and path is watchable, otherwise None.
    """
    import logging

    from qtpie.translations.loader import can_watch_path

    if not config.translations:
        return None

    translations_path = config.translations
    is_qm_file = translations_path.endswith(".qm")
    is_watchable = can_watch_path(translations_path)

    # Resolve language - use system locale if not specified
    language = config.language if config.language is not None else _get_system_language()

    # Handle .qm files (Qt binary translation format)
    if is_qm_file:
        from qtpy.QtCore import QCoreApplication, QTranslator

        translator = QTranslator()
        if translator.load(translations_path):
            app = QCoreApplication.instance()
            if app is not None:
                app.installTranslator(translator)

        if config.watch_translations and not is_watchable:
            logging.getLogger("qtpie").info(f"watch_translations ignored for QRC path: {translations_path}")
        return None

    # Handle YAML files
    from qtpie.translations.store import load_translations_from_yaml, set_language
    from qtpie.translations.translatable import enable_memory_store

    if config.watch_translations:
        if is_watchable:
            # Set up watcher - it handles initial load (filesystem paths only)
            return TranslationWatcher(Path(translations_path), language)
        else:
            # QRC path - can't watch, just load once
            logging.getLogger("qtpie").info(f"watch_translations ignored for QRC path: {translations_path}")

    # One-shot load (no watching) - works for both filesystem and QRC
    enable_memory_store(True)
    set_language(language)
    load_translations_from_yaml(translations_path)

    return None


def _apply_stylesheet(app: QApplication, config: EntryConfig) -> QssWatcher | ScssWatcher | None:
    """
    Apply stylesheet to the application based on config.

    Returns a watcher if watch_stylesheet=True, otherwise None.
    """
    if not config.stylesheet:
        return None

    stylesheet_path = config.stylesheet
    is_qrc = stylesheet_path.startswith(":/")
    is_scss = stylesheet_path.endswith(".scss")

    # Determine search paths for SCSS
    if config.scss_search_paths:
        # Use explicit paths only
        search_paths = list(config.scss_search_paths)
    elif is_scss:
        # Auto-add the SCSS file's parent folder
        search_paths = [str(Path(stylesheet_path).parent)]
    else:
        search_paths = []

    if config.watch_stylesheet and not is_qrc:
        # Set up a watcher - it will handle initial load too
        if is_scss:
            # Create a temp file for compiled QSS
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


def _run_entrypoint(target: Any, config: EntryConfig) -> None:
    """Execute the entry point."""
    App = _get_app_class()
    run_app_fn = _get_run_app_fn()

    # Create the App instance
    app_kwargs: dict[str, Any] = {}
    if config.dark_mode:
        app_kwargs["dark_mode"] = True
    if config.light_mode:
        app_kwargs["light_mode"] = True

    # Determine what kind of target we have
    is_function = callable(target) and not isinstance(target, type)
    is_class = isinstance(target, type)
    is_app_subclass = is_class and issubclass(target, QApplication)

    window: QWidget | None = None
    app: QApplication

    # Keep watchers alive for duration of app
    _watcher: QssWatcher | ScssWatcher | None = None
    _translation_watcher: TranslationWatcher | None = None

    # Apply translations BEFORE creating widgets (so tr["..."] works)
    _translation_watcher = _apply_translations(config)

    if is_app_subclass:
        # Target is an App or QApplication subclass
        app = cast(QApplication, target())

        # Apply stylesheet to the app
        _watcher = _apply_stylesheet(app, config)

        # Call create_window if it exists and is overridden
        create_window_method: Callable[[], QWidget | None] | None = getattr(app, "create_window", None)
        if create_window_method is not None and callable(create_window_method):
            result = create_window_method()
            if isinstance(result, QWidget):
                window = result
    else:
        # Create a default App
        app = App(**app_kwargs)

        # Apply stylesheet to the app
        _watcher = _apply_stylesheet(app, config)

        if is_function:
            # Target is a function
            func = cast(Callable[..., Any], target)
            if asyncio.iscoroutinefunction(func):
                # Async function - need to run it in the event loop
                # We'll run it before the main loop
                import signal

                import qasync  # type: ignore[import-untyped]
                from qtpy.QtCore import QTimer

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
                # Sync function
                result = func()
                if isinstance(result, QWidget):
                    window = result
        elif is_class:
            # Target is a widget class (decorated with @widget or @window)
            widget_cls = cast(type[QWidget], target)
            window = widget_cls()

        # Handle window= parameter
        if config.window is not None and window is None:
            window = config.window()

    # Apply config to window
    if window is not None:
        _apply_window_config(window, config)
        window.show()

    # Run the app using the standalone helper
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
    window: type[QWidget] | None = ...,
    translations: str | None = ...,
    language: str | None = ...,
    watch_translations: bool = ...,
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
    window: type[QWidget] | None = ...,
    translations: str | None = ...,
    language: str | None = ...,
    watch_translations: bool = ...,
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
    window: type[QWidget] | None = ...,
    translations: str | None = ...,
    language: str | None = ...,
    watch_translations: bool = ...,
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
    window: type[QWidget] | None = None,
    translations: str | None = None,
    language: str | None = None,
    watch_translations: bool = False,
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
        window: A widget class to instantiate as the main window.
        translations: Path to YAML translation file.
        language: Language code for translations. If None (default), uses system locale.
        watch_translations: If True, hot-reload translations on file changes.

    Examples:
        # Simplest - function returning a widget
        @entrypoint
        def main():
            return QLabel("Hello World!")

        # With configuration
        @entrypoint(dark_mode=True, title="My App", size=(800, 600))
        def main():
            return MyWidget()

        # On a @widget class
        @entrypoint
        @widget
        class MyApp(QWidget):
            label: QLabel = make(QLabel, "Hello!")

        # On a @window class
        @entrypoint(dark_mode=True)
        @window(title="My Application")
        class MyApp(QMainWindow):
            ...

        # Async function
        @entrypoint
        async def main():
            data = await fetch_data()
            return DataViewer(data)

        # App subclass with lifecycle hooks
        @entrypoint
        class MyApp(App):
            def setup(self):
                self.load_stylesheet("styles.qss")

            def create_window(self):
                return MyMainWindow()
    """
    config = EntryConfig(
        dark_mode=dark_mode,
        light_mode=light_mode,
        title=title,
        size=size,
        stylesheet=stylesheet,
        watch_stylesheet=watch_stylesheet,
        scss_search_paths=tuple(scss_search_paths) if scss_search_paths else (),
        window=window,
        translations=translations,
        language=language,
        watch_translations=watch_translations,
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
