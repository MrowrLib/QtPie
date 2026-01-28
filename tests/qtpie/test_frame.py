# pyright: reportPrivateUsage=false
# pyright: reportMissingParameterType=false
# pyright: reportUnknownParameterType=false
# pyright: reportUntypedBaseClass=false
# pyright: reportUntypedClassDecorator=false
# pyright: reportUnknownArgumentType=false
# pyright: reportUnknownVariableType=false
"""Tests for @frame decorator and Frame base class.

This tests that Frame (QFrame + WidgetBase) works with the @frame decorator
(alias for @widget) to provide the same declarative features as Widget.
"""

from dataclasses import dataclass

import pytest
from assertpy import assert_that
from qtpy.QtWidgets import QFrame, QLabel, QLineEdit, QPushButton, QSpinBox, QVBoxLayout

from qtpie import Frame, Variable, Widget, frame, new, widget
from qtpie.testing import QtDriver


class TestFrameBasics:
    """Basic Frame functionality."""

    def test_frame_is_qframe(self, qt: QtDriver) -> None:
        """Frame should be a QFrame subclass."""

        @frame
        class TestFrame(Frame):
            pass

        instance = qt.track(TestFrame())
        assert_that(instance).is_instance_of(QFrame)
        assert_that(instance).is_instance_of(Frame)

    def test_frame_with_widgets(self, qt: QtDriver) -> None:
        """Frame should support widget children like Widget does."""

        @frame
        class TestFrame(Frame):
            _label: QLabel = new("Hello")
            _button: QPushButton = new("Click")

        instance = qt.track(TestFrame())

        assert_that(instance._label).is_instance_of(QLabel)
        assert_that(instance._label.text()).is_equal_to("Hello")
        assert_that(instance._button).is_instance_of(QPushButton)
        assert_that(instance._button.text()).is_equal_to("Click")

    def test_frame_with_layout(self, qt: QtDriver) -> None:
        """Frame should support layout configuration."""

        @frame(layout="vertical")
        class TestFrame(Frame):
            _label1: QLabel = new("First")
            _label2: QLabel = new("Second")

        instance = qt.track(TestFrame())

        layout = instance.layout()
        assert layout is not None
        assert_that(layout).is_instance_of(QVBoxLayout)
        assert_that(layout.count()).is_equal_to(2)

    def test_frame_no_layout(self, qt: QtDriver) -> None:
        """Frame with layout=None should not have automatic layout."""

        @frame(layout=None)
        class TestFrame(Frame):
            pass

        instance = qt.track(TestFrame())
        assert_that(instance.layout()).is_none()

    def test_frame_bare_decorator(self, qt: QtDriver) -> None:
        """@frame without parens should work."""

        @frame
        class TestFrame(Frame):
            _label: QLabel = new("Test")

        instance = qt.track(TestFrame())
        assert_that(instance._label.text()).is_equal_to("Test")


class TestFrameProperties:
    """QFrame-specific properties."""

    def test_frame_shape(self, qt: QtDriver) -> None:
        """Frame should support frameShape via decorator kwargs."""

        @frame(frameShape=QFrame.Shape.Box)
        class TestFrame(Frame):
            _label: QLabel = new("Content")

        instance = qt.track(TestFrame())
        assert_that(instance.frameShape()).is_equal_to(QFrame.Shape.Box)

    def test_frame_shadow(self, qt: QtDriver) -> None:
        """Frame should support frameShadow via decorator kwargs."""

        @frame(frameShape=QFrame.Shape.Panel, frameShadow=QFrame.Shadow.Raised)
        class TestFrame(Frame):
            _label: QLabel = new("Content")

        instance = qt.track(TestFrame())
        assert_that(instance.frameShape()).is_equal_to(QFrame.Shape.Panel)
        assert_that(instance.frameShadow()).is_equal_to(QFrame.Shadow.Raised)

    def test_frame_line_width(self, qt: QtDriver) -> None:
        """Frame should support lineWidth via decorator kwargs."""

        @frame(frameShape=QFrame.Shape.Box, lineWidth=3)
        class TestFrame(Frame):
            _label: QLabel = new("Content")

        instance = qt.track(TestFrame())
        assert_that(instance.lineWidth()).is_equal_to(3)

    def test_frame_styled_panel(self, qt: QtDriver) -> None:
        """Frame with StyledPanel shape."""

        @frame(frameShape=QFrame.Shape.StyledPanel)
        class TestFrame(Frame):
            _label: QLabel = new("Styled content")

        instance = qt.track(TestFrame())
        assert_that(instance.frameShape()).is_equal_to(QFrame.Shape.StyledPanel)


