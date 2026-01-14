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
from qtpy.QtWidgets import QLabel, QSplitter

from qtpie import new
from qtpie.testing import QtDriver

from .conftest import WIDGET_ONLY, create_and_track


@pytest.mark.parametrize("base_class,decorator", WIDGET_ONLY)
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
        layout = instance.layout()
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
        layout = instance.layout()
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
        layout = instance.layout()
        assert_that(layout.count()).is_equal_to(2)

        # Each splitter has 2 widgets
        assert_that(instance._top_splitter.count()).is_equal_to(2)
        assert_that(instance._bottom_splitter.count()).is_equal_to(2)

        assert_that(instance._top_splitter.widget(0).text()).is_equal_to("Top Left")
        assert_that(instance._bottom_splitter.widget(1).text()).is_equal_to("Bottom Right")
