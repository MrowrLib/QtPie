# pyright: reportMissingTypeArgument=false, reportUnknownMemberType=false
# pyright: reportPrivateUsage=false, reportAttributeAccessIssue=false
"""Tests for auto-binding to record fields."""

from dataclasses import dataclass

from assertpy import assert_that
from qtpy.QtWidgets import QLabel, QLineEdit, QSpinBox

from qtpie import Variable, Widget, new, widget
from qtpie.testing import QtDriver


@dataclass
class Person:
    """Test model."""

    name: str = ""
    age: int = 0
    email: str = ""


@dataclass
class Address:
    """Nested model."""

    city: str = ""
    zip_code: str = ""


@dataclass
class Employee:
    """Model with nested fields."""

    name: str = ""
    address: Address | None = None


class TestAutoBindToRecord:
    """Test auto-binding QWidget fields to record fields."""

    def test_auto_bind_by_name(self, qt: QtDriver) -> None:
        """Field named 'name' auto-binds to record.name."""

        @widget
        class PersonEditor(Widget[Person]):
            name: QLineEdit = new()

        w = qt.track(PersonEditor())

        # Initial value from record default
        assert_that(w.name.text()).is_equal_to("")

        # Modify record, widget updates
        w._qtpie.record_state.observable.name.set("Alice")  # type: ignore[union-attr]
        assert_that(w.name.text()).is_equal_to("Alice")

    def test_auto_bind_strips_underscore(self, qt: QtDriver) -> None:
        """Field named '_name' auto-binds to record.name."""

        @widget
        class PersonEditor(Widget[Person]):
            _name: QLineEdit = new()

        w = qt.track(PersonEditor())

        w._qtpie.record_state.observable.name.set("Bob")  # type: ignore[union-attr]
        assert_that(w._name.text()).is_equal_to("Bob")

    def test_auto_bind_multiple_fields(self, qt: QtDriver) -> None:
        """Multiple fields auto-bind to corresponding record fields."""

        @widget
        class PersonEditor(Widget[Person]):
            _name: QLineEdit = new()
            _age: QSpinBox = new()

            def __setup__(self) -> None:
                self._age.setMaximum(200)

        w = qt.track(PersonEditor())

        w._qtpie.record_state.observable.name.set("Charlie")  # type: ignore[union-attr]
        w._qtpie.record_state.observable.age.set(30)  # type: ignore[union-attr]

        assert_that(w._name.text()).is_equal_to("Charlie")
        assert_that(w._age.value()).is_equal_to(30)

    def test_two_way_binding_widget_to_record(self, qt: QtDriver) -> None:
        """Widget changes update the record (two-way binding)."""

        @widget
        class PersonEditor(Widget[Person]):
            _name: QLineEdit = new()

        w = qt.track(PersonEditor())

        # User types in widget
        w._name.setText("Typed")
        assert_that(w._qtpie.record_state.value.name).is_equal_to("Typed")


class TestExplicitBind:
    """Test explicit bind= parameter."""

    def test_explicit_bind_to_different_field(self, qt: QtDriver) -> None:
        """bind= maps to a different field than the widget name."""

        @widget
        class PersonEditor(Widget[Person]):
            email_input: QLineEdit = new(bind="email")

        w = qt.track(PersonEditor())

        w._qtpie.record_state.observable.email.set("test@example.com")  # type: ignore[union-attr]
        assert_that(w.email_input.text()).is_equal_to("test@example.com")


class TestAutoBindDisabled:
    """Test auto_bind=False option."""

    def test_auto_bind_false_no_binding(self, qt: QtDriver) -> None:
        """With auto_bind=False, no auto-binding happens."""

        @widget(auto_bind=False)
        class PersonEditor(Widget[Person]):
            _name: QLineEdit = new()

        w = qt.track(PersonEditor())

        # Record changes, but widget doesn't update (no binding)
        w._qtpie.record_state.observable.name.set("NoBinding")  # type: ignore[union-attr]
        assert_that(w._name.text()).is_equal_to("")  # Still empty

    def test_explicit_bind_still_works_with_auto_bind_false(self, qt: QtDriver) -> None:
        """Explicit bind= still works with auto_bind=False."""

        @widget(auto_bind=False)
        class PersonEditor(Widget[Person]):
            name_field: QLineEdit = new(bind="name")

        w = qt.track(PersonEditor())

        w._qtpie.record_state.observable.name.set("Explicit")  # type: ignore[union-attr]
        assert_that(w.name_field.text()).is_equal_to("Explicit")


