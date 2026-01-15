"""Bindings for QPlainTextEdit/QTextEdit highlighter and content_type."""

from typing import Any, override

from observant import Observable
from qtpy.QtGui import QSyntaxHighlighter
from qtpy.QtWidgets import QPlainTextEdit, QTextEdit, QWidget

from qtpie.new_field import NewField

type HighlighterType = type[QSyntaxHighlighter] | QSyntaxHighlighter | None


def _set_highlighter_on_editor(
    editor: QPlainTextEdit | QTextEdit,
    highlighter_class_or_instance: HighlighterType,
) -> None:
    """Set a highlighter on a text editor, properly disposing the old one.

    Args:
        editor: The QPlainTextEdit or QTextEdit
        highlighter_class_or_instance: Either a highlighter class to instantiate,
            an instance to use directly, or None to remove highlighting
    """
    doc = editor.document()

    # The old highlighter will be garbage collected when we create a new one
    # because QSyntaxHighlighter's parent is the document
    if highlighter_class_or_instance is None:
        # Setting a "null" highlighter - create an empty one to clear formatting
        _EmptyHighlighter(doc)
    elif isinstance(highlighter_class_or_instance, type):
        # It's a class - instantiate it
        highlighter_class_or_instance(doc)
    else:
        # It's an instance - set its document
        highlighter_class_or_instance.setDocument(doc)


class _EmptyHighlighter(QSyntaxHighlighter):
    """A no-op highlighter to clear formatting."""

    @override
    def highlightBlock(self, text: str) -> None:
        pass


def apply_text_editor_bindings(
    host: QWidget,
    editor: QPlainTextEdit | QTextEdit,
    field_info: NewField,
    resolve_or_create_variable_fn: Any,
) -> None:
    """Apply highlighter and content_type bindings to a text editor.

    Args:
        host: The parent Widget/Window
        editor: The QPlainTextEdit or QTextEdit instance
        field_info: The NewField with binding info
        resolve_or_create_variable_fn: Function to resolve/create Variables
    """
    from qtpie.variable import Variable as VarType

    # Handle highlighter= binding
    if field_info.highlighter is not None:
        highlighter_val = field_info.highlighter

        if isinstance(highlighter_val, str):
            # It's a Variable binding - resolve and subscribe
            var = resolve_or_create_variable_fn(host, highlighter_val)
            if var is not None:
                # Set initial value
                if isinstance(var, VarType):
                    initial: HighlighterType = var.value  # pyright: ignore[reportUnknownMemberType,reportUnknownVariableType]
                    _set_highlighter_on_editor(editor, initial)  # pyright: ignore[reportUnknownArgumentType]

                    # Subscribe to changes - capture var reference, read .value in callback
                    # Callback takes *args to handle both Observable (passes value) and
                    # ObservableProxy (passes nothing)
                    def make_highlighter_callback(
                        ed: QPlainTextEdit | QTextEdit,
                        v: Any,
                    ) -> Any:
                        def on_change(*args: Any) -> None:
                            _set_highlighter_on_editor(ed, v.value)

                        return on_change

                    var.on_change(make_highlighter_callback(editor, var))
                elif isinstance(var, Observable):
                    initial_obs: HighlighterType = var.get()  # pyright: ignore[reportUnknownMemberType,reportUnknownVariableType]
                    _set_highlighter_on_editor(editor, initial_obs)  # pyright: ignore[reportUnknownArgumentType]

                    def make_highlighter_callback_obs(
                        ed: QPlainTextEdit | QTextEdit,
                        obs: Any,
                    ) -> Any:
                        def on_change(*args: Any) -> None:
                            _set_highlighter_on_editor(ed, obs.get())

                        return on_change

                    var.on_change(make_highlighter_callback_obs(editor, var))  # pyright: ignore[reportUnknownMemberType]
        else:
            # It's a static class - just instantiate once
            highlighter_val(editor.document())

    # Handle content_type= binding
    if field_info.editor_content_type is not None:
        from qtpie.bindings import create_format_binding, is_format_string
        from qtpie.highlighters.registry import get_highlighter_for_mime

        content_type_path = field_info.editor_content_type

        # Check if it's a format expression like "{headers['content-type']}"
        if is_format_string(content_type_path):
            # Use format binding - creates reactive expression that updates on change
            def make_content_type_setter(ed: QPlainTextEdit | QTextEdit) -> Any:
                def set_content_type(mime_type: str | None) -> None:
                    hl_class = get_highlighter_for_mime(mime_type)
                    _set_highlighter_on_editor(ed, hl_class)

                return set_content_type

            create_format_binding(host, content_type_path, make_content_type_setter(editor))  # type: ignore[arg-type]
        else:
            # Simple variable binding
            var = resolve_or_create_variable_fn(host, content_type_path)

            if var is not None:
                if isinstance(var, VarType):
                    initial_mime: str | None = var.value  # pyright: ignore[reportUnknownMemberType,reportUnknownVariableType]
                    highlighter_class = get_highlighter_for_mime(initial_mime)  # pyright: ignore[reportUnknownArgumentType]
                    _set_highlighter_on_editor(editor, highlighter_class)

                    # Callback captures var reference, reads .value
                    def make_mime_callback_var(
                        ed: QPlainTextEdit | QTextEdit,
                        v: Any,
                    ) -> Any:
                        def update_from_mime(*args: Any) -> None:
                            mime_type: str | None = v.value  # pyright: ignore[reportUnknownMemberType,reportUnknownVariableType]
                            hl_class = get_highlighter_for_mime(mime_type)  # pyright: ignore[reportUnknownArgumentType]
                            _set_highlighter_on_editor(ed, hl_class)

                        return update_from_mime

                    var.on_change(make_mime_callback_var(editor, var))
                elif isinstance(var, Observable):
                    initial_mime_obs: str | None = var.get()  # pyright: ignore[reportUnknownMemberType,reportUnknownVariableType]
                    highlighter_class = get_highlighter_for_mime(initial_mime_obs)  # pyright: ignore[reportUnknownArgumentType]
                    _set_highlighter_on_editor(editor, highlighter_class)

                    def make_mime_callback_obs(
                        ed: QPlainTextEdit | QTextEdit,
                        obs: Any,
                    ) -> Any:
                        def update_from_mime(*args: Any) -> None:
                            mime_type: str | None = obs.get()  # pyright: ignore[reportUnknownMemberType,reportUnknownVariableType]
                            hl_class = get_highlighter_for_mime(mime_type)  # pyright: ignore[reportUnknownArgumentType]
                            _set_highlighter_on_editor(ed, hl_class)

                        return update_from_mime

                    var.on_change(make_mime_callback_obs(editor, var))  # pyright: ignore[reportUnknownMemberType]
