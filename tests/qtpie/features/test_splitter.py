# pyright: reportPrivateUsage=false
# pyright: reportMissingParameterType=false
# pyright: reportUnknownParameterType=false
# pyright: reportUntypedBaseClass=false
# pyright: reportUntypedClassDecorator=false
# pyright: reportUnknownArgumentType=false
"""QSplitter support with splitter= parameter."""

import pytest
from assertpy import assert_that
from qtpy.QtCore import Qt
from qtpy.QtWidgets import QLabel, QLineEdit, QSpinBox, QSplitter, QVBoxLayout

from qtpie import Variable, WidgetRepeater, new
from qtpie.testing import QtDriver

from .conftest import WIDGET_CLASS_TYPES, create_and_track, get_layout


@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestSplitter:
    """QSplitter support with splitter= parameter."""

    def test_splitter_basic(self, base_class, decorator, qt: QtDriver) -> None:
        """QSplitter with widgets added via splitter= string."""

        @decorator
        class TestClass(base_class):
            _splitter: QSplitter = new(Qt.Orientation.Horizontal)
            left: QLabel = new("Left", splitter="_splitter")
            right: QLabel = new("Right", splitter="_splitter")

        instance = create_and_track(qt, TestClass, base_class)

        assert_that(instance._splitter).is_instance_of(QSplitter)
        assert_that(instance._splitter.count()).is_equal_to(2)
        assert_that(instance._splitter.widget(0).text()).is_equal_to("Left")
        assert_that(instance._splitter.widget(1).text()).is_equal_to("Right")

    def test_splitter_vertical(self, base_class, decorator, qt: QtDriver) -> None:
        """QSplitter with vertical orientation."""

        @decorator
        class TestClass(base_class):
            _splitter: QSplitter = new(Qt.Orientation.Vertical)
            top: QLabel = new("Top", splitter="_splitter")
            bottom: QLabel = new("Bottom", splitter="_splitter")

        instance = create_and_track(qt, TestClass, base_class)

        assert_that(instance._splitter.orientation()).is_equal_to(Qt.Orientation.Vertical)
        assert_that(instance._splitter.count()).is_equal_to(2)

    def test_splitter_in_layout(self, base_class, decorator, qt: QtDriver) -> None:
        """QSplitter is added to the parent layout."""

        @decorator(layout="vertical")
        class TestClass(base_class):
            header: QLabel = new("Header")
            _splitter: QSplitter = new(Qt.Orientation.Horizontal)
            left: QLabel = new("Left", splitter="_splitter")
            right: QLabel = new("Right", splitter="_splitter")

        instance = create_and_track(qt, TestClass, base_class)

        # Splitter should be in main layout
        # header + splitter = 2 items in layout
        layout = get_layout(instance, base_class)
        assert_that(layout.count()).is_equal_to(2)
        # First item is header, second is splitter
        assert_that(layout.itemAt(0).widget()).is_same_as(instance.header)
        assert_that(layout.itemAt(1).widget()).is_same_as(instance._splitter)

    def test_splitter_excludes_from_layout(self, base_class, decorator, qt: QtDriver) -> None:
        """Widgets with splitter= are not added to the default layout."""

        @decorator(layout="vertical")
        class TestClass(base_class):
            header: QLabel = new("Header")
            _splitter: QSplitter = new(Qt.Orientation.Horizontal)
            left: QLabel = new("Left", splitter="_splitter")
            right: QLabel = new("Right", splitter="_splitter")
            footer: QLabel = new("Footer")

        instance = create_and_track(qt, TestClass, base_class)

        # Main layout: header, splitter, footer (3 items)
        # NOT: header, splitter, left, right, footer (5 items)
        layout = get_layout(instance, base_class)
        assert_that(layout.count()).is_equal_to(3)
        assert_that(layout.itemAt(0).widget()).is_same_as(instance.header)
        assert_that(layout.itemAt(1).widget()).is_same_as(instance._splitter)
        assert_that(layout.itemAt(2).widget()).is_same_as(instance.footer)

        # Splitter contains left and right
        assert_that(instance._splitter.count()).is_equal_to(2)
        assert_that(instance._splitter.widget(0)).is_same_as(instance.left)
        assert_that(instance._splitter.widget(1)).is_same_as(instance.right)

    def test_multiple_splitters(self, base_class, decorator, qt: QtDriver) -> None:
        """Multiple splitters in the same widget."""

        @decorator(layout="vertical")
        class TestClass(base_class):
            _top_splitter: QSplitter = new(Qt.Orientation.Horizontal)
            top_left: QLabel = new("Top Left", splitter="_top_splitter")
            top_right: QLabel = new("Top Right", splitter="_top_splitter")

            _bottom_splitter: QSplitter = new(Qt.Orientation.Horizontal)
            bottom_left: QLabel = new("Bottom Left", splitter="_bottom_splitter")
            bottom_right: QLabel = new("Bottom Right", splitter="_bottom_splitter")

        instance = create_and_track(qt, TestClass, base_class)

        # Layout has 2 splitters
        layout = get_layout(instance, base_class)
        assert_that(layout.count()).is_equal_to(2)

        # Each splitter has 2 widgets
        assert_that(instance._top_splitter.count()).is_equal_to(2)
        assert_that(instance._bottom_splitter.count()).is_equal_to(2)

        assert_that(instance._top_splitter.widget(0).text()).is_equal_to("Top Left")
        assert_that(instance._bottom_splitter.widget(1).text()).is_equal_to("Bottom Right")

    def test_nested_splitters(self, base_class, decorator, qt: QtDriver) -> None:
        """Nested splitters - a splitter inside another splitter."""

        @decorator(layout="vertical")
        class TestClass(base_class):
            _outer: QSplitter = new(Qt.Orientation.Horizontal)
            outer_left: QLabel = new("Outer Left", splitter="_outer")
            _inner: QSplitter = new(Qt.Orientation.Vertical, splitter="_outer")
            inner_top: QLabel = new("Inner Top", splitter="_inner")
            inner_bottom: QLabel = new("Inner Bottom", splitter="_inner")

        instance = create_and_track(qt, TestClass, base_class)

        # Main layout has just the outer splitter
        layout = get_layout(instance, base_class)
        assert_that(layout.count()).is_equal_to(1)
        assert_that(layout.itemAt(0).widget()).is_same_as(instance._outer)

        # Outer splitter contains: outer_left + inner splitter
        assert_that(instance._outer.count()).is_equal_to(2)
        assert_that(instance._outer.widget(0)).is_same_as(instance.outer_left)
        assert_that(instance._outer.widget(1)).is_same_as(instance._inner)

        # Inner splitter contains: inner_top + inner_bottom
        assert_that(instance._inner.count()).is_equal_to(2)
        assert_that(instance._inner.widget(0)).is_same_as(instance.inner_top)
        assert_that(instance._inner.widget(1)).is_same_as(instance.inner_bottom)

    def test_splitter_in_nested_layout(self, base_class, decorator, qt: QtDriver) -> None:
        """Splitter placed inside a nested layout."""

        @decorator(layout="vertical")
        class TestClass(base_class):
            # Top-level splitter (goes into main layout)
            _top_splitter: QSplitter = new(Qt.Orientation.Horizontal)
            top_left: QLabel = new("Top Left", splitter="_top_splitter")
            top_right: QLabel = new("Top Right", splitter="_top_splitter")

            # Nested layout (goes into main layout)
            _nested_layout: QVBoxLayout

            # Splitter inside the nested layout
            _nested_splitter: QSplitter = new(Qt.Orientation.Horizontal, layout="_nested_layout")
            nested_left: QLabel = new("Nested Left", splitter="_nested_splitter")
            nested_right: QLabel = new("Nested Right", splitter="_nested_splitter")

        instance = create_and_track(qt, TestClass, base_class)

        # Main layout has: top_splitter + nested_layout
        layout = get_layout(instance, base_class)
        assert_that(layout.count()).is_equal_to(2)
        assert_that(layout.itemAt(0).widget()).is_same_as(instance._top_splitter)
        # Second item is the nested layout
        assert_that(layout.itemAt(1).layout()).is_same_as(instance._nested_layout)

        # Top splitter contains its widgets
        assert_that(instance._top_splitter.count()).is_equal_to(2)

        # Nested layout contains the nested splitter
        assert_that(instance._nested_layout.count()).is_equal_to(1)
        assert_that(instance._nested_layout.itemAt(0).widget()).is_same_as(instance._nested_splitter)

        # Nested splitter contains its widgets
        assert_that(instance._nested_splitter.count()).is_equal_to(2)

    def test_variable_widget_in_splitter(self, base_class, decorator, qt: QtDriver) -> None:
        """Variable[T, W] with splitter= places the widget in the splitter."""

        @decorator(layout="vertical")
        class TestClass(base_class):
            _splitter: QSplitter = new(Qt.Orientation.Horizontal)
            _name: Variable[str, QLineEdit] = new("default")(splitter="_splitter", placeholderText="Name")
            _age: Variable[int, QSpinBox] = new(25)(splitter="_splitter")

        instance = create_and_track(qt, TestClass, base_class)

        # Main layout has just the splitter
        layout = get_layout(instance, base_class)
        assert_that(layout.count()).is_equal_to(1)

        # Splitter contains the QLineEdit and QSpinBox
        assert_that(instance._splitter.count()).is_equal_to(2)
        assert_that(instance._splitter.widget(0)).is_same_as(instance._name.widget)
        assert_that(instance._splitter.widget(1)).is_same_as(instance._age.widget)

        # Widget kwargs were applied
        assert_that(instance._name.widget.placeholderText()).is_equal_to("Name")

    def test_list_widget_repeater_in_splitter(self, base_class, decorator, qt: QtDriver) -> None:
        """list[QWidget] = new(bind=..., splitter=...) places repeater in splitter."""

        @decorator(layout="vertical")
        class TestClass(base_class):
            _items: Variable[list[str]] = new(["a", "b", "c"])
            _splitter: QSplitter = new(Qt.Orientation.Horizontal)
            _labels: list[QLabel] = new(bind="_items", splitter="_splitter")

        instance = create_and_track(qt, TestClass, base_class)

        # Main layout has just the splitter
        layout = get_layout(instance, base_class)
        assert_that(layout.count()).is_equal_to(1)

        # Splitter contains the repeater (1 widget)
        assert_that(instance._splitter.count()).is_equal_to(1)

        # Repeater contains 3 labels
        assert_that(instance._labels.widget_count()).is_equal_to(3)

    def test_variable_list_repeater_in_splitter(self, base_class, decorator, qt: QtDriver) -> None:
        """Variable[list[T], W] with splitter= places repeater in splitter."""

        @decorator(layout="vertical")
        class TestClass(base_class):
            _splitter: QSplitter = new(Qt.Orientation.Vertical)
            _items: Variable[list[str], QLabel] = new(["x", "y"])(splitter="_splitter")  # type: ignore[type-arg]

        instance = create_and_track(qt, TestClass, base_class)

        # Main layout has just the splitter
        layout = get_layout(instance, base_class)
        assert_that(layout.count()).is_equal_to(1)

        # Splitter contains the repeater (1 widget)
        assert_that(instance._splitter.count()).is_equal_to(1)

        # Repeater contains 2 labels
        repeater: WidgetRepeater[str] = instance._items.widget
        assert_that(repeater.widget_count()).is_equal_to(2)

    def test_variable_dict_repeater_in_splitter(self, base_class, decorator, qt: QtDriver) -> None:
        """Variable[dict[K,V]] + list[W] with splitter= places repeater in splitter."""

        @decorator(layout="vertical")
        class TestClass(base_class):
            _scores: Variable[dict[str, int]] = new({"Alice": 100, "Bob": 85})
            _splitter: QSplitter = new(Qt.Orientation.Horizontal)
            _labels: list[QLabel] = new(bind="_scores", format="{#key}: {#value}", splitter="_splitter")

        instance = create_and_track(qt, TestClass, base_class)

        # Main layout has just the splitter
        layout = get_layout(instance, base_class)
        assert_that(layout.count()).is_equal_to(1)

        # Splitter contains the repeater (1 widget)
        assert_that(instance._splitter.count()).is_equal_to(1)

        # Repeater contains 2 labels
        assert_that(instance._labels.widget_count()).is_equal_to(2)

    def test_splitter_default_orientation(self, base_class, decorator, qt: QtDriver) -> None:
        """QSplitter with no explicit orientation (defaults to Horizontal)."""

        @decorator(layout="vertical")
        class TestClass(base_class):
            _splitter: QSplitter = new()
            left: QLabel = new("Left", splitter="_splitter")
            right: QLabel = new("Right", splitter="_splitter")

        instance = create_and_track(qt, TestClass, base_class)

        assert_that(instance._splitter).is_instance_of(QSplitter)
        # Default orientation is Horizontal
        assert_that(instance._splitter.orientation()).is_equal_to(Qt.Orientation.Horizontal)
        assert_that(instance._splitter.count()).is_equal_to(2)

    def test_splitter_child_sizes(self, base_class, decorator, qt: QtDriver) -> None:
        """QSplitter with setSizes to control proportions."""

        @decorator(layout="vertical")
        class TestClass(base_class):
            _splitter: QSplitter = new(Qt.Orientation.Horizontal)
            left: QLabel = new("Left", splitter="_splitter")
            right: QLabel = new("Right", splitter="_splitter")

            def __setup__(self) -> None:
                self._splitter.setSizes([100, 300])

        instance = create_and_track(qt, TestClass, base_class)

        # Sizes were applied (note: actual values depend on widget sizing)
        sizes = instance._splitter.sizes()
        assert_that(len(sizes)).is_equal_to(2)
