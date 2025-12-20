"""Tests for stretch support in box layouts."""

from assertpy import assert_that
from qtpy.QtWidgets import QLabel, QPushButton, QSpacerItem, QVBoxLayout, QWidget

from qtpie import Widget, make, stretch, widget
from qtpie_test import QtDriver


class TestStretch:
    """Tests for stretch() factory function in box layouts."""

    def test_stretch_adds_spacer_to_layout(self, qt: QtDriver) -> None:
        """stretch() should add a spacer item to the layout."""

        @widget(layout="vertical")
        class MyWidget(QWidget, Widget):
            header: QLabel = make(QLabel, "Header")
            middle_spacer: QSpacerItem = stretch(1)
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

    def test_stretch_stored_on_instance(self, qt: QtDriver) -> None:
        """The QSpacerItem should be stored on the widget instance."""

        @widget(layout="vertical")
        class MyWidget(QWidget, Widget):
            header: QLabel = make(QLabel, "Header")
            spacer: QSpacerItem = stretch(1)
            footer: QLabel = make(QLabel, "Footer")

        w = MyWidget()
        qt.track(w)

        # Spacer should be accessible on the instance
        assert_that(w.spacer).is_instance_of(QSpacerItem)

    def test_stretch_zero_adds_spacer(self, qt: QtDriver) -> None:
        """stretch() with factor 0 should still add a spacer."""

        @widget(layout="vertical")
        class MyWidget(QWidget, Widget):
            header: QLabel = make(QLabel, "Header")
            spacer: QSpacerItem = stretch()  # default factor is 0
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
            spacer1: QSpacerItem = stretch(1)
            content: QLabel = make(QLabel, "Content")
            spacer2: QSpacerItem = stretch()
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
            spacer: QSpacerItem = stretch(1)
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
            spacer: QSpacerItem = stretch(1)  # Should be ignored in form layout
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
            spacer: QSpacerItem = stretch(1)  # Should be ignored in grid layout
            btn2: QPushButton = make(QPushButton, "2", grid=(0, 1))

        w = MyGrid()
        qt.track(w)

        layout = w.layout()
        assert isinstance(layout, QGridLayout)

        # Should have 2 widgets (stretch ignored)
        assert_that(layout.count()).is_equal_to(2)

    def test_multiple_stretches(self, qt: QtDriver) -> None:
        """Multiple stretch() calls should all work."""

        @widget(layout="vertical")
        class MyWidget(QWidget, Widget):
            top: QLabel = make(QLabel, "Top")
            spacer1: QSpacerItem = stretch(1)
            middle: QLabel = make(QLabel, "Middle")
            spacer2: QSpacerItem = stretch(2)
            bottom: QLabel = make(QLabel, "Bottom")

        w = MyWidget()
        qt.track(w)

        layout = w.layout()
        assert layout is not None

        # Should have 5 items
        assert_that(layout.count()).is_equal_to(5)

        # Both spacers should be stored
        assert_that(w.spacer1).is_instance_of(QSpacerItem)
        assert_that(w.spacer2).is_instance_of(QSpacerItem)

    def test_stretch_factor_is_set(self, qt: QtDriver) -> None:
        """Stretch factor should be set on the layout item."""

        @widget(layout="vertical")
        class MyWidget(QWidget, Widget):
            top: QLabel = make(QLabel, "Top")
            spacer: QSpacerItem = stretch(3)
            bottom: QLabel = make(QLabel, "Bottom")

        w = MyWidget()
        qt.track(w)

        layout = w.layout()
        assert isinstance(layout, QVBoxLayout)

        # Stretch factor should be 3 on the middle item (index 1)
        assert_that(layout.stretch(1)).is_equal_to(3)


class TestStretchSizeConstraints:
    """Tests for stretch() min_size and max_size features."""

    def test_stretch_min_size_vertical(self, qt: QtDriver) -> None:
        """min_size should set the minimum height in vertical layouts."""

        @widget(layout="vertical")
        class MyWidget(QWidget, Widget):
            top: QLabel = make(QLabel, "Top")
            gap: QSpacerItem = stretch(min_size=50)
            bottom: QLabel = make(QLabel, "Bottom")

        w = MyWidget()
        qt.track(w)

        # Spacer should have minimum height of 50
        assert_that(w.gap.sizeHint().height()).is_equal_to(50)
        assert_that(w.gap.sizeHint().width()).is_equal_to(0)

    def test_stretch_min_size_horizontal(self, qt: QtDriver) -> None:
        """min_size should set the minimum width in horizontal layouts."""

        @widget(layout="horizontal")
        class MyWidget(QWidget, Widget):
            left: QLabel = make(QLabel, "Left")
            gap: QSpacerItem = stretch(min_size=100)
            right: QLabel = make(QLabel, "Right")

        w = MyWidget()
        qt.track(w)

        # Spacer should have minimum width of 100
        assert_that(w.gap.sizeHint().width()).is_equal_to(100)
        assert_that(w.gap.sizeHint().height()).is_equal_to(0)

    def test_stretch_fixed_size(self, qt: QtDriver) -> None:
        """Setting min_size == max_size should create a fixed-size spacer."""
        from qtpy.QtWidgets import QSizePolicy

        @widget(layout="vertical")
        class MyWidget(QWidget, Widget):
            top: QLabel = make(QLabel, "Top")
            fixed_spacer: QSpacerItem = stretch(min_size=75, max_size=75)
            bottom: QLabel = make(QLabel, "Bottom")

        w = MyWidget()
        qt.track(w)

        # Should have fixed size policy
        policy = w.fixed_spacer.sizePolicy()
        assert_that(policy.verticalPolicy()).is_equal_to(QSizePolicy.Policy.Fixed)

    def test_stretch_with_min_and_factor(self, qt: QtDriver) -> None:
        """min_size with factor should create an expanding spacer with minimum."""
        from qtpy.QtWidgets import QSizePolicy

        @widget(layout="vertical")
        class MyWidget(QWidget, Widget):
            top: QLabel = make(QLabel, "Top")
            spacer: QSpacerItem = stretch(1, min_size=30)
            bottom: QLabel = make(QLabel, "Bottom")

        w = MyWidget()
        qt.track(w)

        layout = w.layout()
        assert isinstance(layout, QVBoxLayout)

        # Should have stretch factor
        assert_that(layout.stretch(1)).is_equal_to(1)

        # Should have minimum size
        assert_that(w.spacer.sizeHint().height()).is_equal_to(30)

        # Should be expanding
        policy = w.spacer.sizePolicy()
        assert_that(policy.verticalPolicy()).is_equal_to(QSizePolicy.Policy.Expanding)

    def test_stretch_max_size_sets_maximum_policy(self, qt: QtDriver) -> None:
        """max_size should set Maximum size policy."""
        from qtpy.QtWidgets import QSizePolicy

        @widget(layout="vertical")
        class MyWidget(QWidget, Widget):
            top: QLabel = make(QLabel, "Top")
            spacer: QSpacerItem = stretch(max_size=200)
            bottom: QLabel = make(QLabel, "Bottom")

        w = MyWidget()
        qt.track(w)

        # Should have maximum policy
        policy = w.spacer.sizePolicy()
        assert_that(policy.verticalPolicy()).is_equal_to(QSizePolicy.Policy.Maximum)
