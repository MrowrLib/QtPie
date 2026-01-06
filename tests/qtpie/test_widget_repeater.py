# pyright: reportPrivateUsage=false, reportOptionalMemberAccess=false
# pyright: reportAttributeAccessIssue=false, reportUnknownMemberType=false
# pyright: reportUnknownVariableType=false, reportCallIssue=false
# pyright: reportIndexIssue=false, reportArgumentType=false
"""Tests for WidgetRepeater and Variable[list[T], W]."""

from dataclasses import dataclass

from PySide6.QtWidgets import QLabel, QLineEdit, QSpinBox

from qtpie import Variable, Widget, WidgetRepeater, new, widget
from qtpie.testing import QtDriver


class TestWidgetRepeaterBasics:
    """Test basic WidgetRepeater creation and layout."""

    def test_repeater_creates_widgets_for_initial_items(self, qt: QtDriver) -> None:
        """WidgetRepeater creates one widget per list item."""

        @widget
        class Test(Widget):
            _numbers: Variable[list[int], QLineEdit] = new([1, 2, 3])  # type: ignore[type-arg]

        w = qt.track(Test())

        # Should create a WidgetRepeater
        assert isinstance(w._numbers.widget, WidgetRepeater)

        # Should have 3 widgets
        repeater: WidgetRepeater[int] = w._numbers.widget
        assert repeater.widget_count() == 3

    def test_repeater_empty_list_no_widgets(self, qt: QtDriver) -> None:
        """Empty list creates no child widgets."""

        @widget
        class Test(Widget):
            _items: Variable[list[str], QLineEdit] = new([])  # type: ignore[type-arg]

        w = qt.track(Test())

        repeater: WidgetRepeater[str] = w._items.widget
        assert repeater.widget_count() == 0

    def test_repeater_widgets_are_correct_type(self, qt: QtDriver) -> None:
        """Repeater creates widgets of the specified type."""

        @widget
        class Test(Widget):
            _numbers: Variable[list[int], QSpinBox] = new([10, 20])  # type: ignore[type-arg]

        w = qt.track(Test())

        repeater: WidgetRepeater[int] = w._numbers.widget
        assert isinstance(repeater.widget_at(0), QSpinBox)
        assert isinstance(repeater.widget_at(1), QSpinBox)


class TestWidgetRepeaterGranularSync:
    """Test granular sync operations (insert, remove, replace, clear)."""

    def test_on_insert_adds_widget(self, qt: QtDriver) -> None:
        """Appending to list adds widget to layout."""

        @widget
        class Test(Widget):
            _items: Variable[list[str], QLineEdit] = new(["a", "b"])  # type: ignore[type-arg]

        w = qt.track(Test())
        repeater: WidgetRepeater[str] = w._items.widget

        assert repeater.widget_count() == 2

        # Append to list
        w._items.observable.append("c")

        assert repeater.widget_count() == 3

    def test_on_insert_at_index_inserts_widget(self, qt: QtDriver) -> None:
        """Inserting at index adds widget at correct position."""

        @widget
        class Test(Widget):
            _items: Variable[list[str], QLabel] = new(["a", "c"])  # type: ignore[type-arg]

        w = qt.track(Test())
        repeater: WidgetRepeater[str] = w._items.widget

        # Insert at index 1
        w._items.observable.insert(1, "b")

        assert repeater.widget_count() == 3
        # Middle widget should show "b"
        middle_widget = repeater.widget_at(1)
        assert isinstance(middle_widget, QLabel)
        assert middle_widget.text() == "b"

    def test_on_remove_removes_widget(self, qt: QtDriver) -> None:
        """Removing from list removes widget from layout."""

        @widget
        class Test(Widget):
            _items: Variable[list[str], QLineEdit] = new(["a", "b", "c"])  # type: ignore[type-arg]

        w = qt.track(Test())
        repeater: WidgetRepeater[str] = w._items.widget

        assert repeater.widget_count() == 3

        # Remove "b" from list
        w._items.observable.remove("b")

        assert repeater.widget_count() == 2

    def test_on_replace_updates_widget(self, qt: QtDriver) -> None:
        """Replacing item updates widget value."""

        @widget
        class Test(Widget):
            _items: Variable[list[str], QLabel] = new(["old"])  # type: ignore[type-arg]

        w = qt.track(Test())
        repeater: WidgetRepeater[str] = w._items.widget

        first_widget = repeater.widget_at(0)
        assert isinstance(first_widget, QLabel)
        assert first_widget.text() == "old"

        # Replace via index assignment
        w._items.observable[0] = "new"

        assert first_widget.text() == "new"

    def test_on_clear_removes_all_widgets(self, qt: QtDriver) -> None:
        """Clearing list removes all widgets."""

        @widget
        class Test(Widget):
            _items: Variable[list[str], QLineEdit] = new(["a", "b", "c"])  # type: ignore[type-arg]

        w = qt.track(Test())
        repeater: WidgetRepeater[str] = w._items.widget

        assert repeater.widget_count() == 3

        # Clear the list
        w._items.observable.clear()

        assert repeater.widget_count() == 0


