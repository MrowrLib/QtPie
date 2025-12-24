"""App class - a QApplication subclass with lifecycle hooks and qasync support."""

import asyncio
import signal
import sys
from collections.abc import Sequence

import qasync  # type: ignore[import-untyped]
from qtpy.QtWidgets import QApplication, QWidget

from qtpie.styles.color_scheme import ColorScheme, apply_deferred_color_scheme, set_color_scheme
from qtpie.styles.loader import load_stylesheet as _load_stylesheet


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
    from qtpy.QtCore import QTimer

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


class App(QApplication):
    """
    A QApplication subclass with lifecycle hooks and qasync integration.

    Features:
    - Lifecycle hooks: setup(), setup_styles(), create_window()
    - Dark/light mode support
    - Stylesheet loading
    - qasync event loop for async/await support

    Examples:
        # Simple usage
        app = App("My App", dark_mode=True)
        window = MyMainWindow()
        window.show()
        app.run()

        # Subclass with hooks
        class MyApp(App):
            def setup(self):
                self.load_stylesheet("styles.qss")

            def create_window(self):
                return MyMainWindow()
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

        # Initialize QApplication
        if argv is None:
            argv = sys.argv
        super().__init__(list(argv))

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

        # Call lifecycle hooks
        self._call_lifecycle_hooks()

    def _call_lifecycle_hooks(self) -> None:
        """Call lifecycle hooks if defined in subclass."""
        # Check if setup is overridden (not the base class stub)
        if type(self).setup is not App.setup:
            self.setup()

        if type(self).setup_styles is not App.setup_styles:
            self.setup_styles()

    def setup(self) -> None:
        """
        Lifecycle hook called after App initialization.

        Override this method in subclasses to perform custom setup.
        """

    def setup_styles(self) -> None:
        """
        Lifecycle hook for setting up stylesheets.

        Override this method in subclasses to load stylesheets.
        """

    def create_window(self) -> QWidget | None:
        """
        Lifecycle hook to create the main window.

        Override this method in subclasses to return a main window widget.
        The @entrypoint decorator will call this and show the returned widget.

        Returns:
            A QWidget to show as the main window, or None.
        """
        return None

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

        This method blocks until the application exits.

        Returns:
            The application exit code.
        """
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
