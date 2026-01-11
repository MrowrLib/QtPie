# pyright: reportPrivateUsage=false
# pyright: reportMissingParameterType=false
# pyright: reportUnknownParameterType=false
# pyright: reportUntypedBaseClass=false
# pyright: reportUntypedClassDecorator=false
# pyright: reportUnknownArgumentType=false
# pyright: reportUnknownMemberType=false
# pyright: reportIncompatibleMethodOverride=false
"""Tests for edge cases that might reveal bugs."""

from assertpy import assert_that
from PySide6.QtWidgets import QLabel, QLineEdit

from qtpie import AppBase, Variable, Widget, app, new, widget
from qtpie.testing import QtDriver

# =============================================================================
# TEST: Empty/None values in Variables
# =============================================================================


class TestEmptyVariableValues:
    """Test handling of empty/None values."""

    def test_empty_string_variable(self, qt: QtDriver) -> None:
        """Empty string Variable works."""

        @widget
        class MyWidget(Widget):
            _text: Variable[str] = new("")

        w = MyWidget()
        qt.track(w)

        assert_that(w._text.value).is_equal_to("")
        assert_that(w.is_dirty.get()).is_false()

    def test_none_in_optional_variable(self, qt: QtDriver) -> None:
        """None in optional Variable works."""

        @widget
        class MyWidget(Widget):
            _maybe: Variable[str | None] = new(None)

        w = MyWidget()
        qt.track(w)

        assert_that(w._maybe.value).is_none()
        w._maybe.value = "set"
        assert_that(w._maybe.value).is_equal_to("set")

    def test_empty_list_variable(self, qt: QtDriver) -> None:
        """Empty list Variable works."""

        @widget
        class MyWidget(Widget):
            _items: Variable[list[str]] = new([])

        w = MyWidget()
        qt.track(w)

        assert_that(w._items.value).is_length(0)

    def test_empty_dict_variable(self, qt: QtDriver) -> None:
        """Empty dict Variable works."""

        @widget
        class MyWidget(Widget):
            _data: Variable[dict[str, int]] = new({})

        w = MyWidget()
        qt.track(w)

        assert_that(len(w._data.value)).is_equal_to(0)


# =============================================================================
# TEST: Multiple Variable changes in sequence
# =============================================================================


class TestRapidVariableChanges:
    """Test rapid successive Variable changes."""

    def test_rapid_value_changes(self, qt: QtDriver) -> None:
        """Multiple rapid value changes work correctly."""

        @widget
        class MyWidget(Widget):
            _count: Variable[int] = new(0)

        w = MyWidget()
        qt.track(w)

        for i in range(100):
            w._count.value = i

        assert_that(w._count.value).is_equal_to(99)

    def test_rapid_list_changes(self, qt: QtDriver) -> None:
        """Multiple rapid list operations work."""

        @widget
        class MyWidget(Widget):
            _items: Variable[list[str]] = new([])

        w = MyWidget()
        qt.track(w)

        for i in range(50):
            w._items.append(f"item{i}")

        assert_that(w._items.value).is_length(50)

        for _ in range(25):
            w._items.pop()

        assert_that(w._items.value).is_length(25)


# =============================================================================
# TEST: Nested format expressions
# =============================================================================


class TestComplexFormatExpressions:
    """Test complex format string expressions."""

    def test_nested_property_access(self, qt: QtDriver) -> None:
        """Nested property access in format strings."""
        from dataclasses import dataclass

        @dataclass
        class Address:
            city: str = ""

        @dataclass
        class Person:
            name: str = ""
            address: Address | None = None

        @widget(record=Person("John", Address("NYC")))
        class MyWidget(Widget[Person]):
            city_label: QLabel = new(bind="{record.address.city}")

        w = MyWidget()
        qt.track(w)

        assert_that(w.city_label.text()).is_equal_to("NYC")

    def test_math_expression_in_bind(self, qt: QtDriver) -> None:
        """Math expressions in bind work."""

        @widget
        class MyWidget(Widget):
            _x: Variable[int] = new(10)
            _y: Variable[int] = new(5)
            result: QLabel = new(bind="{_x + _y}")

        w = MyWidget()
        qt.track(w)

        assert_that(w.result.text()).is_equal_to("15")

        w._x.value = 20
        assert_that(w.result.text()).is_equal_to("25")

    def test_string_method_in_bind(self, qt: QtDriver) -> None:
        """String methods in bind work."""

        @widget
        class MyWidget(Widget):
            _name: Variable[str] = new("hello")
            upper_label: QLabel = new(bind="{_name.upper()}")

        w = MyWidget()
        qt.track(w)

        assert_that(w.upper_label.text()).is_equal_to("HELLO")

        w._name.value = "world"
        assert_that(w.upper_label.text()).is_equal_to("WORLD")

    def test_len_function_in_bind(self, qt: QtDriver) -> None:
        """len() in bind works."""

        @widget
        class MyWidget(Widget):
            _items: Variable[list[str]] = new(["a", "b", "c"])
            count_label: QLabel = new(bind="Count: {len(_items)}")

        w = MyWidget()
        qt.track(w)

        assert_that(w.count_label.text()).is_equal_to("Count: 3")

        w._items.append("d")
        assert_that(w.count_label.text()).is_equal_to("Count: 4")


