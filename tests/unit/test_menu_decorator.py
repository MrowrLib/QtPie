"""Tests for the @menu decorator."""

from dataclasses import field

from assertpy import assert_that
from qtpy.QtGui import QAction
from qtpy.QtWidgets import QMenu

from qtpie import action, make, menu, separator
from qtpie.testing import QtDriver


class TestMenuDecorator:
    """Phase 4: Basic @menu functionality."""

    def test_menu_creates_valid_qmenu(self, qt: QtDriver) -> None:
        """A decorated class should be a valid QMenu."""

        @menu()
        class MyMenu(QMenu):
            pass

        m = MyMenu()
        qt.track(m)

        assert_that(m).is_instance_of(QMenu)

    def test_menu_without_parens(self, qt: QtDriver) -> None:
        """@menu without parentheses should work with defaults."""

        @menu
        class FileMenu(QMenu):
            pass

        m = FileMenu()
        qt.track(m)

        assert_that(m).is_instance_of(QMenu)
        assert_that(m.title()).is_equal_to("File")


class TestMenuText:
    """Tests for the text parameter."""

    def test_text_sets_menu_title(self, qt: QtDriver) -> None:
        """text parameter should set the menu title."""

        @menu(text="&File")
        class FileMenu(QMenu):
            pass

        m = FileMenu()
        qt.track(m)

        assert_that(m.title()).is_equal_to("&File")

    def test_text_as_positional_arg(self, qt: QtDriver) -> None:
        """text can be passed as first positional argument."""

        @menu("&Edit")
        class EditMenu(QMenu):
            pass

        m = EditMenu()
        qt.track(m)

        assert_that(m.title()).is_equal_to("&Edit")

    def test_auto_text_from_class_name(self, qt: QtDriver) -> None:
        """Without text, menu title should be derived from class name."""

        @menu()
        class FileMenu(QMenu):
            pass

        m = FileMenu()
        qt.track(m)

        # "Menu" suffix should be stripped
        assert_that(m.title()).is_equal_to("File")

    def test_auto_text_without_menu_suffix(self, qt: QtDriver) -> None:
        """Class name without Menu suffix should be used as-is."""

        @menu()
        class Tools(QMenu):
            pass

        m = Tools()
        qt.track(m)

        assert_that(m.title()).is_equal_to("Tools")


class TestMenuActions:
    """Tests for auto-adding actions to menu."""

    def test_qaction_field_added_to_menu(self, qt: QtDriver) -> None:
        """QAction fields should be auto-added to menu."""

        @action("&New")
        class NewAction(QAction):
            pass

        @menu("&File")
        class FileMenu(QMenu):
            new: NewAction = make(NewAction)

        m = FileMenu()
        qt.track(m)

        actions = m.actions()
        assert_that(len(actions)).is_equal_to(1)
        assert_that(actions[0]).is_same_as(m.new)

    def test_multiple_actions_in_order(self, qt: QtDriver) -> None:
        """Multiple actions should be added in declaration order."""

        @action("&New")
        class NewAction(QAction):
            pass

        @action("&Open")
        class OpenAction(QAction):
            pass

        @action("&Save")
        class SaveAction(QAction):
            pass

        @menu("&File")
        class FileMenu(QMenu):
            new: NewAction = make(NewAction)
            open_file: OpenAction = make(OpenAction)
            save: SaveAction = make(SaveAction)

        m = FileMenu()
        qt.track(m)

        actions = m.actions()
        assert_that(len(actions)).is_equal_to(3)
        assert_that(actions[0]).is_same_as(m.new)
        assert_that(actions[1]).is_same_as(m.open_file)
        assert_that(actions[2]).is_same_as(m.save)

    def test_plain_qaction_field_added(self, qt: QtDriver) -> None:
        """Plain QAction fields should also be added."""

        @menu("&Edit")
        class EditMenu(QMenu):
            undo: QAction = field(default_factory=lambda: QAction("&Undo"))

        m = EditMenu()
        qt.track(m)

        actions = m.actions()
        assert_that(len(actions)).is_equal_to(1)
        assert_that(actions[0].text()).is_equal_to("&Undo")