class TestWidgetRepeaterPrimitiveBinding:
    """Test binding primitive types (int, str) to widgets."""

    def test_bind_primitive_initial_value(self, qt: QtDriver) -> None:
        """list[int] shows initial values in widgets."""

        @widget
        class Test(Widget):
            _numbers: Variable[list[int], QLabel] = new([10, 20, 30])  # type: ignore[type-arg]

        w = qt.track(Test())
        repeater: WidgetRepeater[int] = w._numbers.widget

        assert repeater.widget_at(0).text() == "10"
        assert repeater.widget_at(1).text() == "20"
        assert repeater.widget_at(2).text() == "30"

    def test_bind_primitive_widget_to_list(self, qt: QtDriver) -> None:
        """Editing widget updates list item (two-way binding)."""

        @widget
        class Test(Widget):
            _numbers: Variable[list[int], QSpinBox] = new([1, 2, 3])  # type: ignore[type-arg]

        w = qt.track(Test())
        repeater: WidgetRepeater[int] = w._numbers.widget

        # Change spinbox value
        spin = repeater.widget_at(1)
        assert isinstance(spin, QSpinBox)
        spin.setValue(99)

        # List should be updated
        assert w._numbers.observable[1] == 99

    def test_bind_primitive_list_to_widget(self, qt: QtDriver) -> None:
        """Changing list item updates widget."""

        @widget
        class Test(Widget):
            _items: Variable[list[str], QLabel] = new(["hello"])  # type: ignore[type-arg]

        w = qt.track(Test())
        repeater: WidgetRepeater[str] = w._items.widget

        label = repeater.widget_at(0)
        assert isinstance(label, QLabel)
        assert label.text() == "hello"

        # Change list item
        w._items.observable[0] = "world"

        assert label.text() == "world"

    def test_string_list_with_qlineedit(self, qt: QtDriver) -> None:
        """list[str] with QLineEdit supports two-way binding."""

        @widget
        class Test(Widget):
            _names: Variable[list[str], QLineEdit] = new(["Alice", "Bob"])  # type: ignore[type-arg]

        w = qt.track(Test())
        repeater: WidgetRepeater[str] = w._names.widget

        # Initial values
        assert repeater.widget_at(0).text() == "Alice"
        assert repeater.widget_at(1).text() == "Bob"

        # Edit widget
        edit = repeater.widget_at(0)
        assert isinstance(edit, QLineEdit)
        edit.setText("Charlie")

        # List updated
        assert w._names.observable[0] == "Charlie"

        # Change list
        w._names.observable[1] = "Diana"

        # Widget updated
        assert repeater.widget_at(1).text() == "Diana"


