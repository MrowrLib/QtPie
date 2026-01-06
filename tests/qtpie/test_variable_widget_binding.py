# pyright: reportPrivateUsage=false, reportOptionalMemberAccess=false
# pyright: reportAttributeAccessIssue=false, reportUnknownMemberType=false
# pyright: reportUnknownVariableType=false, reportCallIssue=false
# pyright: reportIndexIssue=false, reportArgumentType=false
"""Tests for Variable[T, Widget[T]] binding - binding Variables to custom Widget[T] subclasses."""

from dataclasses import dataclass

import pytest
from qtpy.QtWidgets import QLabel, QLineEdit, QSpinBox

from qtpie import Variable, Widget, new, widget
from qtpie.testing import QtDriver


@dataclass
class Dog:
    """Test model class."""

    name: str
    age: int


@widget(layout="form")
class DogEditor(Widget[Dog]):
    """Editor widget for Dog records."""

    _name: QLineEdit = new(label="Dog's Name")
    _age: QSpinBox = new(label="Dog's Age")


class TestSingleWidgetBinding:
    """Test Variable[T, Widget[T]] for single records."""

    def test_variable_with_widget_subclass_creates_widget(self, qt: QtDriver) -> None:
        """Variable[Dog, DogEditor] creates a DogEditor widget."""

        @widget
        class TestWidget(Widget):
            dog: Variable[Dog, DogEditor] = new(Dog("Fido", 3))  # type: ignore[type-arg]

        w = qt.track(TestWidget())

        # Should have created a DogEditor
        assert isinstance(w.dog.widget, DogEditor)

    def test_variable_shares_proxy_with_widget_record(self, qt: QtDriver) -> None:
        """Variable and Widget[T].record share the same ObservableProxy."""

        @widget
        class TestWidget(Widget):
            dog: Variable[Dog, DogEditor] = new(Dog("Fido", 3))  # type: ignore[type-arg]

        w = qt.track(TestWidget())
        editor = w.dog.widget

        # The underlying observable should be shared
        assert w.dog.observable is editor.record_state.observable

    def test_variable_change_updates_widget_record(self, qt: QtDriver) -> None:
        """Changing Variable fields updates Widget[T].record."""

        @widget
        class TestWidget(Widget):
            dog: Variable[Dog, DogEditor] = new(Dog("Fido", 3))  # type: ignore[type-arg]

        w = qt.track(TestWidget())
        editor = w.dog.widget

        # Change via parent's Variable
        w.dog.observable.name.set("Buddy")

        # Should be visible in child widget's record
        assert editor.record.name == "Buddy"

    def test_widget_record_change_updates_variable(self, qt: QtDriver) -> None:
        """Changing Widget[T].record updates the parent Variable."""

        @widget
        class TestWidget(Widget):
            dog: Variable[Dog, DogEditor] = new(Dog("Fido", 3))  # type: ignore[type-arg]

        w = qt.track(TestWidget())
        editor = w.dog.widget

        # Change via child widget's record
        editor.record.name = "Rex"

        # Should be visible in parent's Variable
        assert w.dog.observable.name.get() == "Rex"

    def test_widget_bindings_work(self, qt: QtDriver) -> None:
        """DogEditor's internal QLineEdit/QSpinBox bind to record fields."""

        @widget
        class TestWidget(Widget):
            dog: Variable[Dog, DogEditor] = new(Dog("Fido", 3))  # type: ignore[type-arg]

        w = qt.track(TestWidget())
        editor = w.dog.widget

        # The name field should show "Fido"
        assert editor._name.text() == "Fido"
        assert editor._age.value() == 3

        # Change via parent Variable
        w.dog.observable.name.set("Buddy")
        assert editor._name.text() == "Buddy"

        # Change via child widget's QLineEdit
        editor._name.setText("Max")
        assert w.dog.observable.name.get() == "Max"

    def test_initial_value_populates_widget(self, qt: QtDriver) -> None:
        """Initial Variable value populates Widget[T].record."""

        @widget
        class TestWidget(Widget):
            dog: Variable[Dog, DogEditor] = new(Dog("Spot", 5))  # type: ignore[type-arg]

        w = qt.track(TestWidget())
        editor = w.dog.widget

        assert editor.record.name == "Spot"
        assert editor.record.age == 5


