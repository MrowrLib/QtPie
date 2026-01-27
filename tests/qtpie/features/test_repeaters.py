# pyright: reportPrivateUsage=false
# pyright: reportMissingParameterType=false
# pyright: reportUnknownParameterType=false
# pyright: reportUntypedBaseClass=false
# pyright: reportUntypedClassDecorator=false
# pyright: reportUnknownArgumentType=false
# pyright: reportUnknownMemberType=false
# pyright: reportCallIssue=false
# pyright: reportAttributeAccessIssue=false
# pyright: reportArgumentType=false
# pyright: reportIndexIssue=false
# pyright: reportUnknownLambdaType=false
# pyright: reportOptionalMemberAccess=false
"""Tests for widget repeaters across Widget, Window, and App.

Tests list, dict, and set repeaters (widget generation from collections).
Menu is excluded as it uses QAction repeaters, not QWidget repeaters.
"""

from dataclasses import dataclass

import pytest
from assertpy import assert_that
from PySide6.QtWidgets import QLabel, QLineEdit, QSpinBox

from qtpie import DictWidgetRepeater, SetWidgetRepeater, Variable, WidgetRepeater, new
from qtpie.testing import QtDriver

from .conftest import WIDGET_CLASS_TYPES, create_and_track


@dataclass
class Dog:
    """Test dataclass for object binding."""

    name: str
    age: int = 0


# =============================================================================
# List Repeater Basic
# =============================================================================


@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestListRepeaterBasic:
    """Basic list repeater functionality."""

    def test_creates_widgets_for_initial_items(self, base_class, decorator, qt: QtDriver) -> None:
        """Variable[list[T], W] creates widgets for initial items."""

        @decorator
        class TestClass(base_class):
            _items: Variable[list[str], QLabel] = new(["a", "b", "c"])  # type: ignore[type-arg]

        instance = create_and_track(qt, TestClass, base_class)
        repeater: WidgetRepeater[str] = instance._items.widget
        assert_that(repeater.widget_count()).is_equal_to(3)

    def test_empty_list_no_widgets(self, base_class, decorator, qt: QtDriver) -> None:
        """Empty list creates no widgets."""

        @decorator
        class TestClass(base_class):
            _items: Variable[list[str], QLabel] = new([])  # type: ignore[type-arg]

        instance = create_and_track(qt, TestClass, base_class)
        repeater: WidgetRepeater[str] = instance._items.widget
        assert_that(repeater.widget_count()).is_equal_to(0)

    def test_widgets_are_correct_type(self, base_class, decorator, qt: QtDriver) -> None:
        """Repeater creates widgets of specified type."""

        @decorator
        class TestClass(base_class):
            _items: Variable[list[int], QSpinBox] = new([1, 2])  # type: ignore[type-arg]

        instance = create_and_track(qt, TestClass, base_class)
        repeater: WidgetRepeater[int] = instance._items.widget
        assert_that(repeater.widget_at(0)).is_instance_of(QSpinBox)
        assert_that(repeater.widget_at(1)).is_instance_of(QSpinBox)

    def test_primitives_show_values(self, base_class, decorator, qt: QtDriver) -> None:
        """Primitive values display in widgets."""

        @decorator
        class TestClass(base_class):
            _items: Variable[list[int], QLabel] = new([10, 20, 30])  # type: ignore[type-arg]

        instance = create_and_track(qt, TestClass, base_class)
        repeater: WidgetRepeater[int] = instance._items.widget
        assert_that(repeater.widget_at(0).text()).is_equal_to("10")
        assert_that(repeater.widget_at(1).text()).is_equal_to("20")
        assert_that(repeater.widget_at(2).text()).is_equal_to("30")


# =============================================================================
# List Repeater Granular Sync
# =============================================================================