# =============================================================================
# TEST: Two-way bindings
# =============================================================================


class TestTwoWayBindings:
    """Test two-way bindings work correctly."""

    def test_lineedit_two_way_binding(self, qt: QtDriver) -> None:
        """QLineEdit two-way binding syncs both directions."""

        @widget
        class MyWidget(Widget):
            _name: Variable[str] = new("")
            name_input: QLineEdit = new(bind="_name")

        w = MyWidget()
        qt.track(w)

        # Variable -> Widget
        w._name.value = "from variable"
        assert_that(w.name_input.text()).is_equal_to("from variable")

        # Widget -> Variable
        w.name_input.setText("from widget")
        w.name_input.textChanged.emit("from widget")  # Trigger signal
        assert_that(w._name.value).is_equal_to("from widget")

    def test_variable_tw_two_way_binding(self, qt: QtDriver) -> None:
        """Variable[T, W] has two-way binding."""

        @widget
        class MyWidget(Widget):
            _name: Variable[str, QLineEdit] = new("")

        w = MyWidget()
        qt.track(w)

        # Variable -> Widget
        w._name.value = "test"
        assert_that(w._name.widget.text()).is_equal_to("test")

        # Widget -> Variable
        w._name.widget.setText("changed")
        w._name.widget.textChanged.emit("changed")
        assert_that(w._name.value).is_equal_to("changed")


# =============================================================================
# TEST: Dirty tracking edge cases
# =============================================================================


class TestDirtyTrackingEdgeCases:
    """Test dirty tracking edge cases."""

    def test_set_same_value_not_dirty(self, qt: QtDriver) -> None:
        """Setting same value doesn't mark dirty."""

        @widget
        class MyWidget(Widget):
            _count: Variable[int] = new(5)

        w = MyWidget()
        qt.track(w)

        assert_that(w.is_dirty.get()).is_false()
        w._count.value = 5  # Same value
        assert_that(w.is_dirty.get()).is_false()

    def test_reset_dirty_clears_all(self, qt: QtDriver) -> None:
        """reset_dirty clears all dirty fields."""

        @widget
        class MyWidget(Widget):
            _a: Variable[int] = new(0)
            _b: Variable[str] = new("")
            _c: Variable[bool] = new(False)

        w = MyWidget()
        qt.track(w)

        w._a.value = 1
        w._b.value = "changed"
        w._c.value = True

        assert_that(w.is_dirty.get()).is_true()
        assert_that(w.dirty_fields).is_length(3)

        w.reset_dirty()

        assert_that(w.is_dirty.get()).is_false()
        assert_that(w.dirty_fields).is_length(0)

    def test_dirty_after_reset_and_change(self, qt: QtDriver) -> None:
        """Dirty works correctly after reset and new change."""

        @widget
        class MyWidget(Widget):
            _count: Variable[int] = new(0)

        w = MyWidget()
        qt.track(w)

        w._count.value = 1
        assert_that(w.is_dirty.get()).is_true()

        w.reset_dirty()
        assert_that(w.is_dirty.get()).is_false()

        w._count.value = 2
        assert_that(w.is_dirty.get()).is_true()


# =============================================================================
# TEST: Validation edge cases
# =============================================================================


class TestValidationEdgeCases:
    """Test validation edge cases."""

    def test_multiple_validators_same_field(self, qt: QtDriver) -> None:
        """Multiple validators on same field all run."""

        @widget
        class MyWidget(Widget):
            _password: Variable[str] = new("")

            def __setup__(self) -> None:
                self.add_validator("_password", "min_len", lambda v: None if len(v) >= 8 else "Min 8 chars")
                self.add_validator("_password", "has_number", lambda v: None if any(c.isdigit() for c in v) else "Need number")

        w = MyWidget()
        qt.track(w)

        assert_that(w.is_valid.get()).is_false()

        w._password.value = "short1"  # Has number but too short
        assert_that(w.is_valid.get()).is_false()

        w._password.value = "longenough"  # Long enough but no number
        assert_that(w.is_valid.get()).is_false()

        w._password.value = "longenough1"  # Valid!
        assert_that(w.is_valid.get()).is_true()

    def test_remove_validator(self, qt: QtDriver) -> None:
        """Removing validator updates validity."""

        @widget
        class MyWidget(Widget):
            _name: Variable[str] = new("")

            def __setup__(self) -> None:
                self.add_validator("_name", "required", lambda v: None if v else "Required")

        w = MyWidget()
        qt.track(w)

        assert_that(w.is_valid.get()).is_false()

        w.remove_validator("_name", "required")
        assert_that(w.is_valid.get()).is_true()

    def test_validation_errors_structure(self, qt: QtDriver) -> None:
        """validation_errors has correct structure."""

        @widget
        class MyWidget(Widget):
            _name: Variable[str] = new("")
            _age: Variable[int] = new(-1)

            def __setup__(self) -> None:
                self.add_validator("_name", "required", lambda v: None if v else "Name required")
                self.add_validator("_age", "positive", lambda v: None if v >= 0 else "Must be positive")

        w = MyWidget()
        qt.track(w)

        errors = w.validation_errors
        assert_that("_name" in errors).is_true()
        assert_that("_age" in errors).is_true()


