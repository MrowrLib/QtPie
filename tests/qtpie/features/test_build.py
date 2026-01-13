# pyright: reportPrivateUsage=false
# pyright: reportMissingParameterType=false
# pyright: reportUnknownParameterType=false
# pyright: reportUntypedBaseClass=false
# pyright: reportUntypedClassDecorator=false
# pyright: reportUnknownArgumentType=false
# pyright: reportUnknownMemberType=false
# pyright: reportOptionalMemberAccess=false
# pyright: reportAttributeAccessIssue=false
# pyright: reportCallIssue=false
# pyright: reportIndexIssue=false
# pyright: reportArgumentType=false
# pyright: reportImplicitOverride=false
"""Tests for create() - runtime instantiation with new()-like features.

create_instance() is the top-level function.
Widget, Window, App, and Menu all have a .create() method that wraps it.
"""

import pytest
from assertpy import assert_that
from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QLabel, QPushButton

from qtpie import Widget, new, widget
from qtpie.create import create_instance
from qtpie.testing import QtDriver

# =============================================================================
# Signal Connections via create_instance()
# =============================================================================


class TestSignalToMethod:
    """Test connecting signals to methods by name."""

    def test_signal_connects_to_method(self, qt: QtDriver) -> None:
        """Signal connected to method by name string."""

        @widget
        class ChildWidget(Widget):
            on_action = Signal()

        class Parent:
            def __init__(self) -> None:
                self.action_called = False
                self.child = create_instance(self, ChildWidget, on_action="on_action")

            def on_action(self) -> None:
                self.action_called = True

        parent = Parent()
        qt.track(parent.child)

        parent.child.on_action.emit()
        assert_that(parent.action_called).is_true()

    def test_multiple_signals(self, qt: QtDriver) -> None:
        """Multiple signals can be connected."""

        @widget
        class ChildWidget(Widget):
            on_action1 = Signal()
            on_action2 = Signal()

        class Parent:
            def __init__(self) -> None:
                self.calls: list[str] = []
                self.child = create_instance(
                    self,
                    ChildWidget,
                    on_action1="handler1",
                    on_action2="handler2",
                )

            def handler1(self) -> None:
                self.calls.append("handler1")

            def handler2(self) -> None:
                self.calls.append("handler2")

        parent = Parent()
        qt.track(parent.child)

        parent.child.on_action1.emit()
        parent.child.on_action2.emit()
        assert_that(parent.calls).is_equal_to(["handler1", "handler2"])


class TestSignalToLambda:
    """Test connecting signals to lambdas/callables."""

    def test_signal_connects_to_lambda(self, qt: QtDriver) -> None:
        """Signal connected to lambda."""

        @widget
        class ChildWidget(Widget):
            on_action = Signal()

        result: list[str] = []

        # Lambda doesn't need a real context
        child = create_instance(None, ChildWidget, on_action=lambda: result.append("called"))
        qt.track(child)

        child.on_action.emit()
        assert_that(result).is_equal_to(["called"])

    def test_signal_connects_to_callable(self, qt: QtDriver) -> None:
        """Signal connected to callable object."""

        @widget
        class ChildWidget(Widget):
            on_action = Signal()

        class CallableHandler:
            def __init__(self) -> None:
                self.called = False

            def __call__(self) -> None:
                self.called = True

        handler = CallableHandler()
        child = create_instance(None, ChildWidget, on_action=handler)
        qt.track(child)

        child.on_action.emit()
        assert_that(handler.called).is_true()


class TestSignalToSignal:
    """Test connecting signals to other signals."""

    def test_signal_connects_to_signal(self, qt: QtDriver) -> None:
        """Signal can be connected to another signal on the context."""

        @widget
        class ChildWidget(Widget):
            on_action = Signal()

        class ParentQObject(QObject):
            forwarded = Signal()

            def __init__(self) -> None:
                super().__init__()
                self.received = False
                self.child = create_instance(self, ChildWidget, on_action="forwarded")
                self.forwarded.connect(self._on_forwarded)

            def _on_forwarded(self) -> None:
                self.received = True

        parent = ParentQObject()
        qt.track(parent.child)

        parent.child.on_action.emit()
        assert_that(parent.received).is_true()


