# pyright: reportPrivateUsage=false
# pyright: reportUnknownArgumentType=false
# pyright: reportOptionalMemberAccess=false
# pyright: reportUnknownMemberType=false
# pyright: reportAttributeAccessIssue=false
# pyright: reportUnusedClass=false
# pyright: reportMissingImports=false
# pyright: reportUnknownVariableType=false
# pyright: reportUntypedClassDecorator=false
"""Tests for Dialog, DialogButton, DialogButtons, @dialog, @buttons."""

from dataclasses import dataclass
from typing import Any, override

import pytest
from PySide6.QtWidgets import QDialog, QDialogButtonBox, QLabel, QLineEdit, QSpinBox, QVBoxLayout

from qtpie import Dialog, DialogButton, DialogButtons, DialogResult, Variable, Widget, Window, buttons, dialog, new, widget, window
from qtpie.testing import QtDriver


@dataclass
class Person:
    name: str = ""
    age: int = 0


@pytest.fixture
def qt(qtbot) -> QtDriver:  # type: ignore[no-untyped-def]
    return QtDriver(qtbot)


# Components that can call open_dialog() - QtPieComponentBase subclasses only
# (Menu, Frame, GroupBox use WidgetBase which doesn't have open_dialog)
SHOW_DIALOG_CALLER_TYPES = [
    pytest.param(Widget, widget, id="Widget"),
    pytest.param(Window, window, id="Window"),
    pytest.param(Dialog, dialog, id="Dialog"),
]


def create_and_track(qt: QtDriver, decorated_class: type, base_class: type, **kwargs: Any) -> Any:
    """Create an instance and track it appropriately."""
    instance = decorated_class(**kwargs)
    qt.track(instance)
    return instance


# =============================================================================
# Dialog Creation & Basic Structure
# =============================================================================


class TestDialogCreation:
    def test_dialog_is_qdialog(self, qt: QtDriver) -> None:
        @dialog
        class TestDialog(Dialog):
            ok: DialogButton

        d = qt.track(TestDialog())
        assert isinstance(d, QDialog)

    def test_dialog_title(self, qt: QtDriver) -> None:
        @dialog(title="My Title")
        class TestDialog(Dialog):
            ok: DialogButton

        d = qt.track(TestDialog())
        assert d.windowTitle() == "My Title"

    def test_dialog_default_vertical_layout(self, qt: QtDriver) -> None:
        @dialog
        class TestDialog(Dialog):
            label: QLabel = new("Test")
            ok: DialogButton

        d = qt.track(TestDialog())
        assert isinstance(d.layout(), QVBoxLayout)

    def test_dialog_requires_decorator(self, qt: QtDriver) -> None:
        class TestDialog(Dialog):
            ok: DialogButton

        with pytest.raises(TypeError, match="must be decorated with @dialog"):
            qt.track(TestDialog())


# =============================================================================
# DialogButton Basics
# =============================================================================


class TestDialogButtonBasics:
    def test_bare_dialog_button_annotation(self, qt: QtDriver) -> None:
        @dialog
        class TestDialog(Dialog):
            ok: DialogButton

        d = qt.track(TestDialog())
        # Verify button exists
        assert d._button_box is not None
        ok_btn = d._get_button("ok")
        assert ok_btn is not None

    def test_dialog_button_custom_label(self, qt: QtDriver) -> None:
        @dialog
        class TestDialog(Dialog):
            ok: DialogButton = new("Save Changes")

        d = qt.track(TestDialog())
        ok_btn = d._get_button("ok")
        assert ok_btn is not None
        assert ok_btn.text() == "Save Changes"

    def test_common_button_types(self, qt: QtDriver) -> None:
        # Test most common button types (excluding 'close' which conflicts with QWidget.close)
        @dialog
        class TestDialog(Dialog):
            ok: DialogButton
            cancel: DialogButton
            yes: DialogButton
            no: DialogButton
            save: DialogButton
            discard: DialogButton
            apply: DialogButton
            help: DialogButton
            reset: DialogButton

        d = qt.track(TestDialog())
        # Verify 9 button types work (close tested separately due to QWidget conflict)
        for btn_type in ["ok", "cancel", "yes", "no", "save", "discard", "apply", "help", "reset"]:
            btn = d._get_button(btn_type)
            assert btn is not None, f"Button '{btn_type}' not found"

    def test_unknown_button_type_errors(self) -> None:
        with pytest.raises(TypeError, match="Invalid DialogButton field name"):

            @dialog
            class _TestDialog(Dialog):  # noqa: F841 # Unused class is intentional - decorator raises
                foo: DialogButton  # type: ignore[misc] # Invalid button type


# =============================================================================
# Underscore-Prefixed Button Names
# =============================================================================


