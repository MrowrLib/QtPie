"""
Default binding registrations for common Qt widgets.

These are automatically registered when qtpie.bindings is imported.
To add custom bindings for your own widgets, use register_binding():

    from qtpie.bindings import register_binding
    from PySide6.QtWidgets import QSpinBox

    register_binding(
        QSpinBox,
        "value",
        setter=lambda w, v: w.setValue(int(v)),
        getter=lambda w: w.value(),
        signal="valueChanged",
    )
"""

from PySide6.QtWidgets import (
    QComboBox,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QTextEdit,
)

from qtpie.bindings.registry import register_binding


def register_default_bindings() -> None:
    """Register default bindings for common Qt widgets."""

    # QTextEdit - text property
    register_binding(
        QTextEdit,
        "text",
        setter=lambda widget, value: widget.setPlainText(str(value)),
        getter=lambda widget: widget.toPlainText(),
        signal="textChanged",
    )

    # QPlainTextEdit - text property
    register_binding(
        QPlainTextEdit,
        "text",
        setter=lambda widget, value: widget.setPlainText(str(value)),
        getter=lambda widget: widget.toPlainText(),
        signal="textChanged",
    )

    # QLabel - text property (one-way, no signal needed)
    register_binding(
        QLabel,
        "text",
        setter=lambda widget, value: widget.setText(str(value)),
    )

    # QLineEdit - text property
    register_binding(
        QLineEdit,
        "text",
        setter=lambda widget, value: widget.setText(str(value)),
        getter=lambda widget: widget.text(),
        signal="textChanged",
    )

    # QComboBox - text property (current text)
    register_binding(
        QComboBox,
        "text",
        setter=lambda widget, value: widget.setCurrentText(str(value)),
        getter=lambda widget: widget.currentText(),
        signal="currentTextChanged",
    )