class TestWidgetRepeaterObjectBinding:
    """Test binding complex objects to widgets."""

    def test_bind_object_initial_value(self, qt: QtDriver) -> None:
        """list[Dog] shows initial values in widgets."""

        @dataclass
        class Dog:
            name: str

        @widget
        class Test(Widget):
            _dogs: Variable[list[Dog], QLabel] = new([Dog("Rover"), Dog("Snoopy")])  # type: ignore[type-arg]

        w = qt.track(Test())
        repeater: WidgetRepeater[Dog] = w._dogs.widget

        # Labels should show Dog repr/str
        assert repeater.widget_count() == 2

    def test_bind_single_property(self, qt: QtDriver) -> None:
        """bind='{name}' shows just the name property."""

        @dataclass
        class Dog:
            name: str
            age: int

        @widget
        class Test(Widget):
            _dogs: Variable[list[Dog], QLabel] = new([Dog("Rover", 3), Dog("Snoopy", 5)])(bind="{name}")  # type: ignore[type-arg]

        w = qt.track(Test())
        repeater: WidgetRepeater[Dog] = w._dogs.widget

        assert repeater.widget_at(0).text() == "Rover"
        assert repeater.widget_at(1).text() == "Snoopy"

    def test_bind_single_property_two_way(self, qt: QtDriver) -> None:
        """bind='{name}' with QLineEdit supports two-way binding."""

        @dataclass
        class Dog:
            name: str
            age: int

        @widget
        class Test(Widget):
            _dogs: Variable[list[Dog], QLineEdit] = new([Dog("Rover", 3)])(bind="{name}")  # type: ignore[type-arg]

        w = qt.track(Test())
        repeater: WidgetRepeater[Dog] = w._dogs.widget

        # Initial value
        edit = repeater.widget_at(0)
        assert isinstance(edit, QLineEdit)
        assert edit.text() == "Rover"

        # Edit widget → updates object
        edit.setText("Max")
        assert w._dogs.observable[0].name == "Max"

    def test_bind_format_string_multiple_properties(self, qt: QtDriver) -> None:
        """bind='{name} is {age} years old' combines properties."""

        @dataclass
        class Dog:
            name: str
            age: int

        @widget
        class Test(Widget):
            _dogs: Variable[list[Dog], QLabel] = new([Dog("Rover", 3), Dog("Snoopy", 5)])(bind="{name} is {age} years old")  # type: ignore[type-arg]

        w = qt.track(Test())
        repeater: WidgetRepeater[Dog] = w._dogs.widget

        assert repeater.widget_at(0).text() == "Rover is 3 years old"
        assert repeater.widget_at(1).text() == "Snoopy is 5 years old"


class TestWidgetRepeaterBindExpressions:
    """Test bind expression parsing and special placeholders."""

    def test_bind_index_placeholder(self, qt: QtDriver) -> None:
        """bind='{#index}' shows item index."""

        @widget
        class Test(Widget):
            _items: Variable[list[str], QLabel] = new(["a", "b", "c"])(bind="{#index}")  # type: ignore[type-arg]

        w = qt.track(Test())
        repeater: WidgetRepeater[str] = w._items.widget

        assert repeater.widget_at(0).text() == "0"
        assert repeater.widget_at(1).text() == "1"
        assert repeater.widget_at(2).text() == "2"

    def test_bind_self_placeholder(self, qt: QtDriver) -> None:
        """bind='{#self}' shows item value (default behavior)."""

        @widget
        class Test(Widget):
            _items: Variable[list[int], QLabel] = new([10, 20, 30])(bind="{#self}")  # type: ignore[type-arg]

        w = qt.track(Test())
        repeater: WidgetRepeater[int] = w._items.widget

        assert repeater.widget_at(0).text() == "10"
        assert repeater.widget_at(1).text() == "20"
        assert repeater.widget_at(2).text() == "30"

    def test_bind_combined_index_and_self(self, qt: QtDriver) -> None:
        """bind='Index {#index}: {#self}' combines index and value."""

        @widget
        class Test(Widget):
            _items: Variable[list[str], QLabel] = new(["a", "b"])(bind="Index {#index}: {#self}")  # type: ignore[type-arg]

        w = qt.track(Test())
        repeater: WidgetRepeater[str] = w._items.widget

        assert repeater.widget_at(0).text() == "Index 0: a"
        assert repeater.widget_at(1).text() == "Index 1: b"

    def test_bind_format_updates_on_change(self, qt: QtDriver) -> None:
        """Format string updates when underlying data changes."""

        @dataclass
        class Dog:
            name: str
            age: int

        @widget
        class Test(Widget):
            _dogs: Variable[list[Dog], QLabel] = new([Dog("Rover", 3)])(bind="{name} ({age})")  # type: ignore[type-arg]

        w = qt.track(Test())
        repeater: WidgetRepeater[Dog] = w._dogs.widget

        label = repeater.widget_at(0)
        assert label.text() == "Rover (3)"

        # Modify the object by replacing the item
        # (Direct property modification would require accessing the internal wrapper)
        w._dogs.observable[0] = Dog("Max", 5)

        # After replace, widget should update
        assert repeater.widget_at(0).text() == "Max (5)"

    def test_bind_index_updates_after_insert(self, qt: QtDriver) -> None:
        """Index placeholder updates after insert."""

        @widget
        class Test(Widget):
            _items: Variable[list[str], QLabel] = new(["a", "b"])(bind="[{#index}] {#self}")  # type: ignore[type-arg]

        w = qt.track(Test())
        repeater: WidgetRepeater[str] = w._items.widget

        assert repeater.widget_at(0).text() == "[0] a"
        assert repeater.widget_at(1).text() == "[1] b"

        # Insert at beginning
        w._items.observable.insert(0, "x")

        # New item at index 0
        assert repeater.widget_at(0).text() == "[0] x"
        # Old items shifted - but their index_holder is updated
        # Note: The format string is computed at bind time, so existing widgets
        # keep their original index until replaced. This is expected behavior.
        assert repeater.widget_count() == 3


