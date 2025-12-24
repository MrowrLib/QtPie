"""Tests for grid layout support."""

from assertpy import assert_that
from qtpy.QtWidgets import QGridLayout, QLabel, QLineEdit, QPushButton, QWidget

from qtpie import Widget, make, widget
from qtpie.testing import QtDriver


class TestGridLayout:
    """Phase 2: Grid layout functionality."""

    def test_grid_layout_creates_qgridlayout(self, qt: QtDriver) -> None:
        """layout='grid' should create a QGridLayout."""

        @widget(layout="grid")
        class MyGrid(QWidget, Widget):
            pass

        w = MyGrid()
        qt.track(w)

        assert_that(w.layout()).is_instance_of(QGridLayout)

    def test_grid_position_basic(self, qt: QtDriver) -> None:
        """grid=(row, col) should place widget at specified position."""

        @widget(layout="grid")
        class MyGrid(QWidget, Widget):
            btn: QPushButton = make(QPushButton, "Click", grid=(0, 0))

        w = MyGrid()
        qt.track(w)

        layout = w.layout()
        assert isinstance(layout, QGridLayout)

        # Check widget is at position (0, 0)
        item = layout.itemAtPosition(0, 0)
        assert item is not None
        assert_that(item.widget()).is_same_as(w.btn)

    def test_grid_position_different_positions(self, qt: QtDriver) -> None:
        """Multiple widgets should be placed at their specified positions."""

        @widget(layout="grid")
        class MyGrid(QWidget, Widget):
            btn_00: QPushButton = make(QPushButton, "00", grid=(0, 0))
            btn_01: QPushButton = make(QPushButton, "01", grid=(0, 1))
            btn_10: QPushButton = make(QPushButton, "10", grid=(1, 0))
            btn_11: QPushButton = make(QPushButton, "11", grid=(1, 1))

        w = MyGrid()
        qt.track(w)

        layout = w.layout()
        assert isinstance(layout, QGridLayout)

        # Check each position
        item_00 = layout.itemAtPosition(0, 0)
        item_01 = layout.itemAtPosition(0, 1)
        item_10 = layout.itemAtPosition(1, 0)
        item_11 = layout.itemAtPosition(1, 1)

        assert item_00 is not None and item_01 is not None
        assert item_10 is not None and item_11 is not None

        assert_that(item_00.widget()).is_same_as(w.btn_00)
        assert_that(item_01.widget()).is_same_as(w.btn_01)
        assert_that(item_10.widget()).is_same_as(w.btn_10)
        assert_that(item_11.widget()).is_same_as(w.btn_11)

    def test_grid_position_with_colspan(self, qt: QtDriver) -> None:
        """grid=(row, col, rowspan, colspan) should span columns."""

        @widget(layout="grid")
        class MyGrid(QWidget, Widget):
            display: QLineEdit = make(QLineEdit, grid=(0, 0, 1, 4))  # spans 4 cols
            btn_0: QPushButton = make(QPushButton, "0", grid=(1, 0))
            btn_1: QPushButton = make(QPushButton, "1", grid=(1, 1))
            btn_2: QPushButton = make(QPushButton, "2", grid=(1, 2))
            btn_3: QPushButton = make(QPushButton, "3", grid=(1, 3))

        w = MyGrid()
        qt.track(w)

        layout = w.layout()
        assert isinstance(layout, QGridLayout)

        # Display should be at (0, 0)
        item = layout.itemAtPosition(0, 0)
        assert item is not None
        assert_that(item.widget()).is_same_as(w.display)

        # All buttons should be at row 1, different columns
        for col, btn in enumerate([w.btn_0, w.btn_1, w.btn_2, w.btn_3]):
            item = layout.itemAtPosition(1, col)
            assert item is not None
            assert_that(item.widget()).is_same_as(btn)

    def test_grid_position_with_rowspan(self, qt: QtDriver) -> None:
        """grid=(row, col, rowspan, colspan) should span rows."""

        @widget(layout="grid")
        class MyGrid(QWidget, Widget):
            side: QPushButton = make(QPushButton, "+", grid=(0, 1, 2, 1))  # spans 2 rows
            top: QPushButton = make(QPushButton, "T", grid=(0, 0))
            bottom: QPushButton = make(QPushButton, "B", grid=(1, 0))

        w = MyGrid()
        qt.track(w)

        layout = w.layout()
        assert isinstance(layout, QGridLayout)

        # Side button should be at (0, 1)
        item_side = layout.itemAtPosition(0, 1)
        assert item_side is not None
        assert_that(item_side.widget()).is_same_as(w.side)

        # Top and bottom at their positions
        item_top = layout.itemAtPosition(0, 0)
        item_bottom = layout.itemAtPosition(1, 0)
        assert item_top is not None and item_bottom is not None
        assert_that(item_top.widget()).is_same_as(w.top)
        assert_that(item_bottom.widget()).is_same_as(w.bottom)

    def test_grid_widget_without_position_skipped(self, qt: QtDriver) -> None:
        """Widgets without grid position should not be added to grid layout."""

        @widget(layout="grid")
        class MyGrid(QWidget, Widget):
            positioned: QPushButton = make(QPushButton, "Pos", grid=(0, 0))
            not_positioned: QPushButton = make(QPushButton, "No Pos")  # No grid

        w = MyGrid()
        qt.track(w)

        layout = w.layout()
        assert isinstance(layout, QGridLayout)

        # Only one widget should be in the layout
        assert_that(layout.count()).is_equal_to(1)

        # The positioned one should be there
        item = layout.itemAtPosition(0, 0)
        assert item is not None
        assert_that(item.widget()).is_same_as(w.positioned)

    def test_grid_skips_private_fields(self, qt: QtDriver) -> None:
        """Private fields should not be added to grid layout."""

        @widget(layout="grid")
        class MyGrid(QWidget, Widget):
            btn: QPushButton = make(QPushButton, "Public", grid=(0, 0))
            _helper: QLabel = make(QLabel, "Hidden", grid=(0, 1))

        w = MyGrid()
        qt.track(w)

        layout = w.layout()
        assert isinstance(layout, QGridLayout)

        # Only one widget (public)
        assert_that(layout.count()).is_equal_to(1)

    def test_grid_calculator_example(self, qt: QtDriver) -> None:
        """Real-world example: calculator-style grid."""

        @widget(layout="grid")
        class Calculator(QWidget, Widget):
            display: QLineEdit = make(QLineEdit, grid=(0, 0, 1, 4))
            btn_7: QPushButton = make(QPushButton, "7", grid=(1, 0))
            btn_8: QPushButton = make(QPushButton, "8", grid=(1, 1))
            btn_9: QPushButton = make(QPushButton, "9", grid=(1, 2))
            btn_plus: QPushButton = make(QPushButton, "+", grid=(1, 3, 2, 1))
            btn_4: QPushButton = make(QPushButton, "4", grid=(2, 0))
            btn_5: QPushButton = make(QPushButton, "5", grid=(2, 1))
            btn_6: QPushButton = make(QPushButton, "6", grid=(2, 2))

        w = Calculator()
        qt.track(w)

        layout = w.layout()
        assert isinstance(layout, QGridLayout)

        # Should have 8 widgets
        assert_that(layout.count()).is_equal_to(8)

        # Verify display spans all 4 columns
        assert_that(layout.itemAtPosition(0, 0).widget()).is_same_as(w.display)  # type: ignore[union-attr]

        # Verify + button is at (1, 3) and spans 2 rows
        assert_that(layout.itemAtPosition(1, 3).widget()).is_same_as(w.btn_plus)  # type: ignore[union-attr]

        # Verify second row buttons
        assert_that(layout.itemAtPosition(2, 0).widget()).is_same_as(w.btn_4)  # type: ignore[union-attr]
        assert_that(layout.itemAtPosition(2, 1).widget()).is_same_as(w.btn_5)  # type: ignore[union-attr]
        assert_that(layout.itemAtPosition(2, 2).widget()).is_same_as(w.btn_6)  # type: ignore[union-attr]
