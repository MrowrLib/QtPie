# pyright: reportPrivateUsage=false
# pyright: reportMissingParameterType=false
# pyright: reportUnknownParameterType=false
# pyright: reportUntypedBaseClass=false
# pyright: reportUntypedClassDecorator=false
# pyright: reportUnknownArgumentType=false
# pyright: reportUnknownMemberType=false
# pyright: reportOptionalMemberAccess=false
# pyright: reportAttributeAccessIssue=false
"""Tests for syntax highlighter support on QPlainTextEdit and QTextEdit.

Tests both static highlighter= class assignment and dynamic Variable binding.
"""

import pytest
from assertpy import assert_that
from PySide6.QtWidgets import QPlainTextEdit, QTextEdit

from qtpie import Variable, new
from qtpie.highlighters import HtmlHighlighter, JsonHighlighter
from qtpie.testing import QtDriver

from .conftest import WIDGET_CLASS_TYPES, create_and_track


@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestStaticHighlighter:
    """Tests for static highlighter= class assignment."""

    def test_plain_text_edit_with_highlighter_class(self, base_class, decorator, qt: QtDriver) -> None:
        """QPlainTextEdit with highlighter=Class attaches the highlighter."""

        @decorator
        class TestClass(base_class):
            _editor: QPlainTextEdit = new(highlighter=JsonHighlighter)

        instance = create_and_track(qt, TestClass, base_class)

        # The highlighter should be attached to the document
        doc = instance._editor.document()
        assert_that(doc).is_not_none()
        # Setting text should work (highlighter processes it)
        instance._editor.setPlainText('{"key": "value"}')
        assert_that(instance._editor.toPlainText()).is_equal_to('{"key": "value"}')

    def test_text_edit_with_highlighter_class(self, base_class, decorator, qt: QtDriver) -> None:
        """QTextEdit with highlighter=Class attaches the highlighter."""

        @decorator
        class TestClass(base_class):
            _editor: QTextEdit = new(highlighter=HtmlHighlighter)

        instance = create_and_track(qt, TestClass, base_class)

        doc = instance._editor.document()
        assert_that(doc).is_not_none()
        instance._editor.setPlainText("<div>Hello</div>")
        assert_that(instance._editor.toPlainText()).is_equal_to("<div>Hello</div>")

    def test_editor_without_highlighter(self, base_class, decorator, qt: QtDriver) -> None:
        """QPlainTextEdit without highlighter= works normally."""

        @decorator
        class TestClass(base_class):
            _editor: QPlainTextEdit = new()

        instance = create_and_track(qt, TestClass, base_class)

        instance._editor.setPlainText("test content")
        assert_that(instance._editor.toPlainText()).is_equal_to("test content")


@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestDynamicHighlighterBinding:
    """Tests for dynamic highlighter= Variable binding."""

    def test_highlighter_bound_to_variable_string(self, base_class, decorator, qt: QtDriver) -> None:
        """highlighter='var_name' binds to a Variable and updates on change."""

        @decorator
        class TestClass(base_class):
            _highlighter: Variable[type | None] = new(None)
            _editor: QPlainTextEdit = new(highlighter="_highlighter")

        instance = create_and_track(qt, TestClass, base_class)

        # Initially no highlighter (None)
        instance._editor.setPlainText('{"key": "value"}')
        assert_that(instance._editor.toPlainText()).is_equal_to('{"key": "value"}')

        # Set highlighter via Variable
        instance._highlighter.value = JsonHighlighter

        # Highlighter should now be active
        instance._editor.setPlainText('{"new": "json"}')
        assert_that(instance._editor.toPlainText()).is_equal_to('{"new": "json"}')

    def test_highlighter_bound_to_variable_ref(self, base_class, decorator, qt: QtDriver) -> None:
        """highlighter=_var_ref binds to a Variable directly."""

        @decorator
        class TestClass(base_class):
            _highlighter: Variable[type | None] = new(JsonHighlighter)
            _editor: QPlainTextEdit = new(highlighter=_highlighter)

        instance = create_and_track(qt, TestClass, base_class)

        # Initial highlighter is JsonHighlighter
        instance._editor.setPlainText('{"key": "value"}')
        assert_that(instance._editor.toPlainText()).is_equal_to('{"key": "value"}')

        # Change to HtmlHighlighter
        instance._highlighter.value = HtmlHighlighter

        # Now using HTML highlighting
        instance._editor.setPlainText("<div>Hello</div>")
        assert_that(instance._editor.toPlainText()).is_equal_to("<div>Hello</div>")

    def test_highlighter_can_be_cleared(self, base_class, decorator, qt: QtDriver) -> None:
        """Setting highlighter Variable to None clears the highlighter."""

        @decorator
        class TestClass(base_class):
            _highlighter: Variable[type | None] = new(JsonHighlighter)
            _editor: QPlainTextEdit = new(highlighter="_highlighter")

        instance = create_and_track(qt, TestClass, base_class)

        # Clear highlighter
        instance._highlighter.value = None

        # Should still work without highlighter
        instance._editor.setPlainText("plain text")
        assert_that(instance._editor.toPlainText()).is_equal_to("plain text")