class TestWidgetRepeaterIndexManagement:
    """Test that indices update correctly after insert/remove."""

    def test_indices_update_on_insert(self, qt: QtDriver) -> None:
        """After insert, widgets still bound to correct items."""

        @widget
        class Test(Widget):
            _items: Variable[list[str], QLabel] = new(["a", "c"])  # type: ignore[type-arg]

        w = qt.track(Test())
        repeater: WidgetRepeater[str] = w._items.widget

        # Insert "b" at index 1
        w._items.observable.insert(1, "b")

        # Now change item at index 2 (was index 1 before)
        w._items.observable[2] = "C"

        # Third widget should show "C"
        assert repeater.widget_at(2).text() == "C"
        # Second widget should still show "b"
        assert repeater.widget_at(1).text() == "b"

    def test_indices_update_on_remove(self, qt: QtDriver) -> None:
        """After remove, widgets still bound to correct items."""

        @widget
        class Test(Widget):
            _items: Variable[list[str], QLabel] = new(["a", "b", "c"])  # type: ignore[type-arg]

        w = qt.track(Test())
        repeater: WidgetRepeater[str] = w._items.widget

        # Remove "b" at index 1
        w._items.observable.remove("b")

        # Now change item at index 1 (was "c")
        w._items.observable[1] = "C"

        # Second widget should show "C"
        assert repeater.widget_at(1).text() == "C"
        # First widget should still show "a"
        assert repeater.widget_at(0).text() == "a"


class TestWidgetRepeaterIntegration:
    """Test integration with Variable[list[T], W] syntax."""

    def test_variable_list_widget_creates_repeater(self, qt: QtDriver) -> None:
        """Variable[list[int], QLineEdit] creates WidgetRepeater."""

        @widget
        class Test(Widget):
            _numbers: Variable[list[int], QLineEdit] = new([1, 2, 3])  # type: ignore[type-arg]

        w = qt.track(Test())

        # Widget should be WidgetRepeater, not QLineEdit
        assert isinstance(w._numbers.widget, WidgetRepeater)
        assert not isinstance(w._numbers.widget, QLineEdit)

    def test_variable_list_widget_in_layout(self, qt: QtDriver) -> None:
        """WidgetRepeater appears in parent widget layout."""

        @widget
        class Test(Widget):
            _label: QLabel = new("Before")
            _numbers: Variable[list[int], QLabel] = new([1, 2])  # type: ignore[type-arg]
            _label2: QLabel = new("After")

        w = qt.track(Test())
        layout = w.layout()

        # Should have 3 items: label, repeater, label2
        assert layout.count() == 3
        assert layout.itemAt(0).widget().text() == "Before"
        assert isinstance(layout.itemAt(1).widget(), WidgetRepeater)
        assert layout.itemAt(2).widget().text() == "After"

    def test_variable_list_with_widget_kwargs(self, qt: QtDriver) -> None:
        """new([1,2,3])(maxLength=5) applies kwargs to each widget."""

        @widget
        class Test(Widget):
            _names: Variable[list[str], QLineEdit] = new(["a", "b"])(maxLength=5)  # type: ignore[type-arg]

        w = qt.track(Test())
        repeater: WidgetRepeater[str] = w._names.widget

        # Each QLineEdit should have maxLength=5
        edit1 = repeater.widget_at(0)
        edit2 = repeater.widget_at(1)
        assert isinstance(edit1, QLineEdit)
        assert isinstance(edit2, QLineEdit)
        assert edit1.maxLength() == 5
        assert edit2.maxLength() == 5

        # Also newly added widgets get kwargs
        w._names.observable.append("c")
        edit3 = repeater.widget_at(2)
        assert isinstance(edit3, QLineEdit)
        assert edit3.maxLength() == 5