class TestUnderscorePrefixedButtons:
    def test_underscore_prefixed_button_names(self, qt: QtDriver) -> None:
        """Underscore-prefixed button names like _ok and _cancel should work."""

        @dialog
        class TestDialog(Dialog):
            _ok: DialogButton
            _cancel: DialogButton

        d = qt.track(TestDialog())
        # Buttons should be accessible via button type (without underscore)
        assert d._get_button("ok") is not None
        assert d._get_button("cancel") is not None

    def test_underscore_prefixed_with_custom_label(self, qt: QtDriver) -> None:
        """Underscore-prefixed buttons should support custom labels."""

        @dialog
        class TestDialog(Dialog):
            _ok: DialogButton = new("Confirm")
            _cancel: DialogButton = new("Abort")

        d = qt.track(TestDialog())
        ok_btn = d._get_button("ok")
        cancel_btn = d._get_button("cancel")
        assert ok_btn is not None
        assert cancel_btn is not None
        assert ok_btn.text() == "Confirm"
        assert cancel_btn.text() == "Abort"

    def test_mixed_prefixed_and_unprefixed(self, qt: QtDriver) -> None:
        """Can mix underscore-prefixed and unprefixed button names."""

        @dialog
        class TestDialog(Dialog):
            _ok: DialogButton
            cancel: DialogButton

        d = qt.track(TestDialog())
        assert d._get_button("ok") is not None
        assert d._get_button("cancel") is not None

    def test_underscore_prefixed_with_bindings(self, qt: QtDriver) -> None:
        """Underscore-prefixed buttons should support enabled bindings."""

        @dialog
        class TestDialog(Dialog):
            _valid: Variable[bool] = new(False)
            _ok: DialogButton = new(enabled="{_valid}")
            _cancel: DialogButton

        d = qt.track(TestDialog())
        ok_btn = d._get_button("ok")
        assert ok_btn is not None
        assert not ok_btn.isEnabled()
        d._valid.value = True
        qt.process_events()
        assert ok_btn.isEnabled()

    def test_underscore_prefixed_with_clicked(self, qt: QtDriver) -> None:
        """Underscore-prefixed buttons should support clicked handlers."""

        @dialog
        class TestDialog(Dialog):
            _apply: DialogButton = new(clicked="on_apply")
            _cancel: DialogButton

            def on_apply(self) -> None:
                self._applied = True  # type: ignore[attr-defined]

        d = qt.track(TestDialog())
        d._applied = False  # type: ignore[attr-defined]
        apply_btn = d._get_button("apply")
        assert apply_btn is not None
        qt.click(apply_btn)
        assert d._applied is True  # type: ignore[attr-defined]


# =============================================================================
# Button Box Layout Position
# =============================================================================


class TestButtonBoxPosition:
    def test_buttons_at_end_of_layout(self, qt: QtDriver) -> None:
        @dialog
        class TestDialog(Dialog):
            label1: QLabel = new("First")
            label2: QLabel = new("Second")
            ok: DialogButton
            cancel: DialogButton

        d = qt.track(TestDialog())
        layout = d.layout()
        assert layout is not None
        # Verify: label1, label2, QDialogButtonBox (at end)
        assert layout.count() == 3
        assert isinstance(layout.itemAt(2).widget(), QDialogButtonBox)

    def test_buttons_collected_from_mixed_positions(self, qt: QtDriver) -> None:
        @dialog
        class TestDialog(Dialog):
            label1: QLabel = new("First")
            ok: DialogButton
            label2: QLabel = new("Second")
            cancel: DialogButton

        d = qt.track(TestDialog())
        layout = d.layout()
        assert layout is not None
        # Verify: label1, label2, QDialogButtonBox (buttons collected, added at end)
        assert layout.count() == 3  # 2 labels + 1 button box


# =============================================================================
# Dialog Accept/Reject Behavior
# =============================================================================


class TestDialogAcceptReject:
    def test_build_result_accepted(self, qt: QtDriver) -> None:
        @dialog
        class TestDialog(Dialog):
            ok: DialogButton
            cancel: DialogButton

        d = qt.track(TestDialog())
        d._simulate_button_click("ok")
        result = d._build_result(QDialog.DialogCode.Accepted)
        assert result.accepted
        assert result.button is not None
        assert result.button.name == "ok"

    def test_build_result_rejected(self, qt: QtDriver) -> None:
        @dialog
        class TestDialog(Dialog):
            ok: DialogButton
            cancel: DialogButton

        d = qt.track(TestDialog())
        d._simulate_button_click("cancel")
        result = d._build_result(QDialog.DialogCode.Rejected)
        assert result.rejected
        assert result.button is not None
        assert result.button.name == "cancel"

    def test_on_accept_hook_called(self, qt: QtDriver) -> None:
        @dialog
        class TestDialog(Dialog):
            ok: DialogButton
            cancel: DialogButton

            @override
            def on_accept(self) -> bool:
                self.accept_called = True  # type: ignore[attr-defined]
                return False  # Prevent closing

        d = qt.track(TestDialog())
        d.accept_called = False  # type: ignore[attr-defined]
        # Hook returns False = should prevent accept
        assert d.on_accept() is False
        assert d.accept_called is True  # type: ignore[attr-defined]

    def test_on_reject_hook_called(self, qt: QtDriver) -> None:
        @dialog
        class TestDialog(Dialog):
            ok: DialogButton
            cancel: DialogButton

            @override
            def on_reject(self) -> bool:
                self.reject_called = True  # type: ignore[attr-defined]
                return True  # Allow reject

        d = qt.track(TestDialog())
        d.reject_called = False  # type: ignore[attr-defined]
        assert d.on_reject() is True
        assert d.reject_called is True  # type: ignore[attr-defined]


# =============================================================================
# show_dialog() Method
# =============================================================================