@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestListRepeaterSync:
    """List repeater granular sync operations."""

    def test_append_creates_widget(self, base_class, decorator, qt: QtDriver) -> None:
        """Appending to list adds widget."""

        @decorator
        class TestClass(base_class):
            _items: Variable[list[str], QLabel] = new(["a", "b"])  # type: ignore[type-arg]

        instance = create_and_track(qt, TestClass, base_class)
        repeater: WidgetRepeater[str] = instance._items.widget
        assert_that(repeater.widget_count()).is_equal_to(2)

        instance._items.observable.append("c")
        assert_that(repeater.widget_count()).is_equal_to(3)

    def test_insert_creates_widget_at_index(self, base_class, decorator, qt: QtDriver) -> None:
        """Inserting at index adds widget at position."""

        @decorator
        class TestClass(base_class):
            _items: Variable[list[str], QLabel] = new(["a", "c"])  # type: ignore[type-arg]

        instance = create_and_track(qt, TestClass, base_class)
        repeater: WidgetRepeater[str] = instance._items.widget

        instance._items.observable.insert(1, "b")
        assert_that(repeater.widget_count()).is_equal_to(3)
        assert_that(repeater.widget_at(1).text()).is_equal_to("b")

    def test_remove_destroys_widget(self, base_class, decorator, qt: QtDriver) -> None:
        """Removing from list removes widget."""

        @decorator
        class TestClass(base_class):
            _items: Variable[list[str], QLabel] = new(["a", "b", "c"])  # type: ignore[type-arg]

        instance = create_and_track(qt, TestClass, base_class)
        repeater: WidgetRepeater[str] = instance._items.widget
        assert_that(repeater.widget_count()).is_equal_to(3)

        instance._items.observable.remove("b")
        assert_that(repeater.widget_count()).is_equal_to(2)

    def test_clear_destroys_all(self, base_class, decorator, qt: QtDriver) -> None:
        """Clearing list removes all widgets."""

        @decorator
        class TestClass(base_class):
            _items: Variable[list[str], QLabel] = new(["a", "b", "c"])  # type: ignore[type-arg]

        instance = create_and_track(qt, TestClass, base_class)
        repeater: WidgetRepeater[str] = instance._items.widget
        assert_that(repeater.widget_count()).is_equal_to(3)

        instance._items.observable.clear()
        assert_that(repeater.widget_count()).is_equal_to(0)

    def test_replace_updates_widget(self, base_class, decorator, qt: QtDriver) -> None:
        """Replacing item updates widget value."""

        @decorator
        class TestClass(base_class):
            _items: Variable[list[str], QLabel] = new(["old"])  # type: ignore[type-arg]

        instance = create_and_track(qt, TestClass, base_class)
        repeater: WidgetRepeater[str] = instance._items.widget
        assert_that(repeater.widget_at(0).text()).is_equal_to("old")

        instance._items.observable[0] = "new"
        assert_that(repeater.widget_at(0).text()).is_equal_to("new")


# =============================================================================
# List Repeater Format Expressions
# =============================================================================


@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestListRepeaterFormat:
    """List repeater format expressions."""

    def test_format_self(self, base_class, decorator, qt: QtDriver) -> None:
        """{#self} shows item value."""

        @decorator
        class TestClass(base_class):
            _items: Variable[list[int], QLabel] = new([10, 20])(bind="{#self}")  # type: ignore[type-arg]

        instance = create_and_track(qt, TestClass, base_class)
        repeater: WidgetRepeater[int] = instance._items.widget
        assert_that(repeater.widget_at(0).text()).is_equal_to("10")
        assert_that(repeater.widget_at(1).text()).is_equal_to("20")

    def test_format_index(self, base_class, decorator, qt: QtDriver) -> None:
        """{#index} shows item index."""

        @decorator
        class TestClass(base_class):
            _items: Variable[list[str], QLabel] = new(["a", "b", "c"])(bind="{#index}")  # type: ignore[type-arg]

        instance = create_and_track(qt, TestClass, base_class)
        repeater: WidgetRepeater[str] = instance._items.widget
        assert_that(repeater.widget_at(0).text()).is_equal_to("0")
        assert_that(repeater.widget_at(1).text()).is_equal_to("1")
        assert_that(repeater.widget_at(2).text()).is_equal_to("2")

    def test_format_index_and_self(self, base_class, decorator, qt: QtDriver) -> None:
        """Combined {#index} and {#self}."""

        @decorator
        class TestClass(base_class):
            _items: Variable[list[str], QLabel] = new(["a", "b"])(bind="[{#index}] {#self}")  # type: ignore[type-arg]

        instance = create_and_track(qt, TestClass, base_class)
        repeater: WidgetRepeater[str] = instance._items.widget
        assert_that(repeater.widget_at(0).text()).is_equal_to("[0] a")
        assert_that(repeater.widget_at(1).text()).is_equal_to("[1] b")

    def test_format_object_property(self, base_class, decorator, qt: QtDriver) -> None:
        """Object property binding {name}."""

        @decorator
        class TestClass(base_class):
            _dogs: Variable[list[Dog], QLabel] = new([Dog("Fido", 3), Dog("Rex", 5)])(bind="{name}")  # type: ignore[type-arg]

        instance = create_and_track(qt, TestClass, base_class)
        repeater: WidgetRepeater[Dog] = instance._dogs.widget
        assert_that(repeater.widget_at(0).text()).is_equal_to("Fido")
        assert_that(repeater.widget_at(1).text()).is_equal_to("Rex")

    def test_format_multiple_properties(self, base_class, decorator, qt: QtDriver) -> None:
        """Multiple object properties in format."""

        @decorator
        class TestClass(base_class):
            _dogs: Variable[list[Dog], QLabel] = new([Dog("Fido", 3)])(bind="{name} is {age}")  # type: ignore[type-arg]

        instance = create_and_track(qt, TestClass, base_class)
        repeater: WidgetRepeater[Dog] = instance._dogs.widget
        assert_that(repeater.widget_at(0).text()).is_equal_to("Fido is 3")


