# pyright: reportPrivateUsage=false
# pyright: reportUnknownMemberType=false
# pyright: reportUnusedFunction=false
"""Tests for confirm() and messagebox() functions."""

from unittest.mock import MagicMock, patch

import pytest
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import QDialogButtonBox, QMessageBox

from qtpie import MessageBoxResult, confirm, messagebox
from qtpie.dialog import ButtonInfo
from qtpie.messagebox import _normalize_button_name

# =============================================================================
# Button Name Normalization
# =============================================================================


class TestButtonNameNormalization:
    def test_lowercase(self) -> None:
        assert _normalize_button_name("OK") == "ok"
        assert _normalize_button_name("Cancel") == "cancel"
        assert _normalize_button_name("YES") == "yes"

    def test_remove_underscores(self) -> None:
        assert _normalize_button_name("yes_to_all") == "yestoall"
        assert _normalize_button_name("no_to_all") == "notoall"
        assert _normalize_button_name("restore_defaults") == "restoredefaults"

    def test_camelcase(self) -> None:
        assert _normalize_button_name("yesToAll") == "yestoall"
        assert _normalize_button_name("noToAll") == "notoall"
        assert _normalize_button_name("restoreDefaults") == "restoredefaults"

    def test_mixed_formats(self) -> None:
        assert _normalize_button_name("YES_TO_ALL") == "yestoall"
        assert _normalize_button_name("YesToAll") == "yestoall"
        assert _normalize_button_name("yes-to-all") == "yestoall"  # Hyphens removed too

    def test_already_normalized(self) -> None:
        assert _normalize_button_name("ok") == "ok"
        assert _normalize_button_name("cancel") == "cancel"
        assert _normalize_button_name("yestoall") == "yestoall"


# =============================================================================
# MessageBoxResult
# =============================================================================


class TestMessageBoxResult:
    def test_accepted_for_positive_button(self) -> None:
        for name in ["ok", "yes", "save", "saveall", "apply", "open", "retry", "yestoall"]:
            result = MessageBoxResult(button=ButtonInfo(name=name, text=name.title(), role=QDialogButtonBox.ButtonRole.AcceptRole))
            assert result.accepted is True
            assert result.rejected is False
            assert bool(result) is True

    def test_rejected_for_negative_button(self) -> None:
        for name in ["cancel", "no", "discard", "close", "abort", "notoall"]:
            result = MessageBoxResult(button=ButtonInfo(name=name, text=name.title(), role=QDialogButtonBox.ButtonRole.RejectRole))
            assert result.accepted is False
            assert result.rejected is True
            assert bool(result) is False

    def test_button_info_accessible(self) -> None:
        result = MessageBoxResult(button=ButtonInfo(name="save", text="Save Changes", role=QDialogButtonBox.ButtonRole.AcceptRole))
        assert result.button.name == "save"
        assert result.button.text == "Save Changes"


# =============================================================================
# confirm() Function - Mocked Tests
# =============================================================================


