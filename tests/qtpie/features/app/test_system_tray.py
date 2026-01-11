# pyright: reportPrivateUsage=false
# pyright: reportMissingParameterType=false
# pyright: reportUnknownParameterType=false
# pyright: reportUntypedBaseClass=false
# pyright: reportUntypedClassDecorator=false
# pyright: reportUnknownArgumentType=false
# pyright: reportUnknownMemberType=false
# pyright: reportArgumentType=false
# pyright: reportOptionalMemberAccess=false
# pyright: reportIncompatibleMethodOverride=false
"""Tests for App system tray functionality.

System tray allows apps to show an icon in the system notification area
with an optional context menu.

NOTE: Apps with only QAction fields (no QWidgets) don't create an auto-window.
The system tray is created independently of the window.
"""

from assertpy import assert_that
from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import QLabel

from qtpie import AppBase, Menu, Variable, app, menu, new
from qtpie.menu import Separator
from qtpie.testing import QtDriver


class TestSystemTrayMenu:
    """System tray with explicit menu field."""

    def test_system_tray_menu_field(self, qt: QtDriver) -> None:
        """system_tray field defines tray context menu."""

        @menu(text="Tray")
        class TrayMenu(Menu):
            show: QAction = new("Show")
            quit: QAction = new("Quit")

        @app(system_tray=True)
        class MyApp(AppBase):
            system_tray: TrayMenu = new()

        a = MyApp()
        # No window to track (only Menu field, no QWidgets)

        assert_that(a.system_tray).is_instance_of(TrayMenu)
        assert_that(a.system_tray.actions()).is_length(2)

    def test_system_tray_with_underscore_prefix(self, qt: QtDriver) -> None:
        """_system_tray field also works."""

        @menu(text="Tray")
        class TrayMenu(Menu):
            show: QAction = new("Show")

        @app(system_tray=True)
        class MyApp(AppBase):
            _system_tray: TrayMenu = new()

        a = MyApp()
        # No window to track (only Menu field, no QWidgets)

        assert_that(a._system_tray).is_instance_of(TrayMenu)

    def test_system_tray_not_in_menu_bar(self, qt: QtDriver) -> None:
        """System tray menu is NOT added to window menu bar."""

        @menu(text="&File")
        class FileMenu(Menu):
            new_action: QAction = new("New")

        @menu(text="Tray")
        class TrayMenu(Menu):
            show: QAction = new("Show")

        @app(system_tray=True)
        class MyApp(AppBase):
            file_menu: FileMenu = new()  # Goes to menu bar
            system_tray: TrayMenu = new()  # Tray only
            label: QLabel = new("Content")  # Creates window

        a = MyApp()
        qt.track(a.window)

        # Only FileMenu in menu bar
        menu_bar_actions = a.window.menuBar().actions()
        menu_titles = [action.text() for action in menu_bar_actions]
        assert_that(menu_titles).contains("&File")
        assert_that(menu_titles).does_not_contain("Tray")


class TestSystemTrayActions:
    """System tray with QAction fields (auto-created menu)."""

    def test_qaction_fields_create_tray_menu(self, qt: QtDriver) -> None:
        """QAction fields are added to auto-created tray menu."""

        @app(system_tray=True)
        class MyApp(AppBase):
            show: QAction = new("Show Window")
            quit: QAction = new("Quit")

        a = MyApp()
        # No window to track (only QAction fields)

        # Actions should be accessible
        assert_that(a.show.text()).is_equal_to("Show Window")
        assert_that(a.quit.text()).is_equal_to("Quit")

    def test_qaction_with_separators(self, qt: QtDriver) -> None:
        """Separators work in tray action menu."""

        @app(system_tray=True)
        class MyApp(AppBase):
            show: QAction = new("Show")
            ____: Separator
            quit: QAction = new("Quit")

        a = MyApp()
        # No window to track (only QAction fields)

        assert_that(a.show.text()).is_equal_to("Show")
        assert_that(a.quit.text()).is_equal_to("Quit")


class TestSystemTrayDisabled:
    """System tray disabled."""

    def test_system_tray_disabled(self, qt: QtDriver) -> None:
        """system_tray=False prevents tray creation."""

        @app(system_tray=False)
        class MyApp(AppBase):
            label: QLabel = new("Hello")

        a = MyApp()
        qt.track(a.window)

        # App still works, just no tray
        assert_that(a.label.text()).is_equal_to("Hello")


class TestSystemTrayIcons:
    """System tray icon configuration."""

    def test_tray_icon_parameter(self, qt: QtDriver) -> None:
        """tray_icon parameter sets tray-specific icon."""

        @app(system_tray=True, tray_icon=QIcon())
        class MyApp(AppBase):
            show: QAction = new("Show")

        a = MyApp()
        # No window to track (only QAction field)

        # App created successfully with tray icon
        assert_that(a.show.text()).is_equal_to("Show")

    def test_icon_fallback_to_window_icon(self, qt: QtDriver) -> None:
        """icon parameter used as fallback for tray."""

        @app(system_tray=True, icon=QIcon())
        class MyApp(AppBase):
            show: QAction = new("Show")

        a = MyApp()
        # No window to track (only QAction field)

        assert_that(a.show.text()).is_equal_to("Show")


class TestSystemTrayWithWindow:
    """System tray combined with window."""

    def test_system_tray_with_window_content(self, qt: QtDriver) -> None:
        """App can have both window content and system tray."""

        @menu(text="Tray")
        class TrayMenu(Menu):
            show: QAction = new("Show")

        @app(title="My App", system_tray=True)
        class MyApp(AppBase):
            label: QLabel = new("Window Content")
            system_tray: TrayMenu = new()

        a = MyApp()
        qt.track(a.window)

        assert_that(a.label.text()).is_equal_to("Window Content")
        assert_that(a.system_tray).is_instance_of(TrayMenu)
        assert_that(a.window.windowTitle()).is_equal_to("My App")


class TestSystemTraySignals:
    """System tray action signal connections."""

    def test_tray_action_triggered(self, qt: QtDriver) -> None:
        """triggered= connects tray action to method."""

        @app(system_tray=True)
        class MyApp(AppBase):
            clicked: bool = False
            show: QAction = new("Show", triggered="on_show")

            def on_show(self) -> None:
                self.clicked = True

        a = MyApp()
        # No window to track (only QAction field)

        a.show.trigger()
        assert_that(a.clicked).is_true()

    def test_tray_menu_action_triggered(self, qt: QtDriver) -> None:
        """triggered= works in system_tray Menu."""

        @menu(text="Tray")
        class TrayMenu(Menu):
            clicked: bool = False
            show: QAction = new("Show", triggered="on_show")

            def on_show(self) -> None:
                self.clicked = True

        @app(system_tray=True)
        class MyApp(AppBase):
            system_tray: TrayMenu = new()

        a = MyApp()
        # No window to track (only Menu field)

        a.system_tray.show.trigger()
        assert_that(a.system_tray.clicked).is_true()


class TestSystemTrayWithVariables:
    """System tray with reactive variables."""

    def test_tray_action_enabled_binding(self, qt: QtDriver) -> None:
        """Tray action enabled= binds to Variable."""

        @app(system_tray=True)
        class MyApp(AppBase):
            _can_quit: Variable[bool] = new(False)
            quit: QAction = new("Quit", enabled="_can_quit")

        a = MyApp()
        # No window to track (only Variable + QAction)

        assert_that(a.quit.isEnabled()).is_false()

        a._can_quit.value = True
        assert_that(a.quit.isEnabled()).is_true()