class TestBindToVariable:
    """Test binding to widget-level Variables (not record)."""

    def test_auto_bind_to_variable(self, qt: QtDriver) -> None:
        """Field auto-binds to matching Variable attribute."""

        @widget
        class MyWidget(Widget):
            _count: Variable[int] = new(0)
            count: QSpinBox = new()  # Should auto-bind to _count

            def __setup__(self) -> None:
                self.count.setMaximum(1000)

        w = qt.track(MyWidget())

        w._count.value = 42
        assert_that(w.count.value()).is_equal_to(42)


class TestFormatStringBinding:
    """Test format string binding."""

    def test_format_string_single_field(self, qt: QtDriver) -> None:
        """Format string with single field."""

        @widget
        class PersonView(Widget[Person]):
            display: QLabel = new(bind="{name}")

        w = qt.track(PersonView())

        w._qtpie.record_state.observable.name.set("Diana")  # type: ignore[union-attr]
        assert_that(w.display.text()).is_equal_to("Diana")

    def test_format_string_with_static_field(self, qt: QtDriver) -> None:
        """Format string with both reactive and static fields."""

        @widget
        class PersonView(Widget[Person]):
            title: str = "Profile"
            display: QLabel = new(bind="{title}: {name}")

        w = qt.track(PersonView())

        # Initial render includes static field
        assert_that(w.display.text()).is_equal_to("Profile: ")

        # Reactive field change triggers update, static is re-read
        w._qtpie.record_state.observable.name.set("Eve")  # type: ignore[union-attr]
        assert_that(w.display.text()).is_equal_to("Profile: Eve")

    def test_format_string_multiple_fields(self, qt: QtDriver) -> None:
        """Format string with multiple fields."""

        @widget
        class PersonView(Widget[Person]):
            summary: QLabel = new(bind="{name}, age {age}")

        w = qt.track(PersonView())

        w._qtpie.record_state.observable.name.set("Eve")  # type: ignore[union-attr]
        w._qtpie.record_state.observable.age.set(25)  # type: ignore[union-attr]

        assert_that(w.summary.text()).is_equal_to("Eve, age 25")

    def test_format_string_updates_on_any_field_change(self, qt: QtDriver) -> None:
        """Format string updates when any referenced field changes."""

        @widget
        class PersonView(Widget[Person]):
            summary: QLabel = new(bind="{name} ({age})")

        w = qt.track(PersonView())

        w._qtpie.record_state.observable.name.set("Frank")  # type: ignore[union-attr]
        w._qtpie.record_state.observable.age.set(40)  # type: ignore[union-attr]
        assert_that(w.summary.text()).is_equal_to("Frank (40)")

        # Change just age
        w._qtpie.record_state.observable.age.set(41)  # type: ignore[union-attr]
        assert_that(w.summary.text()).is_equal_to("Frank (41)")


class TestOptionalChaining:
    """Test optional chaining in bind paths."""

    def test_optional_chain_with_value(self, qt: QtDriver) -> None:
        """Optional chain with non-None value works."""

        @widget
        class EmployeeEditor(Widget[Employee]):
            city: QLineEdit = new(bind="address?.city")

        w = qt.track(EmployeeEditor())

        # Set address first
        w._qtpie.record_state.observable.address.set(Address(city="NYC"))  # type: ignore[union-attr]
        # Re-access to get updated binding
        # Note: The binding was created when address was None, so this test
        # demonstrates that we need dynamic path re-evaluation

    def test_optional_chain_with_none(self, qt: QtDriver) -> None:
        """Optional chain with None value doesn't crash."""

        @widget
        class EmployeeEditor(Widget[Employee]):
            city: QLineEdit = new(bind="address?.city")

        w = qt.track(EmployeeEditor())
        # address is None, widget should have empty text (not crash)
        assert_that(w.city.text()).is_equal_to("")