class TestSignalErrors:
    """Test error handling for signal connections."""

    def test_missing_handler_raises(self, qt: QtDriver) -> None:
        """Missing handler raises AttributeError with helpful message."""

        @widget
        class ChildWidget(Widget):
            on_action = Signal()

        class Parent:
            pass

        parent = Parent()

        with pytest.raises(AttributeError, match="nonexistent"):
            create_instance(parent, ChildWidget, on_action="nonexistent")

    def test_non_callable_handler_raises(self, qt: QtDriver) -> None:
        """Non-callable, non-signal handler raises AttributeError."""

        @widget
        class ChildWidget(Widget):
            on_action = Signal()

        class Parent:
            not_callable = "just a string"

        parent = Parent()

        with pytest.raises(AttributeError, match="not callable"):
            create_instance(parent, ChildWidget, on_action="not_callable")


# =============================================================================
# Widget.build() method
# =============================================================================


class TestWidgetBuildMethod:
    """Test the .build() method on Widget."""

    def test_widget_build_method(self, qt: QtDriver) -> None:
        """Widget.build() connects signals to parent widget methods."""

        @widget
        class ChildWidget(Widget):
            on_action = Signal()

        @widget
        class ParentWidget(Widget):
            def __setup__(self) -> None:
                self.action_called = False
                self.child = self.build(ChildWidget, on_action="on_action")

            def on_action(self) -> None:
                self.action_called = True

        parent = ParentWidget()
        qt.track(parent)

        parent.child.on_action.emit()
        assert_that(parent.action_called).is_true()


# =============================================================================
# Constructor Args
# =============================================================================


class TestConstructorArgs:
    """Test that constructor args are passed through."""

    def test_positional_args(self, qt: QtDriver) -> None:
        """Positional args are passed to constructor."""
        label = create_instance(None, QLabel, "Hello World")
        qt.track(label)

        assert_that(label.text()).is_equal_to("Hello World")

    def test_keyword_args(self, qt: QtDriver) -> None:
        """Non-signal/prop kwargs are passed to constructor."""
        btn = create_instance(None, QPushButton, text="Click Me")
        qt.track(btn)

        assert_that(btn.text()).is_equal_to("Click Me")


# =============================================================================
# Widget Props (setXxx methods)
# =============================================================================


class TestWidgetProps:
    """Test that widget properties are applied via setXxx methods."""

    def test_enabled_prop(self, qt: QtDriver) -> None:
        """enabled= calls setEnabled()."""
        btn = create_instance(None, QPushButton, "Click", enabled=False)
        qt.track(btn)

        assert_that(btn.isEnabled()).is_false()

    def test_visible_prop(self, qt: QtDriver) -> None:
        """visible= calls setVisible()."""
        label = create_instance(None, QLabel, "Hidden", visible=False)
        qt.track(label)

        assert_that(label.isVisible()).is_false()

    def test_toolTip_prop(self, qt: QtDriver) -> None:
        """toolTip= calls setToolTip()."""
        btn = create_instance(None, QPushButton, "Hover me", toolTip="This is a tooltip")
        qt.track(btn)

        assert_that(btn.toolTip()).is_equal_to("This is a tooltip")

    def test_objectName_via_name(self, qt: QtDriver) -> None:
        """name= sets objectName."""
        label = create_instance(None, QLabel, "Test", name="my-label")
        qt.track(label)

        assert_that(label.objectName()).is_equal_to("my-label")


# =============================================================================
# CSS Classes
# =============================================================================