class TestShowDialog:
    def test_instance_show_dialog(self, qt: QtDriver) -> None:
        @dialog
        class TestDialog(Dialog):
            ok: DialogButton

        d = qt.track(TestDialog())
        # Override _show_dialog to avoid blocking exec()
        d._show_dialog = lambda: d._build_result(QDialog.DialogCode.Accepted)  # type: ignore[method-assign]
        result = d.show_dialog()
        assert isinstance(result, DialogResult)
        assert result.accepted

    def test_show_dialog_rejected(self, qt: QtDriver) -> None:
        @dialog
        class TestDialog(Dialog):
            ok: DialogButton
            cancel: DialogButton

        d = qt.track(TestDialog())
        d._show_dialog = lambda: d._build_result(QDialog.DialogCode.Rejected)  # type: ignore[method-assign]
        result = d.show_dialog()
        assert result.rejected

    def test_class_method_show_dialog(self, qt: QtDriver) -> None:
        """Test calling show_dialog() on the class (not instance)."""
        # Track instances created
        instances_created: list[QDialog] = []

        @dialog
        class TestDialog(Dialog):
            ok: DialogButton

            def __init__(self) -> None:
                super().__init__()
                instances_created.append(self)
                # Override _show_dialog to avoid blocking exec()
                self._show_dialog = lambda: self._build_result(QDialog.DialogCode.Accepted)  # type: ignore[method-assign]

        # Call on CLASS, not instance
        result = TestDialog.show_dialog()

        # Verify it created an instance
        assert len(instances_created) == 1
        qt.track(instances_created[0])  # Track for cleanup

        # Verify result
        assert isinstance(result, DialogResult)
        assert result.accepted

    def test_class_method_show_dialog_with_record(self, qt: QtDriver) -> None:
        """Test class method show_dialog() with record parameter."""
        instances_created: list[QDialog] = []

        @dialog
        class TestDialog(Dialog[Person]):
            name: QLineEdit = new()
            ok: DialogButton

            def __init__(self) -> None:
                super().__init__()
                instances_created.append(self)
                self._show_dialog = lambda: self._build_result(QDialog.DialogCode.Accepted)  # type: ignore[method-assign]

        # Call class method with record
        person = Person("Alice", 30)
        result = TestDialog.show_dialog(person)

        assert len(instances_created) == 1
        qt.track(instances_created[0])

        # Verify record was set and returned
        assert result.accepted
        assert result.record is not None
        assert result.record.name == "Alice"
        assert result.record.age == 30


# =============================================================================
# DialogResult
# =============================================================================


class TestDialogResult:
    def test_result_accepted_property(self, qt: QtDriver) -> None:
        @dialog
        class TestDialog(Dialog):
            ok: DialogButton

        d = qt.track(TestDialog())
        result = d._build_result(QDialog.DialogCode.Accepted)
        assert result.accepted
        assert not result.rejected

    def test_result_rejected_property(self, qt: QtDriver) -> None:
        @dialog
        class TestDialog(Dialog):
            ok: DialogButton
            cancel: DialogButton

        d = qt.track(TestDialog())
        result = d._build_result(QDialog.DialogCode.Rejected)
        assert not result.accepted
        assert result.rejected

    def test_result_button_info(self, qt: QtDriver) -> None:
        @dialog
        class TestDialog(Dialog):
            save: DialogButton = new("Save Changes")
            cancel: DialogButton

        d = qt.track(TestDialog())
        d._simulate_button_click("save")
        result = d._build_result(QDialog.DialogCode.Accepted)
        assert result.button is not None
        assert result.button.name == "save"
        assert result.button.text == "Save Changes"

    def test_result_no_button_when_closed_via_x(self, qt: QtDriver) -> None:
        @dialog
        class TestDialog(Dialog):
            ok: DialogButton

        d = qt.track(TestDialog())
        # No _simulate_button_click - closed via X or Escape
        result = d._build_result(QDialog.DialogCode.Rejected)
        assert result.rejected
        assert result.button is None


# =============================================================================
# Dialog[T] Record Support
# =============================================================================


class TestDialogRecord:
    def test_dialog_with_record_type(self, qt: QtDriver) -> None:
        @dialog
        class TestDialog(Dialog[Person]):
            name: QLineEdit = new()
            age: QSpinBox = new()
            ok: DialogButton

        d = qt.track(TestDialog())
        d.record = Person("Alice", 30)
        assert d.name.text() == "Alice"
        assert d.age.value() == 30

    def test_record_two_way_binding(self, qt: QtDriver) -> None:
        @dialog
        class TestDialog(Dialog[Person]):
            name: QLineEdit = new()
            ok: DialogButton

        d = qt.track(TestDialog())
        d.record = Person("Alice", 30)
        d.name.setText("Bob")
        qt.process_events()
        assert d.record.name == "Bob"

    def test_result_record_for_dialog_t(self, qt: QtDriver) -> None:
        @dialog
        class TestDialog(Dialog[Person]):
            name: QLineEdit = new()
            ok: DialogButton

        d = qt.track(TestDialog())
        d.record = Person("Bob", 25)
        result = d._build_result(QDialog.DialogCode.Accepted)
        assert result.record is not None
        assert result.record.name == "Bob"
        assert result.record.age == 25


# =============================================================================
# Reactive Button Bindings
# =============================================================================


class TestDialogButtonBindings:
    def test_button_enabled_binding(self, qt: QtDriver) -> None:
        @dialog
        class TestDialog(Dialog):
            _valid: Variable[bool] = new(False)
            ok: DialogButton = new(enabled="{_valid}")
            cancel: DialogButton

        d = qt.track(TestDialog())
        ok_btn = d._get_button("ok")
        assert ok_btn is not None
        assert not ok_btn.isEnabled()
        d._valid.value = True
        qt.process_events()
        assert ok_btn.isEnabled()

    def test_button_clicked_signal_connection(self, qt: QtDriver) -> None:
        @dialog
        class TestDialog(Dialog):
            apply: DialogButton = new(clicked="on_apply")
            cancel: DialogButton

            def on_apply(self) -> None:
                self._applied = True  # type: ignore[attr-defined]

        d = qt.track(TestDialog())
        d._applied = False  # type: ignore[attr-defined]
        apply_btn = d._get_button("apply")
        assert apply_btn is not None
        qt.click(apply_btn)
        assert d._applied is True  # type: ignore[attr-defined]