class TestFrameVariables:
    """Frame with Variable support."""

    def test_frame_with_variable(self, qt: QtDriver) -> None:
        """Frame should support Variable fields."""

        @frame
        class TestFrame(Frame):
            _count: Variable[int] = new(42)

        instance = qt.track(TestFrame())

        assert_that(instance._count.value).is_equal_to(42)
        instance._count.value = 100
        assert_that(instance._count.value).is_equal_to(100)

    def test_frame_with_variable_widget(self, qt: QtDriver) -> None:
        """Frame should support Variable[T, W] with auto-created widget."""

        @frame
        class TestFrame(Frame):
            _name: Variable[str, QLineEdit] = new("default")(placeholderText="Enter name")

        instance = qt.track(TestFrame())

        assert_that(instance._name.value).is_equal_to("default")
        assert_that(instance._name.widget).is_instance_of(QLineEdit)
        assert_that(instance._name.widget.placeholderText()).is_equal_to("Enter name")

    def test_frame_variable_binding(self, qt: QtDriver) -> None:
        """Frame should support binding Variables to widgets."""

        @frame
        class TestFrame(Frame):
            _message: Variable[str] = new("Hello")
            _label: QLabel = new(bind="{_message}")

        instance = qt.track(TestFrame())

        assert_that(instance._label.text()).is_equal_to("Hello")
        instance._message.value = "Updated"
        assert_that(instance._label.text()).is_equal_to("Updated")


class TestFrameRecord:
    """Frame with record type (Frame[T])."""

    def test_frame_with_record_type(self, qt: QtDriver) -> None:
        """Frame[T] should support record type like Widget[T]."""

        @dataclass
        class Person:
            name: str = ""
            age: int = 0

        @frame
        class PersonFrame(Frame[Person]):
            pass

        instance = qt.track(PersonFrame())
        instance.record = Person("Alice", 30)

        assert_that(instance.record.name).is_equal_to("Alice")
        assert_that(instance.record.age).is_equal_to(30)

    def test_frame_record_auto_binding(self, qt: QtDriver) -> None:
        """Frame[T] should auto-bind fields named same as record properties."""

        @dataclass
        class Person:
            name: str = ""
            age: int = 0

        @frame(record=Person("Bob", 25))
        class PersonFrame(Frame[Person]):
            name: QLineEdit = new()
            age: QSpinBox = new()

        instance = qt.track(PersonFrame())

        # Fields should be bound to record
        assert_that(instance.name.text()).is_equal_to("Bob")
        assert_that(instance.age.value()).is_equal_to(25)

        # Changing record should update fields
        instance.record.name = "Charlie"
        assert_that(instance.name.text()).is_equal_to("Charlie")

    def test_frame_record_dirty_tracking(self, qt: QtDriver) -> None:
        """Frame should support dirty tracking from WidgetBase."""

        @dataclass
        class Person:
            name: str = ""

        @frame(record=Person("Original"))
        class PersonFrame(Frame[Person]):
            name: QLineEdit = new()

        instance = qt.track(PersonFrame())

        assert_that(instance.is_dirty.get()).is_false()
        instance.record.name = "Changed"
        assert_that(instance.is_dirty.get()).is_true()

        instance.reset_dirty()
        assert_that(instance.is_dirty.get()).is_false()


class TestFrameSetup:
    """Frame lifecycle hooks."""

    def test_frame_setup_hook(self, qt: QtDriver) -> None:
        """Frame should call __setup__ after initialization."""
        setup_called: list[bool] = []

        @frame
        class TestFrame(Frame):
            _label: QLabel = new("Before")

            def __setup__(self) -> None:
                setup_called.append(True)
                self._label.setText("After")

        instance = qt.track(TestFrame())

        assert_that(setup_called).is_length(1)
        assert_that(instance._label.text()).is_equal_to("After")


