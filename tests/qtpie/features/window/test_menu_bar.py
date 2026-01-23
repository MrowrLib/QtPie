# pyright: reportPrivateUsage=false
# pyright: reportMissingParameterType=false
# pyright: reportUnknownParameterType=false
# pyright: reportUntypedBaseClass=false
# pyright: reportUntypedClassDecorator=false
# pyright: reportUnknownArgumentType=false
# pyright: reportUnknownMemberType=false
"""Tests for Window menu bar integration.

Window class automatically adds Menu fields to the window's menu bar.
"""

from assertpy import assert_that
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QLabel

from qtpie import Menu, Variable, Window, menu, new, window
from qtpie.testing import QtDriver


class TestMenuBarBasic:
    """Basic menu bar functionality."""

    def test_single_menu_in_menu_bar(self, qt: QtDriver) -> None:
        """Single Menu field is added to window menu bar."""

        @menu(text="&File")
        class FileMenu(Menu):
            new_action: QAction = new("&New")
            exit_action: QAction = new("E&xit")

        @window(title="Test App")
        class TestWindow(Window):
            file_menu: FileMenu = new()
            content: QLabel = new("Content")

        w = TestWindow()
        qt.track(w)

        # Menu should be in menu bar
        menu_bar = w.menuBar()
        actions = menu_bar.actions()
        assert_that(actions).is_length(1)
        assert_that(actions[0].text()).is_equal_to("&File")

    def test_multiple_menus_in_menu_bar(self, qt: QtDriver) -> None:
        """Multiple Menu fields are added to menu bar in order."""

        @menu(text="&File")
        class FileMenu(Menu):
            new_action: QAction = new("&New")

        @menu(text="&Edit")
        class EditMenu(Menu):
            cut: QAction = new("Cu&t")

        @menu(text="&Help")
        class HelpMenu(Menu):
            about: QAction = new("&About")

        @window(title="Test App")
        class TestWindow(Window):
            file_menu: FileMenu = new()
            edit_menu: EditMenu = new()
            help_menu: HelpMenu = new()
            content: QLabel = new("Content")

        w = TestWindow()
        qt.track(w)

        menu_bar = w.menuBar()
        actions = menu_bar.actions()
        assert_that(actions).is_length(3)
        assert_that([a.text() for a in actions]).is_equal_to(["&File", "&Edit", "&Help"])

    def test_menu_actions_accessible(self, qt: QtDriver) -> None:
        """Menu actions are accessible via nested attribute access."""

        @menu(text="&File")
        class FileMenu(Menu):
            new_action: QAction = new("&New")
            save_action: QAction = new("&Save")

        @window(title="Test App")
        class TestWindow(Window):
            file_menu: FileMenu = new()

        w = TestWindow()
        qt.track(w)

        assert_that(w.file_menu.new_action.text()).is_equal_to("&New")
        assert_that(w.file_menu.save_action.text()).is_equal_to("&Save")


class TestMenuBarOrder:
    """Menu bar ordering and field positioning."""

    def test_menus_before_widgets(self, qt: QtDriver) -> None:
        """Menu fields declared before widgets still go to menu bar."""

        @menu(text="&File")
        class FileMenu(Menu):
            action: QAction = new("Action")

        @window(title="Test")
        class TestWindow(Window):
            file_menu: FileMenu = new()
            label: QLabel = new("Label")

        w = TestWindow()
        qt.track(w)

        # Menu in menu bar
        assert_that(w.menuBar().actions()).is_length(1)
        # Label is widget, not in menu bar
        assert_that(w.label.text()).is_equal_to("Label")

    def test_menus_after_widgets(self, qt: QtDriver) -> None:
        """Menu fields declared after widgets still go to menu bar."""

        @menu(text="&File")
        class FileMenu(Menu):
            action: QAction = new("Action")

        @window(title="Test")
        class TestWindow(Window):
            label: QLabel = new("Label")
            file_menu: FileMenu = new()

        w = TestWindow()
        qt.track(w)

        # Menu in menu bar
        assert_that(w.menuBar().actions()).is_length(1)
        # Label is widget
        assert_that(w.label.text()).is_equal_to("Label")