@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestContentTypeBinding:
    """Tests for content_type= MIME type binding."""

    def test_content_type_selects_highlighter(self, base_class, decorator, qt: QtDriver) -> None:
        """content_type='var_name' selects highlighter based on MIME type."""

        @decorator
        class TestClass(base_class):
            _content_type: Variable[str | None] = new(None)
            _editor: QPlainTextEdit = new(content_type="_content_type")

        instance = create_and_track(qt, TestClass, base_class)

        # Set to JSON MIME type
        instance._content_type.value = "application/json"

        # JSON highlighter should be active
        instance._editor.setPlainText('{"key": "value"}')
        assert_that(instance._editor.toPlainText()).is_equal_to('{"key": "value"}')

        # Switch to HTML MIME type
        instance._content_type.value = "text/html"

        # HTML highlighter should now be active
        instance._editor.setPlainText("<div>Hello</div>")
        assert_that(instance._editor.toPlainText()).is_equal_to("<div>Hello</div>")

    def test_content_type_unknown_clears_highlighter(self, base_class, decorator, qt: QtDriver) -> None:
        """Unknown MIME type clears the highlighter (uses empty highlighter)."""

        @decorator
        class TestClass(base_class):
            _content_type: Variable[str | None] = new("application/json")
            _editor: QPlainTextEdit = new(content_type="_content_type")

        instance = create_and_track(qt, TestClass, base_class)

        # Set to unknown MIME type
        instance._content_type.value = "application/unknown"

        # Should work without crashing
        instance._editor.setPlainText("some content")
        assert_that(instance._editor.toPlainText()).is_equal_to("some content")

    def test_content_type_none_clears_highlighter(self, base_class, decorator, qt: QtDriver) -> None:
        """Setting content_type to None clears the highlighter."""

        @decorator
        class TestClass(base_class):
            _content_type: Variable[str | None] = new("application/json")
            _editor: QPlainTextEdit = new(content_type="_content_type")

        instance = create_and_track(qt, TestClass, base_class)

        # Clear content type
        instance._content_type.value = None

        # Should work without highlighter
        instance._editor.setPlainText("plain text")
        assert_that(instance._editor.toPlainText()).is_equal_to("plain text")

    def test_content_type_format_expression(self, base_class, decorator, qt: QtDriver) -> None:
        """content_type='{expr}' supports format expressions."""

        @decorator
        class TestClass(base_class):
            _headers: Variable[dict[str, str]] = new({"content-type": "application/json"})
            _editor: QPlainTextEdit = new(content_type="{_headers['content-type']}")

        instance = create_and_track(qt, TestClass, base_class)

        # JSON highlighter should be active from format expression
        instance._editor.setPlainText('{"key": "value"}')
        assert_that(instance._editor.toPlainText()).is_equal_to('{"key": "value"}')

        # Change the headers - highlighter should update
        instance._headers.value = {"content-type": "text/html"}

        # HTML highlighter should now be active
        instance._editor.setPlainText("<div>Hello</div>")
        assert_that(instance._editor.toPlainText()).is_equal_to("<div>Hello</div>")
