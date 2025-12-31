"""Tests for the tr[] declarative translation syntax."""

from typing import override

from assertpy import assert_that
from qtpy.QtWidgets import QLabel, QLineEdit, QPushButton, QWidget

from qtpie import Widget, make, tr, widget
from qtpie.testing import QtDriver
from qtpie.translations.translatable import (
    Translatable,
    get_translation_context,
    set_translation_context,
)


class TestTranslatableMarker:
    """Tests for the Translatable marker class."""

    def test_tr_getitem_returns_translatable(self) -> None:
        """tr["text"] returns a Translatable marker."""
        result = tr["Hello"]
        assert_that(result).is_instance_of(Translatable)
        assert_that(result.text).is_equal_to("Hello")
        assert_that(result.disambiguation).is_none()

    def test_tr_getitem_with_disambiguation(self) -> None:
        """tr["text", "disambiguation"] returns Translatable with both."""
        result = tr["Open", "menu"]
        assert_that(result).is_instance_of(Translatable)
        assert_that(result.text).is_equal_to("Open")
        assert_that(result.disambiguation).is_equal_to("menu")

    def test_translatable_resolve_without_context(self) -> None:
        """Translatable.resolve() returns original text if no context."""
        set_translation_context("")
        t = Translatable("Hello")
        assert_that(t.resolve()).is_equal_to("Hello")

    def test_translatable_resolve_with_context(self) -> None:
        """Translatable.resolve() uses context for translation lookup."""
        set_translation_context("MyWidget")
        t = Translatable("Hello")
        # Without loaded translator, returns original
        assert_that(t.resolve()).is_equal_to("Hello")

    def test_translatable_resolve_with_explicit_context(self) -> None:
        """Translatable.resolve(context) uses explicit context."""
        t = Translatable("Hello")
        # Without loaded translator, returns original
        assert_that(t.resolve("ExplicitContext")).is_equal_to("Hello")

    def test_translatable_is_frozen(self) -> None:
        """Translatable is immutable (frozen dataclass)."""
        import pytest

        t = Translatable("Hello")
        with pytest.raises(AttributeError):
            t.text = "Changed"  # type: ignore[misc]


class TestTrWithMake:
    """Tests for tr[] used with make()."""

    def test_tr_in_first_positional_arg(self, qt: QtDriver) -> None:
        """tr[] works as first positional argument to make()."""

        @widget()
        class TestWidget(QWidget, Widget):
            label: QLabel = make(QLabel, tr["Hello"])

        w = TestWidget()
        qt.track(w)

        # Without translator, should show original text
        assert_that(w.label.text()).is_equal_to("Hello")

    def test_tr_in_keyword_arg(self, qt: QtDriver) -> None:
        """tr[] works in keyword arguments to make()."""

        @widget()
        class TestWidget(QWidget, Widget):
            edit: QLineEdit = make(QLineEdit, placeholderText=tr["Enter name"])

        w = TestWidget()
        qt.track(w)

        assert_that(w.edit.placeholderText()).is_equal_to("Enter name")

    def test_tr_multiple_args(self, qt: QtDriver) -> None:
        """tr[] works with multiple translatable arguments."""

        @widget()
        class TestWidget(QWidget, Widget):
            button: QPushButton = make(
                QPushButton,
                tr["Save"],
                toolTip=tr["Save changes"],
            )

        w = TestWidget()
        qt.track(w)

        assert_that(w.button.text()).is_equal_to("Save")
        assert_that(w.button.toolTip()).is_equal_to("Save changes")

    def test_tr_with_disambiguation(self, qt: QtDriver) -> None:
        """tr["text", "disambiguation"] works in make()."""

        @widget()
        class TestWidget(QWidget, Widget):
            open_menu: QPushButton = make(QPushButton, tr["Open", "menu"])
            open_status: QLabel = make(QLabel, tr["Open", "status"])

        w = TestWidget()
        qt.track(w)

        # Both show "Open" (no translator loaded)
        assert_that(w.open_menu.text()).is_equal_to("Open")
        assert_that(w.open_status.text()).is_equal_to("Open")

    def test_mixed_tr_and_regular_strings(self, qt: QtDriver) -> None:
        """Can mix tr[] and regular strings in same widget."""

        @widget()
        class TestWidget(QWidget, Widget):
            translated: QLabel = make(QLabel, tr["Hello"])
            not_translated: QLabel = make(QLabel, "Static text")

        w = TestWidget()
        qt.track(w)

        assert_that(w.translated.text()).is_equal_to("Hello")
        assert_that(w.not_translated.text()).is_equal_to("Static text")


class TestTrContext:
    """Tests for translation context being set correctly."""

    def test_context_set_during_widget_init(self, qt: QtDriver) -> None:
        """Translation context is set to class name during widget init."""
        captured_context: str = ""

        @widget()
        class CaptureContextWidget(QWidget, Widget):
            label: QLabel = make(QLabel, "test")

            @override
            def setup(self) -> None:
                nonlocal captured_context
                captured_context = get_translation_context()

        w = CaptureContextWidget()
        qt.track(w)

        assert_that(captured_context).is_equal_to("CaptureContextWidget")

    def test_context_available_in_make_factory(self, qt: QtDriver) -> None:
        """Context is available when make() factory runs."""

        @widget()
        class MyTestWidget(QWidget, Widget):
            # The tr[] marker gets resolved with "MyTestWidget" as context
            label: QLabel = make(QLabel, tr["Hello"])

        w = MyTestWidget()
        qt.track(w)

        # Can't directly test the context was used, but widget should work
        assert_that(w.label.text()).is_equal_to("Hello")


class TestTrEdgeCases:
    """Edge cases and error handling."""

    def test_tr_with_empty_string(self, qt: QtDriver) -> None:
        """tr[""] with empty string works."""

        @widget()
        class TestWidget(QWidget, Widget):
            label: QLabel = make(QLabel, tr[""])

        w = TestWidget()
        qt.track(w)

        assert_that(w.label.text()).is_equal_to("")

    def test_tr_with_special_characters(self, qt: QtDriver) -> None:
        """tr[] with special characters works."""

        @widget()
        class TestWidget(QWidget, Widget):
            label: QLabel = make(QLabel, tr["Hello & Goodbye <world>"])

        w = TestWidget()
        qt.track(w)

        assert_that(w.label.text()).is_equal_to("Hello & Goodbye <world>")

    def test_tr_with_unicode(self, qt: QtDriver) -> None:
        """tr[] with unicode characters works."""

        @widget()
        class TestWidget(QWidget, Widget):
            label: QLabel = make(QLabel, tr["你好世界"])

        w = TestWidget()
        qt.track(w)

        assert_that(w.label.text()).is_equal_to("你好世界")

    def test_tr_with_newlines(self, qt: QtDriver) -> None:
        """tr[] with newlines works."""

        @widget()
        class TestWidget(QWidget, Widget):
            label: QLabel = make(QLabel, tr["Line 1\nLine 2"])

        w = TestWidget()
        qt.track(w)

        assert_that(w.label.text()).is_equal_to("Line 1\nLine 2")

    def test_tr_with_format_placeholders(self, qt: QtDriver) -> None:
        """tr[] with Qt format placeholders works."""

        @widget()
        class TestWidget(QWidget, Widget):
            label: QLabel = make(QLabel, tr["Hello, %1!"])

        w = TestWidget()
        qt.track(w)

        # The placeholder stays as-is, can be filled with .arg() later
        assert_that(w.label.text()).is_equal_to("Hello, %1!")
