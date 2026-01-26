# pyright: reportPrivateUsage=false, reportOptionalMemberAccess=false
# pyright: reportAttributeAccessIssue=false, reportUnknownMemberType=false
# pyright: reportUnknownVariableType=false, reportCallIssue=false
# pyright: reportIndexIssue=false, reportArgumentType=false
"""Tests for form and grid layouts with label= and grid= params."""

import pytest
from qtpy.QtWidgets import QCheckBox, QFormLayout, QGridLayout, QLabel, QLineEdit, QSpinBox

from qtpie import Variable, Widget, new, widget
from qtpie.testing import QtDriver


class TestFormLayout:
    """Test form layout with label= param."""

    def test_form_layout_with_label(self, qt: QtDriver) -> None:
        """Form layout uses label= for row labels."""

        @widget(layout="form")
        class TestForm(Widget):
            _name: QLineEdit = new(label="Full Name")
            _email: QLineEdit = new(label="Email Address")

        w = qt.track(TestForm())
        layout = w.layout()

        assert isinstance(layout, QFormLayout)
        assert layout.rowCount() == 2

        # Check that labels were added
        label_item = layout.itemAt(0, QFormLayout.ItemRole.LabelRole)
        assert label_item is not None
        label_widget = label_item.widget()
        assert isinstance(label_widget, QLabel)
        assert label_widget.text() == "Full Name"

    def test_form_layout_requires_label(self, qt: QtDriver) -> None:
        """Form layout raises error if label= is missing."""

        @widget(layout="form")
        class TestForm(Widget):
            _name: QLineEdit = new()  # Missing label=

        with pytest.raises(TypeError, match="requires label="):
            qt.track(TestForm())

    def test_form_layout_variable_with_label(self, qt: QtDriver) -> None:
        """Variable[T, W] in form layout uses label= from widget_kwargs."""

        @widget(layout="form")
        class TestForm(Widget):
            _age: Variable[int, QSpinBox] = new(25)(label="Age")  # type: ignore[type-arg]

        w = qt.track(TestForm())
        layout = w.layout()

        assert isinstance(layout, QFormLayout)
        assert layout.rowCount() == 1

        # Check label
        label_item = layout.itemAt(0, QFormLayout.ItemRole.LabelRole)
        assert label_item is not None
        label_widget = label_item.widget()
        assert isinstance(label_widget, QLabel)
        assert label_widget.text() == "Age"

    def test_form_layout_variable_requires_label(self, qt: QtDriver) -> None:
        """Variable[T, W] in form layout raises error if label= missing."""

        @widget(layout="form")
        class TestForm(Widget):
            _age: Variable[int, QSpinBox] = new(25)()  # Missing label=  # type: ignore[type-arg]

        with pytest.raises(TypeError, match="requires label="):
            qt.track(TestForm())


