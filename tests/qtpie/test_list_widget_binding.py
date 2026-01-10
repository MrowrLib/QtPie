# pyright: reportMissingTypeArgument=false
# pyright: reportPrivateUsage=false, reportAttributeAccessIssue=false, reportOptionalMemberAccess=false, reportUnknownMemberType=false, reportUnknownVariableType=false
"""Tests for list[QWidget] = new(bind="...") binding."""

import pytest
from assertpy import assert_that
from qtpy.QtWidgets import QLabel, QLineEdit

from qtpie import Variable, Widget, new, widget
from qtpie.testing import QtDriver
from qtpie.widget_repeater import WidgetRepeater


class TestListWidgetBasic:
    """Test basic list[QWidget] binding functionality."""

    def test_list_widget_creates_repeater(self, qt: QtDriver) -> None:
        """list[QWidget] = new(bind=...) creates a WidgetRepeater."""

        @widget
        class MyWidget(Widget):
            items: Variable[list[str]] = new(["a", "b", "c"])
            labels: list[QLabel] = new(bind="items")

        w = qt.track(MyWidget())

        # The field should be a WidgetRepeater
        assert_that(w.labels).is_instance_of(WidgetRepeater)

    def test_list_widget_initial_values(self, qt: QtDriver) -> None:
        """List widget renders initial values."""

        @widget
        class MyWidget(Widget):
            items: Variable[list[str]] = new(["Hello", "World"])
            labels: list[QLabel] = new(bind="items")

        w = qt.track(MyWidget())

        # Should have 2 labels with the correct text
        assert_that(w.labels.layout().count()).is_equal_to(2)
        assert_that(w.labels.layout().itemAt(0).widget().text()).is_equal_to("Hello")
        assert_that(w.labels.layout().itemAt(1).widget().text()).is_equal_to("World")

    def test_list_widget_reactive_add(self, qt: QtDriver) -> None:
        """Adding items to the source list creates new widgets."""

        @widget
        class MyWidget(Widget):
            items: Variable[list[str]] = new(["a"])
            labels: list[QLabel] = new(bind="items")

        w = qt.track(MyWidget())
        assert_that(w.labels.layout().count()).is_equal_to(1)

        # Add an item
        w.items.append("b")
        assert_that(w.labels.layout().count()).is_equal_to(2)
        assert_that(w.labels.layout().itemAt(1).widget().text()).is_equal_to("b")

    def test_list_widget_reactive_remove(self, qt: QtDriver) -> None:
        """Removing items from the source list removes widgets."""

        @widget
        class MyWidget(Widget):
            items: Variable[list[str]] = new(["a", "b", "c"])
            labels: list[QLabel] = new(bind="items")

        w = qt.track(MyWidget())
        assert_that(w.labels.layout().count()).is_equal_to(3)

        # Remove an item
        w.items.remove("b")
        assert_that(w.labels.layout().count()).is_equal_to(2)
        assert_that(w.labels.layout().itemAt(0).widget().text()).is_equal_to("a")
        assert_that(w.labels.layout().itemAt(1).widget().text()).is_equal_to("c")

    def test_list_widget_in_layout(self, qt: QtDriver) -> None:
        """list[QWidget] is added to the parent layout."""

        @widget
        class MyWidget(Widget):
            header: QLabel = new("Header")
            items: Variable[list[str]] = new(["a", "b"])
            labels: list[QLabel] = new(bind="items")
            footer: QLabel = new("Footer")

        w = qt.track(MyWidget())
        layout = w.layout()

        # Should have header, repeater, footer
        assert_that(layout.count()).is_equal_to(3)
        assert_that(layout.itemAt(0).widget()).is_equal_to(w.header)
        assert_that(layout.itemAt(1).widget()).is_equal_to(w.labels)
        assert_that(layout.itemAt(2).widget()).is_equal_to(w.footer)

    def test_list_widget_exclude_from_layout(self, qt: QtDriver) -> None:
        """list[QWidget] with layout=False is excluded from layout."""

        @widget
        class MyWidget(Widget):
            header: QLabel = new("Header")
            items: Variable[list[str]] = new(["a", "b"])
            labels: list[QLabel] = new(bind="items", layout=False)
            footer: QLabel = new("Footer")

        w = qt.track(MyWidget())
        layout = w.layout()

        # Should only have header and footer
        assert_that(layout.count()).is_equal_to(2)
        assert_that(layout.itemAt(0).widget()).is_equal_to(w.header)
        assert_that(layout.itemAt(1).widget()).is_equal_to(w.footer)

        # But the repeater still exists
        assert_that(w.labels).is_instance_of(WidgetRepeater)


