"""Quick message box dialogs - confirm() and messagebox()."""

from dataclasses import dataclass
from typing import Literal

from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import QApplication, QDialogButtonBox, QMessageBox, QWidget

from .dialog import ButtonInfo

# Icon preset type for autocomplete
IconPreset = Literal["question", "information", "warning", "critical"]
IconType = IconPreset | str | QIcon | QPixmap | None

# Button type aliases
ButtonList = list[str]
ButtonDict = dict[str, str]
ButtonsType = ButtonList | ButtonDict

# Map normalized button names to QMessageBox.StandardButton
_BUTTON_MAP: dict[str, QMessageBox.StandardButton] = {
    "ok": QMessageBox.StandardButton.Ok,
    "cancel": QMessageBox.StandardButton.Cancel,
    "yes": QMessageBox.StandardButton.Yes,
    "no": QMessageBox.StandardButton.No,
    "save": QMessageBox.StandardButton.Save,
    "saveall": QMessageBox.StandardButton.SaveAll,
    "discard": QMessageBox.StandardButton.Discard,
    "close": QMessageBox.StandardButton.Close,
    "apply": QMessageBox.StandardButton.Apply,
    "reset": QMessageBox.StandardButton.Reset,
    "restoredefaults": QMessageBox.StandardButton.RestoreDefaults,
    "help": QMessageBox.StandardButton.Help,
    "open": QMessageBox.StandardButton.Open,
    "abort": QMessageBox.StandardButton.Abort,
    "retry": QMessageBox.StandardButton.Retry,
    "ignore": QMessageBox.StandardButton.Ignore,
    "yestoall": QMessageBox.StandardButton.YesToAll,
    "notoall": QMessageBox.StandardButton.NoToAll,
}

# Reverse map: StandardButton -> normalized name
_BUTTON_NAME_MAP: dict[QMessageBox.StandardButton, str] = {v: k for k, v in _BUTTON_MAP.items()}

# Buttons that count as "positive" / "accepted"
_POSITIVE_BUTTONS: set[str] = {"ok", "yes", "save", "saveall", "apply", "open", "retry", "yestoall"}

# Map icon preset strings to QMessageBox.Icon
_ICON_PRESET_MAP: dict[str, QMessageBox.Icon] = {
    "question": QMessageBox.Icon.Question,
    "information": QMessageBox.Icon.Information,
    "warning": QMessageBox.Icon.Warning,
    "critical": QMessageBox.Icon.Critical,
}

# Map StandardButton to ButtonRole
_BUTTON_ROLE_MAP: dict[QMessageBox.StandardButton, QDialogButtonBox.ButtonRole] = {
    QMessageBox.StandardButton.Ok: QDialogButtonBox.ButtonRole.AcceptRole,
    QMessageBox.StandardButton.Cancel: QDialogButtonBox.ButtonRole.RejectRole,
    QMessageBox.StandardButton.Yes: QDialogButtonBox.ButtonRole.YesRole,
    QMessageBox.StandardButton.No: QDialogButtonBox.ButtonRole.NoRole,
    QMessageBox.StandardButton.Save: QDialogButtonBox.ButtonRole.AcceptRole,
    QMessageBox.StandardButton.SaveAll: QDialogButtonBox.ButtonRole.AcceptRole,
    QMessageBox.StandardButton.Discard: QDialogButtonBox.ButtonRole.DestructiveRole,
    QMessageBox.StandardButton.Close: QDialogButtonBox.ButtonRole.RejectRole,
    QMessageBox.StandardButton.Apply: QDialogButtonBox.ButtonRole.ApplyRole,
    QMessageBox.StandardButton.Reset: QDialogButtonBox.ButtonRole.ResetRole,
    QMessageBox.StandardButton.RestoreDefaults: QDialogButtonBox.ButtonRole.ResetRole,
    QMessageBox.StandardButton.Help: QDialogButtonBox.ButtonRole.HelpRole,
    QMessageBox.StandardButton.Open: QDialogButtonBox.ButtonRole.AcceptRole,
    QMessageBox.StandardButton.Abort: QDialogButtonBox.ButtonRole.RejectRole,
    QMessageBox.StandardButton.Retry: QDialogButtonBox.ButtonRole.AcceptRole,
    QMessageBox.StandardButton.Ignore: QDialogButtonBox.ButtonRole.AcceptRole,
    QMessageBox.StandardButton.YesToAll: QDialogButtonBox.ButtonRole.YesRole,
    QMessageBox.StandardButton.NoToAll: QDialogButtonBox.ButtonRole.NoRole,
}


def _normalize_button_name(name: str) -> str:
    """Normalize button name by removing non-alpha chars and lowercasing.

    Examples:
        "YES_TO_ALL" -> "yestoall"
        "yesToAll" -> "yestoall"
        "Ok" -> "ok"
    """
    return "".join(c for c in name if c.isalpha()).lower()


@dataclass
class MessageBoxResult:
    """Result from messagebox()."""

    button: ButtonInfo

    @property
    def accepted(self) -> bool:
        """True if a positive button was clicked."""
        return self.button.name in _POSITIVE_BUTTONS

    @property
    def rejected(self) -> bool:
        """True if a negative button was clicked."""
        return not self.accepted

    def __bool__(self) -> bool:
        """True if dialog was accepted (positive button clicked)."""
        return self.accepted


