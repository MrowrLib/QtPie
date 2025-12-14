"""Tests for the @action decorator.

Note: QAction is not a QWidget, so we can't use qt.track() for these tests.
We still use the qt fixture to ensure QApplication exists.
"""

from assertpy import assert_that
from qtpy.QtGui import QAction, QKeySequence

from qtpie import action
from qtpie_test import QtDriver


class TestActionDecorator:
    """Phase 4: Basic @action functionality."""

    def test_action_creates_valid_qaction(self, qt: QtDriver) -> None:
        """A decorated class should be a valid QAction."""
        _ = qt  # Ensures QApplication exists

        @action()
        class MyAction(QAction):
            pass

        a = MyAction()

        assert_that(a).is_instance_of(QAction)

    def test_action_without_parens(self, qt: QtDriver) -> None:
        """@action without parentheses should work with defaults."""
        _ = qt

        @action
        class MyAction(QAction):
            pass

        a = MyAction()

        assert_that(a).is_instance_of(QAction)


class TestActionText:
    """Tests for the text parameter."""

    def test_text_sets_action_text(self, qt: QtDriver) -> None:
        """text parameter should set the action text."""
        _ = qt

        @action(text="&New File")
        class NewAction(QAction):
            pass

        a = NewAction()

        assert_that(a.text()).is_equal_to("&New File")

    def test_text_as_positional_arg(self, qt: QtDriver) -> None:
        """text can be passed as first positional argument."""
        _ = qt

        @action("&Open")
        class OpenAction(QAction):
            pass

        a = OpenAction()

        assert_that(a.text()).is_equal_to("&Open")

    def test_auto_text_from_class_name(self, qt: QtDriver) -> None:
        """Without text, action text should be derived from class name."""
        _ = qt

        @action()
        class SaveAction(QAction):
            pass

        a = SaveAction()

        # "Action" suffix should be stripped
        assert_that(a.text()).is_equal_to("Save")

    def test_auto_text_without_action_suffix(self, qt: QtDriver) -> None:
        """Class name without Action suffix should be used as-is."""
        _ = qt

        @action()
        class Quit(QAction):
            pass

        a = Quit()

        assert_that(a.text()).is_equal_to("Quit")


class TestActionShortcut:
    """Tests for the shortcut parameter."""

    def test_shortcut_string_sets_shortcut(self, qt: QtDriver) -> None:
        """shortcut parameter with string should set keyboard shortcut."""
        _ = qt

        @action("&New", shortcut="Ctrl+N")
        class NewAction(QAction):
            pass

        a = NewAction()

        assert_that(a.shortcut().toString()).is_equal_to("Ctrl+N")

    def test_shortcut_qkeysequence(self, qt: QtDriver) -> None:
        """shortcut parameter can be QKeySequence."""
        _ = qt

        @action("&Save", shortcut=QKeySequence.StandardKey.Save)
        class SaveAction(QAction):
            pass

        a = SaveAction()

        # QKeySequence.Save is Ctrl+S on most platforms
        assert_that(a.shortcut().isEmpty()).is_false()


class TestActionTooltip:
    """Tests for the tooltip parameter."""

    def test_tooltip_sets_status_tip(self, qt: QtDriver) -> None:
        """tooltip parameter should set status tip."""
        _ = qt

        @action("&New", tooltip="Create a new file")
        class NewAction(QAction):
            pass

        a = NewAction()

        assert_that(a.statusTip()).is_equal_to("Create a new file")

    def test_tooltip_sets_tooltip(self, qt: QtDriver) -> None:
        """tooltip parameter should also set toolTip."""
        _ = qt

        @action("&New", tooltip="Create a new file")
        class NewAction(QAction):
            pass

        a = NewAction()

        assert_that(a.toolTip()).is_equal_to("Create a new file")


class TestActionCheckable:
    """Tests for the checkable parameter."""

    def test_checkable_makes_action_checkable(self, qt: QtDriver) -> None:
        """checkable=True should make action checkable."""
        _ = qt

        @action("&Bold", checkable=True)
        class BoldAction(QAction):
            pass

        a = BoldAction()

        assert_that(a.isCheckable()).is_true()

    def test_not_checkable_by_default(self, qt: QtDriver) -> None:
        """Actions should not be checkable by default."""
        _ = qt

        @action("&New")
        class NewAction(QAction):
            pass

        a = NewAction()

        assert_that(a.isCheckable()).is_false()


class TestActionTriggered:
    """Tests for triggered signal auto-connection."""

    def test_on_triggered_auto_connected(self, qt: QtDriver) -> None:
        """on_triggered method should be auto-connected to triggered signal."""
        _ = qt
        triggered = False

        @action("&Test")
        class TestAction(QAction):
            def on_triggered(self) -> None:
                nonlocal triggered
                triggered = True

        a = TestAction()

        a.trigger()

        assert_that(triggered).is_true()


class TestActionToggled:
    """Tests for toggled signal auto-connection."""

    def test_on_toggled_auto_connected(self, qt: QtDriver) -> None:
        """on_toggled method should be auto-connected to toggled signal."""
        _ = qt
        toggled_value: bool | None = None

        @action("&Toggle", checkable=True)
        class ToggleAction(QAction):
            def on_toggled(self, checked: bool) -> None:
                nonlocal toggled_value
                toggled_value = checked

        a = ToggleAction()

        a.setChecked(True)

        assert_that(toggled_value).is_true()

        a.setChecked(False)

        assert_that(toggled_value).is_false()


class TestActionSetup:
    """Tests for setup lifecycle hook."""

    def test_setup_called_on_init(self, qt: QtDriver) -> None:
        """setup() should be called after action initialization."""
        _ = qt
        calls: list[str] = []

        @action("&Test")
        class TestAction(QAction):
            def setup(self) -> None:
                calls.append("setup")

        TestAction()

        assert_that(calls).is_equal_to(["setup"])


class TestActionCombined:
    """Tests combining multiple action features."""

    def test_full_featured_action(self, qt: QtDriver) -> None:
        """Action with all features should work correctly."""
        _ = qt

        @action("&Bold", shortcut="Ctrl+B", tooltip="Toggle bold", checkable=True)
        class BoldAction(QAction):
            pass

        a = BoldAction()

        assert_that(a.text()).is_equal_to("&Bold")
        assert_that(a.shortcut().toString()).is_equal_to("Ctrl+B")
        assert_that(a.statusTip()).is_equal_to("Toggle bold")
        assert_that(a.isCheckable()).is_true()