# =============================================================================
# List Repeater Two-Way Binding
# =============================================================================


@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestListRepeaterTwoWay:
    """List repeater two-way binding."""

    def test_edit_widget_updates_list(self, base_class, decorator, qt: QtDriver) -> None:
        """Editing widget updates list item."""

        @decorator
        class TestClass(base_class):
            _items: Variable[list[str], QLineEdit] = new(["hello"])  # type: ignore[type-arg]

        instance = create_and_track(qt, TestClass, base_class)
        repeater: WidgetRepeater[str] = instance._items.widget

        edit = repeater.widget_at(0)
        edit.setText("world")
        assert_that(instance._items.observable[0]).is_equal_to("world")

    def test_list_change_updates_widget(self, base_class, decorator, qt: QtDriver) -> None:
        """Changing list updates widget."""

        @decorator
        class TestClass(base_class):
            _items: Variable[list[str], QLabel] = new(["hello"])  # type: ignore[type-arg]

        instance = create_and_track(qt, TestClass, base_class)
        repeater: WidgetRepeater[str] = instance._items.widget

        instance._items.observable[0] = "world"
        assert_that(repeater.widget_at(0).text()).is_equal_to("world")


# =============================================================================
# Dict Repeater Basic
# =============================================================================


@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestDictRepeaterBasic:
    """Basic dict repeater functionality."""

    def test_creates_widgets_for_items(self, base_class, decorator, qt: QtDriver) -> None:
        """Variable[dict[K, V], W] creates widgets for items."""

        @decorator
        class TestClass(base_class):
            _items: Variable[dict[str, int]] = new({"a": 1, "b": 2})
            _labels: list[QLabel] = new(bind="_items")

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance._labels).is_instance_of(DictWidgetRepeater)
        assert_that(instance._labels.widget_count()).is_equal_to(2)

    def test_empty_dict_no_widgets(self, base_class, decorator, qt: QtDriver) -> None:
        """Empty dict creates no widgets."""

        @decorator
        class TestClass(base_class):
            _items: Variable[dict[str, int]] = new({})
            _labels: list[QLabel] = new(bind="_items")

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance._labels.widget_count()).is_equal_to(0)

    def test_setitem_creates_widget(self, base_class, decorator, qt: QtDriver) -> None:
        """Setting new key creates widget."""

        @decorator
        class TestClass(base_class):
            _items: Variable[dict[str, int]] = new({"a": 1})
            _labels: list[QLabel] = new(bind="_items", format="{#key}={#value}")

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance._labels.widget_count()).is_equal_to(1)

        instance._items["b"] = 2
        assert_that(instance._labels.widget_count()).is_equal_to(2)

    def test_delitem_destroys_widget(self, base_class, decorator, qt: QtDriver) -> None:
        """Deleting key removes widget."""

        @decorator
        class TestClass(base_class):
            _items: Variable[dict[str, int]] = new({"a": 1, "b": 2})
            _labels: list[QLabel] = new(bind="_items")

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance._labels.widget_count()).is_equal_to(2)

        del instance._items.observable["a"]
        assert_that(instance._labels.widget_count()).is_equal_to(1)


# =============================================================================
# Dict Repeater Format Expressions
# =============================================================================


@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestDictRepeaterFormat:
    """Dict repeater format expressions."""

    def test_format_key_value(self, base_class, decorator, qt: QtDriver) -> None:
        """{#key} and {#value} placeholders."""

        @decorator
        class TestClass(base_class):
            _items: Variable[dict[str, int]] = new({"Alice": 100})
            _labels: list[QLabel] = new(bind="_items", format="{#key}: {#value}")

        instance = create_and_track(qt, TestClass, base_class)
        label = instance._labels.widget_for_key("Alice")
        assert_that(label).is_not_none()
        assert_that(label.text()).is_equal_to("Alice: 100")

    def test_format_value_property(self, base_class, decorator, qt: QtDriver) -> None:
        """Object value properties in format."""

        @decorator
        class TestClass(base_class):
            _dogs: Variable[dict[str, Dog]] = new({"fido": Dog("Fido", 3)})
            _labels: list[QLabel] = new(bind="_dogs", format="{#key}: {name} is {age}")

        instance = create_and_track(qt, TestClass, base_class)
        label = instance._labels.widget_for_key("fido")
        assert_that(label.text()).is_equal_to("fido: Fido is 3")


# =============================================================================
# Set Repeater Basic (Variable[set[T], W] syntax)
# =============================================================================


