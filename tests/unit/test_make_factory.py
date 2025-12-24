"""Tests for the make() factory function."""

from assertpy import assert_that
from qtpy.QtWidgets import QLabel, QLineEdit, QPushButton, QSlider, QVBoxLayout, QWidget

from qtpie import Widget, make, widget
from qtpie.factories.make import parse_selector
from qtpie.testing import QtDriver


class TestMakeFactory:
    """Phase 2: make() factory functionality."""

    def test_make_creates_widget_instance(self, qt: QtDriver) -> None:
        """make() should create a widget instance via default_factory."""

        @widget()
        class MyWidget(QWidget, Widget):
            label: QLabel = make(QLabel)

        w = MyWidget()
        qt.track(w)

        assert_that(w.label).is_instance_of(QLabel)

    def test_make_with_positional_args(self, qt: QtDriver) -> None:
        """make() should pass positional args to the constructor."""

        @widget()
        class MyWidget(QWidget, Widget):
            label: QLabel = make(QLabel, "Hello World")

        w = MyWidget()
        qt.track(w)

        assert_that(w.label.text()).is_equal_to("Hello World")

    def test_make_with_kwargs_as_properties(self, qt: QtDriver) -> None:
        """make() kwargs that aren't signals should be set as properties."""

        @widget()
        class MyWidget(QWidget, Widget):
            edit: QLineEdit = make(QLineEdit, placeholderText="Enter name")

        w = MyWidget()
        qt.track(w)

        assert_that(w.edit.placeholderText()).is_equal_to("Enter name")

    def test_make_signal_connection_by_method_name(self, qt: QtDriver) -> None:
        """make() should connect signals to methods by name string."""

        @widget()
        class MyWidget(QWidget, Widget):
            button: QPushButton = make(QPushButton, "Click", clicked="on_click")
            click_count: int = 0

            def on_click(self) -> None:
                self.click_count += 1

        w = MyWidget()
        qt.track(w)

        # Click the button
        qt.click(w.button)

        assert_that(w.click_count).is_equal_to(1)

    def test_make_signal_connection_with_lambda(self, qt: QtDriver) -> None:
        """make() should connect signals to callable (lambda)."""
        captured: list[bool] = []

        @widget()
        class MyWidget(QWidget, Widget):
            button: QPushButton = make(QPushButton, "Click", clicked=lambda: captured.append(True))

        w = MyWidget()
        qt.track(w)

        qt.click(w.button)

        assert_that(captured).is_length(1)

    def test_make_multiple_signal_connections(self, qt: QtDriver) -> None:
        """make() should support connecting multiple signals."""

        @widget()
        class MyWidget(QWidget, Widget):
            slider: QSlider = make(
                QSlider,
                valueChanged="on_value_changed",
                sliderReleased="on_released",
            )
            value_changes: int = 0
            releases: int = 0

            def on_value_changed(self, value: int) -> None:
                self.value_changes += 1

            def on_released(self) -> None:
                self.releases += 1

        w = MyWidget()
        qt.track(w)

        # Change the value programmatically (fires valueChanged)
        w.slider.setValue(50)

        assert_that(w.value_changes).is_equal_to(1)

    def test_make_combined_with_layout(self, qt: QtDriver) -> None:
        """make() widgets should be added to layout correctly."""

        @widget()
        class MyWidget(QWidget, Widget):
            label: QLabel = make(QLabel, "First")
            button: QPushButton = make(QPushButton, "Second")

        w = MyWidget()
        qt.track(w)

        layout = w.layout()
        assert layout is not None
        assert_that(layout).is_instance_of(QVBoxLayout)
        assert_that(layout.count()).is_equal_to(2)
        item0 = layout.itemAt(0)
        item1 = layout.itemAt(1)
        assert item0 is not None and item1 is not None
        assert_that(item0.widget()).is_same_as(w.label)
        assert_that(item1.widget()).is_same_as(w.button)

    def test_make_cleaner_than_field_default_factory(self, qt: QtDriver) -> None:
        """make() should be cleaner than field(default_factory=...)."""
        # This test just demonstrates the cleaner syntax
        # Compare: make(QLabel, "Hello") vs field(default_factory=lambda: QLabel("Hello"))

        @widget()
        class MyWidget(QWidget, Widget):
            label: QLabel = make(QLabel, "Clean syntax!")

        w = MyWidget()
        qt.track(w)

        assert_that(w.label.text()).is_equal_to("Clean syntax!")