class TestMenuSubmenus:
    """Tests for nested submenus."""

    def test_qmenu_field_added_as_submenu(self, qt: QtDriver) -> None:
        """QMenu fields should be auto-added as submenus."""

        @menu("&Recent Files")
        class RecentMenu(QMenu):
            pass

        @menu("&File")
        class FileMenu(QMenu):
            recent: RecentMenu = make(RecentMenu)

        m = FileMenu()
        qt.track(m)

        # The submenu should appear as an action with a menu
        actions = m.actions()
        assert_that(len(actions)).is_equal_to(1)
        assert_that(actions[0].menu()).is_same_as(m.recent)

    def test_mixed_actions_and_submenus(self, qt: QtDriver) -> None:
        """Menu can have both actions and submenus."""

        @action("&New")
        class NewAction(QAction):
            pass

        @menu("&Recent")
        class RecentMenu(QMenu):
            pass

        @action("E&xit")
        class ExitAction(QAction):
            pass

        @menu("&File")
        class FileMenu(QMenu):
            new: NewAction = make(NewAction)
            recent: RecentMenu = make(RecentMenu)
            exit_app: ExitAction = make(ExitAction)

        m = FileMenu()
        qt.track(m)

        actions = m.actions()
        assert_that(len(actions)).is_equal_to(3)

        # First is action
        assert_that(actions[0]).is_same_as(m.new)
        assert_that(actions[0].menu()).is_none()

        # Second is submenu
        assert_that(actions[1].menu()).is_same_as(m.recent)

        # Third is action
        assert_that(actions[2]).is_same_as(m.exit_app)


class TestMenuSetup:
    """Tests for setup lifecycle hook."""

    def test_setup_called_on_init(self, qt: QtDriver) -> None:
        """setup() should be called after menu initialization."""
        calls: list[str] = []

        @menu("&Test")
        class TestMenu(QMenu):
            def setup(self) -> None:
                calls.append("setup")

        m = TestMenu()
        qt.track(m)

        assert_that(calls).is_equal_to(["setup"])


class TestMenuPrivateFields:
    """Tests for private field handling."""

    def test_private_fields_not_added(self, qt: QtDriver) -> None:
        """Private fields (starting with _) should not be added to menu."""

        @action("&Public")
        class PublicAction(QAction):
            pass

        @action("&Private")
        class PrivateAction(QAction):
            pass

        @menu("&Test")
        class TestMenu(QMenu):
            public: PublicAction = make(PublicAction)
            _private: PrivateAction = make(PrivateAction)

        m = TestMenu()
        qt.track(m)

        # Only public action should be added
        actions = m.actions()
        assert_that(len(actions)).is_equal_to(1)
        assert_that(actions[0]).is_same_as(m.public)


class TestMenuFields:
    """Tests for dataclass field handling."""

    def test_field_with_default_value(self, qt: QtDriver) -> None:
        """Menu fields with default values should be initialized."""

        @menu("&Test")
        class TestMenu(QMenu):
            count: int = 5
            name: str = "default"

        m = TestMenu()
        qt.track(m)

        assert_that(m.count).is_equal_to(5)
        assert_that(m.name).is_equal_to("default")

    def test_field_via_kwargs(self, qt: QtDriver) -> None:
        """Menu fields can be set via kwargs."""

        @menu("&Test")
        class TestMenu(QMenu):
            count: int = 0
            name: str = "default"

        m = TestMenu(count=99, name="custom")
        qt.track(m)

        assert_that(m.count).is_equal_to(99)
        assert_that(m.name).is_equal_to("custom")