# =============================================================================
# Custom DialogButtons Class
# =============================================================================


class TestDialogButtonsClass:
    def test_custom_buttons_class(self, qt: QtDriver) -> None:
        @buttons
        class MyButtons(DialogButtons):
            ok: DialogButton = new("Yes!")
            cancel: DialogButton = new("Nope")

        @dialog
        class TestDialog(Dialog):
            _buttons_field: MyButtons = new()  # Use different name to not clash with _buttons dict

        d = qt.track(TestDialog())
        assert isinstance(d._buttons_field, QDialogButtonBox)

    def test_buttons_positioning_in_layout(self, qt: QtDriver) -> None:
        @buttons
        class MyButtons(DialogButtons):
            ok: DialogButton
            cancel: DialogButton

        @dialog
        class TestDialog(Dialog):
            header: QLabel = new("Header")
            my_buttons: MyButtons = new()
            footer: QLabel = new("Footer")

        d = qt.track(TestDialog())
        layout = d.layout()
        assert layout is not None
        # Verify order: header, buttons, footer
        assert layout.itemAt(0).widget().text() == "Header"
        assert isinstance(layout.itemAt(1).widget(), QDialogButtonBox)
        assert layout.itemAt(2).widget().text() == "Footer"


# =============================================================================
# Validation Integration
# =============================================================================


class TestDialogValidation:
    def test_positive_buttons_auto_bind_is_valid(self, qt: QtDriver) -> None:
        @dialog
        class TestDialog(Dialog):
            _name: Variable[str] = new("")
            ok: DialogButton  # Should auto-bind to is_valid
            cancel: DialogButton

        d = qt.track(TestDialog())
        d.add_validator("_name", "required", lambda v: "Required" if not v else None)
        qt.process_events()
        ok_btn = d._get_button("ok")
        assert ok_btn is not None
        assert not ok_btn.isEnabled()  # Invalid initially
        d._name.value = "Alice"
        qt.process_events()
        assert ok_btn.isEnabled()  # Valid now


# =============================================================================
# Dialog Icon
# =============================================================================


class TestDialogIcon:
    def test_dialog_icon_from_path(self, qt: QtDriver) -> None:
        @dialog(title="Icon Test", icon=":/icons/test.png")
        class TestDialog(Dialog):
            ok: DialogButton

        d = qt.track(TestDialog())
        # Icon object is created (even if resource doesn't exist)
        icon = d.windowIcon()
        assert icon is not None

    def test_dialog_icon_from_qicon(self, qt: QtDriver) -> None:
        from PySide6.QtGui import QIcon, QPixmap

        pixmap = QPixmap(16, 16)
        test_icon = QIcon(pixmap)

        @dialog(title="Icon Test", icon=test_icon)
        class TestDialog(Dialog):
            ok: DialogButton

        d = qt.track(TestDialog())
        assert not d.windowIcon().isNull()

    def test_dialog_icon_from_qpixmap(self, qt: QtDriver) -> None:
        from PySide6.QtGui import QPixmap

        pixmap = QPixmap(16, 16)

        @dialog(title="Icon Test", icon=pixmap)
        class TestDialog(Dialog):
            ok: DialogButton

        d = qt.track(TestDialog())
        assert not d.windowIcon().isNull()

    def test_dialog_inherits_icon_from_active_window(self, qt: QtDriver) -> None:
        from PySide6.QtGui import QIcon, QPixmap
        from PySide6.QtWidgets import QMainWindow

        # Create a main window with an icon
        pixmap = QPixmap(16, 16)
        window_icon = QIcon(pixmap)
        main_window = qt.track(QMainWindow())
        main_window.setWindowIcon(window_icon)
        main_window.show()
        main_window.activateWindow()
        qt.process_events()

        # Dialog without explicit icon should inherit from active window
        @dialog(title="Inherits Icon")
        class TestDialog(Dialog):
            ok: DialogButton

        d = qt.track(TestDialog())
        # Should have inherited the icon
        assert not d.windowIcon().isNull()

    def test_dialog_icon_false_opts_out(self, qt: QtDriver) -> None:
        from PySide6.QtGui import QIcon, QPixmap
        from PySide6.QtWidgets import QMainWindow

        # Create a main window with an icon
        pixmap = QPixmap(16, 16)
        window_icon = QIcon(pixmap)
        main_window = qt.track(QMainWindow())
        main_window.setWindowIcon(window_icon)
        main_window.show()
        main_window.activateWindow()
        qt.process_events()

        # Dialog with icon=False should NOT inherit
        @dialog(title="No Icon", icon=False)
        class TestDialog(Dialog):
            ok: DialogButton

        d = qt.track(TestDialog())
        # Should have NO icon (opted out)
        assert d.windowIcon().isNull()


# =============================================================================
# Edge Cases
# =============================================================================


class TestDialogEdgeCases:
    def test_dialog_with_only_cancel(self, qt: QtDriver) -> None:
        @dialog
        class TestDialog(Dialog):
            cancel: DialogButton

        d = qt.track(TestDialog())
        assert d._get_button("cancel") is not None

    def test_multiple_dialogs(self, qt: QtDriver) -> None:
        @dialog
        class Dialog1(Dialog):
            ok: DialogButton

        @dialog
        class Dialog2(Dialog):
            ok: DialogButton

        d1 = qt.track(Dialog1())
        d2 = qt.track(Dialog2())
        # Both should work independently
        assert d1._get_button("ok") is not None
        assert d2._get_button("ok") is not None