class TestGridLayout:
    """Test grid layout with grid= param."""

    def test_grid_layout_with_position(self, qt: QtDriver) -> None:
        """Grid layout uses grid= for positioning."""

        @widget(layout="grid")
        class TestGrid(Widget):
            _btn_00: QLabel = new("00", grid=(0, 0))
            _btn_01: QLabel = new("01", grid=(0, 1))
            _btn_10: QLabel = new("10", grid=(1, 0))
            _btn_11: QLabel = new("11", grid=(1, 1))

        w = qt.track(TestGrid())
        layout = w.layout()

        assert isinstance(layout, QGridLayout)

        # Check positions
        item_00 = layout.itemAtPosition(0, 0)
        assert item_00 is not None
        assert item_00.widget().text() == "00"

        item_01 = layout.itemAtPosition(0, 1)
        assert item_01 is not None
        assert item_01.widget().text() == "01"

        item_10 = layout.itemAtPosition(1, 0)
        assert item_10 is not None
        assert item_10.widget().text() == "10"

        item_11 = layout.itemAtPosition(1, 1)
        assert item_11 is not None
        assert item_11.widget().text() == "11"

    def test_grid_layout_with_span(self, qt: QtDriver) -> None:
        """Grid layout supports rowspan and colspan."""

        @widget(layout="grid")
        class TestGrid(Widget):
            # Spans 1 row, 4 cols
            _display: QLineEdit = new(grid=(0, 0, 1, 4))
            # Regular cell
            _btn: QLabel = new("X", grid=(1, 0))

        w = qt.track(TestGrid())
        layout = w.layout()

        assert isinstance(layout, QGridLayout)

        # Display should span 4 columns
        item = layout.itemAtPosition(0, 0)
        assert item is not None
        # QGridLayout doesn't expose span info easily, but we can check widget is there
        assert isinstance(item.widget(), QLineEdit)

        # Button at (1, 0)
        btn_item = layout.itemAtPosition(1, 0)
        assert btn_item is not None
        assert btn_item.widget().text() == "X"

    def test_grid_layout_requires_grid(self, qt: QtDriver) -> None:
        """Grid layout raises error if grid= is missing."""

        @widget(layout="grid")
        class TestGrid(Widget):
            _btn: QLabel = new("X")  # Missing grid=

        with pytest.raises(TypeError, match="requires grid="):
            qt.track(TestGrid())

    def test_grid_layout_variable_with_grid(self, qt: QtDriver) -> None:
        """Variable[T, W] in grid layout uses grid= from widget_kwargs."""

        @widget(layout="grid")
        class TestGrid(Widget):
            _value: Variable[int, QSpinBox] = new(10)(grid=(0, 0))  # type: ignore[type-arg]
            _label: Variable[str, QLabel] = new("Hello")(grid=(0, 1))  # type: ignore[type-arg]

        w = qt.track(TestGrid())
        layout = w.layout()

        assert isinstance(layout, QGridLayout)

        # Check positions
        item_00 = layout.itemAtPosition(0, 0)
        assert item_00 is not None
        assert isinstance(item_00.widget(), QSpinBox)

        item_01 = layout.itemAtPosition(0, 1)
        assert item_01 is not None
        assert isinstance(item_01.widget(), QLabel)

    def test_grid_layout_variable_requires_grid(self, qt: QtDriver) -> None:
        """Variable[T, W] in grid layout raises error if grid= missing."""

        @widget(layout="grid")
        class TestGrid(Widget):
            _value: Variable[int, QSpinBox] = new(10)()  # Missing grid=  # type: ignore[type-arg]

        with pytest.raises(TypeError, match="requires grid="):
            qt.track(TestGrid())


class TestLabelGridPassthrough:
    """Test that label=/grid= pass through to constructors for non-QWidget types."""

    def test_label_passes_to_non_qwidget_constructor(self, qt: QtDriver) -> None:
        """label= kwarg passes through for non-QWidget types."""

        class MyConfig:
            def __init__(self, label: str) -> None:
                self.label = label

        @widget
        class TestWidget(Widget):
            _config: MyConfig = new(label="Test Label")

        w = qt.track(TestWidget())
        assert w._config.label == "Test Label"

    def test_grid_passes_to_non_qwidget_constructor(self, qt: QtDriver) -> None:
        """grid= kwarg passes through for non-QWidget types."""

        class MyPosition:
            def __init__(self, grid: tuple[int, int]) -> None:
                self.grid = grid

        @widget
        class TestWidget(Widget):
            _pos: MyPosition = new(grid=(5, 10))

        w = qt.track(TestWidget())
        assert w._pos.grid == (5, 10)


class TestVerticalHorizontalLayout:
    """Test that vertical/horizontal layouts don't require label=/grid=."""

    def test_vertical_layout_no_label_required(self, qt: QtDriver) -> None:
        """Vertical layout doesn't require label=."""

        @widget(layout="vertical")
        class TestWidget(Widget):
            _name: QLineEdit = new()
            _email: QLineEdit = new()

        w = qt.track(TestWidget())
        assert w.layout().count() == 2

    def test_horizontal_layout_no_grid_required(self, qt: QtDriver) -> None:
        """Horizontal layout doesn't require grid=."""

        @widget(layout="horizontal")
        class TestWidget(Widget):
            _name: QLineEdit = new()
            _email: QLineEdit = new()

        w = qt.track(TestWidget())
        assert w.layout().count() == 2

    def test_vertical_layout_ignores_label(self, qt: QtDriver) -> None:
        """Vertical layout accepts but ignores label= (no error)."""

        @widget(layout="vertical")
        class TestWidget(Widget):
            _name: QLineEdit = new(label="Name")  # label is ignored but allowed

        w = qt.track(TestWidget())
        assert w.layout().count() == 1

    def test_horizontal_layout_ignores_grid(self, qt: QtDriver) -> None:
        """Horizontal layout accepts but ignores grid= (no error)."""

        @widget(layout="horizontal")
        class TestWidget(Widget):
            _name: QLineEdit = new(grid=(0, 0))  # grid is ignored but allowed

        w = qt.track(TestWidget())
        assert w.layout().count() == 1


