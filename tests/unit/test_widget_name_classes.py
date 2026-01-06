# pyright: reportPrivateUsage=false, reportUnknownParameterType=false, reportMissingParameterType=false
"""Tests for widget name and classes parameters."""

import pytest
from qtpy.QtWidgets import QApplication, QLabel, QLineEdit, QPushButton

from qtpie import Widget, new, widget
from qtpie.styles import get_classes


@pytest.fixture(scope="module")
def app():
    """Create QApplication for tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


class TestWidgetDecoratorNameClasses:
    """Test @widget(name=..., classes=[...]) decorator parameters."""

    def test_widget_decorator_sets_object_name(self, app):
        """Test that @widget(name=...) sets objectName."""

        @widget(name="my-widget")
        class MyWidget(Widget):
            pass

        w = MyWidget()
        assert w.objectName() == "my-widget"

    def test_widget_decorator_sets_css_classes(self, app):
        """Test that @widget(classes=[...]) sets CSS classes."""

        @widget(classes=["card", "primary"])
        class MyWidget(Widget):
            pass

        w = MyWidget()
        assert get_classes(w) == ["card", "primary"]

    def test_widget_decorator_sets_both_name_and_classes(self, app):
        """Test that @widget(name=..., classes=[...]) sets both."""

        @widget(name="styled-card", classes=["card", "elevated"])
        class MyWidget(Widget):
            pass

        w = MyWidget()
        assert w.objectName() == "styled-card"
        assert get_classes(w) == ["card", "elevated"]


class TestNewFieldNameClasses:
    """Test new(name=..., classes=[...]) for QWidget fields."""

    def test_new_field_sets_object_name(self, app):
        """Test that new(name=...) sets objectName on QWidget fields."""

        @widget
        class MyWidget(Widget):
            _button: QPushButton = new("Click", name="action-button")

        w = MyWidget()
        assert w._button.objectName() == "action-button"

    def test_new_field_sets_css_classes(self, app):
        """Test that new(classes=[...]) sets CSS classes on QWidget fields."""

        @widget
        class MyWidget(Widget):
            _button: QPushButton = new("Click", classes=["btn", "btn-primary"])

        w = MyWidget()
        assert get_classes(w._button) == ["btn", "btn-primary"]

    def test_new_field_sets_both_name_and_classes(self, app):
        """Test that new(name=..., classes=[...]) sets both on QWidget fields."""

        @widget
        class MyWidget(Widget):
            _label: QLabel = new("Hello", name="greeting", classes=["text", "large"])

        w = MyWidget()
        assert w._label.objectName() == "greeting"
        assert get_classes(w._label) == ["text", "large"]


class TestVariableWidgetNameClasses:
    """Test Variable[T, W] = new(...)(name=..., classes=[...])."""

    def test_variable_widget_sets_object_name(self, app):
        """Test that Variable[str, QLineEdit] = new(...)(name=...) sets objectName."""
        from qtpie import Variable

        @widget
        class MyWidget(Widget):
            _name: Variable[str, QLineEdit] = new("initial")(name="name-input")

        w = MyWidget()
        assert w._name.widget.objectName() == "name-input"

    def test_variable_widget_sets_css_classes(self, app):
        """Test that Variable[str, QLineEdit] = new(...)(classes=[...]) sets classes."""
        from qtpie import Variable

        @widget
        class MyWidget(Widget):
            _name: Variable[str, QLineEdit] = new("initial")(classes=["input", "bordered"])

        w = MyWidget()
        assert get_classes(w._name.widget) == ["input", "bordered"]

    def test_variable_widget_sets_both_name_and_classes(self, app):
        """Test that Variable[str, QLineEdit] = new(...)(name=..., classes=[...]) sets both."""
        from qtpie import Variable

        @widget
        class MyWidget(Widget):
            _name: Variable[str, QLineEdit] = new("initial")(name="name-field", classes=["input", "large"])

        w = MyWidget()
        assert w._name.widget.objectName() == "name-field"
        assert get_classes(w._name.widget) == ["input", "large"]


class TestListWidgetNameClasses:
    """Test list[QWidget] = new(bind=..., name=..., classes=[...])."""

    def test_list_widget_sets_object_name_on_items(self, app):
        """Test that list[QLabel] = new(bind=..., name=...) sets objectName on each item."""
        from qtpie import Variable

        @widget
        class MyWidget(Widget):
            _items: Variable[list[str]] = new(["a", "b", "c"])
            _labels: list[QLabel] = new(bind="_items", name="list-item")

        w = MyWidget()
        for label in w._labels:
            assert label.objectName() == "list-item"

    def test_list_widget_sets_css_classes_on_items(self, app):
        """Test that list[QLabel] = new(bind=..., classes=[...]) sets classes on each item."""
        from qtpie import Variable

        @widget
        class MyWidget(Widget):
            _items: Variable[list[str]] = new(["a", "b", "c"])
            _labels: list[QLabel] = new(bind="_items", classes=["item", "clickable"])

        w = MyWidget()
        for label in w._labels:
            assert get_classes(label) == ["item", "clickable"]

    def test_list_widget_sets_both_on_items(self, app):
        """Test that list[QLabel] = new(bind=..., name=..., classes=[...]) sets both on each item."""
        from qtpie import Variable

        @widget
        class MyWidget(Widget):
            _items: Variable[list[str]] = new(["x", "y"])
            _labels: list[QLabel] = new(bind="_items", name="entry", classes=["row"])

        w = MyWidget()
        for label in w._labels:
            assert label.objectName() == "entry"
            assert get_classes(label) == ["row"]


class TestVariableListWidgetNameClasses:
    """Test Variable[list[T], QWidget] = new(...)(name=..., classes=[...])."""

    def test_variable_list_widget_sets_object_name_on_items(self, app):
        """Test that Variable[list[str], QLabel] sets objectName on each item widget."""
        from qtpie import Variable

        @widget
        class MyWidget(Widget):
            _items: Variable[list[str], QLabel] = new(["a", "b"])(name="list-label")

        w = MyWidget()
        repeater = w._items.widget
        for widget_item in repeater:
            assert widget_item.objectName() == "list-label"

    def test_variable_list_widget_sets_css_classes_on_items(self, app):
        """Test that Variable[list[str], QLabel] sets classes on each item widget."""
        from qtpie import Variable

        @widget
        class MyWidget(Widget):
            _items: Variable[list[str], QLabel] = new(["a", "b"])(classes=["list-item"])

        w = MyWidget()
        repeater = w._items.widget
        for widget_item in repeater:
            assert get_classes(widget_item) == ["list-item"]


class TestVariableDictWidgetNameClasses:
    """Test Variable[dict[K, V], QWidget] = new(...)(name=..., classes=[...])."""

    def test_variable_dict_widget_sets_object_name_on_items(self, app):
        """Test that Variable[dict[str, int], QLabel] sets objectName on each item widget."""
        from qtpie import Variable

        @widget
        class MyWidget(Widget):
            _items: Variable[dict[str, int], QLabel] = new({"a": 1, "b": 2})(name="dict-label")

        w = MyWidget()
        repeater = w._items.widget
        for widget_item in repeater:
            assert widget_item.objectName() == "dict-label"

    def test_variable_dict_widget_sets_css_classes_on_items(self, app):
        """Test that Variable[dict[str, int], QLabel] sets classes on each item widget."""
        from qtpie import Variable

        @widget
        class MyWidget(Widget):
            _items: Variable[dict[str, int], QLabel] = new({"a": 1, "b": 2})(classes=["dict-item"])

        w = MyWidget()
        repeater = w._items.widget
        for widget_item in repeater:
            assert get_classes(widget_item) == ["dict-item"]


class TestNonQWidgetNameClasses:
    """Test that non-QWidget classes get name/classes passed to constructor."""

    def test_regular_class_receives_name_in_constructor(self, app):
        """Test that regular (non-QWidget) classes receive name= in constructor."""

        class RegularClass:
            def __init__(self, name: str = "default"):
                self.name = name

        @widget
        class MyWidget(Widget):
            _obj: RegularClass = new(name="custom-name")

        w = MyWidget()
        assert w._obj.name == "custom-name"

    def test_regular_class_receives_classes_in_constructor(self, app):
        """Test that regular (non-QWidget) classes receive classes= in constructor."""

        class RegularClass:
            def __init__(self, classes: list[str] | None = None):
                self.classes = classes or []

        @widget
        class MyWidget(Widget):
            _obj: RegularClass = new(classes=["one", "two"])

        w = MyWidget()
        assert w._obj.classes == ["one", "two"]

    def test_regular_class_receives_both_name_and_classes(self, app):
        """Test that regular classes receive both name= and classes= as kwargs."""

        class DataHolder:
            def __init__(self, name: str = "", classes: list[str] | None = None):
                self.name = name
                self.classes = classes or []

        @widget
        class MyWidget(Widget):
            _data: DataHolder = new(name="holder", classes=["data", "container"])

        w = MyWidget()
        assert w._data.name == "holder"
        assert w._data.classes == ["data", "container"]

    def test_regular_class_with_positional_args_and_name_classes(self, app):
        """Test that regular classes work with positional args plus name/classes kwargs."""

        class ConfiguredClass:
            def __init__(self, value: int, name: str = "", classes: list[str] | None = None):
                self.value = value
                self.name = name
                self.classes = classes or []

        @widget
        class MyWidget(Widget):
            _config: ConfiguredClass = new(42, name="my-config", classes=["config"])

        w = MyWidget()
        assert w._config.value == 42
        assert w._config.name == "my-config"
        assert w._config.classes == ["config"]


class TestDynamicListItemsNameClasses:
    """Test that dynamically added list items also get name/classes applied."""

    def test_new_list_items_get_object_name(self, app):
        """Test that items added after creation also get objectName."""
        from qtpie import Variable

        @widget
        class MyWidget(Widget):
            _items: Variable[list[str]] = new([])
            _labels: list[QLabel] = new(bind="_items", name="dynamic-item")

        w = MyWidget()
        assert len(w._labels) == 0

        # Add items dynamically
        w._items.append("new1")
        w._items.append("new2")

        assert len(w._labels) == 2
        for label in w._labels:
            assert label.objectName() == "dynamic-item"

    def test_new_list_items_get_css_classes(self, app):
        """Test that items added after creation also get CSS classes."""
        from qtpie import Variable

        @widget
        class MyWidget(Widget):
            _items: Variable[list[str]] = new([])
            _labels: list[QLabel] = new(bind="_items", classes=["dynamic", "styled"])

        w = MyWidget()
        assert len(w._labels) == 0

        # Add items dynamically
        w._items.append("new1")

        assert len(w._labels) == 1
        assert get_classes(w._labels[0]) == ["dynamic", "styled"]


class TestDefaultObjectName:
    """Test automatic objectName defaults."""

    def test_widget_class_defaults_to_class_name(self, app):
        """Test that @widget without name= defaults objectName to class name."""

        @widget
        class MyDefaultWidget(Widget):
            pass

        w = MyDefaultWidget()
        assert w.objectName() == "MyDefaultWidget"

    def test_qwidget_field_defaults_to_field_name(self, app):
        """Test that QWidget fields without name= default objectName to field name."""

        @widget
        class MyWidget(Widget):
            _button: QPushButton = new("Click")
            _label: QLabel = new("Hello")

        w = MyWidget()
        assert w._button.objectName() == "_button"
        assert w._label.objectName() == "_label"

    def test_variable_widget_defaults_to_field_name(self, app):
        """Test that Variable[T, W] widgets without name= default objectName to field name."""
        from qtpie import Variable

        @widget
        class MyWidget(Widget):
            _name: Variable[str, QLineEdit] = new("initial")

        w = MyWidget()
        assert w._name.widget.objectName() == "_name"

    def test_list_widget_defaults_to_field_name(self, app):
        """Test that list[QWidget] items without name= default objectName to field name."""
        from qtpie import Variable

        @widget
        class MyWidget(Widget):
            _items: Variable[list[str]] = new(["a", "b"])
            _labels: list[QLabel] = new(bind="_items")

        w = MyWidget()
        for label in w._labels:
            assert label.objectName() == "_labels"

    def test_variable_list_widget_defaults_to_field_name(self, app):
        """Test that Variable[list[T], W] items default objectName to field name."""
        from qtpie import Variable

        @widget
        class MyWidget(Widget):
            _items: Variable[list[str], QLabel] = new(["a", "b"])

        w = MyWidget()
        for widget_item in w._items.widget:
            assert widget_item.objectName() == "_items"

    def test_variable_dict_widget_defaults_to_field_name(self, app):
        """Test that Variable[dict[K, V], W] items default objectName to field name."""
        from qtpie import Variable

        @widget
        class MyWidget(Widget):
            _entries: Variable[dict[str, int], QLabel] = new({"a": 1, "b": 2})

        w = MyWidget()
        for widget_item in w._entries.widget:
            assert widget_item.objectName() == "_entries"

    def test_explicit_name_overrides_default(self, app):
        """Test that explicit name= overrides default field name."""

        @widget(name="custom-widget")
        class MyWidget(Widget):
            _button: QPushButton = new("Click", name="custom-button")

        w = MyWidget()
        assert w.objectName() == "custom-widget"
        assert w._button.objectName() == "custom-button"

    def test_qss_selector_works_with_defaults(self, app):
        """Test that QSS selectors work with default objectNames."""

        @widget(
            stylesheet="""
#TestQssWidget {
    background-color: red;
}
#_my_label {
    color: blue;
}
"""
        )
        class TestQssWidget(Widget):
            _my_label: QLabel = new("Label")

        w = TestQssWidget()
        assert w.objectName() == "TestQssWidget"
        assert w._my_label.objectName() == "_my_label"