class TestConfirmMocked:
    @patch("qtpie.messagebox.QMessageBox")
    def test_confirm_returns_true_for_ok(self, mock_msgbox_class: MagicMock) -> None:
        mock_msgbox = MagicMock()
        mock_msgbox_class.return_value = mock_msgbox

        # Setup: clicking OK button
        mock_button = MagicMock()
        mock_button.text.return_value = "OK"
        mock_msgbox.clickedButton.return_value = mock_button
        mock_msgbox.standardButton.return_value = QMessageBox.StandardButton.Ok

        result = confirm("Test message")
        assert result is True

    @patch("qtpie.messagebox.QMessageBox")
    def test_confirm_returns_false_for_cancel(self, mock_msgbox_class: MagicMock) -> None:
        mock_msgbox = MagicMock()
        mock_msgbox_class.return_value = mock_msgbox

        mock_button = MagicMock()
        mock_button.text.return_value = "Cancel"
        mock_msgbox.clickedButton.return_value = mock_button
        mock_msgbox.standardButton.return_value = QMessageBox.StandardButton.Cancel

        result = confirm("Test message")
        assert result is False

    @patch("qtpie.messagebox.QMessageBox")
    def test_confirm_returns_true_for_yes(self, mock_msgbox_class: MagicMock) -> None:
        mock_msgbox = MagicMock()
        mock_msgbox_class.return_value = mock_msgbox

        mock_button = MagicMock()
        mock_button.text.return_value = "Yes"
        mock_msgbox.clickedButton.return_value = mock_button
        mock_msgbox.standardButton.return_value = QMessageBox.StandardButton.Yes

        result = confirm("Test message", buttons=["yes", "no"])
        assert result is True

    @patch("qtpie.messagebox.QMessageBox")
    def test_confirm_returns_false_for_no(self, mock_msgbox_class: MagicMock) -> None:
        mock_msgbox = MagicMock()
        mock_msgbox_class.return_value = mock_msgbox

        mock_button = MagicMock()
        mock_button.text.return_value = "No"
        mock_msgbox.clickedButton.return_value = mock_button
        mock_msgbox.standardButton.return_value = QMessageBox.StandardButton.No

        result = confirm("Test message", buttons=["yes", "no"])
        assert result is False


# =============================================================================
# messagebox() Function - Mocked Tests
# =============================================================================


class TestMessageboxMocked:
    @patch("qtpie.messagebox.QMessageBox")
    def test_messagebox_returns_result(self, mock_msgbox_class: MagicMock) -> None:
        mock_msgbox = MagicMock()
        mock_msgbox_class.return_value = mock_msgbox

        mock_button = MagicMock()
        mock_button.text.return_value = "Save"
        mock_msgbox.clickedButton.return_value = mock_button
        mock_msgbox.standardButton.return_value = QMessageBox.StandardButton.Save

        result = messagebox("Save changes?", buttons=["save", "discard", "cancel"])

        assert isinstance(result, MessageBoxResult)
        assert result.button.name == "save"
        assert result.accepted is True

    @patch("qtpie.messagebox.QMessageBox")
    def test_messagebox_button_text_from_dict(self, mock_msgbox_class: MagicMock) -> None:
        mock_msgbox = MagicMock()
        mock_msgbox_class.return_value = mock_msgbox

        # Track button text changes
        button_texts: dict[QMessageBox.StandardButton, str] = {}
        mock_buttons: dict[QMessageBox.StandardButton, MagicMock] = {}

        def mock_button(std_btn: QMessageBox.StandardButton) -> MagicMock:
            if std_btn not in mock_buttons:
                btn = MagicMock()

                def make_set_text(s: QMessageBox.StandardButton) -> None:
                    def set_text(t: str) -> None:
                        button_texts[s] = t

                    btn.setText = set_text

                def make_get_text(s: QMessageBox.StandardButton) -> None:
                    def get_text() -> str:
                        return button_texts.get(s, "")

                    btn.text = get_text

                make_set_text(std_btn)
                make_get_text(std_btn)
                mock_buttons[std_btn] = btn
            return mock_buttons[std_btn]

        mock_msgbox.button = mock_button

        mock_clicked = MagicMock()
        mock_clicked.text.return_value = "Yep!"
        mock_msgbox.clickedButton.return_value = mock_clicked
        mock_msgbox.standardButton.return_value = QMessageBox.StandardButton.Yes

        messagebox("Continue?", buttons={"yes": "Yep!", "no": "Nope"})

        # Verify custom text was set
        assert button_texts.get(QMessageBox.StandardButton.Yes) == "Yep!"
        assert button_texts.get(QMessageBox.StandardButton.No) == "Nope"


# =============================================================================
# Icon Handling - Mocked Tests
# =============================================================================