class TestFormLayoutRowVisibility:
    """Test that visible= on a widget in QFormLayout also hides the label row."""

    def test_visible_false_hides_row(self, qt: QtDriver) -> None:
        """Setting visible=False on widget in form layout hides entire row."""

        @widget(layout="form")
        class TestForm(Widget):
            _show: Variable[bool] = new(True)
            _name: QLineEdit = new(label="Name", visible="_show")

        w = qt.track(TestForm())
        layout = w.layout()
        assert isinstance(layout, QFormLayout)

        # Initially visible (use isHidden() - isVisible() needs visible parent)
        assert not w._name.isHidden()
        # Check row is visible
        assert layout.isRowVisible(w._name)

        # Hide via variable
        w._show.value = False
        qt.process_events()

        # Widget hidden
        assert w._name.isHidden()
        # Row should also be hidden
        assert not layout.isRowVisible(w._name)

    def test_visible_nested_layout_hides_row(self, qt: QtDriver) -> None:
        """Setting visible=False hides row when using layout= to target nested layout."""

        @widget
        class TestForm(Widget):
            _show: Variable[bool] = new(False)  # Start hidden!
            _form_layout: QFormLayout = new()
            _name: QLineEdit = new(label="Name", layout="_form_layout", visible="_show")

        w = qt.track(TestForm())
        # The widget's layout is vertical by default, but _form_layout is the QFormLayout
        layout = w._form_layout
        assert isinstance(layout, QFormLayout)

        # Initially hidden (use isHidden() - isVisible() needs visible parent)
        assert w._name.isHidden()
        # Check row is also hidden
        assert not layout.isRowVisible(w._name)

        # Show via variable
        w._show.value = True
        qt.process_events()

        # Widget visible
        assert not w._name.isHidden()
        # Row should also be visible
        assert layout.isRowVisible(w._name)

        # Initially visible (use isHidden() - isVisible() needs visible parent)
        assert not w._name.isHidden()
        # Check row is visible
        assert layout.isRowVisible(w._name)

        # Hide via variable
        w._show.value = False
        qt.process_events()

        # Widget hidden
        assert w._name.isHidden()
        # Row should also be hidden
        assert not layout.isRowVisible(w._name)

    def test_visible_expression_hides_row(self, qt: QtDriver) -> None:
        """Expression binding visible= hides entire form row."""

        @widget(layout="form")
        class TestForm(Widget):
            _count: Variable[int] = new(5)
            _name: QLineEdit = new(label="Name", visible="{_count > 3}")

        w = qt.track(TestForm())
        layout = w.layout()
        assert isinstance(layout, QFormLayout)

        # Initially visible (5 > 3) - use isHidden() instead of isVisible()
        assert not w._name.isHidden()
        assert layout.isRowVisible(w._name)

        # Change to make expression false
        w._count.value = 2
        qt.process_events()

        # Row should be hidden
        assert w._name.isHidden()
        assert not layout.isRowVisible(w._name)

        # Change back to make visible
        w._count.value = 10
        qt.process_events()

        assert not w._name.isHidden()
        assert layout.isRowVisible(w._name)

    def test_variable_with_widget_visible_hides_row(self, qt: QtDriver) -> None:
        """Variable[T, W] in form layout with visible= hides entire row."""

        @widget(layout="form")
        class TestForm(Widget):
            _show: Variable[bool] = new(True)
            _check: Variable[bool, QCheckBox] = new(False)(label="Check Me", visible="_show")

        w = qt.track(TestForm())
        layout = w.layout()
        assert isinstance(layout, QFormLayout)

        # Get the checkbox widget from the Variable
        checkbox = w._check.widget
        assert isinstance(checkbox, QCheckBox)

        # Initially visible
        assert not checkbox.isHidden()
        assert layout.isRowVisible(checkbox)

        # Hide via variable
        w._show.value = False
        qt.process_events()

        # Widget hidden
        assert checkbox.isHidden()
        # Row should also be hidden (THIS IS THE BUG - row label stays visible)
        assert not layout.isRowVisible(checkbox)

    def test_variable_with_widget_visible_expression_hides_row(self, qt: QtDriver) -> None:
        """Variable[T, W] in form layout with expression visible= hides entire row."""

        @widget(layout="form")
        class TestForm(Widget):
            _count: Variable[int] = new(5)
            _check: Variable[bool, QCheckBox] = new(False)(label="Check Me", visible="{_count > 3}")

        w = qt.track(TestForm())
        layout = w.layout()
        assert isinstance(layout, QFormLayout)

        checkbox = w._check.widget
        assert isinstance(checkbox, QCheckBox)

        # Initially visible (5 > 3)
        assert not checkbox.isHidden()
        assert layout.isRowVisible(checkbox)

        # Change to make expression false
        w._count.value = 2
        qt.process_events()

        # Row should be hidden
        assert checkbox.isHidden()
        assert not layout.isRowVisible(checkbox)
