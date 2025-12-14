"""Tests for stretch support in box layouts."""

from assertpy import assert_that
from qtpy.QtWidgets import QLabel, QPushButton, QVBoxLayout, QWidget

from qtpie import Widget, make, widget
from qtpie_test import QtDriver


class TestStretch:
    """Phase 2: Stretch support for box layouts."""

    def test_stretch_field_adds_stretch(self, qt: QtDriver) -> None:
        """_stretch field with int type should add stretch to layout."""

        @widget(layout="vertical")
        class MyWidget(QWidget, Widget):
            header: QLabel = make(QLabel, "Header")
            _stretch1: int = 1
            footer: QLabel = make(QLabel, "Footer")

        w = MyWidget()
        qt.track(w)

        layout = w.layout()
        assert isinstance(layout, QVBoxLayout)

        # Should have 3 items: header, stretch, footer
        assert_that(layout.count()).is_equal_to(3)

        # Item 0: header widget
        item0 = layout.itemAt(0)
        assert item0 is not None
        assert_that(item0.widget()).is_same_as(w.header)

        # Item 1: spacer/stretch
        item1 = layout.itemAt(1)
        assert item1 is not None
        assert_that(item1.spacerItem()).is_not_none()

        # Item 2: footer widget
        item2 = layout.itemAt(2)
        assert item2 is not None
        assert_that(item2.widget()).is_same_as(w.footer)

    def test_stretch_zero_adds_spacer(self, qt: QtDriver) -> None:
        """_stretch with value 0 should still add a spacer."""

        @widget(layout="vertical")
        class MyWidget(QWidget, Widget):
            header: QLabel = make(QLabel, "Header")
            _stretch1: int = 0
            footer: QLabel = make(QLabel, "Footer")

        w = MyWidget()
        qt.track(w)

        layout = w.layout()
        assert isinstance(layout, QVBoxLayout)

        # Should have 3 items
        assert_that(layout.count()).is_equal_to(3)

        # Middle item should be spacer
        item1 = layout.itemAt(1)
        assert item1 is not None
        assert_that(item1.spacerItem()).is_not_none()

    def test_stretch_between_widgets(self, qt: QtDriver) -> None:
        """Stretch should be placed between widgets in layout order."""

        @widget(layout="vertical")
        class ToolPanel(QWidget, Widget):
            toolbar: QPushButton = make(QPushButton, "Toolbar")
            _stretch_middle: int = 1
            content: QLabel = make(QLabel, "Content")
            _stretch_bottom: int = 0
            footer: QLabel = make(QLabel, "Footer")

        w = ToolPanel()
        qt.track(w)

        layout = w.layout()
        assert layout is not None

        # Should have 5 items: toolbar, stretch, content, stretch, footer
        assert_that(layout.count()).is_equal_to(5)

        # Check order
        assert_that(layout.itemAt(0).widget()).is_same_as(w.toolbar)  # type: ignore[union-attr]
        assert_that(layout.itemAt(1).spacerItem()).is_not_none()  # type: ignore[union-attr]
        assert_that(layout.itemAt(2).widget()).is_same_as(w.content)  # type: ignore[union-attr]
        assert_that(layout.itemAt(3).spacerItem()).is_not_none()  # type: ignore[union-attr]
        assert_that(layout.itemAt(4).widget()).is_same_as(w.footer)  # type: ignore[union-attr]

    def test_stretch_in_horizontal_layout(self, qt: QtDriver) -> None:
        """Stretch should work in horizontal layouts too."""

        @widget(layout="horizontal")
        class MyWidget(QWidget, Widget):
            left: QLabel = make(QLabel, "Left")
            _stretch1: int = 1
            right: QLabel = make(QLabel, "Right")

        w = MyWidget()
        qt.track(w)

        layout = w.layout()
        assert layout is not None

        # Should have 3 items
        assert_that(layout.count()).is_equal_to(3)

        # Check middle is spacer
        item1 = layout.itemAt(1)
        assert item1 is not None
        assert_that(item1.spacerItem()).is_not_none()

    def test_stretch_ignored_in_form_layout(self, qt: QtDriver) -> None:
        """Stretch fields should be ignored in form layouts."""
        from qtpy.QtWidgets import QFormLayout

        @widget(layout="form")
        class MyForm(QWidget, Widget):
            name: QLabel = make(QLabel, form_label="Name")
            _stretch1: int = 1  # Should be ignored
            email: QLabel = make(QLabel, form_label="Email")

        w = MyForm()
        qt.track(w)

        layout = w.layout()
        assert isinstance(layout, QFormLayout)

        # Should have 2 rows (stretch ignored)
        assert_that(layout.rowCount()).is_equal_to(2)

    def test_stretch_ignored_in_grid_layout(self, qt: QtDriver) -> None:
        """Stretch fields should be ignored in grid layouts."""
        from qtpy.QtWidgets import QGridLayout

        @widget(layout="grid")
        class MyGrid(QWidget, Widget):
            btn1: QPushButton = make(QPushButton, "1", grid=(0, 0))
            _stretch1: int = 1  # Should be ignored
            btn2: QPushButton = make(QPushButton, "2", grid=(0, 1))

        w = MyGrid()
        qt.track(w)

        layout = w.layout()
        assert isinstance(layout, QGridLayout)

        # Should have 2 widgets (stretch ignored)
        assert_that(layout.count()).is_equal_to(2)

    def test_multiple_stretch_names(self, qt: QtDriver) -> None:
        """Any field starting with _stretch should work."""

        @widget(layout="vertical")
        class MyWidget(QWidget, Widget):
            top: QLabel = make(QLabel, "Top")
            _stretch_a: int = 1
            middle: QLabel = make(QLabel, "Middle")
            _stretch_b: int = 2
            bottom: QLabel = make(QLabel, "Bottom")

        w = MyWidget()
        qt.track(w)

        layout = w.layout()
        assert layout is not None

        # Should have 5 items
        assert_that(layout.count()).is_equal_to(5)