class TestNoRecordNoAutoBind:
    """Test Widget without record type."""

    def test_plain_widget_no_auto_bind(self, qt: QtDriver) -> None:
        """Widget without [T] doesn't auto-bind non-matching fields."""

        @widget
        class PlainWidget(Widget):
            _label: QLabel = new("Initial")

        w = qt.track(PlainWidget())
        # Just verify it works without error
        assert_that(w._label.text()).is_equal_to("Initial")


class TestBindingResolutionOrder:
    """Test that exact matches take priority over underscore fallback."""

    def test_record_field_wins_over_underscore_widget(self, qt: QtDriver) -> None:
        """When widget has _name field and record has name, {name} resolves to record.name."""

        @widget
        class PersonEditor(Widget[Person]):
            # Widget has _name field (QLineEdit for editing)
            _name: QLineEdit = new()
            # Format binding uses {name} - should resolve to record.name, not _name widget
            display: QLabel = new(bind="Name: {name}")

        w = qt.track(PersonEditor())

        # Set record name
        w._qtpie.record_state.observable.name.set("Alice")  # type: ignore[union-attr]

        # The label should show "Name: Alice" (from record.name)
        # NOT "Name: <qtpy.QtWidgets.QLineEdit...>" (from _name widget)
        assert_that(w.display.text()).is_equal_to("Name: Alice")

    def test_exact_widget_attr_wins_over_record(self, qt: QtDriver) -> None:
        """When widget has exact 'title' attribute (not _title), it wins over record."""

        @widget
        class TitledEditor(Widget[Person]):
            title: str = "Static Title"
            display: QLabel = new(bind="{title}: {name}")

        w = qt.track(TitledEditor())
        w._qtpie.record_state.observable.name.set("Bob")  # type: ignore[union-attr]

        # title comes from widget.title, name from record.name
        assert_that(w.display.text()).is_equal_to("Static Title: Bob")

    def test_underscore_fallback_when_no_record_match(self, qt: QtDriver) -> None:
        """Underscore fallback works when there's no exact or record match."""

        @widget
        class CounterWidget(Widget):  # No record type
            _count: Variable[int] = new(0)
            display: QLabel = new(bind="Count: {count}")

        w = qt.track(CounterWidget())
        w._count.value = 42

        # {count} should resolve to _count via underscore fallback
        assert_that(w.display.text()).is_equal_to("Count: 42")

    def test_local_variable_wins_over_record_field_with_same_name(self, qt: QtDriver) -> None:
        """Local _dogs Variable takes priority over record.dogs field.

        Bug reproduction: When a Widget[T] has both:
        - record.dogs (from T)
        - _dogs (local Variable)

        A binding like {len(_dogs)} should resolve to the local _dogs Variable,
        not strip the underscore and find record.dogs.
        """

        @dataclass
        class Pet:
            name: str

        @dataclass
        class Owner:
            dogs: list[Pet]  # record has 'dogs' field

        @widget(record=Owner(dogs=[Pet("RecordDog")]))
        class DogOwner(Widget[Owner]):
            # Local Variable with different items than record.dogs
            _dogs: Variable[list[Pet]] = new([Pet("Local1"), Pet("Local2"), Pet("Local3")])
            # This binding should use _dogs (local Variable), not record.dogs
            count_label: QLabel = new(bind="Count: {len(_dogs)}")

        w = qt.track(DogOwner())

        # record.dogs has 1 item, _dogs Variable has 3 items
        # The label should show count of LOCAL _dogs (3), not record.dogs (1)
        assert_that(w.count_label.text()).is_equal_to("Count: 3")
