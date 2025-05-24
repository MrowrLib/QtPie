from assertpy import assert_that
from pytestqt.qtbot import QtBot
from qtpy.QtWidgets import QWidget

from qtpie.styles.classes import (
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


class ExampleWidget(QWidget):
    pass


class TestStyleClasses:
    def test_set_and_get_classes(self, qtbot: QtBot) -> None:
        widget = ExampleWidget()
        qtbot.addWidget(widget)

        set_classes(widget, ["foo", "bar"])
        assert_that(get_classes(widget)).is_equal_to(["foo", "bar"])

    def test_add_class(self, qtbot: QtBot) -> None:
        widget = ExampleWidget()
        qtbot.addWidget(widget)

        add_class(widget, "foo")
        assert_that(get_classes(widget)).contains("foo")

        add_class(widget, "foo")  # should not duplicate
        assert_that(get_classes(widget)).is_length(1)

    def test_add_classes(self, qtbot: QtBot) -> None:
        widget = ExampleWidget()
        qtbot.addWidget(widget)

        add_classes(widget, ["foo", "bar"])
        assert_that(get_classes(widget)).contains("foo", "bar")

        add_classes(widget, ["bar", "baz"])
        assert_that(get_classes(widget)).contains("foo", "bar", "baz")

    def test_has_class(self, qtbot: QtBot) -> None:
        widget = ExampleWidget()
        qtbot.addWidget(widget)

        set_classes(widget, ["foo"])
        assert_that(has_class(widget, "foo")).is_true()
        assert_that(has_class(widget, "bar")).is_false()

    def test_has_any_class(self, qtbot: QtBot) -> None:
        widget = ExampleWidget()
        qtbot.addWidget(widget)

        set_classes(widget, ["foo"])
        assert_that(has_any_class(widget, ["bar", "foo"])).is_true()
        assert_that(has_any_class(widget, ["bar", "baz"])).is_false()

    def test_remove_class(self, qtbot: QtBot) -> None:
        widget = ExampleWidget()
        qtbot.addWidget(widget)

        set_classes(widget, ["foo", "bar"])
        remove_class(widget, "foo")
        assert_that(get_classes(widget)).is_equal_to(["bar"])

        remove_class(widget, "baz")  # should not raise
        assert_that(get_classes(widget)).is_equal_to(["bar"])

    def test_replace_class(self, qtbot: QtBot) -> None:
        widget = ExampleWidget()
        qtbot.addWidget(widget)

        set_classes(widget, ["foo", "bar"])
        replace_class(widget, "foo", "baz")
        assert_that(get_classes(widget)).is_equal_to(["baz", "bar"])

        replace_class(widget, "qux", "zap")  # no-op
        assert_that(get_classes(widget)).is_equal_to(["baz", "bar"])

    def test_toggle_class(self, qtbot: QtBot) -> None:
        widget = ExampleWidget()
        qtbot.addWidget(widget)

        toggle_class(widget, "foo")
        assert_that(get_classes(widget)).contains("foo")

        toggle_class(widget, "foo")
        assert_that(get_classes(widget)).does_not_contain("foo")