@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestSetRepeaterBasic:
    """Basic set repeater functionality using Variable[set[T], W] syntax."""

    def test_creates_widgets_for_items(self, base_class, decorator, qt: QtDriver) -> None:
        """Variable[set[T], W] creates widgets for items."""

        @decorator
        class TestClass(base_class):
            _items: Variable[set[str], QLabel] = new({"a", "b", "c"})  # type: ignore[type-arg]

        instance = create_and_track(qt, TestClass, base_class)
        repeater: SetWidgetRepeater[str] = instance._items.widget
        assert_that(repeater.widget_count()).is_equal_to(3)

    def test_empty_set_no_widgets(self, base_class, decorator, qt: QtDriver) -> None:
        """Empty set creates no widgets."""

        @decorator
        class TestClass(base_class):
            _items: Variable[set[str], QLabel] = new(set())  # type: ignore[type-arg]

        instance = create_and_track(qt, TestClass, base_class)
        repeater: SetWidgetRepeater[str] = instance._items.widget
        assert_that(repeater.widget_count()).is_equal_to(0)

    def test_add_creates_widget(self, base_class, decorator, qt: QtDriver) -> None:
        """Adding to set creates widget."""

        @decorator
        class TestClass(base_class):
            _items: Variable[set[str], QLabel] = new({"a"})  # type: ignore[type-arg]

        instance = create_and_track(qt, TestClass, base_class)
        repeater: SetWidgetRepeater[str] = instance._items.widget
        assert_that(repeater.widget_count()).is_equal_to(1)

        instance._items.observable.add("b")
        assert_that(repeater.widget_count()).is_equal_to(2)

    def test_discard_destroys_widget(self, base_class, decorator, qt: QtDriver) -> None:
        """Discarding from set removes widget."""

        @decorator
        class TestClass(base_class):
            _items: Variable[set[str], QLabel] = new({"a", "b"})  # type: ignore[type-arg]

        instance = create_and_track(qt, TestClass, base_class)
        repeater: SetWidgetRepeater[str] = instance._items.widget
        assert_that(repeater.widget_count()).is_equal_to(2)

        instance._items.observable.discard("a")
        assert_that(repeater.widget_count()).is_equal_to(1)


# =============================================================================
# Set Repeater Format
# =============================================================================


@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestSetRepeaterFormat:
    """Set repeater format expressions."""

    def test_format_self(self, base_class, decorator, qt: QtDriver) -> None:
        """{#self} shows item value via bind=."""

        @decorator
        class TestClass(base_class):
            _items: Variable[set[str], QLabel] = new({"hello"})(bind="{#self}")  # type: ignore[type-arg]

        instance = create_and_track(qt, TestClass, base_class)
        repeater: SetWidgetRepeater[str] = instance._items.widget
        # Set order is not guaranteed, so just check count
        assert_that(repeater.widget_count()).is_equal_to(1)


# =============================================================================
# list[QWidget] = new(bind=...) Syntax
# =============================================================================


@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestListWidgetBindSyntax:
    """list[QWidget] = new(bind=...) syntax."""

    def test_list_qlabel_bound_to_list_variable(self, base_class, decorator, qt: QtDriver) -> None:
        """list[QLabel] = new(bind='_items') creates repeater."""

        @decorator
        class TestClass(base_class):
            _items: Variable[list[str]] = new(["a", "b"])
            _labels: list[QLabel] = new(bind="_items")

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance._labels).is_instance_of(WidgetRepeater)
        assert_that(instance._labels.widget_count()).is_equal_to(2)

    def test_list_qlabel_with_format_string(self, base_class, decorator, qt: QtDriver) -> None:
        """list[QLabel] with format= template."""

        @decorator
        class TestClass(base_class):
            _dogs: Variable[list[Dog]] = new([Dog("Fido", 3)])
            _labels: list[QLabel] = new(bind="_dogs", format="{name}: {age}")

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance._labels.widget_at(0).text()).is_equal_to("Fido: 3")

    def test_list_qlabel_syncs_with_variable(self, base_class, decorator, qt: QtDriver) -> None:
        """list[QLabel] syncs when bound variable changes."""

        @decorator
        class TestClass(base_class):
            _items: Variable[list[str]] = new(["a"])
            _labels: list[QLabel] = new(bind="_items")

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance._labels.widget_count()).is_equal_to(1)

        instance._items.append("b")
        assert_that(instance._labels.widget_count()).is_equal_to(2)


# =============================================================================
# Widget Kwargs Applied to Repeater Items
# =============================================================================


@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestRepeaterWidgetKwargs:
    """Widget kwargs applied to each repeater item."""

    def test_kwargs_applied_to_initial_items(self, base_class, decorator, qt: QtDriver) -> None:
        """Widget kwargs applied to initial items."""

        @decorator
        class TestClass(base_class):
            _items: Variable[list[str], QLineEdit] = new(["a", "b"])(maxLength=5)  # type: ignore[type-arg]

        instance = create_and_track(qt, TestClass, base_class)
        repeater: WidgetRepeater[str] = instance._items.widget

        assert_that(repeater.widget_at(0).maxLength()).is_equal_to(5)
        assert_that(repeater.widget_at(1).maxLength()).is_equal_to(5)

    def test_kwargs_applied_to_new_items(self, base_class, decorator, qt: QtDriver) -> None:
        """Widget kwargs applied to dynamically added items."""

        @decorator
        class TestClass(base_class):
            _items: Variable[list[str], QLineEdit] = new([])(maxLength=10)  # type: ignore[type-arg]

        instance = create_and_track(qt, TestClass, base_class)
        repeater: WidgetRepeater[str] = instance._items.widget

        instance._items.append("new")
        assert_that(repeater.widget_at(0).maxLength()).is_equal_to(10)