class TestCssClasses:
    """Test CSS class application."""

    def test_single_class(self, qt: QtDriver) -> None:
        """classes= with single class."""
        label = create_instance(None, QLabel, "Test", classes=["highlight"])
        qt.track(label)

        # Classes are stored in "class" property (for QSS selector matching)
        assert_that(label.property("class")).contains("highlight")

    def test_multiple_classes(self, qt: QtDriver) -> None:
        """classes= with multiple classes."""
        label = create_instance(None, QLabel, "Test", classes=["highlight", "large", "bold"])
        qt.track(label)

        classes = label.property("class")
        assert_that(classes).contains("highlight")
        assert_that(classes).contains("large")
        assert_that(classes).contains("bold")


# =============================================================================
# bind= format bindings
# =============================================================================


class TestBindExpr:
    """Test bind= format string bindings."""

    def test_bind_to_variable(self, qt: QtDriver) -> None:
        """bind= creates reactive binding to parent Variable."""
        from qtpie import Variable

        @widget
        class Parent(Widget):
            _count: Variable[int] = new(42)

            def __setup__(self) -> None:
                self.label = self.build(QLabel, bind="Count: {_count}")

        parent = Parent()
        qt.track(parent)

        assert_that(parent.label.text()).is_equal_to("Count: 42")

        # Update the variable
        parent._count.value = 100
        assert_that(parent.label.text()).is_equal_to("Count: 100")

    def test_bind_with_expression(self, qt: QtDriver) -> None:
        """bind= with complex expression."""
        from qtpie import Variable

        @widget
        class Parent(Widget):
            _x: Variable[int] = new(10)
            _y: Variable[int] = new(20)

            def __setup__(self) -> None:
                self.label = self.build(QLabel, bind="Sum: {_x + _y}")

        parent = Parent()
        qt.track(parent)

        assert_that(parent.label.text()).is_equal_to("Sum: 30")

        parent._x.value = 5
        assert_that(parent.label.text()).is_equal_to("Sum: 25")


# =============================================================================
# visible=/enabled= property bindings
# =============================================================================


class TestPropertyBindings:
    """Test visible= and enabled= property bindings."""

    def test_visible_binding_simple(self, qt: QtDriver) -> None:
        """visible= with simple variable reference."""
        from qtpie import Variable

        @widget
        class Parent(Widget):
            _show_label: Variable[bool] = new(True)

            def __setup__(self) -> None:
                self.label = self.build(QLabel, "Hello", visible="_show_label")

        parent = Parent()
        qt.track(parent)

        assert_that(parent.label.isVisible()).is_true()

        parent._show_label.value = False
        assert_that(parent.label.isVisible()).is_false()

    def test_enabled_binding_expression(self, qt: QtDriver) -> None:
        """enabled= with expression binding."""
        from qtpie import Variable

        @widget
        class Parent(Widget):
            _count: Variable[int] = new(0)

            def __setup__(self) -> None:
                self.btn = self.build(QPushButton, "Submit", enabled="{_count > 0}")

        parent = Parent()
        qt.track(parent)

        assert_that(parent.btn.isEnabled()).is_false()

        parent._count.value = 5
        assert_that(parent.btn.isEnabled()).is_true()


# =============================================================================
# ref() deferred bindings
# =============================================================================


class TestRefBindings:
    """Test ref() deferred attribute references."""

    def test_ref_resolves_at_build_time(self, qt: QtDriver) -> None:
        """ref() resolves attribute from context."""
        from qtpie import ref

        @widget
        class Parent(Widget):
            my_tooltip = "This is my tooltip"

            def __setup__(self) -> None:
                self.btn = self.build(QPushButton, "Click", toolTip=ref("my_tooltip"))

        parent = Parent()
        qt.track(parent)

        assert_that(parent.btn.toolTip()).is_equal_to("This is my tooltip")


# =============================================================================
# t() translatable support
# =============================================================================


