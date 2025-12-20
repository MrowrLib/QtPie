"""The @entry_point decorator for declarative app entry points."""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, cast, overload

from qtpy.QtWidgets import QApplication, QWidget

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
    """Configuration stored by @entry_point decorator."""

    dark_mode: bool = False
    light_mode: bool = False
    title: str | None = None
    size: tuple[int, int] | None = None
    stylesheet: str | None = None
    window: type[QWidget] | None = None


# Attribute name for storing entry config
ENTRY_CONFIG_ATTR = "_qtpie_entry_config"


def _is_main_module(target: Any) -> bool:
    """Check if target's module is __main__."""
    return getattr(target, "__module__", None) == "__main__"


def _should_auto_run(target: Any) -> bool:
    """Check if we should auto-run the entry point."""
    return _is_main_module(target) and QApplication.instance() is None


def _run_entry_point(target: Any, config: EntryConfig) -> None:
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

    if is_app_subclass:
        # Target is an App or QApplication subclass
        app = cast(QApplication, target())

        # Call create_window if it exists and is overridden
        create_window_method: Callable[[], QWidget | None] | None = getattr(app, "create_window", None)
        if create_window_method is not None and callable(create_window_method):
            result = create_window_method()
            if isinstance(result, QWidget):
                window = result
    else:
        # Create a default App
        app = App(**app_kwargs)

        if is_function:
            # Target is a function
            func = cast(Callable[..., Any], target)
            if asyncio.iscoroutinefunction(func):
                # Async function - need to run it in the event loop
                # We'll run it before the main loop
                import qasync  # type: ignore[import-untyped]

                loop = qasync.QEventLoop(app)
                asyncio.set_event_loop(loop)
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
def entry_point[T](
    _target: type[T],
    *,
    dark_mode: bool = ...,
    light_mode: bool = ...,
    title: str | None = ...,
    size: tuple[int, int] | None = ...,
    stylesheet: str | None = ...,
    window: type[QWidget] | None = ...,
) -> type[T]: ...


@overload
def entry_point[T](
    _target: Callable[..., T],
    *,
    dark_mode: bool = ...,
    light_mode: bool = ...,
    title: str | None = ...,
    size: tuple[int, int] | None = ...,
    stylesheet: str | None = ...,
    window: type[QWidget] | None = ...,
) -> Callable[..., T]: ...


@overload
def entry_point[T](
    _target: None = None,
    *,
    dark_mode: bool = ...,
    light_mode: bool = ...,
    title: str | None = ...,
    size: tuple[int, int] | None = ...,
    stylesheet: str | None = ...,
    window: type[QWidget] | None = ...,
) -> Callable[[Callable[..., T] | type[T]], Callable[..., T] | type[T]]: ...


def entry_point(
    _target: Callable[..., Any] | type | None = None,
    *,
    dark_mode: bool = False,
    light_mode: bool = False,
    title: str | None = None,
    size: tuple[int, int] | None = None,
    stylesheet: str | None = None,
    window: type[QWidget] | None = None,
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
        stylesheet: Path to a QSS/SCSS stylesheet to load.
        window: A widget class to instantiate as the main window.

    Examples:
        # Simplest - function returning a widget
        @entry_point
        def main():
            return QLabel("Hello World!")

        # With configuration
        @entry_point(dark_mode=True, title="My App", size=(800, 600))
        def main():
            return MyWidget()

        # On a @widget class
        @entry_point
        @widget
        class MyApp(QWidget):
            label: QLabel = make(QLabel, "Hello!")

        # On a @window class
        @entry_point(dark_mode=True)
        @window(title="My Application")
        class MyApp(QMainWindow):
            ...

        # Async function
        @entry_point
        async def main():
            data = await fetch_data()
            return DataViewer(data)

        # App subclass with lifecycle hooks
        @entry_point
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
        window=window,
    )

    def decorator(target: Callable[..., Any] | type) -> Callable[..., Any] | type:
        # Store config on target
        setattr(target, ENTRY_CONFIG_ATTR, config)

        # Check if we should auto-run
        if _should_auto_run(target):
            _run_entry_point(target, config)

        return target

    if _target is not None:
        # Called without parentheses: @entry_point
        return decorator(_target)

    # Called with parentheses: @entry_point(...)
    return decorator