class TestListWidgetWithValidation:
    """Test list[QWidget] binding to validation_error_messages."""

    def test_bind_to_validation_error_messages(self, qt: QtDriver) -> None:
        """list[QLabel] can bind to Variable.validation_error_messages."""

        @widget
        class MyWidget(Widget):
            text: Variable[str] = new("")
            text_input: QLineEdit = new(bind="text")
            errors: list[QLabel] = new(bind="text.validation_error_messages")

            def __setup__(self) -> None:
                self.text.add_validator("required", lambda v: "Required" if not v else None)

        w = qt.track(MyWidget())

        # Initially empty string is invalid
        assert_that(w.errors.layout().count()).is_equal_to(1)
        assert_that(w.errors.layout().itemAt(0).widget().text()).is_equal_to("Required")

        # Enter text - should become valid
        w.text_input.setText("hello")
        assert_that(w.errors.layout().count()).is_equal_to(0)

        # Clear text - should become invalid again
        w.text_input.setText("")
        assert_that(w.errors.layout().count()).is_equal_to(1)

    def test_bind_to_validation_error_messages_multiple(self, qt: QtDriver) -> None:
        """Multiple validation errors show multiple labels."""

        @widget
        class MyWidget(Widget):
            text: Variable[str] = new("")
            errors: list[QLabel] = new(bind="text.validation_error_messages")

            def __setup__(self) -> None:
                self.text.add_validator("required", lambda v: "Required" if not v else None)
                self.text.add_validator("too_short", lambda v: "Too short" if len(v) < 3 else None)

        w = qt.track(MyWidget())

        # Both validators fail
        assert_that(w.errors.layout().count()).is_equal_to(2)

        # Enter 2 chars - still too short
        w.text.value = "ab"
        assert_that(w.errors.layout().count()).is_equal_to(1)
        assert_that(w.errors.layout().itemAt(0).widget().text()).is_equal_to("Too short")

        # Enter 3 chars - valid
        w.text.value = "abc"
        assert_that(w.errors.layout().count()).is_equal_to(0)


class TestListWidgetWithWidgetKwargs:
    """Test list[QWidget] with widget constructor kwargs."""

    def test_widget_kwargs_passed(self, qt: QtDriver) -> None:
        """kwargs passed to new() are forwarded to widget constructor."""

        @widget
        class MyWidget(Widget):
            items: Variable[list[str]] = new(["test"])
            labels: list[QLabel] = new(bind="items", styleSheet="color: red;")

        w = qt.track(MyWidget())

        label = w.labels.layout().itemAt(0).widget()
        assert_that(label.styleSheet()).is_equal_to("color: red;")

    def test_stylesheet_alias(self, qt: QtDriver) -> None:
        """stylesheet= alias works for list[QWidget]."""

        @widget
        class MyWidget(Widget):
            items: Variable[list[str]] = new(["test"])
            labels: list[QLabel] = new(bind="items", stylesheet="color: blue;")

        w = qt.track(MyWidget())

        label = w.labels.layout().itemAt(0).widget()
        assert_that(label.styleSheet()).is_equal_to("color: blue;")