class TestParseSelector:
    """Tests for the parse_selector function."""

    def test_parse_objectname_only(self) -> None:
        """#name should parse to objectName only."""
        result = parse_selector("#hello")
        assert_that(result.object_name).is_equal_to("hello")
        assert_that(result.classes).is_none()

    def test_parse_single_class_only(self) -> None:
        """.class should parse to class only."""
        result = parse_selector(".primary")
        assert_that(result.object_name).is_none()
        assert_that(result.classes).is_equal_to(["primary"])

    def test_parse_multiple_classes(self) -> None:
        """.class1.class2 should parse to multiple classes."""
        result = parse_selector(".primary.large")
        assert_that(result.object_name).is_none()
        assert_that(result.classes).is_equal_to(["primary", "large"])

    def test_parse_objectname_and_classes(self) -> None:
        """#name.class1.class2 should parse both."""
        result = parse_selector("#submit.primary.large")
        assert_that(result.object_name).is_equal_to("submit")
        assert_that(result.classes).is_equal_to(["primary", "large"])

    def test_parse_objectname_with_single_class(self) -> None:
        """#name.class should parse both."""
        result = parse_selector("#btn.primary")
        assert_that(result.object_name).is_equal_to("btn")
        assert_that(result.classes).is_equal_to(["primary"])

    def test_parse_empty_string(self) -> None:
        """Empty string should return empty SelectorInfo."""
        result = parse_selector("")
        assert_that(result.object_name).is_none()
        assert_that(result.classes).is_none()

    def test_parse_invalid_selector(self) -> None:
        """String not starting with # or . should return empty SelectorInfo."""
        result = parse_selector("invalid")
        assert_that(result.object_name).is_none()
        assert_that(result.classes).is_none()


class TestMakeWithSelector:
    """Tests for make() with CSS selector syntax."""

    def test_make_with_objectname_selector(self, qt: QtDriver) -> None:
        """make('#name', ...) should set objectName."""

        @widget()
        class MyWidget(QWidget, Widget):
            label: QLabel = make("#title", QLabel, "Hello")

        w = MyWidget()
        qt.track(w)

        assert_that(w.label.objectName()).is_equal_to("title")
        assert_that(w.label.text()).is_equal_to("Hello")

    def test_make_with_class_selector(self, qt: QtDriver) -> None:
        """make('.class', ...) should set classes."""

        @widget()
        class MyWidget(QWidget, Widget):
            button: QPushButton = make(".primary", QPushButton, "Click")

        w = MyWidget()
        qt.track(w)

        # objectName defaults to field name when not specified
        assert_that(w.button.objectName()).is_equal_to("button")
        # Check class property
        classes = w.button.property("class")
        assert_that(classes).is_equal_to(["primary"])

    def test_make_with_objectname_and_classes(self, qt: QtDriver) -> None:
        """make('#name.class1.class2', ...) should set both."""

        @widget()
        class MyWidget(QWidget, Widget):
            submit: QPushButton = make("#submit-btn.primary.large", QPushButton, "Submit")

        w = MyWidget()
        qt.track(w)

        assert_that(w.submit.objectName()).is_equal_to("submit-btn")
        classes = w.submit.property("class")
        assert_that(classes).is_equal_to(["primary", "large"])

    def test_make_without_selector_uses_field_name(self, qt: QtDriver) -> None:
        """make(Widget, ...) without selector should use field name as objectName."""

        @widget()
        class MyWidget(QWidget, Widget):
            my_label: QLabel = make(QLabel, "Test")

        w = MyWidget()
        qt.track(w)

        assert_that(w.my_label.objectName()).is_equal_to("my_label")

    def test_make_selector_with_kwargs(self, qt: QtDriver) -> None:
        """make() with selector should still support signal connections."""

        @widget()
        class MyWidget(QWidget, Widget):
            button: QPushButton = make("#btn.primary", QPushButton, "Click", clicked="on_click")
            clicked: bool = False

            def on_click(self) -> None:
                self.clicked = True

        w = MyWidget()
        qt.track(w)

        assert_that(w.button.objectName()).is_equal_to("btn")
        qt.click(w.button)
        assert_that(w.clicked).is_true()

    def test_make_selector_with_layout_none(self, qt: QtDriver) -> None:
        """Selector should work even with layout='none'."""

        @widget(layout="none")
        class MyWidget(QWidget, Widget):
            label: QLabel = make("#custom", QLabel, "Test")

        w = MyWidget()
        qt.track(w)

        assert_that(w.label.objectName()).is_equal_to("custom")