class TestMenuSignalConnections:
    """Tests for signal connections via make() metadata."""

    def test_action_signal_connection_by_method_name(self, qt: QtDriver) -> None:
        """Actions with signal connections should connect to menu methods."""
        triggered_count = 0

        @menu("&Test")
        class TestMenu(QMenu):
            save: QAction = make(QAction, "&Save", triggered="on_save")

            def on_save(self) -> None:
                nonlocal triggered_count
                triggered_count += 1

        m = TestMenu()
        qt.track(m)

        # Trigger the action
        m.save.trigger()

        assert_that(triggered_count).is_equal_to(1)

    def test_action_signal_connection_by_lambda(self, qt: QtDriver) -> None:
        """Actions with lambda signal connections should work."""
        triggered_count = 0

        def increment() -> None:
            nonlocal triggered_count
            triggered_count += 1

        @menu("&Test")
        class TestMenu(QMenu):
            run: QAction = make(QAction, "&Run", triggered=increment)

        m = TestMenu()
        qt.track(m)

        # Trigger the action
        m.run.trigger()

        assert_that(triggered_count).is_equal_to(1)


class TestMenuSeparators:
    """Tests for separator() functionality in menus."""

    def test_separator_added_to_menu(self, qt: QtDriver) -> None:
        """separator() should add a separator action to the menu."""

        @action("&New")
        class NewAction(QAction):
            pass

        @action("E&xit")
        class ExitAction(QAction):
            pass

        @menu("&File")
        class FileMenu(QMenu):
            new: NewAction = make(NewAction)
            sep1: QAction = separator()
            exit_app: ExitAction = make(ExitAction)

        m = FileMenu()
        qt.track(m)

        actions = m.actions()
        assert_that(len(actions)).is_equal_to(3)
        assert_that(actions[0]).is_same_as(m.new)
        assert_that(actions[1].isSeparator()).is_true()
        assert_that(actions[2]).is_same_as(m.exit_app)

    def test_separator_stored_on_instance(self, qt: QtDriver) -> None:
        """The separator QAction should be accessible on the instance."""

        @menu("&Test")
        class TestMenu(QMenu):
            sep1: QAction = separator()

        m = TestMenu()
        qt.track(m)

        # The separator field should have the actual QAction
        assert_that(m.sep1).is_instance_of(QAction)
        assert_that(m.sep1.isSeparator()).is_true()

    def test_multiple_separators(self, qt: QtDriver) -> None:
        """Multiple separators can be added to a menu."""

        @action("&Undo")
        class UndoAction(QAction):
            pass

        @action("Cu&t")
        class CutAction(QAction):
            pass

        @action("Select &All")
        class SelectAllAction(QAction):
            pass

        @menu("&Edit")
        class EditMenu(QMenu):
            undo: UndoAction = make(UndoAction)
            sep1: QAction = separator()
            cut: CutAction = make(CutAction)
            sep2: QAction = separator()
            select_all: SelectAllAction = make(SelectAllAction)

        m = EditMenu()
        qt.track(m)

        actions = m.actions()
        assert_that(len(actions)).is_equal_to(5)
        assert_that(actions[0]).is_same_as(m.undo)
        assert_that(actions[1].isSeparator()).is_true()
        assert_that(actions[2]).is_same_as(m.cut)
        assert_that(actions[3].isSeparator()).is_true()
        assert_that(actions[4]).is_same_as(m.select_all)

    def test_separator_with_submenu(self, qt: QtDriver) -> None:
        """Separators work alongside submenus."""

        @menu("&Recent")
        class RecentMenu(QMenu):
            pass

        @action("E&xit")
        class ExitAction(QAction):
            pass

        @menu("&File")
        class FileMenu(QMenu):
            recent: RecentMenu = make(RecentMenu)
            sep1: QAction = separator()
            exit_app: ExitAction = make(ExitAction)

        m = FileMenu()
        qt.track(m)

        actions = m.actions()
        assert_that(len(actions)).is_equal_to(3)
        assert_that(actions[0].menu()).is_same_as(m.recent)
        assert_that(actions[1].isSeparator()).is_true()
        assert_that(actions[2]).is_same_as(m.exit_app)