class TestTranslatableSupport:
    """Test t() translatable strings in build()."""

    def test_translatable_positional_arg(self, qt: QtDriver) -> None:
        """Translatable in positional arg resolves to current translation."""
        from qtpie.translations.translatable import Translatable

        # Create a mock translatable that just returns its text
        class MockTranslatable(Translatable):
            def resolve(self, widget_context: str | None = None) -> str:
                return f"[{self.text}]"

        label = create_instance(None, QLabel, MockTranslatable("Hello"))
        qt.track(label)

        assert_that(label.text()).is_equal_to("[Hello]")

    def test_translatable_in_prop(self, qt: QtDriver) -> None:
        """Translatable in widget prop resolves correctly."""
        from qtpie.translations.translatable import Translatable

        class MockTranslatable(Translatable):
            def resolve(self, widget_context: str | None = None) -> str:
                return f"translated:{self.text}"

        btn = create_instance(None, QPushButton, "Click", toolTip=MockTranslatable("Tooltip"))
        qt.track(btn)

        assert_that(btn.toolTip()).is_equal_to("translated:Tooltip")


# =============================================================================
# layout= support (add to layout)
# =============================================================================


class TestLayoutSupport:
    """Test layout=, label=, grid= support in build().

    NOTE: layout= only works in __setup__ or methods called after construction,
    because nested layouts are created after __init__ runs.
    """

    def test_layout_string_adds_to_named_layout(self, qt: QtDriver) -> None:
        """layout='attr_name' adds widget to that layout on context."""
        from PySide6.QtWidgets import QHBoxLayout

        @widget
        class Parent(Widget):
            _row: QHBoxLayout = new()

            def __setup__(self) -> None:
                self.dynamic_label = self.build(QLabel, "Dynamic", layout="_row")

        parent = Parent()
        qt.track(parent)

        assert_that(parent._row.count()).is_equal_to(1)
        assert_that(parent._row.itemAt(0).widget()).is_same_as(parent.dynamic_label)

    def test_layout_true_adds_to_default_layout(self, qt: QtDriver) -> None:
        """layout=True adds widget to context's default layout."""

        @widget
        class Parent(Widget):
            _existing: QLabel = new("Existing")

            def __setup__(self) -> None:
                self.dynamic_label = self.build(QLabel, "Dynamic", layout=True)

        parent = Parent()
        qt.track(parent)

        main_layout = parent.layout()
        assert_that(main_layout.count()).is_equal_to(2)

    def test_layout_with_form_and_label(self, qt: QtDriver) -> None:
        """layout= with QFormLayout and label= adds row with label."""
        from PySide6.QtWidgets import QFormLayout, QLineEdit

        @widget
        class Parent(Widget):
            _form: QFormLayout = new()

            def __setup__(self) -> None:
                self.name_field = self.build(QLineEdit, layout="_form", label="Name:")
                self.email_field = self.build(QLineEdit, layout="_form", label="Email:")

        parent = Parent()
        qt.track(parent)

        assert_that(parent._form.rowCount()).is_equal_to(2)
        assert_that(parent._form.labelForField(parent.name_field).text()).is_equal_to("Name:")
        assert_that(parent._form.labelForField(parent.email_field).text()).is_equal_to("Email:")

    def test_layout_with_grid_and_position(self, qt: QtDriver) -> None:
        """layout= with QGridLayout and grid= positions widget."""
        from PySide6.QtWidgets import QGridLayout

        @widget
        class Parent(Widget):
            _grid: QGridLayout = new()

            def __setup__(self) -> None:
                self.cell_00 = self.build(QLabel, "(0,0)", layout="_grid", grid=(0, 0))
                self.cell_01 = self.build(QLabel, "(0,1)", layout="_grid", grid=(0, 1))
                self.cell_10 = self.build(QLabel, "(1,0)", layout="_grid", grid=(1, 0))
                self.cell_11 = self.build(QLabel, "(1,1)", layout="_grid", grid=(1, 1))

        parent = Parent()
        qt.track(parent)

        assert_that(parent._grid.count()).is_equal_to(4)
        assert_that(parent._grid.itemAtPosition(0, 0).widget()).is_same_as(parent.cell_00)
        assert_that(parent._grid.itemAtPosition(0, 1).widget()).is_same_as(parent.cell_01)
        assert_that(parent._grid.itemAtPosition(1, 0).widget()).is_same_as(parent.cell_10)
        assert_that(parent._grid.itemAtPosition(1, 1).widget()).is_same_as(parent.cell_11)

    def test_layout_with_grid_span(self, qt: QtDriver) -> None:
        """layout= with QGridLayout and grid= with rowspan/colspan."""
        from PySide6.QtWidgets import QGridLayout

        @widget
        class Parent(Widget):
            _grid: QGridLayout = new()

            def __setup__(self) -> None:
                # Header spans 2 columns
                self.header = self.build(QLabel, "Header", layout="_grid", grid=(0, 0, 1, 2))
                # Sidebar spans 2 rows
                self.sidebar = self.build(QLabel, "Sidebar", layout="_grid", grid=(1, 0, 2, 1))
                # Content cell
                self.content = self.build(QLabel, "Content", layout="_grid", grid=(1, 1))

        parent = Parent()
        qt.track(parent)

        # Header at (0,0) and (0,1)
        assert_that(parent._grid.itemAtPosition(0, 0).widget()).is_same_as(parent.header)
        assert_that(parent._grid.itemAtPosition(0, 1).widget()).is_same_as(parent.header)
        # Sidebar at (1,0) and (2,0)
        assert_that(parent._grid.itemAtPosition(1, 0).widget()).is_same_as(parent.sidebar)
        assert_that(parent._grid.itemAtPosition(2, 0).widget()).is_same_as(parent.sidebar)
        # Content at (1,1)
        assert_that(parent._grid.itemAtPosition(1, 1).widget()).is_same_as(parent.content)

    def test_layout_false_does_not_add(self, qt: QtDriver) -> None:
        """layout=False does not add widget to any layout."""

        @widget
        class Parent(Widget):
            _existing: QLabel = new("Existing")

            def __setup__(self) -> None:
                self.hidden = self.build(QLabel, "Hidden", layout=False)

        parent = Parent()
        qt.track(parent)

        assert_that(parent.layout().count()).is_equal_to(1)
        assert_that(parent.hidden.text()).is_equal_to("Hidden")

    def test_multiple_widgets_to_same_layout(self, qt: QtDriver) -> None:
        """Multiple build() calls can add to the same layout."""
        from PySide6.QtWidgets import QHBoxLayout

        @widget
        class Parent(Widget):
            _buttons: QHBoxLayout = new()

            def __setup__(self) -> None:
                self.btn1 = self.build(QPushButton, "OK", layout="_buttons")
                self.btn2 = self.build(QPushButton, "Cancel", layout="_buttons")
                self.btn3 = self.build(QPushButton, "Apply", layout="_buttons")

        parent = Parent()
        qt.track(parent)

        assert_that(parent._buttons.count()).is_equal_to(3)
        assert_that(parent._buttons.itemAt(0).widget()).is_same_as(parent.btn1)
        assert_that(parent._buttons.itemAt(1).widget()).is_same_as(parent.btn2)
        assert_that(parent._buttons.itemAt(2).widget()).is_same_as(parent.btn3)

    def test_layout_to_vbox(self, qt: QtDriver) -> None:
        """layout= works with QVBoxLayout."""
        from PySide6.QtWidgets import QVBoxLayout

        @widget
        class Parent(Widget):
            _column: QVBoxLayout = new()

            def __setup__(self) -> None:
                self.top = self.build(QLabel, "Top", layout="_column")
                self.middle = self.build(QLabel, "Middle", layout="_column")
                self.bottom = self.build(QLabel, "Bottom", layout="_column")

        parent = Parent()
        qt.track(parent)

        assert_that(parent._column.count()).is_equal_to(3)
        assert_that(parent._column.itemAt(0).widget()).is_same_as(parent.top)
        assert_that(parent._column.itemAt(1).widget()).is_same_as(parent.middle)
        assert_that(parent._column.itemAt(2).widget()).is_same_as(parent.bottom)

    def test_layout_to_hbox(self, qt: QtDriver) -> None:
        """layout= works with QHBoxLayout."""
        from PySide6.QtWidgets import QHBoxLayout

        @widget
        class Parent(Widget):
            _row: QHBoxLayout = new()

            def __setup__(self) -> None:
                self.left = self.build(QLabel, "Left", layout="_row")
                self.center = self.build(QLabel, "Center", layout="_row")
                self.right = self.build(QLabel, "Right", layout="_row")

        parent = Parent()
        qt.track(parent)

        assert_that(parent._row.count()).is_equal_to(3)
        assert_that(parent._row.itemAt(0).widget()).is_same_as(parent.left)
        assert_that(parent._row.itemAt(1).widget()).is_same_as(parent.center)
        assert_that(parent._row.itemAt(2).widget()).is_same_as(parent.right)

    def test_layout_from_method_after_construction(self, qt: QtDriver) -> None:
        """layout= works when called from a method after construction."""
        from PySide6.QtWidgets import QHBoxLayout

        @widget
        class Parent(Widget):
            _row: QHBoxLayout = new()

            def add_item(self, text: str) -> QLabel:
                return self.build(QLabel, text, layout="_row")

        parent = Parent()
        qt.track(parent)

        # Add items dynamically
        label1 = parent.add_item("Item 1")
        label2 = parent.add_item("Item 2")
        label3 = parent.add_item("Item 3")

        assert_that(parent._row.count()).is_equal_to(3)
        assert_that(parent._row.itemAt(0).widget()).is_same_as(label1)
        assert_that(parent._row.itemAt(1).widget()).is_same_as(label2)
        assert_that(parent._row.itemAt(2).widget()).is_same_as(label3)

    def test_layout_with_other_build_features(self, qt: QtDriver) -> None:
        """layout= works together with other build() features."""
        from PySide6.QtWidgets import QHBoxLayout

        from qtpie import Variable

        @widget
        class Parent(Widget):
            _row: QHBoxLayout = new()
            _enabled: Variable[bool] = new(True)

            def __setup__(self) -> None:
                self.btn = self.build(
                    QPushButton,
                    "Click",
                    layout="_row",
                    enabled="_enabled",
                    clicked="on_click",
                    toolTip="A button",
                )
                self.clicked_count = 0

            def on_click(self) -> None:
                self.clicked_count += 1

        parent = Parent()
        qt.track(parent)

        # In layout
        assert_that(parent._row.count()).is_equal_to(1)
        # Props applied
        assert_that(parent.btn.toolTip()).is_equal_to("A button")
        # Signal connected
        parent.btn.click()
        assert_that(parent.clicked_count).is_equal_to(1)
        # Binding works
        parent._enabled.value = False
        assert_that(parent.btn.isEnabled()).is_false()

    def test_form_layout_without_label(self, qt: QtDriver) -> None:
        """QFormLayout without label= adds widget spanning both columns."""
        from PySide6.QtWidgets import QFormLayout, QLineEdit

        @widget
        class Parent(Widget):
            _form: QFormLayout = new()

            def __setup__(self) -> None:
                self.labeled = self.build(QLineEdit, layout="_form", label="Name:")
                self.spanning = self.build(QLineEdit, layout="_form")  # No label

        parent = Parent()
        qt.track(parent)

        assert_that(parent._form.rowCount()).is_equal_to(2)
        # First row has label
        assert_that(parent._form.labelForField(parent.labeled)).is_not_none()
        # Second row spans (no label widget)
        assert_that(parent._form.labelForField(parent.spanning)).is_none()

    def test_grid_layout_without_position(self, qt: QtDriver) -> None:
        """QGridLayout without grid= adds widget at next available position."""
        from PySide6.QtWidgets import QGridLayout

        @widget
        class Parent(Widget):
            _grid: QGridLayout = new()

            def __setup__(self) -> None:
                self.first = self.build(QLabel, "First", layout="_grid")
                self.second = self.build(QLabel, "Second", layout="_grid")

        parent = Parent()
        qt.track(parent)

        assert_that(parent._grid.count()).is_equal_to(2)