class TestFrameNesting:
    """Frame used as child component."""

    def test_frame_in_widget(self, qt: QtDriver) -> None:
        """Frame should work as a child component in a Widget."""

        @frame(frameShape=QFrame.Shape.Box)
        class Card(Frame):
            _title: QLabel = new("Card Title")
            _content: QLabel = new("Card Content")

        @widget
        class MyWidget(Widget):
            _header: QLabel = new("Header")
            _card: Card = new()
            _footer: QLabel = new("Footer")

        instance = qt.track(MyWidget())

        assert_that(instance._card).is_instance_of(Card)
        assert_that(instance._card).is_instance_of(QFrame)
        assert_that(instance._card._title.text()).is_equal_to("Card Title")
        assert_that(instance._card._content.text()).is_equal_to("Card Content")
        assert_that(instance._card.frameShape()).is_equal_to(QFrame.Shape.Box)

    def test_nested_frames(self, qt: QtDriver) -> None:
        """Frames should be nestable."""

        @frame(frameShape=QFrame.Shape.Box)
        class InnerFrame(Frame):
            _inner_label: QLabel = new("Inner")

        @frame(frameShape=QFrame.Shape.Panel)
        class OuterFrame(Frame):
            _outer_label: QLabel = new("Outer")
            _inner: InnerFrame = new()

        instance = qt.track(OuterFrame())

        assert_that(instance.frameShape()).is_equal_to(QFrame.Shape.Panel)
        assert_that(instance._inner.frameShape()).is_equal_to(QFrame.Shape.Box)
        assert_that(instance._outer_label.text()).is_equal_to("Outer")
        assert_that(instance._inner._inner_label.text()).is_equal_to("Inner")


class TestFrameSignals:
    """Frame signal connections."""

    def test_frame_signal_connection(self, qt: QtDriver) -> None:
        """Frame should support signal connections like Widget."""
        clicked_count: list[int] = []

        @frame
        class TestFrame(Frame):
            _button: QPushButton = new("Click", clicked="on_click")

            def on_click(self) -> None:
                clicked_count.append(1)

        instance = qt.track(TestFrame())
        instance._button.click()

        assert_that(clicked_count).is_length(1)


class TestFrameObjectName:
    """Frame objectName and CSS classes."""

    def test_frame_object_name(self, qt: QtDriver) -> None:
        """Frame should support name= for objectName."""

        @frame(name="my-card")
        class TestFrame(Frame):
            pass

        instance = qt.track(TestFrame())
        assert_that(instance.objectName()).is_equal_to("my-card")

    def test_frame_css_classes(self, qt: QtDriver) -> None:
        """Frame should support classes= for CSS classes."""

        @frame(classes=["card", "elevated"])
        class TestFrame(Frame):
            pass

        instance = qt.track(TestFrame())
        # CSS classes are stored in property()
        classes = instance.property("class")
        assert_that(classes).contains("card")
        assert_that(classes).contains("elevated")

    def test_frame_default_object_name(self, qt: QtDriver) -> None:
        """Frame without name= should use class name as objectName."""

        @frame
        class MyCustomFrame(Frame):
            pass

        instance = qt.track(MyCustomFrame())
        assert_that(instance.objectName()).is_equal_to("MyCustomFrame")


class TestFrameValidation:
    """Frame validation support."""

    def test_frame_is_valid(self, qt: QtDriver) -> None:
        """Frame should support is_valid from WidgetBase."""

        @frame
        class TestFrame(Frame):
            _name: Variable[str] = new("")

            def __setup__(self) -> None:
                self.add_validator("_name", "required", lambda v: None if v else "Name required")

        instance = qt.track(TestFrame())

        # Empty name should be invalid
        assert_that(instance.is_valid.get()).is_false()

        # Set name should be valid
        instance._name.value = "Test"
        assert_that(instance.is_valid.get()).is_true()

    def test_frame_validation_errors(self, qt: QtDriver) -> None:
        """Frame should expose validation_error_messages."""

        @frame
        class TestFrame(Frame):
            _name: Variable[str] = new("")

            def __setup__(self) -> None:
                self.add_validator("_name", "required", lambda v: None if v else "Name is required")

        instance = qt.track(TestFrame())

        errors = instance.validation_error_messages.get()
        assert_that(errors).contains("Name is required")


class TestFrameRequiresDecorator:
    """Frame should require @frame decorator."""

    def test_frame_without_decorator_raises(self, qt: QtDriver) -> None:
        """Instantiating Frame without @frame should raise TypeError."""

        class UndecoratedFrame(Frame):
            pass

        with pytest.raises(TypeError, match="must be decorated with @frame"):
            UndecoratedFrame()


