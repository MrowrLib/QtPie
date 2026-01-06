# pyright: reportMissingTypeArgument=false
# pyright: reportPrivateUsage=false, reportAttributeAccessIssue=false, reportUnknownMemberType=false
"""Tests for @action decorator."""

from assertpy import assert_that
from qtpy.QtGui import QAction, QKeySequence
from qtpy.QtWidgets import QStyle

from qtpie import action
from qtpie.testing import QtDriver


class TestActionDecorator:
    """Test @action decorator functionality."""

    def test_action_creates_qaction(self, qt: QtDriver) -> None:
        """@action creates a QAction subclass."""

        @action
        class SaveAction(QAction):
            pass

        a = SaveAction()
        assert_that(a).is_instance_of(QAction)

    def test_action_text_from_class_name(self, qt: QtDriver) -> None:
        """@action derives text from class name, stripping 'Action' suffix."""

        @action
        class SaveAction(QAction):
            pass

        a = SaveAction()
        assert_that(a.text()).is_equal_to("Save")

    def test_action_text_keeps_name_without_suffix(self, qt: QtDriver) -> None:
        """@action keeps full name if no 'Action' suffix."""

        @action
        class Undo(QAction):
            pass

        a = Undo()
        assert_that(a.text()).is_equal_to("Undo")

    def test_action_explicit_text(self, qt: QtDriver) -> None:
        """@action with explicit text uses that text."""

        @action("&Save")
        class SaveAction(QAction):
            pass

        a = SaveAction()
        assert_that(a.text()).is_equal_to("&Save")

    def test_action_explicit_text_kwarg(self, qt: QtDriver) -> None:
        """@action with text= kwarg uses that text."""

        @action(text="&Undo")
        class UndoAction(QAction):
            pass

        a = UndoAction()
        assert_that(a.text()).is_equal_to("&Undo")


class TestActionShortcut:
    """Test @action shortcut functionality."""

    def test_action_shortcut_string(self, qt: QtDriver) -> None:
        """@action can set shortcut from string."""

        @action("Save", shortcut="Ctrl+S")
        class SaveAction(QAction):
            pass

        a = SaveAction()
        assert_that(a.shortcut().toString()).is_equal_to("Ctrl+S")

    def test_action_shortcut_qkeysequence(self, qt: QtDriver) -> None:
        """@action can set shortcut from QKeySequence."""

        @action("Save", shortcut=QKeySequence("Ctrl+S"))
        class SaveAction(QAction):
            pass

        a = SaveAction()
        assert_that(a.shortcut().toString()).is_equal_to("Ctrl+S")

    def test_action_shortcut_standard_key(self, qt: QtDriver) -> None:
        """@action can set shortcut from StandardKey."""

        @action("Save", shortcut=QKeySequence.StandardKey.Save)
        class SaveAction(QAction):
            pass

        a = SaveAction()
        # StandardKey.Save is typically Ctrl+S
        assert_that(a.shortcut().isEmpty()).is_false()


class TestActionTooltip:
    """Test @action tooltip functionality."""

    def test_action_tooltip(self, qt: QtDriver) -> None:
        """@action can set tooltip."""

        @action("Save", tooltip="Save the current file")
        class SaveAction(QAction):
            pass

        a = SaveAction()
        assert_that(a.toolTip()).is_equal_to("Save the current file")

    def test_action_tooltip_sets_statustip(self, qt: QtDriver) -> None:
        """@action tooltip also sets statusTip."""

        @action("Save", tooltip="Save the current file")
        class SaveAction(QAction):
            pass

        a = SaveAction()
        assert_that(a.statusTip()).is_equal_to("Save the current file")


class TestActionIcon:
    """Test @action icon functionality."""

    def test_action_icon_standard_pixmap(self, qt: QtDriver) -> None:
        """@action can set icon from QStyle.StandardPixmap."""

        @action("Save", icon=QStyle.StandardPixmap.SP_DialogSaveButton)
        class SaveAction(QAction):
            pass

        a = SaveAction()
        assert_that(a.icon().isNull()).is_false()


class TestActionCheckable:
    """Test @action checkable functionality."""

    def test_action_checkable(self, qt: QtDriver) -> None:
        """@action can be checkable."""

        @action("Bold", checkable=True)
        class BoldAction(QAction):
            pass

        a = BoldAction()
        assert_that(a.isCheckable()).is_true()

    def test_action_not_checkable_by_default(self, qt: QtDriver) -> None:
        """@action is not checkable by default."""

        @action("Save")
        class SaveAction(QAction):
            pass

        a = SaveAction()
        assert_that(a.isCheckable()).is_false()


class TestActionSignalConnections:
    """Test @action auto signal connections."""

    def test_on_triggered_auto_connected(self, qt: QtDriver) -> None:
        """on_triggered method is auto-connected to triggered signal."""
        triggered_count = [0]

        @action("Save")
        class SaveAction(QAction):
            def on_triggered(self) -> None:
                triggered_count[0] += 1

        a = SaveAction()
        a.trigger()
        assert_that(triggered_count[0]).is_equal_to(1)

    def test_on_toggled_auto_connected(self, qt: QtDriver) -> None:
        """on_toggled method is auto-connected to toggled signal."""
        toggled_values: list[bool] = []

        @action("Bold", checkable=True)
        class BoldAction(QAction):
            def on_toggled(self, checked: bool) -> None:
                toggled_values.append(checked)

        a = BoldAction()
        a.setChecked(True)
        a.setChecked(False)
        assert_that(toggled_values).is_equal_to([True, False])


class TestActionSetupHook:
    """Test __setup__ hook in @action."""

    def test_setup_hook_called(self, qt: QtDriver) -> None:
        """__setup__ is called after action initialization."""
        setup_called = [False]

        @action("Save")
        class SaveAction(QAction):
            def __setup__(self) -> None:
                setup_called[0] = True

        SaveAction()
        assert_that(setup_called[0]).is_true()