# =============================================================================
# TEST: Repeater edge cases
# =============================================================================


class TestRepeaterEdgeCases:
    """Test widget repeater edge cases."""

    def test_repeater_empty_list(self, qt: QtDriver) -> None:
        """Repeater with empty list creates no widgets."""

        @widget
        class MyWidget(Widget):
            _items: Variable[list[str]] = new([])
            items: list[QLabel] = new(bind="_items")

        w = MyWidget()
        qt.track(w)

        # .widgets is on WidgetRepeater, but type annotation is list[QLabel]
        assert_that(w.items.widgets).is_length(0)  # pyright: ignore[reportAttributeAccessIssue]

    def test_repeater_add_to_empty(self, qt: QtDriver) -> None:
        """Adding to empty list creates widget."""

        @widget
        class MyWidget(Widget):
            _items: Variable[list[str]] = new([])
            items: list[QLabel] = new(bind="_items")

        w = MyWidget()
        qt.track(w)

        w._items.append("first")
        assert_that(w.items.widgets).is_length(1)  # pyright: ignore[reportAttributeAccessIssue]

    def test_repeater_clear_all(self, qt: QtDriver) -> None:
        """Clearing list removes all widgets."""

        @widget
        class MyWidget(Widget):
            _items: Variable[list[str]] = new(["a", "b", "c"])
            items: list[QLabel] = new(bind="_items")

        w = MyWidget()
        qt.track(w)

        assert_that(w.items.widgets).is_length(3)  # pyright: ignore[reportAttributeAccessIssue]

        w._items.clear()
        assert_that(w.items.widgets).is_length(0)  # pyright: ignore[reportAttributeAccessIssue]


# =============================================================================
# TEST: Layout exclusion
# =============================================================================


class TestLayoutExclusion:
    """Test layout=False excludes widgets."""

    def test_widget_layout_false(self, qt: QtDriver) -> None:
        """layout=False excludes widget from layout."""

        @widget
        class MyWidget(Widget):
            visible_label: QLabel = new("Visible")
            hidden_label: QLabel = new("Hidden", layout=False)

        w = MyWidget()
        qt.track(w)

        # Both exist as fields
        assert_that(w.visible_label.text()).is_equal_to("Visible")
        assert_that(w.hidden_label.text()).is_equal_to("Hidden")

    def test_variable_tw_layout_false(self, qt: QtDriver) -> None:
        """Variable[T, W] with layout=False excludes widget."""

        @widget
        class MyWidget(Widget):
            _visible: Variable[str, QLineEdit] = new("")
            _hidden: Variable[str, QLineEdit] = new("")(layout=False)

        w = MyWidget()
        qt.track(w)

        # Both exist
        assert_that(w._visible.widget).is_instance_of(QLineEdit)
        assert_that(w._hidden.widget).is_instance_of(QLineEdit)


# =============================================================================
# TEST: Multiple instances are independent
# =============================================================================


class TestMultipleInstances:
    """Test multiple instances are independent."""

    def test_widget_instances_independent(self, qt: QtDriver) -> None:
        """Multiple Widget instances have independent state."""

        @widget
        class MyWidget(Widget):
            _count: Variable[int] = new(0)

        w1 = MyWidget()
        w2 = MyWidget()
        qt.track(w1)
        qt.track(w2)

        w1._count.value = 10
        assert_that(w1._count.value).is_equal_to(10)
        assert_that(w2._count.value).is_equal_to(0)

    def test_app_instances_independent(self, qt: QtDriver) -> None:
        """Multiple App instances have independent state."""

        @app(system_tray=False, window=False)
        class MyApp(AppBase):
            _count: Variable[int] = new(0)

        a1 = MyApp()
        a2 = MyApp()

        a1._count.value = 5
        assert_that(a1._count.value).is_equal_to(5)
        assert_that(a2._count.value).is_equal_to(0)
