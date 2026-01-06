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
