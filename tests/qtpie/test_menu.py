# pyright: reportMissingTypeArgument=false
# pyright: reportPrivateUsage=false, reportAttributeAccessIssue=false, reportUnknownMemberType=false
"""Tests for @menu decorator."""

from assertpy import assert_that
from qtpy.QtGui import QAction
from qtpy.QtWidgets import QMenu

from qtpie import menu, new, separator
from qtpie.testing import QtDriver


class TestMenuDecorator:
    """Test @menu decorator functionality."""

    def test_menu_creates_qmenu(self, qt: QtDriver) -> None:
        """@menu creates a QMenu subclass."""

        @menu
        class FileMenu(QMenu):
            pass

        m = qt.track(FileMenu())
        assert_that(m).is_instance_of(QMenu)

    def test_menu_title_from_class_name(self, qt: QtDriver) -> None:
        """@menu derives title from class name, stripping 'Menu' suffix."""

        @menu
        class FileMenu(QMenu):
            pass

        m = qt.track(FileMenu())
        assert_that(m.title()).is_equal_to("File")

    def test_menu_title_keeps_name_without_suffix(self, qt: QtDriver) -> None:
        """@menu keeps full name if no 'Menu' suffix."""

        @menu
        class Edit(QMenu):
            pass

        m = qt.track(Edit())
        assert_that(m.title()).is_equal_to("Edit")

    def test_menu_explicit_title(self, qt: QtDriver) -> None:
        """@menu with explicit title uses that title."""

        @menu("&File")
        class FileMenu(QMenu):
            pass

        m = qt.track(FileMenu())
        assert_that(m.title()).is_equal_to("&File")

    def test_menu_explicit_title_kwarg(self, qt: QtDriver) -> None:
        """@menu with text= kwarg uses that title."""

        @menu(text="&Edit")
        class EditMenu(QMenu):
            pass

        m = qt.track(EditMenu())
        assert_that(m.title()).is_equal_to("&Edit")


class TestMenuActions:
    """Test @menu with QAction fields."""

    def test_menu_adds_actions(self, qt: QtDriver) -> None:
        """@menu auto-adds QAction fields via addAction()."""

        @menu
        class FileMenu(QMenu):
            new_action: QAction = new("&New")
            open_action: QAction = new("&Open")

        m = qt.track(FileMenu())
        actions = m.actions()
        assert_that(actions).is_length(2)
        assert_that(actions[0].text()).is_equal_to("&New")
        assert_that(actions[1].text()).is_equal_to("&Open")

    def test_menu_actions_in_order(self, qt: QtDriver) -> None:
        """@menu adds actions in field declaration order."""

        @menu
        class FileMenu(QMenu):
            first: QAction = new("First")
            second: QAction = new("Second")
            third: QAction = new("Third")

        m = qt.track(FileMenu())
        texts = [a.text() for a in m.actions()]
        assert_that(texts).is_equal_to(["First", "Second", "Third"])

    def test_menu_underscore_fields_not_added(self, qt: QtDriver) -> None:
        """Fields starting with _ are not added to menu."""

        @menu
        class FileMenu(QMenu):
            visible: QAction = new("Visible")
            _hidden: QAction = new("Hidden")

        m = qt.track(FileMenu())
        actions = m.actions()
        assert_that(actions).is_length(1)
        assert_that(actions[0].text()).is_equal_to("Visible")

    def test_menu_action_shortcut(self, qt: QtDriver) -> None:
        """QAction fields can have shortcuts via new()."""

        @menu
        class FileMenu(QMenu):
            new_action: QAction = new("&New", shortcut="Ctrl+N")

        m = qt.track(FileMenu())
        action = m.actions()[0]
        assert_that(action.shortcut().toString()).is_equal_to("Ctrl+N")


class TestMenuSeparator:
    """Test separator() in menus."""

    def test_separator_adds_separator_action(self, qt: QtDriver) -> None:
        """separator() adds a separator to the menu."""

        @menu
        class FileMenu(QMenu):
            new_action: QAction = new("&New")
            sep: QAction = separator()
            exit_action: QAction = new("E&xit")

        m = qt.track(FileMenu())
        actions = m.actions()
        assert_that(actions).is_length(3)
        assert_that(actions[1].isSeparator()).is_true()

    def test_multiple_separators(self, qt: QtDriver) -> None:
        """Multiple separators work correctly."""

        @menu
        class FileMenu(QMenu):
            new_action: QAction = new("&New")
            sep1: QAction = separator()
            save_action: QAction = new("&Save")
            sep2: QAction = separator()
            exit_action: QAction = new("E&xit")

        m = qt.track(FileMenu())
        actions = m.actions()
        assert_that(actions).is_length(5)
        assert_that(actions[1].isSeparator()).is_true()
        assert_that(actions[3].isSeparator()).is_true()


class TestMenuSubmenus:
    """Test @menu with submenu fields."""

    def test_menu_adds_submenus(self, qt: QtDriver) -> None:
        """@menu auto-adds QMenu fields as submenus."""

        @menu
        class RecentMenu(QMenu):
            file1: QAction = new("file1.txt")

        @menu
        class FileMenu(QMenu):
            new_action: QAction = new("&New")
            recent: RecentMenu = new()

        m = qt.track(FileMenu())
        actions = m.actions()
        assert_that(actions).is_length(2)
        # Second action should be the submenu
        assert_that(actions[1].menu()).is_not_none()
        assert_that(actions[1].menu().title()).is_equal_to("Recent")


class TestMenuSignalConnections:
    """Test signal connections in @menu."""

    def test_action_triggered_connection(self, qt: QtDriver) -> None:
        """QAction triggered signal can be connected to method."""
        triggered_count = [0]

        @menu
        class FileMenu(QMenu):
            new_action: QAction = new("&New", triggered="on_new")

            def on_new(self) -> None:
                triggered_count[0] += 1

        m = qt.track(FileMenu())
        m.new_action.trigger()
        assert_that(triggered_count[0]).is_equal_to(1)


class TestMenuSetupHook:
    """Test __setup__ hook in @menu."""

    def test_setup_hook_called(self, qt: QtDriver) -> None:
        """__setup__ is called after menu initialization."""
        setup_called = [False]

        @menu
        class FileMenu(QMenu):
            new_action: QAction = new("&New")

            def __setup__(self) -> None:
                setup_called[0] = True

        qt.track(FileMenu())
        assert_that(setup_called[0]).is_true()
