"""Tests for the make() factory function."""

from assertpy import assert_that
from qtpy.QtWidgets import QLabel, QLineEdit, QPushButton, QSlider, QVBoxLayout, QWidget

from qtpie import Widget, make, widget
from qtpie_test import QtDriver


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
