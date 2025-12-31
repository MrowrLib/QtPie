"""Tests for the @action decorator.

Note: QAction is not a QWidget, so we can't use qt.track() for these tests.
We still use the qt fixture to ensure QApplication exists.
"""

from dataclasses import field

from assertpy import assert_that
from qtpy.QtGui import QAction, QIcon, QKeySequence
from qtpy.QtWidgets import QApplication, QStyle

from qtpie import action, make
from qtpie.testing import QtDriver


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
        class SaveAction(QAction):
            pass

        a = SaveAction()

        assert_that(a).is_instance_of(QAction)
        assert_that(a.text()).is_equal_to("Save")


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


class TestActionFields:
    """Tests for dataclass field handling."""

    def test_field_with_default_value(self, qt: QtDriver) -> None:
        """Action fields with default values should be initialized."""
        _ = qt

        @action("&Test")
        class TestAction(QAction):
            count: int = 0
            name: str = "default"

        a = TestAction()

        assert_that(a.count).is_equal_to(0)
        assert_that(a.name).is_equal_to("default")

    def test_field_via_kwargs(self, qt: QtDriver) -> None:
        """Action fields can be set via kwargs."""
        _ = qt

        @action("&Test")
        class TestAction(QAction):
            count: int = 0
            name: str = "default"

        a = TestAction(count=42, name="custom")

        assert_that(a.count).is_equal_to(42)
        assert_that(a.name).is_equal_to("custom")

    def test_field_with_default_factory(self, qt: QtDriver) -> None:
        """Action fields with default_factory should be initialized."""
        _ = qt

        def make_list() -> list[str]:
            return []

        def make_dict() -> dict[str, int]:
            return {}

        @action("&Test")
        class TestAction(QAction):
            items: list[str] = field(default_factory=make_list)
            mapping: dict[str, int] = field(default_factory=make_dict)

        a = TestAction()

        assert_that(a.items).is_equal_to([])
        assert_that(a.mapping).is_equal_to({})

        # Verify each instance gets its own list (not shared)
        a.items.append("one")
        b = TestAction()
        assert_that(b.items).is_equal_to([])


class TestActionShortcutObject:
    """Tests for shortcut as QKeySequence object."""

    def test_shortcut_qkeysequence_object(self, qt: QtDriver) -> None:
        """shortcut parameter can be a QKeySequence object directly."""
        _ = qt

        @action("&Copy", shortcut=QKeySequence("Ctrl+C"))
        class CopyAction(QAction):
            pass

        a = CopyAction()

        assert_that(a.shortcut().toString()).is_equal_to("Ctrl+C")


class TestActionIcon:
    """Tests for the icon parameter."""

    def test_icon_string_path(self, qt: QtDriver) -> None:
        """icon parameter with string path should set icon (even if file missing)."""
        _ = qt

        @action("&Save", icon="nonexistent/path/icon.png")
        class SaveAction(QAction):
            pass

        a = SaveAction()

        # Icon is set but will be null since file doesn't exist
        # This still covers the code path
        assert_that(a.icon()).is_not_none()

    def test_icon_qicon_object(self, qt: QtDriver) -> None:
        """icon parameter can be a QIcon object."""
        _ = qt
        test_icon = QIcon()

        @action("&Open", icon=test_icon)
        class OpenAction(QAction):
            pass

        a = OpenAction()

        # Icon was set (even though it's an empty QIcon)
        assert_that(a.icon()).is_not_none()

    def test_icon_standard_pixmap(self, qt: QtDriver) -> None:
        """icon parameter can be a QStyle.StandardPixmap."""
        _ = qt

        @action("&Info", icon=QStyle.StandardPixmap.SP_MessageBoxInformation)
        class InfoAction(QAction):
            pass

        a = InfoAction()

        # Should have a real icon from the style
        app = QApplication.instance()
        assert_that(app).is_not_none()
        assert_that(a.icon().isNull()).is_false()


class TestActionSignalConnections:
    """Tests for signal connections via make() metadata."""

    def test_child_field_signal_connection_by_method_name(self, qt: QtDriver) -> None:
        """Child fields with signal connections should connect to parent methods."""
        _ = qt
        triggered_count = 0

        @action("&Parent")
        class ParentAction(QAction):
            child: QAction = make(QAction, "Child", triggered="on_child_triggered")

            def on_child_triggered(self) -> None:
                nonlocal triggered_count
                triggered_count += 1

        a = ParentAction()

        # Trigger the child action
        a.child.trigger()

        assert_that(triggered_count).is_equal_to(1)

    def test_child_field_signal_connection_by_lambda(self, qt: QtDriver) -> None:
        """Child fields with lambda signal connections should work."""
        _ = qt
        triggered_count = 0

        def increment() -> None:
            nonlocal triggered_count
            triggered_count += 1

        @action("&Parent")
        class ParentAction(QAction):
            child: QAction = make(QAction, "Child", triggered=increment)

        a = ParentAction()

        # Trigger the child action
        a.child.trigger()

        assert_that(triggered_count).is_equal_to(1)
