"""Delegate for applying validators to inline editors."""

from collections.abc import Callable
from typing import Any, override

from qtpy.QtCore import QModelIndex, QPersistentModelIndex
from qtpy.QtWidgets import QLineEdit, QStyledItemDelegate, QStyleOptionViewItem, QWidget


class ValidatorItemDelegate(QStyledItemDelegate):
    """Delegate that applies a validator to the default line edit editor.

    When a QTreeView or QListView is set to editable, Qt uses a default
    QLineEdit for inline editing. This delegate intercepts createEditor()
    to apply a validator to that line edit.

    Usage:
        validator_delegate = ValidatorItemDelegate(filename_safe_validator, parent=view)
        view.setItemDelegate(validator_delegate)
    """

    def __init__(
        self,
        validator_spec: str | Callable[..., Any],
        parent: QWidget | None = None,
    ) -> None:
        """Initialize the delegate.

        Args:
            validator_spec: Validator specification (same format as QLineEdit validator=):
                - str (regex pattern): Creates QRegularExpressionValidator
                - str (method name): Creates MethodValidator (resolved on parent widgets)
                - Callable[[str], bool]: Simple predicate validator
                - Callable[[str, int], State]: Full QValidator.State validator
            parent: Qt parent widget.
        """
        super().__init__(parent)
        self._validator_spec = validator_spec

    @override
    def createEditor(
        self,
        parent: QWidget,
        option: QStyleOptionViewItem,
        index: QModelIndex | QPersistentModelIndex,
    ) -> QWidget:
        """Create the editor widget and apply the validator.

        Args:
            parent: The parent widget for the created editor.
            option: Style options.
            index: The model index being edited.

        Returns:
            A QLineEdit with the validator applied.
        """
        # Call the base implementation to get the default editor
        editor = super().createEditor(parent, option, index)

        # If it's a QLineEdit, apply our validator
        if isinstance(editor, QLineEdit):
            from qtpie.input_validator import apply_validator

            apply_validator(editor, self._validator_spec)

        return editor