class TestFrameChildWidgetRecordPropagation:
    """Frame should propagate records to child widgets the same as Widget does."""

    def test_frame_with_same_record_type_as_child(self, qt: QtDriver) -> None:
        """Test that Frame[T] propagates record to child Widget[T] with same T.

        This is simpler - just test same-type propagation works for Frame.
        """
        from dataclasses import dataclass, field

        @dataclass
        class Collection:
            name: str = ""
            items: list[str] = field(default_factory=list)

        # Child widget with same record type
        @widget
        class CollectionWidget(Widget[Collection]):
            _name_label: QLabel = new(bind="Name: {name}")
            _item_count: QLabel = new(bind="Items: {len(items)}")

        # Test with Widget parent - should work
        @widget
        class ParentAsWidget(Widget[Collection]):
            _header: QLabel = new("Widget Parent")
            _collection: CollectionWidget

        # Test with Frame parent - should also work
        @frame
        class ParentAsFrame(Frame[Collection]):
            _header: QLabel = new("Frame Parent")
            _collection: CollectionWidget

        # Create test data
        collection = Collection(name="My Collection", items=["a", "b", "c"])

        # Test Widget parent
        widget_parent = qt.track(ParentAsWidget())
        widget_parent.record = collection
        assert_that(widget_parent._collection._name_label.text()).is_equal_to("Name: My Collection")
        assert_that(widget_parent._collection._item_count.text()).is_equal_to("Items: 3")

        # Test Frame parent - this should also work
        frame_parent = qt.track(ParentAsFrame())
        frame_parent.record = collection
        # THIS IS THE BUG: Frame doesn't propagate record to children
        assert_that(frame_parent._collection._name_label.text()).is_equal_to("Name: My Collection")
        assert_that(frame_parent._collection._item_count.text()).is_equal_to("Items: 3")

    def test_frame_child_auto_binds_by_field_name(self, qt: QtDriver) -> None:
        """Test auto-bind by field name: _collection binds to parent.record.collection.

        When a Frame[Workspace] has a child Widget[Collection] field named '_collection',
        the child should auto-bind to parent.record.collection.
        """
        from dataclasses import dataclass, field

        @dataclass
        class Collection:
            name: str = ""
            items: list[str] = field(default_factory=list)

        @dataclass
        class Workspace:
            name: str = ""
            collection: Collection | None = None

        # Child widget expects Collection record
        @widget
        class CollectionWidget(Widget[Collection | None]):
            _name_label: QLabel = new(bind="Name: {name}")
            _item_count: QLabel = new(bind="Items: {len(items)}")

        # Test with Widget parent - should work
        @widget
        class ParentAsWidget(Widget[Workspace]):
            _header: QLabel = new(bind="{name}")
            # Field name '_collection' matches parent.record.collection
            _collection: CollectionWidget

        # Test with Frame parent - should also work
        @frame
        class ParentAsFrame(Frame[Workspace]):
            _header: QLabel = new(bind="{name}")
            # Field name '_collection' matches parent.record.collection
            _collection: CollectionWidget

        # Create test data
        collection = Collection(name="My Collection", items=["a", "b", "c"])
        workspace = Workspace(name="Test Workspace", collection=collection)

        # Test Widget parent - auto-bind by field name works
        widget_parent = qt.track(ParentAsWidget())
        widget_parent.record = workspace
        assert_that(widget_parent._header.text()).is_equal_to("Test Workspace")
        # Child should have received collection record via field name auto-bind
        assert_that(widget_parent._collection._name_label.text()).is_equal_to("Name: My Collection")
        assert_that(widget_parent._collection._item_count.text()).is_equal_to("Items: 3")

        # Test Frame parent - auto-bind by field name should also work
        frame_parent = qt.track(ParentAsFrame())
        frame_parent.record = workspace
        assert_that(frame_parent._header.text()).is_equal_to("Test Workspace")
        # Child should have received collection record via field name auto-bind
        # THIS MIGHT BE THE BUG - Frame may not support field-name auto-bind
        assert_that(frame_parent._collection._name_label.text()).is_equal_to("Name: My Collection")
        assert_that(frame_parent._collection._item_count.text()).is_equal_to("Items: 3")