# =============================================================================
# DialogResult.dialog Field
# =============================================================================


class TestDialogResultDialog:
    def test_result_has_dialog_instance(self, qt: QtDriver) -> None:
        """result.dialog gives access to the dialog instance."""

        @dialog
        class TestDialog(Dialog):
            ok: DialogButton

        d = qt.track(TestDialog())
        result = d._build_result(QDialog.DialogCode.Accepted)
        assert result.dialog is d

    def test_result_dialog_accessible_after_accept(self, qt: QtDriver) -> None:
        """Can access dialog fields after accept."""

        @dialog
        class TestDialog(Dialog):
            _value: Variable[str] = new("test_value")
            ok: DialogButton

        d = qt.track(TestDialog())
        result = d._build_result(QDialog.DialogCode.Accepted)
        assert result.dialog is not None
        assert result.dialog._value.value == "test_value"

    def test_result_dialog_accessible_after_reject(self, qt: QtDriver) -> None:
        """Can access dialog fields after reject."""

        @dialog
        class TestDialog(Dialog):
            _value: Variable[str] = new("rejected_value")
            ok: DialogButton
            cancel: DialogButton

        d = qt.track(TestDialog())
        result = d._build_result(QDialog.DialogCode.Rejected)
        assert result.dialog is not None
        assert result.dialog._value.value == "rejected_value"

    def test_result_dialog_is_same_instance(self, qt: QtDriver) -> None:
        """result.dialog is the exact same object."""

        @dialog
        class TestDialog(Dialog):
            ok: DialogButton

        d = qt.track(TestDialog())
        result = d._build_result(QDialog.DialogCode.Accepted)
        assert result.dialog is d
        # Verify it's the same instance by id
        assert id(result.dialog) == id(d)


# =============================================================================
# Dialog Parent Variable Resolution
# =============================================================================


class TestDialogParentVariableResolution:
    def test_bare_variable_resolves_from_parent(self, qt: QtDriver) -> None:
        """Dialog bare Variable[T] resolves from parent widget."""

        @dialog
        class TestDialog(Dialog):
            _name: Variable[str]  # Bare - should resolve from parent
            ok: DialogButton

        @widget
        class ParentWidget(Widget):
            _name: Variable[str] = new("parent_value")

        parent = qt.track(ParentWidget())
        # Create dialog with parent
        d = qt.track(TestDialog(parent=parent))
        # Bare variable should have resolved from parent
        assert d._name.value == "parent_value"

    def test_bare_variable_bidirectional_sync(self, qt: QtDriver) -> None:
        """Changes to dialog's resolved bare Variable sync back to parent."""

        @dialog
        class TestDialog(Dialog):
            _count: Variable[int]  # Bare - resolves from parent
            ok: DialogButton

        @widget
        class ParentWidget(Widget):
            _count: Variable[int] = new(10)

        parent = qt.track(ParentWidget())
        d = qt.track(TestDialog(parent=parent))

        # Verify initial resolution
        assert d._count.value == 10

        # Change via dialog - should sync to parent
        d._count.value = 20
        assert parent._count.value == 20

        # Change via parent - should sync to dialog
        parent._count.value = 30
        assert d._count.value == 30

    def test_multiple_bare_variables_resolve(self, qt: QtDriver) -> None:
        """Multiple bare Variables each resolve correctly."""

        @dialog
        class TestDialog(Dialog):
            _name: Variable[str]
            _count: Variable[int]
            _active: Variable[bool]
            ok: DialogButton

        @widget
        class ParentWidget(Widget):
            _name: Variable[str] = new("Alice")
            _count: Variable[int] = new(42)
            _active: Variable[bool] = new(True)

        parent = qt.track(ParentWidget())
        d = qt.track(TestDialog(parent=parent))

        assert d._name.value == "Alice"
        assert d._count.value == 42
        assert d._active.value is True


# =============================================================================
# Dialog Parent Patterns
# =============================================================================


# =============================================================================
# Regression: Dialog Actually Opens
# =============================================================================


class TestDialogActuallyOpens:
    """Regression tests to ensure dialogs actually open (exec() works).

    These tests verify the dialog is visible and responsive, not just that
    the DialogResult is returned. Previous tests mocked _show_dialog which
    hid bugs where the dialog wouldn't actually show.
    """

    def test_dialog_exec_shows_dialog(self, qt: QtDriver) -> None:
        """Dialog.exec() actually shows the dialog (not mocked)."""
        from PySide6.QtCore import QTimer

        dialog_was_visible = False

        @dialog
        class TestDialog(Dialog):
            ok: DialogButton

        d = qt.track(TestDialog())

        # Schedule accept after dialog opens
        def accept_dialog() -> None:
            nonlocal dialog_was_visible
            dialog_was_visible = d.isVisible()
            d.accept()

        QTimer.singleShot(50, accept_dialog)
        result = d.show_dialog()

        assert result.accepted
        assert dialog_was_visible, "Dialog was never visible - exec() broken"

    def test_open_dialog_actually_opens(self, qt: QtDriver) -> None:
        """open_dialog() actually shows the dialog (not mocked)."""
        from PySide6.QtCore import QTimer

        dialog_instance: Dialog | None = None
        dialog_was_visible = False

        @dialog
        class TestDialog(Dialog):
            ok: DialogButton

            def __init__(self, **kwargs) -> None:  # type: ignore[no-untyped-def]
                nonlocal dialog_instance
                super().__init__(**kwargs)
                dialog_instance = self

        @widget
        class ParentWidget(Widget):
            pass

        parent = qt.track(ParentWidget())

        def accept_dialog() -> None:
            nonlocal dialog_was_visible
            if dialog_instance is not None:
                dialog_was_visible = dialog_instance.isVisible()
                dialog_instance.accept()

        QTimer.singleShot(50, accept_dialog)
        result = parent.open_dialog(TestDialog)

        assert result.accepted
        assert dialog_was_visible, "Dialog was never visible - open_dialog() broken"
        if dialog_instance:
            qt.track(dialog_instance)

    def test_class_show_dialog_actually_opens(self, qt: QtDriver) -> None:
        """Class.show_dialog() actually shows the dialog (not mocked)."""
        from PySide6.QtCore import QTimer

        dialog_instance: Dialog | None = None
        dialog_was_visible = False

        @dialog
        class TestDialog(Dialog):
            ok: DialogButton

            def __init__(self, **kwargs) -> None:  # type: ignore[no-untyped-def]
                nonlocal dialog_instance
                super().__init__(**kwargs)
                dialog_instance = self

        @widget
        class ParentWidget(Widget):
            pass

        parent = qt.track(ParentWidget())

        def accept_dialog() -> None:
            nonlocal dialog_was_visible
            if dialog_instance is not None:
                dialog_was_visible = dialog_instance.isVisible()
                dialog_instance.accept()

        QTimer.singleShot(50, accept_dialog)
        result = TestDialog.show_dialog(parent=parent)

        assert result.accepted
        assert dialog_was_visible, "Dialog was never visible - show_dialog(parent=) broken"
        if dialog_instance:
            qt.track(dialog_instance)