class TestIconHandling:
    @patch("qtpie.messagebox.QMessageBox")
    def test_icon_preset_question(self, mock_msgbox_class: MagicMock) -> None:
        mock_msgbox = MagicMock()
        mock_msgbox_class.return_value = mock_msgbox
        mock_msgbox.clickedButton.return_value = MagicMock(text=lambda: "OK")
        mock_msgbox.standardButton.return_value = QMessageBox.StandardButton.Ok

        confirm("Question?", icon="question")

        mock_msgbox.setIcon.assert_called_once_with(QMessageBox.Icon.Question)

    @patch("qtpie.messagebox.QMessageBox")
    def test_icon_preset_warning(self, mock_msgbox_class: MagicMock) -> None:
        mock_msgbox = MagicMock()
        mock_msgbox_class.return_value = mock_msgbox
        mock_msgbox.clickedButton.return_value = MagicMock(text=lambda: "OK")
        mock_msgbox.standardButton.return_value = QMessageBox.StandardButton.Ok

        confirm("Warning!", icon="warning")

        mock_msgbox.setIcon.assert_called_once_with(QMessageBox.Icon.Warning)

    @patch("qtpie.messagebox.QMessageBox")
    def test_icon_preset_critical(self, mock_msgbox_class: MagicMock) -> None:
        mock_msgbox = MagicMock()
        mock_msgbox_class.return_value = mock_msgbox
        mock_msgbox.clickedButton.return_value = MagicMock(text=lambda: "OK")
        mock_msgbox.standardButton.return_value = QMessageBox.StandardButton.Ok

        confirm("Error!", icon="critical")

        mock_msgbox.setIcon.assert_called_once_with(QMessageBox.Icon.Critical)

    @patch("qtpie.messagebox.QMessageBox")
    def test_icon_preset_information(self, mock_msgbox_class: MagicMock) -> None:
        mock_msgbox = MagicMock()
        mock_msgbox_class.return_value = mock_msgbox
        mock_msgbox.clickedButton.return_value = MagicMock(text=lambda: "OK")
        mock_msgbox.standardButton.return_value = QMessageBox.StandardButton.Ok

        confirm("Info", icon="information")

        mock_msgbox.setIcon.assert_called_once_with(QMessageBox.Icon.Information)

    @patch("qtpie.messagebox.QMessageBox")
    @patch("qtpie.messagebox.QPixmap")
    def test_icon_from_path(self, mock_pixmap_class: MagicMock, mock_msgbox_class: MagicMock) -> None:
        mock_msgbox = MagicMock()
        mock_msgbox_class.return_value = mock_msgbox
        mock_msgbox.clickedButton.return_value = MagicMock(text=lambda: "OK")
        mock_msgbox.standardButton.return_value = QMessageBox.StandardButton.Ok

        mock_pixmap = MagicMock()
        mock_pixmap_class.return_value = mock_pixmap

        confirm("Test", icon=":/icons/test.png")

        mock_pixmap_class.assert_called_once_with(":/icons/test.png")
        mock_msgbox.setIconPixmap.assert_called_once_with(mock_pixmap)

    @patch("qtpie.messagebox.QMessageBox")
    def test_icon_from_qpixmap(self, mock_msgbox_class: MagicMock) -> None:
        mock_msgbox = MagicMock()
        mock_msgbox_class.return_value = mock_msgbox
        mock_msgbox.clickedButton.return_value = MagicMock(text=lambda: "OK")
        mock_msgbox.standardButton.return_value = QMessageBox.StandardButton.Ok

        pixmap = QPixmap(16, 16)
        confirm("Test", icon=pixmap)

        mock_msgbox.setIconPixmap.assert_called_once_with(pixmap)

    @patch("qtpie.messagebox.QMessageBox")
    def test_icon_from_qicon(self, mock_msgbox_class: MagicMock) -> None:
        mock_msgbox = MagicMock()
        mock_msgbox_class.return_value = mock_msgbox
        mock_msgbox.clickedButton.return_value = MagicMock(text=lambda: "OK")
        mock_msgbox.standardButton.return_value = QMessageBox.StandardButton.Ok

        icon = QIcon(QPixmap(16, 16))
        confirm("Test", icon=icon)

        # Should call setIconPixmap with the icon's pixmap
        mock_msgbox.setIconPixmap.assert_called_once()