# =============================================================================
# list[QWidget] Bound to Record Property (record set later)
# =============================================================================


@dataclass
class Response:
    """HTTP response for testing record binding."""

    status_code: int
    headers: dict[str, str]


@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestListWidgetRecordBinding:
    """list[QWidget] = new(bind="record_property") when record is set later."""

    def test_list_qlabel_bound_to_record_dict_property(self, base_class, decorator, qt: QtDriver) -> None:
        """list[QLabel] bound to record's dict property updates when record is set."""

        @decorator
        class TestClass(base_class[Response]):
            _headers: list[QLabel] = new(bind="headers", format="{#key}: {#value}")

        instance = create_and_track(qt, TestClass, base_class)

        # Record not set yet - should have no widgets (or NewField)
        # Now set the record
        instance.record = Response(200, {"Content-Type": "application/json", "Accept": "text/html"})

        # After setting record, list widget should have items
        assert_that(instance._headers.widget_count()).is_equal_to(2)

    def test_list_qlabel_in_child_widget_via_variable_binding(self, base_class, decorator, qt: QtDriver) -> None:
        """list[QLabel] in child Widget[T] works when parent binds via Variable."""
        from qtpie import Widget, widget

        # Child widget with list[QLabel] bound to record's dict property
        @widget
        class ChildWidget(Widget[Response]):
            _headers: list[QLabel] = new(bind="headers", format="{#key}: {#value}")

        # Parent widget with Variable[Response | None] that binds to child's record
        @widget
        class ParentWidget(Widget):
            response: Variable[Response | None] = new(None)
            _child: ChildWidget = new(bind="response")

        parent = create_and_track(qt, ParentWidget, Widget)

        # Now set the response Variable
        parent.response = Response(200, {"Content-Type": "application/json", "Accept": "text/html"})

        # After setting the Variable's value, the list widget should be created with items
        assert_that(parent._child._headers.widget_count()).is_equal_to(2)

    def test_list_qlabel_in_grandchild_widget_via_variable_binding(self, base_class, decorator, qt: QtDriver) -> None:
        """list[QLabel] in grandchild Widget[T] works when grandparent binds via Variable.

        This tests the exact scenario from the Forc sample app:
        - Grandparent has: response: Variable[Response | None] = new(None)
        - Parent is: ResponseViewerWidget(Widget[Response]) with bare child annotation
        - Child is: ResponseHeadersTabContent(Widget[Response]) with list[QLabel]
        """
        from qtpie import Widget, widget

        # Grandchild widget with list[QLabel] bound to record's dict property
        @widget
        class GrandchildWidget(Widget[Response]):
            _headers: list[QLabel] = new(bind="headers", format="{#key}: {#value}")

        # Child widget (matches ResponseViewerWidget) with:
        # 1. A bare annotation to grandchild (auto-record-bind to child.record)
        # 2. Its own list[QLabel] bound to record
        @widget
        class ChildWidget(Widget[Response]):
            _grandchild: GrandchildWidget  # Bare annotation - auto-binds to record
            _headers: list[QLabel] = new(bind="headers", format="{#key}: {#value}")

        # Grandparent widget with Variable[Response | None] that binds to child's record
        @widget
        class GrandparentWidget(Widget):
            response: Variable[Response | None] = new(None)
            _child: ChildWidget = new(bind="response")

        grandparent = create_and_track(qt, GrandparentWidget, Widget)

        # Now set the response Variable
        grandparent.response = Response(200, {"Content-Type": "application/json", "Accept": "text/html"})

        # After setting the Variable's value, all levels should have list widgets with items
        # Level 1: Child's own list widget
        assert_that(grandparent._child._headers.widget_count()).is_equal_to(2)
        # Level 2: Grandchild's list widget
        assert_that(grandparent._child._grandchild._headers.widget_count()).is_equal_to(2)

    def test_list_qlabel_forc_exact_structure(self, base_class, decorator, qt: QtDriver) -> None:
        """Exact match of Forc app structure where list[QLabel] should work."""
        from qtpy.QtCore import Qt
        from qtpy.QtWidgets import QSplitter

        from qtpie import Widget, widget

        # ResponseHeadersTabContent equivalent
        @widget(title="Headers")
        class ResponseHeadersTabContent(Widget[Response]):
            _headers_label: QLabel = new(bind="{headers}")  # Format string binding works
            _label_above: QLabel = new("ABOVE")
            _headers_xxx: list[QLabel] = new(bind="headers", format="HEADER: {#key}: {#value}")
            _label_below: QLabel = new("BELOW")

        # ResponseViewerWidget equivalent - Widget[Response] with nested Widget[Response]
        @widget
        class ResponseViewerWidget(Widget[Response]):
            _headers_outside_of_tab: ResponseHeadersTabContent  # Bare annotation
            _headers_xxx: list[QLabel] = new(bind="headers", format="HEADER: {#key}: {#value}")

        # RequestWidget equivalent - Widget with Variable[Response | None] and splitter
        @widget
        class RequestWidget(Widget):
            response: Variable[Response | None] = new(None)
            _splitter: QSplitter = new(Qt.Orientation.Horizontal)
            _response: ResponseViewerWidget = new(bind="response", splitter="_splitter")

        request_widget = create_and_track(qt, RequestWidget, Widget)

        # Set response
        request_widget.response = Response(200, {"Content-Type": "application/json", "Accept": "text/html"})

        # Verify all levels work
        # Direct child's list widget
        assert_that(request_widget._response._headers_xxx.widget_count()).is_equal_to(2)
        # Nested child's list widget
        assert_that(request_widget._response._headers_outside_of_tab._headers_xxx.widget_count()).is_equal_to(2)

    def test_list_qlabel_forc_with_parent_record_type(self, base_class, decorator, qt: QtDriver) -> None:
        """Exact match of Forc app where parent is Widget[Request] not Widget."""
        from dataclasses import dataclass

        from qtpy.QtCore import Qt
        from qtpy.QtWidgets import QSplitter

        from qtpie import Widget, widget

        @dataclass
        class Request:
            method: str = "GET"
            url: str = ""

        # ResponseHeadersTabContent equivalent - EXACT COPY from user's code
        @widget(title="Headers")
        class ResponseHeadersTabContent(Widget[Response]):
            _headers_label: QLabel = new(bind="{headers}")  # binds to the headers successfully
            _label_above: QLabel = new("ABOVE")
            _headers_xxx: list[QLabel] = new(bind="headers", format="HEADER: {#key}: {#value}")  # nothing shows up!
            _label_below: QLabel = new("BELOW")

        # ResponseViewerWidget equivalent - EXACT COPY from user's code
        @widget
        class ResponseViewerWidget(Widget[Response]):
            _headers_outside_of_tab: ResponseHeadersTabContent  # Bare annotation
            _headers_xxx: list[QLabel] = new(bind="headers", format="HEADER: {#key}: {#value}")  # nothing shows up!

        # RequestWidget equivalent - Widget[Request] with Variable[Response | None]
        @widget
        class RequestWidget(Widget[Request]):
            response: Variable[Response | None] = new(None)
            _splitter: QSplitter = new(Qt.Orientation.Horizontal)
            _response: ResponseViewerWidget = new(bind="response", splitter="_splitter")

        request_widget = create_and_track(qt, RequestWidget, Widget)

        # Before setting response - should be NewField still
        print(f"Before set: _response._headers_xxx = {type(request_widget._response._headers_xxx).__name__}")
        print(f"Before set: _response._headers_outside_of_tab._headers_xxx = {type(request_widget._response._headers_outside_of_tab._headers_xxx).__name__}")

        # Set response
        request_widget.response = Response(200, {"Content-Type": "application/json", "Accept": "text/html"})

        # After setting response - should be DictWidgetRepeater
        print(f"After set: _response._headers_xxx = {type(request_widget._response._headers_xxx).__name__}")
        print(f"After set: _response._headers_outside_of_tab._headers_xxx = {type(request_widget._response._headers_outside_of_tab._headers_xxx).__name__}")

        # Verify all levels work
        assert_that(request_widget._response._headers_xxx.widget_count()).is_equal_to(2)
        assert_that(request_widget._response._headers_outside_of_tab._headers_xxx.widget_count()).is_equal_to(2)


