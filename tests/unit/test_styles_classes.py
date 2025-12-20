"""Tests for CSS class helpers."""

from assertpy import assert_that
from qtpy.QtWidgets import QWidget

from qtpie.styles import (
    add_class,
    add_classes,
    get_classes,
    has_any_class,
    has_class,
    remove_class,
    replace_class,
    set_classes,
    toggle_class,
)
from qtpie_test import QtDriver


class TestGetSetClasses:
    """Tests for get_classes and set_classes."""

    def test_get_classes_returns_empty_list_when_no_classes(self, qt: QtDriver) -> None:
        widget = QWidget()
        qt.track(widget)

        assert_that(get_classes(widget)).is_equal_to([])

    def test_set_and_get_classes(self, qt: QtDriver) -> None:
        widget = QWidget()
        qt.track(widget)

        set_classes(widget, ["foo", "bar"])

        assert_that(get_classes(widget)).is_equal_to(["foo", "bar"])

    def test_set_classes_with_refresh_false(self, qt: QtDriver) -> None:
        widget = QWidget()
        qt.track(widget)

        set_classes(widget, ["foo"], refresh=False)

        assert_that(get_classes(widget)).is_equal_to(["foo"])


class TestAddClass:
    """Tests for add_class and add_classes."""

    def test_add_class_to_empty_widget(self, qt: QtDriver) -> None:
        widget = QWidget()
        qt.track(widget)

        add_class(widget, "foo")

        assert_that(get_classes(widget)).contains("foo")

    def test_add_class_does_not_duplicate(self, qt: QtDriver) -> None:
        widget = QWidget()
        qt.track(widget)

        add_class(widget, "foo")
        add_class(widget, "foo")

        assert_that(get_classes(widget)).is_length(1)

    def test_add_classes_multiple(self, qt: QtDriver) -> None:
        widget = QWidget()
        qt.track(widget)

        add_classes(widget, ["foo", "bar"])

        assert_that(get_classes(widget)).contains("foo", "bar")

    def test_add_classes_does_not_duplicate(self, qt: QtDriver) -> None:
        widget = QWidget()
        qt.track(widget)

        add_classes(widget, ["foo", "bar"])
        add_classes(widget, ["bar", "baz"])

        assert_that(get_classes(widget)).is_equal_to(["foo", "bar", "baz"])


class TestHasClass:
    """Tests for has_class and has_any_class."""

    def test_has_class_returns_true_when_present(self, qt: QtDriver) -> None:
        widget = QWidget()
        qt.track(widget)
        set_classes(widget, ["foo"])

        assert_that(has_class(widget, "foo")).is_true()

    def test_has_class_returns_false_when_not_present(self, qt: QtDriver) -> None:
        widget = QWidget()
        qt.track(widget)
        set_classes(widget, ["foo"])

        assert_that(has_class(widget, "bar")).is_false()

    def test_has_any_class_returns_true_when_one_matches(self, qt: QtDriver) -> None:
        widget = QWidget()
        qt.track(widget)
        set_classes(widget, ["foo"])

        assert_that(has_any_class(widget, ["bar", "foo"])).is_true()

    def test_has_any_class_returns_false_when_none_match(self, qt: QtDriver) -> None:
        widget = QWidget()
        qt.track(widget)
        set_classes(widget, ["foo"])

        assert_that(has_any_class(widget, ["bar", "baz"])).is_false()


class TestRemoveClass:
    """Tests for remove_class."""

    def test_remove_class_removes_existing_class(self, qt: QtDriver) -> None:
        widget = QWidget()
        qt.track(widget)
        set_classes(widget, ["foo", "bar"])

        remove_class(widget, "foo")

        assert_that(get_classes(widget)).is_equal_to(["bar"])

    def test_remove_class_noop_when_not_present(self, qt: QtDriver) -> None:
        widget = QWidget()
        qt.track(widget)
        set_classes(widget, ["foo", "bar"])

        remove_class(widget, "baz")

        assert_that(get_classes(widget)).is_equal_to(["foo", "bar"])


class TestReplaceClass:
    """Tests for replace_class."""

    def test_replace_class_swaps_in_place(self, qt: QtDriver) -> None:
        widget = QWidget()
        qt.track(widget)
        set_classes(widget, ["foo", "bar"])

        replace_class(widget, "foo", "baz")

        assert_that(get_classes(widget)).is_equal_to(["baz", "bar"])

    def test_replace_class_noop_when_old_not_present(self, qt: QtDriver) -> None:
        widget = QWidget()
        qt.track(widget)
        set_classes(widget, ["foo", "bar"])

        replace_class(widget, "qux", "baz")

        assert_that(get_classes(widget)).is_equal_to(["foo", "bar"])


class TestToggleClass:
    """Tests for toggle_class."""

    def test_toggle_class_adds_when_not_present(self, qt: QtDriver) -> None:
        widget = QWidget()
        qt.track(widget)

        toggle_class(widget, "foo")

        assert_that(get_classes(widget)).contains("foo")

    def test_toggle_class_removes_when_present(self, qt: QtDriver) -> None:
        widget = QWidget()
        qt.track(widget)
        set_classes(widget, ["foo"])

        toggle_class(widget, "foo")

        assert_that(get_classes(widget)).does_not_contain("foo")

    def test_toggle_class_twice_restores_original(self, qt: QtDriver) -> None:
        widget = QWidget()
        qt.track(widget)

        toggle_class(widget, "foo")
        toggle_class(widget, "foo")

        assert_that(get_classes(widget)).does_not_contain("foo")