# =============================================================================
# Error Handling
# =============================================================================


class TestErrorHandling:
    @patch("qtpie.messagebox.QMessageBox")
    def test_invalid_button_name_raises(self, mock_msgbox_class: MagicMock) -> None:
        mock_msgbox = MagicMock()
        mock_msgbox_class.return_value = mock_msgbox

        with pytest.raises(ValueError, match="Unknown button type"):
            confirm("Test", buttons=["ok", "invalid_button"])

    @patch("qtpie.messagebox.QMessageBox")
    def test_invalid_button_in_dict_raises(self, mock_msgbox_class: MagicMock) -> None:
        mock_msgbox = MagicMock()
        mock_msgbox_class.return_value = mock_msgbox

        with pytest.raises(ValueError, match="Unknown button type"):
            confirm("Test", buttons={"ok": "OK", "foo": "Foo"})


# =============================================================================
# Title and Default Button
# =============================================================================


class TestTitleAndDefaultButton:
    @patch("qtpie.messagebox.QMessageBox")
    def test_title_is_set(self, mock_msgbox_class: MagicMock) -> None:
        mock_msgbox = MagicMock()
        mock_msgbox_class.return_value = mock_msgbox
        mock_msgbox.clickedButton.return_value = MagicMock(text=lambda: "OK")
        mock_msgbox.standardButton.return_value = QMessageBox.StandardButton.Ok

        confirm("Message", title="My Title")

        mock_msgbox.setWindowTitle.assert_called_once_with("My Title")

    @patch("qtpie.messagebox.QMessageBox")
    def test_default_button_is_set(self, mock_msgbox_class: MagicMock) -> None:
        mock_msgbox = MagicMock()
        mock_msgbox_class.return_value = mock_msgbox
        mock_msgbox.clickedButton.return_value = MagicMock(text=lambda: "Cancel")
        mock_msgbox.standardButton.return_value = QMessageBox.StandardButton.Cancel

        confirm("Message", buttons=["ok", "cancel"], default_button="cancel")

        mock_msgbox.setDefaultButton.assert_called_once_with(QMessageBox.StandardButton.Cancel)

    @patch("qtpie.messagebox.QMessageBox")
    def test_default_button_normalized(self, mock_msgbox_class: MagicMock) -> None:
        mock_msgbox = MagicMock()
        mock_msgbox_class.return_value = mock_msgbox
        mock_msgbox.clickedButton.return_value = MagicMock(text=lambda: "Yes")
        mock_msgbox.standardButton.return_value = QMessageBox.StandardButton.Yes

        confirm("Message", buttons=["yes", "no"], default_button="YES")

        mock_msgbox.setDefaultButton.assert_called_once_with(QMessageBox.StandardButton.Yes)


# =============================================================================
# All Button Types
# =============================================================================


class TestAllButtonTypes:
    @patch("qtpie.messagebox.QMessageBox")
    def test_all_standard_buttons_recognized(self, mock_msgbox_class: MagicMock) -> None:
        mock_msgbox = MagicMock()
        mock_msgbox_class.return_value = mock_msgbox
        mock_msgbox.clickedButton.return_value = MagicMock(text=lambda: "OK")
        mock_msgbox.standardButton.return_value = QMessageBox.StandardButton.Ok

        all_buttons = [
            "ok",
            "cancel",
            "yes",
            "no",
            "save",
            "saveall",
            "discard",
            "close",
            "apply",
            "reset",
            "restoredefaults",
            "help",
            "open",
            "abort",
            "retry",
            "ignore",
            "yestoall",
            "notoall",
        ]

        # Each button should be accepted without raising
        for button in all_buttons:
            confirm("Test", buttons=[button])