# =============================================================================
# Dialog Parent Patterns
# =============================================================================


class TestDialogParentPatterns:
    def test_parent_via_constructor(self, qt: QtDriver) -> None:
        """MyDialog(parent=widget) sets parent correctly."""

        @dialog
        class TestDialog(Dialog):
            ok: DialogButton

        @widget
        class ParentWidget(Widget):
            pass

        parent = qt.track(ParentWidget())
        d = qt.track(TestDialog(parent=parent))
        assert d.parent() is parent

    def test_parent_via_class_show_dialog(self, qt: QtDriver) -> None:
        """MyDialog.show_dialog(parent=widget) passes parent to constructor."""
        instances_created: list[Dialog] = []

        @dialog
        class TestDialog(Dialog):
            ok: DialogButton

            def __init__(self) -> None:
                super().__init__()
                instances_created.append(self)
                self._show_dialog = lambda: self._build_result(QDialog.DialogCode.Accepted)  # type: ignore[method-assign]

        @widget
        class ParentWidget(Widget):
            pass

        parent = qt.track(ParentWidget())
        TestDialog.show_dialog(parent=parent)

        assert len(instances_created) == 1
        d = instances_created[0]
        qt.track(d)
        assert d.parent() is parent

    def test_parent_via_instance_after_constructor(self, qt: QtDriver) -> None:
        """dialog = MyDialog(parent=w); dialog.show_dialog() uses existing parent."""

        @dialog
        class TestDialog(Dialog):
            ok: DialogButton

        @widget
        class ParentWidget(Widget):
            pass

        parent = qt.track(ParentWidget())
        d = qt.track(TestDialog(parent=parent))
        d._show_dialog = lambda: d._build_result(QDialog.DialogCode.Accepted)  # type: ignore[method-assign]

        result = d.show_dialog()
        assert result.accepted
        assert d.parent() is parent


# =============================================================================
# open_dialog() Helper Method (Parameterized)
# =============================================================================


@pytest.mark.parametrize("base_class,decorator", SHOW_DIALOG_CALLER_TYPES)
class TestOpenDialogHelper:
    def test_open_dialog_returns_result(self, base_class: type, decorator, qt: QtDriver) -> None:  # type: ignore[no-untyped-def]
        """self.open_dialog(DialogClass) returns DialogResult from all component types."""

        @dialog
        class TestDialog(Dialog):
            ok: DialogButton

            def __init__(self, **kwargs) -> None:  # type: ignore[no-untyped-def]
                super().__init__(**kwargs)
                self._show_dialog = lambda: self._build_result(QDialog.DialogCode.Accepted)  # type: ignore[method-assign]

        @decorator
        class TestComponent(base_class):  # type: ignore[misc]
            pass

        component = create_and_track(qt, TestComponent, base_class)
        result = component.open_dialog(TestDialog)

        assert isinstance(result, DialogResult)
        assert result.accepted

    def test_open_dialog_passes_parent_for_variable_resolution(self, base_class: type, decorator, qt: QtDriver) -> None:  # type: ignore[no-untyped-def]
        """self.open_dialog() passes parent so bare Variables resolve."""

        @dialog
        class TestDialog(Dialog):
            _api_url: Variable[str]  # Bare - should resolve from parent
            ok: DialogButton

            def __init__(self, **kwargs) -> None:  # type: ignore[no-untyped-def]
                super().__init__(**kwargs)
                self._show_dialog = lambda: self._build_result(QDialog.DialogCode.Accepted)  # type: ignore[method-assign]

        @decorator
        class TestComponent(base_class):  # type: ignore[misc]
            _api_url: Variable[str] = new("http://api.example.com")

        component = create_and_track(qt, TestComponent, base_class)
        result = component.open_dialog(TestDialog)

        # Dialog should have resolved _api_url from parent
        assert result.dialog is not None
        assert result.dialog._api_url.value == "http://api.example.com"

    def test_open_dialog_with_kwargs(self, base_class: type, decorator, qt: QtDriver) -> None:  # type: ignore[no-untyped-def]
        """self.open_dialog(DialogClass, var=value) passes kwargs to constructor."""

        @dialog
        class TestDialog(Dialog):
            _custom: Variable[str] = new("default")
            ok: DialogButton

            def __init__(self, **kwargs) -> None:  # type: ignore[no-untyped-def]
                super().__init__(**kwargs)
                self._show_dialog = lambda: self._build_result(QDialog.DialogCode.Accepted)  # type: ignore[method-assign]

        @decorator
        class TestComponent(base_class):  # type: ignore[misc]
            pass

        component = create_and_track(qt, TestComponent, base_class)
        result = component.open_dialog(TestDialog, _custom="custom_value")

        assert result.dialog is not None
        assert result.dialog._custom.value == "custom_value"

    def test_open_dialog_with_record(self, base_class: type, decorator, qt: QtDriver) -> None:  # type: ignore[no-untyped-def]
        """self.open_dialog(DialogClass, record=obj) sets record on Dialog[T]."""

        @dialog
        class TestDialog(Dialog[Person]):
            name: QLineEdit = new()
            ok: DialogButton

            def __init__(self, **kwargs) -> None:  # type: ignore[no-untyped-def]
                super().__init__(**kwargs)
                self._show_dialog = lambda: self._build_result(QDialog.DialogCode.Accepted)  # type: ignore[method-assign]

        @decorator
        class TestComponent(base_class):  # type: ignore[misc]
            pass

        component = create_and_track(qt, TestComponent, base_class)
        person = Person("Bob", 25)
        result = component.open_dialog(TestDialog, record=person)

        assert result.record is not None
        assert result.record.name == "Bob"
        assert result.record.age == 25


