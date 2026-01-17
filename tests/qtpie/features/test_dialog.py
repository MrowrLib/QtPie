# pyright: reportPrivateUsage=false
# pyright: reportUnknownArgumentType=false
# pyright: reportOptionalMemberAccess=false
# pyright: reportUnknownMemberType=false
# pyright: reportAttributeAccessIssue=false
# pyright: reportUnusedClass=false
"""Tests for Dialog, DialogButton, DialogButtons, @dialog, @buttons."""

from dataclasses import dataclass
from typing import override

import pytest
from PySide6.QtWidgets import QDialog, QDialogButtonBox, QLabel, QLineEdit, QSpinBox, QVBoxLayout

from qtpie import Dialog, DialogButton, DialogButtons, DialogResult, Variable, buttons, dialog, new
from qtpie.testing import QtDriver


@dataclass
class Person:
    name: str = ""
    age: int = 0


@pytest.fixture
def qt(qtbot) -> QtDriver:  # type: ignore[no-untyped-def]
    return QtDriver(qtbot)


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