class TestMenuSignals:
    """Menu action signals in Window context."""

    def test_menu_action_triggered_in_menu(self, qt: QtDriver) -> None:
        """triggered= connects menu action to Menu method."""

        @menu(text="&File")
        class FileMenu(Menu):
            clicked: bool = False
            action: QAction = new("Action", triggered="on_action")

            def on_action(self) -> None:
                self.clicked = True

        @window(title="Test")
        class TestWindow(Window):
            file_menu: FileMenu = new()

        w = TestWindow()
        qt.track(w)

        w.file_menu.action.trigger()
        assert_that(w.file_menu.clicked).is_true()

    def test_menu_action_can_access_parent_window(self, qt: QtDriver) -> None:
        """Menu action can access parent window via #parent."""

        @menu(text="&File")
        class FileMenu(Menu):
            action: QAction = new("Action", triggered="toggle_flag")

            def toggle_flag(self) -> None:
                # Menu can access _parent_window set by Window
                parent = getattr(self, "_parent_window", None)
                if parent is not None:
                    parent.flag = True  # type: ignore[attr-defined]

        @window(title="Test")
        class TestWindow(Window):
            flag: bool = False
            file_menu: FileMenu = new()

        w = TestWindow()
        qt.track(w)

        w.file_menu.action.trigger()
        assert_that(w.flag).is_true()


class TestNoMenuBar:
    """Windows without menus."""

    def test_window_without_menus(self, qt: QtDriver) -> None:
        """Window without Menu fields has empty menu bar."""

        @window(title="Simple Window")
        class TestWindow(Window):
            label: QLabel = new("Just a label")

        w = TestWindow()
        qt.track(w)

        # Menu bar exists but is empty
        assert_that(w.menuBar().actions()).is_length(0)
        assert_that(w.label.text()).is_equal_to("Just a label")


class TestMenuVisibility:
    """Menu visibility binding tests."""

    def test_menu_visible_binding_simple(self, qt: QtDriver) -> None:
        """visible= binding on Menu uses menuAction().setVisible()."""

        @menu(text="&File")
        class FileMenu(Menu):
            action: QAction = new("Action")

        @window(title="Test")
        class TestWindow(Window):
            _show_file_menu: Variable[bool] = new(True)
            file_menu: FileMenu = new(visible="_show_file_menu")

        w = TestWindow()
        qt.track(w)

        # Menu should be visible initially
        assert_that(w.file_menu.menuAction().isVisible()).is_true()

        # Hide the menu via Variable
        w._show_file_menu.value = False
        assert_that(w.file_menu.menuAction().isVisible()).is_false()

        # Show it again
        w._show_file_menu.value = True
        assert_that(w.file_menu.menuAction().isVisible()).is_true()

    def test_menu_visible_binding_expression(self, qt: QtDriver) -> None:
        """visible= expression binding on Menu."""

        @menu(text="&Edit")
        class EditMenu(Menu):
            action: QAction = new("Action")

        @window(title="Test")
        class TestWindow(Window):
            _data_loaded: Variable[bool] = new(False)
            edit_menu: EditMenu = new(visible="{_data_loaded}")

        w = TestWindow()
        qt.track(w)

        # Menu should be hidden initially (data not loaded)
        assert_that(w.edit_menu.menuAction().isVisible()).is_false()

        # Load data - menu should appear
        w._data_loaded.value = True
        assert_that(w.edit_menu.menuAction().isVisible()).is_true()

    def test_menu_visible_initially_hidden(self, qt: QtDriver) -> None:
        """Menu can be initially hidden via visible= binding."""

        @menu(text="&View")
        class ViewMenu(Menu):
            action: QAction = new("Action")

        @window(title="Test")
        class TestWindow(Window):
            _show_view: Variable[bool] = new(False)
            view_menu: ViewMenu = new(visible="_show_view")

        w = TestWindow()
        qt.track(w)

        # Menu should be hidden initially
        assert_that(w.view_menu.menuAction().isVisible()).is_false()

        # Show it
        w._show_view.value = True
        assert_that(w.view_menu.menuAction().isVisible()).is_true()