# =============================================================================
# Nested Dialogs
# =============================================================================


class TestNestedDialogs:
    def test_dialog_can_spawn_another_dialog(self, qt: QtDriver) -> None:
        """Dialog.show_dialog(AnotherDialog) works."""

        @dialog
        class InnerDialog(Dialog):
            ok: DialogButton

            def __init__(self, **kwargs) -> None:  # type: ignore[no-untyped-def]
                super().__init__(**kwargs)
                self._show_dialog = lambda: self._build_result(QDialog.DialogCode.Accepted)  # type: ignore[method-assign]

        @dialog
        class OuterDialog(Dialog):
            ok: DialogButton

            def spawn_inner(self) -> DialogResult:  # type: ignore[type-arg]
                return self.open_dialog(InnerDialog)

        outer = qt.track(OuterDialog())
        result = outer.spawn_inner()

        assert isinstance(result, DialogResult)
        assert result.accepted

    def test_nested_dialog_variable_resolution(self, qt: QtDriver) -> None:
        """Nested dialog resolves variables from first dialog's parent."""

        @dialog
        class InnerDialog(Dialog):
            _api_url: Variable[str]  # Should resolve from OuterDialog's parent
            ok: DialogButton

            def __init__(self, **kwargs) -> None:  # type: ignore[no-untyped-def]
                super().__init__(**kwargs)
                self._show_dialog = lambda: self._build_result(QDialog.DialogCode.Accepted)  # type: ignore[method-assign]

        @dialog
        class OuterDialog(Dialog):
            ok: DialogButton

            def __init__(self, **kwargs) -> None:  # type: ignore[no-untyped-def]
                super().__init__(**kwargs)
                self._show_dialog = lambda: self._build_result(QDialog.DialogCode.Accepted)  # type: ignore[method-assign]

            def spawn_inner(self) -> DialogResult:  # type: ignore[type-arg]
                return self.open_dialog(InnerDialog)

        @widget
        class RootWidget(Widget):
            _api_url: Variable[str] = new("http://root.example.com")

        root = qt.track(RootWidget())
        outer = qt.track(OuterDialog(parent=root))
        result = outer.spawn_inner()

        # InnerDialog should have resolved _api_url from OuterDialog's hierarchy
        # which includes RootWidget
        assert result.dialog is not None
        assert result.dialog._api_url.value == "http://root.example.com"

    def test_deeply_nested_dialogs(self, qt: QtDriver) -> None:
        """Dialog → Dialog → Dialog works (3 levels)."""

        @dialog
        class DeepDialog(Dialog):
            ok: DialogButton

            def __init__(self, **kwargs) -> None:  # type: ignore[no-untyped-def]
                super().__init__(**kwargs)
                self._show_dialog = lambda: self._build_result(QDialog.DialogCode.Accepted)  # type: ignore[method-assign]

        @dialog
        class MiddleDialog(Dialog):
            ok: DialogButton

            def __init__(self, **kwargs) -> None:  # type: ignore[no-untyped-def]
                super().__init__(**kwargs)
                self._show_dialog = lambda: self._build_result(QDialog.DialogCode.Accepted)  # type: ignore[method-assign]

            def spawn_deep(self) -> DialogResult:  # type: ignore[type-arg]
                return self.open_dialog(DeepDialog)

        @dialog
        class OuterDialog(Dialog):
            ok: DialogButton

            def __init__(self, **kwargs) -> None:  # type: ignore[no-untyped-def]
                super().__init__(**kwargs)
                self._show_dialog = lambda: self._build_result(QDialog.DialogCode.Accepted)  # type: ignore[method-assign]

            def spawn_middle(self) -> DialogResult:  # type: ignore[type-arg]
                return self.open_dialog(MiddleDialog)

        outer = qt.track(OuterDialog())
        middle_result = outer.spawn_middle()
        assert middle_result.dialog is not None
        qt.track(middle_result.dialog)

        deep_result = middle_result.dialog.spawn_deep()
        assert deep_result.accepted
        assert deep_result.dialog is not None
        qt.track(deep_result.dialog)