# =============================================================================
# Proxy Cleanup on Widget Removal (prevents RuntimeError on deleted Qt objects)
# =============================================================================


@dataclass
class Person:
    """Test dataclass for proxy cleanup tests."""

    name: str
    age: int = 0


@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestListRepeaterProxyCleanup:
    """Test that removing and re-adding items doesn't crash due to stale proxies."""

    def test_remove_and_readd_same_item_no_crash(self, base_class, decorator, qt: QtDriver) -> None:
        """Removing an item and re-adding the same object should not crash.

        When a widget is removed, its ObservableProxy callbacks must be cleaned up.
        Otherwise, when the same item is re-added, sibling proxy notifications
        will fire stale callbacks that reference deleted Qt widgets.
        """
        from qtpie import Widget, widget

        @widget
        class PersonWidget(Widget[Person]):
            _name: QLabel = new(bind="{name}")
            _age: QLabel = new(bind="{age}")

        @decorator
        class TestClass(base_class):
            _people: Variable[list[Person], PersonWidget] = new([])  # type: ignore[type-arg]

        instance = create_and_track(qt, TestClass, base_class)
        repeater = instance._people.widget

        # Create a person and add it
        alice = Person("Alice", 30)
        instance._people.append(alice)
        qt.process_events()
        assert_that(repeater.widget_count()).is_equal_to(1)

        # Remove it
        instance._people.remove(alice)
        qt.process_events()
        assert_that(repeater.widget_count()).is_equal_to(0)

        # Re-add the SAME object - this should not crash
        instance._people.append(alice)
        qt.process_events()
        assert_that(repeater.widget_count()).is_equal_to(1)

        # Trigger a change on the item - this is where the crash would happen
        # if stale callbacks weren't cleaned up
        alice.name = "Alice Updated"
        instance._people.observable[0] = alice  # Trigger replace notification
        qt.process_events()

    def test_remove_and_readd_triggers_change_no_crash(self, base_class, decorator, qt: QtDriver) -> None:
        """After remove/re-add, changing the item's properties should not crash."""
        from qtpie import Widget, widget

        @widget
        class PersonWidget(Widget[Person]):
            _name: QLineEdit = new(bind="name")

        @decorator
        class TestClass(base_class):
            _people: Variable[list[Person], PersonWidget] = new([])  # type: ignore[type-arg]

        instance = create_and_track(qt, TestClass, base_class)

        bob = Person("Bob", 25)
        instance._people.append(bob)
        qt.process_events()

        # Remove and re-add
        instance._people.remove(bob)
        qt.process_events()
        instance._people.append(bob)
        qt.process_events()

        # Get the new widget and change the value via the widget
        # This triggers proxy notifications that would crash with stale callbacks
        new_widget = instance._people.widget.widget_at(0)
        new_widget._name.setText("Bob Changed")
        qt.process_events()

    def test_clear_and_readd_no_crash(self, base_class, decorator, qt: QtDriver) -> None:
        """Clearing all items and re-adding should not crash."""
        from qtpie import Widget, widget

        @widget
        class PersonWidget(Widget[Person]):
            _name: QLabel = new(bind="{name}")

        @decorator
        class TestClass(base_class):
            _people: Variable[list[Person], PersonWidget] = new([])  # type: ignore[type-arg]

        instance = create_and_track(qt, TestClass, base_class)

        alice = Person("Alice", 30)
        bob = Person("Bob", 25)
        instance._people.append(alice)
        instance._people.append(bob)
        qt.process_events()

        # Clear all
        instance._people.clear()
        qt.process_events()

        # Re-add the same objects
        instance._people.append(alice)
        instance._people.append(bob)
        qt.process_events()

        assert_that(instance._people.widget.widget_count()).is_equal_to(2)