class TestListWidgetBinding:
    """Test Variable[list[T], Widget[T]] with WidgetRepeater."""

    def test_list_variable_creates_multiple_editors(self, qt: QtDriver) -> None:
        """Variable[list[Dog], DogEditor] creates one DogEditor per item."""

        @widget
        class TestWidget(Widget):
            dogs: Variable[list[Dog], DogEditor] = new(
                [  # type: ignore[type-arg]
                    Dog("Fido", 3),
                    Dog("Rex", 5),
                ]
            )

        w = qt.track(TestWidget())

        # Should have created a WidgetRepeater with 2 editors
        repeater = w.dogs.widget
        assert repeater.widget_count() == 2

        # Each should be a DogEditor
        assert isinstance(repeater.widget_at(0), DogEditor)
        assert isinstance(repeater.widget_at(1), DogEditor)

    def test_list_editors_show_correct_values(self, qt: QtDriver) -> None:
        """Each DogEditor shows its item's values."""

        @widget
        class TestWidget(Widget):
            dogs: Variable[list[Dog], DogEditor] = new(
                [  # type: ignore[type-arg]
                    Dog("Fido", 3),
                    Dog("Rex", 5),
                ]
            )

        w = qt.track(TestWidget())
        repeater = w.dogs.widget

        editor0 = repeater.widget_at(0)
        editor1 = repeater.widget_at(1)

        assert editor0._name.text() == "Fido"
        assert editor0._age.value() == 3

        assert editor1._name.text() == "Rex"
        assert editor1._age.value() == 5

    def test_list_append_adds_editor(self, qt: QtDriver) -> None:
        """Appending to list adds a new DogEditor."""

        @widget
        class TestWidget(Widget):
            dogs: Variable[list[Dog], DogEditor] = new([Dog("Fido", 3)])  # type: ignore[type-arg]

        w = qt.track(TestWidget())
        repeater = w.dogs.widget

        assert repeater.widget_count() == 1

        # Append a new dog
        w.dogs.append(Dog("Buddy", 2))

        assert repeater.widget_count() == 2
        editor1 = repeater.widget_at(1)
        assert editor1._name.text() == "Buddy"
        assert editor1._age.value() == 2

    def test_list_remove_removes_editor(self, qt: QtDriver) -> None:
        """Removing from list removes the DogEditor."""

        @widget
        class TestWidget(Widget):
            dogs: Variable[list[Dog], DogEditor] = new(
                [  # type: ignore[type-arg]
                    Dog("Fido", 3),
                    Dog("Rex", 5),
                ]
            )

        w = qt.track(TestWidget())
        repeater = w.dogs.widget

        assert repeater.widget_count() == 2

        # Remove first dog
        w.dogs.remove(Dog("Fido", 3))

        assert repeater.widget_count() == 1
        editor0 = repeater.widget_at(0)
        assert editor0._name.text() == "Rex"

    def test_edit_in_one_editor_updates_list(self, qt: QtDriver) -> None:
        """Editing in a DogEditor updates the underlying list item."""

        @widget
        class TestWidget(Widget):
            dogs: Variable[list[Dog], DogEditor] = new([Dog("Fido", 3)])  # type: ignore[type-arg]

        w = qt.track(TestWidget())
        repeater = w.dogs.widget
        editor = repeater.widget_at(0)

        # Edit via the editor's QLineEdit
        editor._name.setText("Buddy")

        # The underlying list should reflect the change
        assert w.dogs[0].name == "Buddy"


class TestMixedScenarios:
    """Test various edge cases and mixed scenarios."""

    def test_widget_without_record_type_raises_error(self, qt: QtDriver) -> None:
        """Using Widget (not Widget[T]) as widget type fails gracefully."""

        @widget
        class PlainWidget(Widget):
            _label: QLabel = new("Hello")

        # This should fail because PlainWidget has no record type
        @widget
        class TestWidget(Widget):
            plain: Variable[str, PlainWidget] = new("test")  # type: ignore[type-arg]

        # Should raise because PlainWidget doesn't know how to bind
        with pytest.raises(ValueError, match="No binding registered"):
            qt.track(TestWidget())

    def test_nested_widget_with_record(self, qt: QtDriver) -> None:
        """Widget[T] containing Variable[U, Widget[U]] works."""

        @dataclass
        class Owner:
            name: str

        @widget(layout="form")
        class OwnerEditor(Widget[Owner]):
            _name: QLineEdit = new(label="Owner Name")

        @dataclass
        class Pet:
            pet_name: str
            owner: Owner

        @widget(layout="vertical")
        class PetWithOwner(Widget[Pet]):
            _pet_name: QLineEdit = new()
            owner_editor: Variable[Owner, OwnerEditor] = new(Owner("John"))  # type: ignore[type-arg]

        w = qt.track(PetWithOwner())

        # Set up the record with an owner
        w.record = Pet("Fido", Owner("Jane"))

        # The nested owner editor should work
        assert w.owner_editor.widget._name.text() == "John"  # Initial value from new()

        # Change via the variable
        w.owner_editor.observable.name.set("Bob")
        assert w.owner_editor.widget._name.text() == "Bob"