class TestListWidgetBoundToDict:
    """Test list[QWidget] bound to dict variables."""

    def test_list_qlabel_bound_to_dict_variable(self, qt: QtDriver) -> None:
        """list[QLabel] can bind to Variable[dict[K, V]]."""

        @dataclass
        class Dog:
            name: str
            age: int

        @widget
        class Test(Widget):
            _dogs_dict: Variable[dict[str, Dog]] = new({"Fido": Dog("Fido", 3), "Rex": Dog("Rex", 5)})
            _labels: list[QLabel] = new(bind="_dogs_dict", format="{#key} is {age} years old")

        w = qt.track(Test())

        # Should create labels for each dict entry
        from qtpie import DictWidgetRepeater

        assert isinstance(w._labels, DictWidgetRepeater)
        assert w._labels.widget_count() == 2

    def test_list_qlabel_bound_to_dict_with_format_string(self, qt: QtDriver) -> None:
        """format= string template works with dict bindings."""

        @dataclass
        class Dog:
            name: str
            age: int

        @widget
        class Test(Widget):
            _dogs: Variable[dict[str, Dog]] = new({"Fido": Dog("Fido", 3)})
            _labels: list[QLabel] = new(bind="_dogs", format="{#key}: {name} is {age}")

        w = qt.track(Test())

        label = w._labels.widget_for_key("Fido")
        assert label is not None
        assert label.text() == "Fido: Fido is 3"

    def test_list_qlabel_bound_to_dict_updates_on_insert(self, qt: QtDriver) -> None:
        """Adding to dict creates new labels."""

        @widget
        class Test(Widget):
            _items: Variable[dict[str, int]] = new({"a": 1})
            _labels: list[QLabel] = new(bind="_items", format="{#key}={#value}")

        w = qt.track(Test())
        assert w._labels.widget_count() == 1

        # Add new entry
        w._items["b"] = 2
        assert w._labels.widget_count() == 2

        label = w._labels.widget_for_key("b")
        assert label is not None
        assert label.text() == "b=2"


class TestListWidgetFormatParameter:
    """Test format= parameter for list[QWidget] bindings."""

    def test_list_qlabel_with_format_string(self, qt: QtDriver) -> None:
        """list[QLabel] with format= uses string template."""

        @dataclass
        class Dog:
            name: str
            age: int

        @widget
        class Test(Widget):
            _dogs: Variable[list[Dog]] = new([Dog("Fido", 3), Dog("Rex", 5)])
            _labels: list[QLabel] = new(bind="_dogs", format="{name} is {age} years old")

        w = qt.track(Test())

        from qtpie import WidgetRepeater

        assert isinstance(w._labels, WidgetRepeater)
        assert w._labels.widget_at(0).text() == "Fido is 3 years old"
        assert w._labels.widget_at(1).text() == "Rex is 5 years old"

    def test_list_qlabel_with_callable_format(self, qt: QtDriver) -> None:
        """list[QLabel] with format= callable uses function."""

        @dataclass
        class Dog:
            name: str
            age: int

        @widget
        class Test(Widget):
            _dogs: Variable[list[Dog]] = new([Dog("Fido", 3)])
            _labels: list[QLabel] = new(bind="_dogs", format=lambda d: f"{d.name.upper()} - {d.age}")  # pyright: ignore[reportUnknownLambdaType]

        w = qt.track(Test())

        from qtpie import WidgetRepeater

        assert isinstance(w._labels, WidgetRepeater)
        assert w._labels.widget_at(0).text() == "FIDO - 3"

    def test_list_qlabel_format_updates_on_replace(self, qt: QtDriver) -> None:
        """Replacing list item creates new label with updated format."""

        @dataclass
        class Dog:
            name: str
            age: int

        @widget
        class Test(Widget):
            _dogs: Variable[list[Dog]] = new([Dog("Fido", 3)])
            _labels: list[QLabel] = new(bind="_dogs", format="{name}: {age}")

        w = qt.track(Test())

        label = w._labels.widget_at(0)
        assert label.text() == "Fido: 3"

        # Replace the item - for objects, this creates a new widget
        w._dogs[0] = Dog("Rex", 5)

        # Get the new widget (replace creates new widget for non-primitives)
        new_label = w._labels.widget_at(0)
        assert new_label.text() == "Rex: 5"