@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestDictRepeaterProxyCleanup:
    """Test dict repeater proxy cleanup on removal."""

    def test_remove_and_readd_same_key_no_crash(self, base_class, decorator, qt: QtDriver) -> None:
        """Removing a key and re-adding it should not crash."""
        from qtpie import Widget, widget

        @widget
        class PersonWidget(Widget[Person]):
            _name: QLabel = new(bind="{name}")

        @decorator
        class TestClass(base_class):
            _people: Variable[dict[str, Person]] = new({})
            _widgets: list[PersonWidget] = new(bind="_people")

        instance = create_and_track(qt, TestClass, base_class)

        alice = Person("Alice", 30)
        instance._people["alice"] = alice
        qt.process_events()

        # Remove
        del instance._people.observable["alice"]
        qt.process_events()

        # Re-add same key with same object
        instance._people["alice"] = alice
        qt.process_events()

        assert_that(instance._widgets.widget_count()).is_equal_to(1)


@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestSetRepeaterProxyCleanup:
    """Test set repeater proxy cleanup on removal."""

    def test_discard_and_readd_same_item_no_crash(self, base_class, decorator, qt: QtDriver) -> None:
        """Discarding an item and re-adding it should not crash."""

        # Use a simple hashable type for set
        @decorator
        class TestClass(base_class):
            _tags: Variable[set[str], QLabel] = new(set())  # type: ignore[type-arg]

        instance = create_and_track(qt, TestClass, base_class)

        instance._tags.observable.add("python")
        qt.process_events()

        instance._tags.observable.discard("python")
        qt.process_events()

        instance._tags.observable.add("python")
        qt.process_events()

        assert_that(instance._tags.widget.widget_count()).is_equal_to(1)


# =============================================================================
# Plain QLabel Repeater Proxy Cleanup (wrapper.dispose() is essential here)
# =============================================================================
# These tests use plain Qt widgets (QLabel) instead of Widget[T] subclasses.
# Unlike Widget[T], plain QLabel has no _qtpie state, so dispose_widget_proxies
# won't find the wrapper proxy. The wrapper.dispose() call is the ONLY thing
# that cleans up these proxies.