def _build_messagebox(
    text: str,
    title: str = "",
    icon: IconType = None,
    buttons: ButtonsType | None = None,
    default_button: str | None = None,
    parent: QWidget | None = None,
) -> MessageBoxResult:
    """Build and show a QMessageBox, return the result."""
    if buttons is None:
        buttons = ["ok", "cancel"]

    # Get parent - use active window if not specified
    if parent is None:
        parent = QApplication.activeWindow()

    # Build the message box
    msg = QMessageBox(parent)
    msg.setText(text)
    if title:
        msg.setWindowTitle(title)

    # Set icon
    if icon is not None:
        if isinstance(icon, str):
            if icon in _ICON_PRESET_MAP:
                msg.setIcon(_ICON_PRESET_MAP[icon])
            else:
                # Treat as path
                msg.setIconPixmap(QPixmap(icon))
        elif isinstance(icon, QIcon):
            # QMessageBox doesn't have setIcon(QIcon), use pixmap
            msg.setIconPixmap(icon.pixmap(64, 64))
        else:
            # Must be QPixmap
            msg.setIconPixmap(icon)

    # Parse buttons - build mapping from normalized name to custom text
    button_configs: dict[str, str | None] = {}  # normalized_name -> custom_text or None
    if isinstance(buttons, dict):
        for name, custom_text in buttons.items():
            normalized = _normalize_button_name(name)
            if normalized not in _BUTTON_MAP:
                raise ValueError(f"Unknown button type: {name!r} (normalized: {normalized!r})")
            button_configs[normalized] = custom_text
    else:
        for name in buttons:
            normalized = _normalize_button_name(name)
            if normalized not in _BUTTON_MAP:
                raise ValueError(f"Unknown button type: {name!r} (normalized: {normalized!r})")
            button_configs[normalized] = None

    # Add buttons to message box
    for normalized_name, custom_text in button_configs.items():
        std_button = _BUTTON_MAP[normalized_name]
        msg.addButton(std_button)
        if custom_text is not None:
            btn = msg.button(std_button)
            btn.setText(custom_text)

    # Set default button
    if default_button is not None:
        normalized_default = _normalize_button_name(default_button)
        if normalized_default in _BUTTON_MAP:
            msg.setDefaultButton(_BUTTON_MAP[normalized_default])

    # Show dialog
    msg.exec()

    # Get clicked button
    clicked = msg.clickedButton()
    clicked_std = msg.standardButton(clicked) if clicked else QMessageBox.StandardButton.NoButton

    # Build result
    if clicked_std in _BUTTON_NAME_MAP:
        name = _BUTTON_NAME_MAP[clicked_std]
        text_value = clicked.text() if clicked else ""
        role = _BUTTON_ROLE_MAP.get(clicked_std, QDialogButtonBox.ButtonRole.InvalidRole)
        button_info = ButtonInfo(name=name, text=text_value, role=role)
    else:
        # Fallback - shouldn't happen with proper button setup
        button_info = ButtonInfo(
            name="unknown",
            text=clicked.text() if clicked else "",
            role=QDialogButtonBox.ButtonRole.InvalidRole,
        )

    return MessageBoxResult(button=button_info)


def confirm(
    text: str,
    title: str = "",
    icon: IconType = None,
    buttons: ButtonsType | None = None,
    default_button: str | None = None,
    parent: QWidget | None = None,
) -> bool:
    """Show a confirmation dialog and return True if accepted.

    Args:
        text: The message to display.
        title: Window title (optional).
        icon: Icon to display. Can be a preset ("question", "information", "warning",
            "critical"), a file path, QIcon, or QPixmap.
        buttons: Button configuration. Either a list of button names like ["yes", "no"]
            or a dict mapping names to custom text like {"yes": "Yep!", "no": "Nope"}.
            Defaults to ["ok", "cancel"].
        default_button: Which button is focused by default.
        parent: Parent widget. Defaults to active window.

    Returns:
        True if a positive button (ok, yes, save, etc.) was clicked, False otherwise.

    Example:
        if confirm("Delete this item?"):
            delete_item()

        if confirm("Save changes?", buttons=["save", "discard", "cancel"]):
            save()
    """
    result = _build_messagebox(text, title, icon, buttons, default_button, parent)
    return result.accepted


def messagebox(
    text: str,
    title: str = "",
    icon: IconType = None,
    buttons: ButtonsType | None = None,
    default_button: str | None = None,
    parent: QWidget | None = None,
) -> MessageBoxResult:
    """Show a message box dialog and return detailed result.

    Args:
        text: The message to display.
        title: Window title (optional).
        icon: Icon to display. Can be a preset ("question", "information", "warning",
            "critical"), a file path, QIcon, or QPixmap.
        buttons: Button configuration. Either a list of button names like ["yes", "no"]
            or a dict mapping names to custom text like {"yes": "Yep!", "no": "Nope"}.
            Defaults to ["ok", "cancel"].
        default_button: Which button is focused by default.
        parent: Parent widget. Defaults to active window.

    Returns:
        MessageBoxResult with button info. Use result.button.name to check which
        button was clicked, or result.accepted/result.rejected for quick checks.

    Example:
        result = messagebox("What would you like to do?", buttons=["yes", "no", "cancel"])
        if result.button.name == "yes":
            do_yes()
        elif result.button.name == "no":
            do_no()
        else:
            cancel()
    """
    return _build_messagebox(text, title, icon, buttons, default_button, parent)