class TestListWidgetListInterface:
    """Test list-like interface on WidgetRepeater."""

    def test_getitem_positive_index(self, qt: QtDriver) -> None:
        """Can access widgets by positive index."""

        @widget
        class MyWidget(Widget):
            items: Variable[list[str]] = new(["a", "b", "c"])
            labels: list[QLabel] = new(bind="items")

        w = qt.track(MyWidget())

        assert_that(w.labels[0].text()).is_equal_to("a")
        assert_that(w.labels[1].text()).is_equal_to("b")
        assert_that(w.labels[2].text()).is_equal_to("c")

    def test_getitem_negative_index(self, qt: QtDriver) -> None:
        """Can access widgets by negative index."""

        @widget
        class MyWidget(Widget):
            items: Variable[list[str]] = new(["a", "b", "c"])
            labels: list[QLabel] = new(bind="items")

        w = qt.track(MyWidget())

        assert_that(w.labels[-1].text()).is_equal_to("c")
        assert_that(w.labels[-2].text()).is_equal_to("b")
        assert_that(w.labels[-3].text()).is_equal_to("a")

    def test_getitem_out_of_range_raises(self, qt: QtDriver) -> None:
        """Accessing out of range index raises IndexError."""

        @widget
        class MyWidget(Widget):
            items: Variable[list[str]] = new(["a"])
            labels: list[QLabel] = new(bind="items")

        w = qt.track(MyWidget())

        try:
            _ = w.labels[5]
            pytest.fail("Expected IndexError")
        except IndexError:
            pass

    def test_len(self, qt: QtDriver) -> None:
        """len() returns number of widgets."""

        @widget
        class MyWidget(Widget):
            items: Variable[list[str]] = new(["a", "b", "c"])
            labels: list[QLabel] = new(bind="items")

        w = qt.track(MyWidget())

        assert_that(len(w.labels)).is_equal_to(3)

        w.items.append("d")
        assert_that(len(w.labels)).is_equal_to(4)

    def test_iter(self, qt: QtDriver) -> None:
        """Can iterate over widgets."""

        @widget
        class MyWidget(Widget):
            items: Variable[list[str]] = new(["a", "b", "c"])
            labels: list[QLabel] = new(bind="items")

        w = qt.track(MyWidget())

        texts = [label.text() for label in w.labels]
        assert_that(texts).is_equal_to(["a", "b", "c"])

    def test_modify_widget_in_setup(self, qt: QtDriver) -> None:
        """Can modify widgets in __setup__."""

        @widget
        class MyWidget(Widget):
            items: Variable[list[str]] = new(["first", "second"])
            labels: list[QLabel] = new(bind="items")

            def __setup__(self) -> None:
                self.labels[0].setStyleSheet("color: red;")
                self.labels[1].setStyleSheet("color: blue;")

        w = qt.track(MyWidget())

        assert_that(w.labels[0].styleSheet()).is_equal_to("color: red;")
        assert_that(w.labels[1].styleSheet()).is_equal_to("color: blue;")


class TestListWidgetAggregatedValidation:
    """Test list[QWidget] binding to widget-level validation_error_messages."""

    def test_bind_to_widget_validation_error_messages(self, qt: QtDriver) -> None:
        """list[QLabel] can bind to widget's aggregated validation_error_messages."""

        @widget
        class MyWidget(Widget):
            text1: Variable[str] = new("")
            text2: Variable[str] = new("")
            errors: list[QLabel] = new(bind="validation_error_messages")

            def __setup__(self) -> None:
                self.text1.add_validator("req1", lambda v: "Text1 required" if not v else None)
                self.text2.add_validator("req2", lambda v: "Text2 required" if not v else None)

        w = qt.track(MyWidget())

        # Both invalid initially
        assert_that(w.errors.layout().count()).is_equal_to(2)

        # Fix one
        w.text1.value = "hello"
        assert_that(w.errors.layout().count()).is_equal_to(1)
        assert_that(w.errors.layout().itemAt(0).widget().text()).is_equal_to("Text2 required")

        # Fix both
        w.text2.value = "world"
        assert_that(w.errors.layout().count()).is_equal_to(0)

    def test_bind_via_validation_error_messages(self, qt: QtDriver) -> None:
        """list[QLabel] can bind via validation_error_messages path."""

        @widget
        class MyWidget(Widget):
            text: Variable[str] = new("")
            errors: list[QLabel] = new(bind="validation_error_messages")

            def __setup__(self) -> None:
                self.text.add_validator("required", lambda v: "Required" if not v else None)

        w = qt.track(MyWidget())

        assert_that(w.errors.layout().count()).is_equal_to(1)
        w.text.value = "ok"
        assert_that(w.errors.layout().count()).is_equal_to(0)


class TestListWidgetErrors:
    """Test error handling for list[QWidget] binding."""

    def test_missing_bind_raises_error(self, qt: QtDriver) -> None:
        """list[QWidget] without bind= raises an error."""
        try:

            @widget
            class MyWidget(Widget):
                labels: list[QLabel] = new()

            qt.track(MyWidget())
            pytest.fail("Expected ValueError")
        except ValueError as e:
            assert_that(str(e)).contains("requires bind=")

    def test_invalid_bind_path_raises_error(self, qt: QtDriver) -> None:
        """list[QWidget] with invalid bind path raises an error."""
        try:

            @widget
            class MyWidget(Widget):
                labels: list[QLabel] = new(bind="nonexistent")

            qt.track(MyWidget())
            pytest.fail("Expected ValueError")
        except ValueError as e:
            assert_that(str(e)).contains("Could not resolve")

    def test_bind_to_non_list_raises_error(self, qt: QtDriver) -> None:
        """list[QWidget] bound to non-list raises an error."""
        try:

            @widget
            class MyWidget(Widget):
                name: Variable[str] = new("hello")
                labels: list[QLabel] = new(bind="name")

            qt.track(MyWidget())
            pytest.fail("Expected TypeError")
        except TypeError as e:
            assert_that(str(e)).contains("expected list")