@dataclass
class Animal:
    """Test dataclass for plain widget proxy cleanup tests."""

    name: str
    species: str = "unknown"


@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestPlainWidgetRepeaterProxyCleanup:
    """Test that wrapper.dispose() is essential for plain Qt widget repeaters.

    When using list[QLabel] bound to complex objects, the wrapper proxy is NOT
    assigned to the QLabel (it has no _qtpie state). So dispose_widget_proxies
    cannot find it. Only wrapper.dispose() cleans up these proxies.

    These tests SHOULD FAIL when wrapper.dispose() is commented out.
    """

    def test_list_qlabel_proxy_cleanup_on_remove(self, base_class, decorator, qt: QtDriver) -> None:
        """Removing item from list[QLabel] repeater should dispose the wrapper proxy.

        THIS TEST SHOULD FAIL when wrapper.dispose() is commented out.
        """
        from observant.observable_proxy import _proxy_registry

        @decorator
        class TestClass(base_class):
            _animals: Variable[list[Animal], QLabel] = new([])  # type: ignore[type-arg]

        instance = create_and_track(qt, TestClass, base_class)

        # Create an animal and add it
        cat = Animal("Whiskers", "cat")
        cat_id = id(cat)

        instance._animals.append(cat)
        qt.process_events()

        # Verify proxy was created
        assert cat_id in _proxy_registry, "Proxy should be registered for the animal"
        proxies_before = len(_proxy_registry[cat_id])
        assert proxies_before > 0, "At least one proxy should exist"

        # Remove the animal
        instance._animals.remove(cat)
        qt.process_events()

        # Check if proxy was cleaned up
        proxies_after = len(_proxy_registry.get(cat_id, []))

        assert proxies_after == 0, (
            f"Wrapper proxy should be disposed when item is removed from plain QLabel repeater, "
            f"but {proxies_after} proxies remain (was {proxies_before}). "
            f"This fails when wrapper.dispose() is commented out."
        )

    def test_list_qlabel_proxy_cleanup_on_clear(self, base_class, decorator, qt: QtDriver) -> None:
        """Clearing list[QLabel] repeater should dispose all wrapper proxies.

        THIS TEST SHOULD FAIL when wrapper.dispose() is commented out.
        """
        from observant.observable_proxy import _proxy_registry

        @decorator
        class TestClass(base_class):
            _animals: Variable[list[Animal], QLabel] = new([])  # type: ignore[type-arg]

        instance = create_and_track(qt, TestClass, base_class)

        # Add multiple animals
        dog = Animal("Rex", "dog")
        bird = Animal("Tweety", "bird")
        dog_id = id(dog)
        bird_id = id(bird)

        instance._animals.append(dog)
        instance._animals.append(bird)
        qt.process_events()

        # Verify proxies were created
        assert dog_id in _proxy_registry, "Proxy should be registered for dog"
        assert bird_id in _proxy_registry, "Proxy should be registered for bird"

        # Clear all
        instance._animals.clear()
        qt.process_events()

        # Check if proxies were cleaned up
        dog_proxies = len(_proxy_registry.get(dog_id, []))
        bird_proxies = len(_proxy_registry.get(bird_id, []))

        assert dog_proxies == 0, f"Dog wrapper proxy should be disposed on clear, but {dog_proxies} remain. This fails when wrapper.dispose() is commented out."
        assert bird_proxies == 0, f"Bird wrapper proxy should be disposed on clear, but {bird_proxies} remain. This fails when wrapper.dispose() is commented out."


@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestPlainDictWidgetProxyCleanup:
    """Test wrapper.dispose() for dict repeaters with plain QLabel widgets."""

    def test_dict_qlabel_proxy_cleanup_on_remove(self, base_class, decorator, qt: QtDriver) -> None:
        """Removing key from dict[str, Animal] with QLabel should dispose proxy.

        THIS TEST SHOULD FAIL when wrapper.dispose() is commented out.
        """
        from observant.observable_proxy import _proxy_registry

        @decorator
        class TestClass(base_class):
            _pets: Variable[dict[str, Animal]] = new({})
            _labels: list[QLabel] = new(bind="_pets", format="{#key}: {name}")

        instance = create_and_track(qt, TestClass, base_class)

        # Add a pet
        hamster = Animal("Hammy", "hamster")
        hamster_id = id(hamster)

        instance._pets["hammy"] = hamster
        qt.process_events()

        # Verify proxy was created
        assert hamster_id in _proxy_registry, "Proxy should be registered"

        # Remove it
        del instance._pets.observable["hammy"]
        qt.process_events()

        # Check cleanup
        proxies_after = len(_proxy_registry.get(hamster_id, []))
        assert proxies_after == 0, f"Wrapper proxy should be disposed, but {proxies_after} remain. This fails when wrapper.dispose() is commented out."