# =============================================================================
# Dialog Form Layout with Variable[T, W] Visibility
# =============================================================================


class TestDialogFormLayoutVariableVisibility:
    """Test that visible= on Variable[T, W] in Dialog form layout hides the row label."""

    def test_variable_widget_visible_hides_form_row(self, qt: QtDriver) -> None:
        """Variable[T, W] in dialog form layout with visible= hides entire row."""
        from PySide6.QtWidgets import QCheckBox, QFormLayout

        @dialog(layout="form")
        class TestDialog(Dialog):
            _show: Variable[bool] = new(True)
            _check: Variable[bool, QCheckBox] = new(False)(label="Check Me", visible="_show")

        d = qt.track(TestDialog())
        layout = d.layout()
        assert isinstance(layout, QFormLayout)

        checkbox = d._check.widget
        assert isinstance(checkbox, QCheckBox)

        # Initially visible
        assert not checkbox.isHidden()
        assert layout.isRowVisible(checkbox)

        # Hide via variable
        d._show.value = False
        qt.process_events()

        # Widget hidden
        assert checkbox.isHidden()
        # Row should also be hidden
        assert not layout.isRowVisible(checkbox)

    def test_variable_widget_visible_with_none_union_expression(self, qt: QtDriver) -> None:
        """Variable[T, W] visible= expression with 'is not None' hides form row."""
        from PySide6.QtWidgets import QCheckBox, QFormLayout

        @dataclass
        class Collection:
            name: str = ""

        @dialog(layout="form")
        class TestDialog(Dialog):
            selected_collection: Variable[Collection | None] = new(None)
            _check: Variable[bool, QCheckBox] = new(False)(
                label="Check Me",
                visible="{selected_collection is not None}",
            )

        d = qt.track(TestDialog())
        d.show()
        qt.process_events()

        layout = d.layout()
        assert isinstance(layout, QFormLayout)

        checkbox = d._check.widget
        assert isinstance(checkbox, QCheckBox)

        # Initially hidden (selected_collection is None)
        assert checkbox.isHidden(), "Checkbox should be hidden when selected_collection is None"
        assert not layout.isRowVisible(checkbox), "Row should be hidden when checkbox is hidden"

        # Set a collection - should become visible
        d.selected_collection.value = Collection("Test")
        qt.process_events()

        assert not checkbox.isHidden(), "Checkbox should be visible when selected_collection is not None"
        assert layout.isRowVisible(checkbox), "Row should be visible when selected_collection is not None"

    def test_variable_widget_visible_simple_bool(self, qt: QtDriver) -> None:
        """Variable[T, W] visible= with simple bool Variable hides form row."""
        from PySide6.QtWidgets import QCheckBox, QFormLayout

        @dialog(layout="form")
        class TestDialog(Dialog):
            _show: Variable[bool] = new(True)
            _check: Variable[bool, QCheckBox] = new(False)(
                label="Check Me",
                visible="_show",
            )

        d = qt.track(TestDialog())
        qt.process_events()

        layout = d.layout()
        assert isinstance(layout, QFormLayout)

        checkbox = d._check.widget
        assert isinstance(checkbox, QCheckBox)

        # Initially visible
        assert not checkbox.isHidden(), "Checkbox should be visible when _show is True"
        assert layout.isRowVisible(checkbox), "Row should be visible when _show is True"

        # Hide
        d._show.value = False
        qt.process_events()

        assert checkbox.isHidden(), "Checkbox should be hidden when _show is False"
        assert not layout.isRowVisible(checkbox), "Row should be hidden when _show is False"

    def test_variable_widget_visible_with_bool_expression(self, qt: QtDriver) -> None:
        """Variable[T, W] visible= with expression using int Variable hides form row."""
        from PySide6.QtWidgets import QCheckBox

        @dialog(layout="form")
        class TestDialog(Dialog):
            _count: Variable[int] = new(5)
            _check: Variable[bool, QCheckBox] = new(False)(
                label="Check Me",
                visible="{_count > 3}",
            )

        d = qt.track(TestDialog())
        qt.process_events()

        layout = d.layout()
        checkbox = d._check.widget

        # Initially visible (5 > 3)
        assert not checkbox.isHidden(), "Checkbox should be visible when _count > 3"
        assert layout.isRowVisible(checkbox), "Row should be visible when _count > 3"

        # Make expression false
        d._count.value = 2
        qt.process_events()

        assert checkbox.isHidden(), "Checkbox should be hidden when _count <= 3"
        assert not layout.isRowVisible(checkbox), "Row should be hidden when _count <= 3"

    def test_variable_widget_visible_with_proxy_expression(self, qt: QtDriver) -> None:
        """Variable[T, W] visible= with expression using ObservableProxy hides form row."""
        from PySide6.QtWidgets import QCheckBox

        @dataclass
        class MyData:
            active: bool = True

        @dialog(layout="form")
        class TestDialog(Dialog):
            _data: Variable[MyData] = new()
            _check: Variable[bool, QCheckBox] = new(False)(
                label="Check Me",
                visible="{_data.active}",
            )

        d = qt.track(TestDialog())
        qt.process_events()

        layout = d.layout()
        checkbox = d._check.widget

        # Initially visible (active=True)
        assert not checkbox.isHidden(), "Checkbox should be visible when _data.active is True"
        assert layout.isRowVisible(checkbox), "Row should be visible when _data.active is True"

        # Make expression false
        d._data.active = False
        qt.process_events()

        assert checkbox.isHidden(), "Checkbox should be hidden when _data.active is False"
        assert not layout.isRowVisible(checkbox), "Row should be hidden when _data.active is False"
