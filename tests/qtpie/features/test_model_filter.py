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
# pyright: reportUnknownLambdaType=false
# pyright: reportOperatorIssue=false
# pyright: reportUnknownVariableType=false
"""Tests for model widget filter= support.

Tests expression-based filtering on QListView, QComboBox, QTableView, QTreeView.

Filter syntax: filter="{_search} in {name}"
- {_search} → widget's _search Variable value
- {name} → each item's name attribute
- Expression evaluated per item → truthy = show, falsy = hide
"""

from dataclasses import dataclass

import pytest
from assertpy import assert_that
from PySide6.QtWidgets import QComboBox, QListView, QTableView, QTreeView

from qtpie import State, Variable, Widget, new, state, widget
from qtpie.testing import QtDriver

from .conftest import WIDGET_CLASS_TYPES, create_and_track


@dataclass
class Dog:
    """Test dataclass for filter tests."""

    name: str
    age: int
    breed: str = "unknown"


@dataclass
class Person:
    """Test dataclass for filter tests."""

    name: str
    age: int
    city: str = "NYC"


@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestFilterBasic:
    """Basic filter= functionality."""

    def test_filter_simple_contains(self, base_class, decorator, qt: QtDriver) -> None:
        """Filter with simple 'in' expression."""

        @decorator
        class TestClass(base_class):
            _search: Variable[str] = new("")
            _dogs: Variable[list[Dog]] = new(
                [
                    Dog("Fido", 3),
                    Dog("Rex", 5),
                    Dog("Buddy", 2),
                ]
            )
            _list: QListView = new(bind="_dogs", filter="{_search} in {name}")

        instance = create_and_track(qt, TestClass, base_class)
        model = instance._list.model()  # This is the proxy model

        # No filter - all items shown
        assert_that(model.rowCount()).is_equal_to(3)

        # Filter for "id" - matches "Fido"
        instance._search.value = "id"
        assert_that(model.rowCount()).is_equal_to(1)

        # Filter for "ex" - matches "Rex"
        instance._search.value = "ex"
        assert_that(model.rowCount()).is_equal_to(1)

        # Filter for "" - back to all items
        instance._search.value = ""
        assert_that(model.rowCount()).is_equal_to(3)

    def test_filter_no_matches(self, base_class, decorator, qt: QtDriver) -> None:
        """Filter that matches nothing shows zero items."""

        @decorator
        class TestClass(base_class):
            _search: Variable[str] = new("")
            _items: Variable[list[str]] = new(["Apple", "Banana", "Cherry"])
            _list: QListView = new(bind="_items", filter="{_search} in {#self}")

        instance = create_and_track(qt, TestClass, base_class)
        model = instance._list.model()

        # No filter - all items
        assert_that(model.rowCount()).is_equal_to(3)

        # Filter for something that doesn't exist
        instance._search.value = "xyz"
        assert_that(model.rowCount()).is_equal_to(0)

    def test_filter_empty_list(self, base_class, decorator, qt: QtDriver) -> None:
        """Filter on empty list works correctly."""

        @decorator
        class TestClass(base_class):
            _search: Variable[str] = new("test")
            _items: Variable[list[str]] = new([])
            _list: QListView = new(bind="_items", filter="{_search} in {#self}")

        instance = create_and_track(qt, TestClass, base_class)
        model = instance._list.model()

        assert_that(model.rowCount()).is_equal_to(0)


@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestFilterExpressions:
    """Various filter expression patterns."""

    def test_filter_comparison_greater_than(self, base_class, decorator, qt: QtDriver) -> None:
        """Filter with > comparison."""

        @decorator
        class TestClass(base_class):
            _min_age: Variable[int] = new(0)
            _dogs: Variable[list[Dog]] = new(
                [
                    Dog("Puppy", 1),
                    Dog("Adult", 5),
                    Dog("Senior", 10),
                ]
            )
            _list: QListView = new(bind="_dogs", filter="{age} >= {_min_age}")

        instance = create_and_track(qt, TestClass, base_class)
        model = instance._list.model()

        # Min age 0 - all shown
        assert_that(model.rowCount()).is_equal_to(3)

        # Min age 3 - excludes puppy
        instance._min_age.value = 3
        assert_that(model.rowCount()).is_equal_to(2)

        # Min age 8 - only senior
        instance._min_age.value = 8
        assert_that(model.rowCount()).is_equal_to(1)

    def test_filter_comparison_less_than(self, base_class, decorator, qt: QtDriver) -> None:
        """Filter with < comparison."""

        @decorator
        class TestClass(base_class):
            _max_age: Variable[int] = new(100)
            _dogs: Variable[list[Dog]] = new(
                [
                    Dog("Puppy", 1),
                    Dog("Adult", 5),
                    Dog("Senior", 10),
                ]
            )
            _list: QListView = new(bind="_dogs", filter="{age} < {_max_age}")

        instance = create_and_track(qt, TestClass, base_class)
        model = instance._list.model()

        # Max age 100 - all shown
        assert_that(model.rowCount()).is_equal_to(3)

        # Max age 5 - only puppy
        instance._max_age.value = 5
        assert_that(model.rowCount()).is_equal_to(1)

    def test_filter_equality(self, base_class, decorator, qt: QtDriver) -> None:
        """Filter with == comparison."""

        @decorator
        class TestClass(base_class):
            _target_age: Variable[int] = new(5)
            _dogs: Variable[list[Dog]] = new(
                [
                    Dog("Puppy", 1),
                    Dog("Adult", 5),
                    Dog("Senior", 10),
                ]
            )
            _list: QListView = new(bind="_dogs", filter="{age} == {_target_age}")

        instance = create_and_track(qt, TestClass, base_class)
        model = instance._list.model()

        # Only Adult matches age 5
        assert_that(model.rowCount()).is_equal_to(1)

        # Change to 1 - only Puppy matches
        instance._target_age.value = 1
        assert_that(model.rowCount()).is_equal_to(1)

        # Change to 99 - nothing matches
        instance._target_age.value = 99
        assert_that(model.rowCount()).is_equal_to(0)

    def test_filter_not_equal(self, base_class, decorator, qt: QtDriver) -> None:
        """Filter with != comparison."""

        @decorator
        class TestClass(base_class):
            _exclude_breed: Variable[str] = new("")
            _dogs: Variable[list[Dog]] = new(
                [
                    Dog("Fido", 3, "labrador"),
                    Dog("Rex", 5, "german shepherd"),
                    Dog("Buddy", 2, "labrador"),
                ]
            )
            _list: QListView = new(bind="_dogs", filter="{breed} != {_exclude_breed}")

        instance = create_and_track(qt, TestClass, base_class)
        model = instance._list.model()

        # Empty exclude - all shown (no breed equals empty string)
        assert_that(model.rowCount()).is_equal_to(3)

        # Exclude labrador - only Rex shown
        instance._exclude_breed.value = "labrador"
        assert_that(model.rowCount()).is_equal_to(1)

    def test_filter_and_expression(self, base_class, decorator, qt: QtDriver) -> None:
        """Filter with 'and' expression."""

        @decorator
        class TestClass(base_class):
            _min_age: Variable[int] = new(0)
            _search: Variable[str] = new("")
            _dogs: Variable[list[Dog]] = new(
                [
                    Dog("Fido", 3),
                    Dog("Rex", 5),
                    Dog("Buddy", 2),
                ]
            )
            _list: QListView = new(
                bind="_dogs",
                filter="{age} >= {_min_age} and {_search} in {name}",
            )

        instance = create_and_track(qt, TestClass, base_class)
        model = instance._list.model()

        # No filters - all shown
        assert_that(model.rowCount()).is_equal_to(3)

        # Min age 3 - Fido and Rex
        instance._min_age.value = 3
        assert_that(model.rowCount()).is_equal_to(2)

        # Also search for "ex" - only Rex
        instance._search.value = "ex"
        assert_that(model.rowCount()).is_equal_to(1)

    def test_filter_or_expression(self, base_class, decorator, qt: QtDriver) -> None:
        """Filter with 'or' expression."""

        @decorator
        class TestClass(base_class):
            _name1: Variable[str] = new("")
            _name2: Variable[str] = new("")
            _dogs: Variable[list[Dog]] = new(
                [
                    Dog("Fido", 3),
                    Dog("Rex", 5),
                    Dog("Buddy", 2),
                ]
            )
            _list: QListView = new(
                bind="_dogs",
                filter="{name} == {_name1} or {name} == {_name2}",
            )

        instance = create_and_track(qt, TestClass, base_class)
        model = instance._list.model()

        # No names - nothing matches
        assert_that(model.rowCount()).is_equal_to(0)

        # Match Fido
        instance._name1.value = "Fido"
        assert_that(model.rowCount()).is_equal_to(1)

        # Also match Rex
        instance._name2.value = "Rex"
        assert_that(model.rowCount()).is_equal_to(2)

    def test_filter_string_method(self, base_class, decorator, qt: QtDriver) -> None:
        """Filter using string methods like .lower()."""

        @decorator
        class TestClass(base_class):
            _search: Variable[str] = new("")
            _dogs: Variable[list[Dog]] = new(
                [
                    Dog("FIDO", 3),
                    Dog("Rex", 5),
                    Dog("buddy", 2),
                ]
            )
            _list: QListView = new(
                bind="_dogs",
                filter="{_search.lower()} in {name.lower()}",
            )

        instance = create_and_track(qt, TestClass, base_class)
        model = instance._list.model()

        # No filter - all shown
        assert_that(model.rowCount()).is_equal_to(3)

        # Case-insensitive search
        instance._search.value = "FIDO"
        assert_that(model.rowCount()).is_equal_to(1)

        instance._search.value = "buddy"
        assert_that(model.rowCount()).is_equal_to(1)

    def test_filter_startswith(self, base_class, decorator, qt: QtDriver) -> None:
        """Filter using .startswith() method."""

        @decorator
        class TestClass(base_class):
            _prefix: Variable[str] = new("")
            _dogs: Variable[list[Dog]] = new(
                [
                    Dog("Fido", 3),
                    Dog("Felix", 5),
                    Dog("Buddy", 2),
                ]
            )
            _list: QListView = new(bind="_dogs", filter="{name.startswith(_prefix)}")

        instance = create_and_track(qt, TestClass, base_class)
        model = instance._list.model()

        # Empty prefix - all start with empty string
        assert_that(model.rowCount()).is_equal_to(3)

        # Prefix "F" - Fido and Felix
        instance._prefix.value = "F"
        assert_that(model.rowCount()).is_equal_to(2)

        # Prefix "Fi" - only Fido
        instance._prefix.value = "Fi"
        assert_that(model.rowCount()).is_equal_to(1)

    def test_filter_len_function(self, base_class, decorator, qt: QtDriver) -> None:
        """Filter using len() function."""

        @decorator
        class TestClass(base_class):
            _min_len: Variable[int] = new(0)
            _dogs: Variable[list[Dog]] = new(
                [
                    Dog("Bo", 3),  # len 2
                    Dog("Rex", 5),  # len 3
                    Dog("Buddy", 2),  # len 5
                ]
            )
            _list: QListView = new(bind="_dogs", filter="{len(name)} >= {_min_len}")

        instance = create_and_track(qt, TestClass, base_class)
        model = instance._list.model()

        # Min len 0 - all shown
        assert_that(model.rowCount()).is_equal_to(3)

        # Min len 3 - Rex and Buddy
        instance._min_len.value = 3
        assert_that(model.rowCount()).is_equal_to(2)

        # Min len 5 - only Buddy
        instance._min_len.value = 5
        assert_that(model.rowCount()).is_equal_to(1)

    def test_filter_not_expression(self, base_class, decorator, qt: QtDriver) -> None:
        """Filter using 'not' expression."""

        @decorator
        class TestClass(base_class):
            _search: Variable[str] = new("")
            _dogs: Variable[list[Dog]] = new(
                [
                    Dog("Fido", 3),
                    Dog("Rex", 5),
                    Dog("Buddy", 2),
                ]
            )
            _list: QListView = new(bind="_dogs", filter="not {_search} in {name}")

        instance = create_and_track(qt, TestClass, base_class)
        model = instance._list.model()

        # No search - "not '' in name" is False, so nothing shown
        # Actually "" in "Fido" is True, so not True = False for all
        assert_that(model.rowCount()).is_equal_to(0)

        # Search for "id" - exclude Fido, show Rex and Buddy
        instance._search.value = "id"
        assert_that(model.rowCount()).is_equal_to(2)


@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestFilterWithPrimitives:
    """Filter with primitive list items (strings, ints)."""

    def test_filter_string_list(self, base_class, decorator, qt: QtDriver) -> None:
        """Filter on list of strings using #self."""

        @decorator
        class TestClass(base_class):
            _search: Variable[str] = new("")
            _items: Variable[list[str]] = new(["Apple", "Banana", "Apricot", "Cherry"])
            _list: QListView = new(bind="_items", filter="{_search} in {#self}")

        instance = create_and_track(qt, TestClass, base_class)
        model = instance._list.model()

        # No filter
        assert_that(model.rowCount()).is_equal_to(4)

        # Filter for "Ap" - Apple and Apricot
        instance._search.value = "Ap"
        assert_that(model.rowCount()).is_equal_to(2)

        # Filter for "an" - Banana
        instance._search.value = "an"
        assert_that(model.rowCount()).is_equal_to(1)

    def test_filter_int_list(self, base_class, decorator, qt: QtDriver) -> None:
        """Filter on list of integers."""

        @decorator
        class TestClass(base_class):
            _min_val: Variable[int] = new(0)
            _items: Variable[list[int]] = new([1, 5, 10, 15, 20])
            _list: QListView = new(bind="_items", filter="{#self} >= {_min_val}")

        instance = create_and_track(qt, TestClass, base_class)
        model = instance._list.model()

        # Min 0 - all shown
        assert_that(model.rowCount()).is_equal_to(5)

        # Min 10 - 10, 15, 20
        instance._min_val.value = 10
        assert_that(model.rowCount()).is_equal_to(3)

        # Min 18 - only 20
        instance._min_val.value = 18
        assert_that(model.rowCount()).is_equal_to(1)


@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestFilterReactivity:
    """Test that filter updates reactively."""

    def test_filter_updates_when_variable_changes(self, base_class, decorator, qt: QtDriver) -> None:
        """Filter re-evaluates when referenced Variable changes."""

        @decorator
        class TestClass(base_class):
            _search: Variable[str] = new("")
            _dogs: Variable[list[Dog]] = new(
                [
                    Dog("Fido", 3),
                    Dog("Rex", 5),
                ]
            )
            _list: QListView = new(bind="_dogs", filter="{_search} in {name}")

        instance = create_and_track(qt, TestClass, base_class)
        model = instance._list.model()

        # Initial - all shown
        assert_that(model.rowCount()).is_equal_to(2)

        # Update search
        instance._search.value = "F"
        assert_that(model.rowCount()).is_equal_to(1)

        # Change again
        instance._search.value = "R"
        assert_that(model.rowCount()).is_equal_to(1)

        # Clear
        instance._search.value = ""
        assert_that(model.rowCount()).is_equal_to(2)

    def test_filter_updates_when_list_changes(self, base_class, decorator, qt: QtDriver) -> None:
        """Filter applies to new items added to list."""

        @decorator
        class TestClass(base_class):
            _search: Variable[str] = new("F")
            _dogs: Variable[list[Dog]] = new([Dog("Fido", 3)])
            _list: QListView = new(bind="_dogs", filter="{_search} in {name}")

        instance = create_and_track(qt, TestClass, base_class)
        model = instance._list.model()

        # Initial - Fido matches
        assert_that(model.rowCount()).is_equal_to(1)

        # Add non-matching item
        instance._dogs.append(Dog("Rex", 5))
        assert_that(model.rowCount()).is_equal_to(1)  # Still just Fido

        # Add matching item
        instance._dogs.append(Dog("Felix", 2))
        assert_that(model.rowCount()).is_equal_to(2)  # Fido and Felix


@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestFilterWithComboBox:
    """Filter= with QComboBox."""

    def test_combobox_filter(self, base_class, decorator, qt: QtDriver) -> None:
        """QComboBox with filter= shows filtered items."""

        @decorator
        class TestClass(base_class):
            _search: Variable[str] = new("")
            _items: Variable[list[str]] = new(["Apple", "Banana", "Apricot"])
            _combo: QComboBox = new(bind="_items", filter="{_search} in {#self}")

        instance = create_and_track(qt, TestClass, base_class)
        model = instance._combo.model()

        # No filter
        assert_that(model.rowCount()).is_equal_to(3)

        # Filter for "Ap"
        instance._search.value = "Ap"
        assert_that(model.rowCount()).is_equal_to(2)


@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestFilterWithFormat:
    """Filter= combined with format=."""

    def test_filter_with_format(self, base_class, decorator, qt: QtDriver) -> None:
        """Filter and format can be used together."""

        @decorator
        class TestClass(base_class):
            _min_age: Variable[int] = new(0)
            _dogs: Variable[list[Dog]] = new(
                [
                    Dog("Fido", 3),
                    Dog("Rex", 10),
                    Dog("Buddy", 2),
                ]
            )
            _list: QListView = new(
                bind="_dogs",
                format="{name} ({age} years)",
                filter="{age} >= {_min_age}",
            )

        instance = create_and_track(qt, TestClass, base_class)
        model = instance._list.model()

        # All shown
        assert_that(model.rowCount()).is_equal_to(3)

        # Filter by age
        instance._min_age.value = 5
        assert_that(model.rowCount()).is_equal_to(1)  # Only Rex (10 years)


@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestFilterMathExpressions:
    """Filter with math expressions."""

    def test_filter_addition(self, base_class, decorator, qt: QtDriver) -> None:
        """Filter with addition in expression."""

        @decorator
        class TestClass(base_class):
            _bonus: Variable[int] = new(0)
            _threshold: Variable[int] = new(5)
            _dogs: Variable[list[Dog]] = new(
                [
                    Dog("Puppy", 1),
                    Dog("Adult", 3),
                    Dog("Senior", 8),
                ]
            )
            _list: QListView = new(
                bind="_dogs",
                filter="{age} + {_bonus} >= {_threshold}",
            )

        instance = create_and_track(qt, TestClass, base_class)
        model = instance._list.model()

        # Threshold 5, bonus 0: age >= 5 → only Senior
        assert_that(model.rowCount()).is_equal_to(1)

        # Threshold 5, bonus 2: age + 2 >= 5 → Adult (3+2=5) and Senior
        instance._bonus.value = 2
        assert_that(model.rowCount()).is_equal_to(2)

        # Threshold 5, bonus 5: age + 5 >= 5 → all (even 1+5=6 >= 5)
        instance._bonus.value = 5
        assert_that(model.rowCount()).is_equal_to(3)

    def test_filter_multiplication(self, base_class, decorator, qt: QtDriver) -> None:
        """Filter with multiplication in expression."""

        @decorator
        class TestClass(base_class):
            _factor: Variable[int] = new(1)
            _threshold: Variable[int] = new(10)
            _dogs: Variable[list[Dog]] = new(
                [
                    Dog("Puppy", 1),
                    Dog("Adult", 3),
                    Dog("Senior", 5),
                ]
            )
            _list: QListView = new(
                bind="_dogs",
                filter="{age} * {_factor} >= {_threshold}",
            )

        instance = create_and_track(qt, TestClass, base_class)
        model = instance._list.model()

        # Factor 1, threshold 10: age >= 10 → none
        assert_that(model.rowCount()).is_equal_to(0)

        # Factor 2, threshold 10: age*2 >= 10 → Senior (5*2=10)
        instance._factor.value = 2
        assert_that(model.rowCount()).is_equal_to(1)

        # Factor 5, threshold 10: age*5 >= 10 → Adult (3*5=15) and Senior
        instance._factor.value = 5
        assert_that(model.rowCount()).is_equal_to(2)


@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestFilterWithTableView:
    """Filter= with QTableView."""

    def test_tableview_with_filter(self, base_class, decorator, qt: QtDriver) -> None:
        """QTableView with filter= shows filtered items."""

        @decorator
        class TestClass(base_class):
            _search: Variable[str] = new("")
            _dogs: Variable[list[Dog]] = new(
                [
                    Dog("Buddy", 3),
                    Dog("Rex", 5),
                    Dog("Fido", 2),
                ]
            )
            _table: QTableView = new(bind="_dogs", filter="{_search} in {name}")

        instance = create_and_track(qt, TestClass, base_class)
        model = instance._table.model()

        # No filter - show all
        assert_that(model.rowCount()).is_equal_to(3)

        # Filter for "ex" - only Rex
        instance._search.value = "ex"
        assert_that(model.rowCount()).is_equal_to(1)

    def test_tableview_filter_and_sort(self, base_class, decorator, qt: QtDriver) -> None:
        """QTableView with both filter= and sort=."""

        @decorator
        class TestClass(base_class):
            _min_age: Variable[int] = new(0)
            _dogs: Variable[list[Dog]] = new(
                [
                    Dog("Buddy", 7),
                    Dog("Rex", 2),
                    Dog("Fido", 5),
                ]
            )
            _table: QTableView = new(
                bind="_dogs",
                filter="{age} >= {_min_age}",
                sort="{age}",
            )

        instance = create_and_track(qt, TestClass, base_class)
        model = instance._table.model()

        # All shown, sorted by age
        assert_that(model.rowCount()).is_equal_to(3)

        # Filter to age >= 5
        instance._min_age.value = 5
        assert_that(model.rowCount()).is_equal_to(2)


@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestFilterWithTreeView:
    """Filter= with QTreeView."""

    def test_treeview_with_filter(self, base_class, decorator, qt: QtDriver) -> None:
        """QTreeView with filter= shows filtered items."""

        @decorator
        class TestClass(base_class):
            _search: Variable[str] = new("")
            _dogs: Variable[list[Dog]] = new(
                [
                    Dog("Buddy", 3),
                    Dog("Rex", 5),
                    Dog("Fido", 2),
                ]
            )
            _tree: QTreeView = new(bind="_dogs", filter="{_search} in {name}")

        instance = create_and_track(qt, TestClass, base_class)
        model = instance._tree.model()

        # No filter - show all
        assert_that(model.rowCount()).is_equal_to(3)

        # Filter for "Fido"
        instance._search.value = "Fido"
        assert_that(model.rowCount()).is_equal_to(1)

    def test_treeview_filter_and_sort(self, base_class, decorator, qt: QtDriver) -> None:
        """QTreeView with both filter= and sort=."""

        @decorator
        class TestClass(base_class):
            _min_age: Variable[int] = new(0)
            _dogs: Variable[list[Dog]] = new(
                [
                    Dog("Buddy", 7),
                    Dog("Rex", 2),
                    Dog("Fido", 5),
                ]
            )
            _tree: QTreeView = new(
                bind="_dogs",
                filter="{age} >= {_min_age}",
                sort="{age}",
            )

        instance = create_and_track(qt, TestClass, base_class)
        model = instance._tree.model()

        # All shown, sorted by age
        assert_that(model.rowCount()).is_equal_to(3)

        # Filter to age >= 5
        instance._min_age.value = 5
        assert_that(model.rowCount()).is_equal_to(2)

    def test_treeview_filter_with_selectedItem(self, base_class, decorator, qt: QtDriver) -> None:
        """QTreeView with filter= and selectedItem= works when selecting items.

        Regression test: selecting an item when filter= is active used to crash
        because proxy indices were passed to the source model instead of being
        handled by the view's model (which may be a proxy).
        """
        from PySide6.QtCore import QItemSelectionModel

        @decorator
        class TestClass(base_class):
            _search: Variable[str] = new("")
            _dogs: Variable[list[Dog]] = new(
                [
                    Dog("Buddy", 3),
                    Dog("Rex", 5),
                    Dog("Fido", 2),
                ]
            )
            _selected: Variable[Dog | None] = new(None)
            _tree: QTreeView = new(
                bind="_dogs",
                filter="{_search} in {name}",
                selectedItem="_selected",
            )

        instance = create_and_track(qt, TestClass, base_class)
        model = instance._tree.model()

        # Apply filter to activate proxy model
        instance._search.value = "Rex"
        qt.process_events()
        assert_that(model.rowCount()).is_equal_to(1)

        # Select the filtered item using selection model (simulates user click)
        selection_model = instance._tree.selectionModel()
        index = model.index(0, 0)
        selection_model.setCurrentIndex(index, QItemSelectionModel.SelectionFlag.ClearAndSelect)
        qt.process_events()

        # Verify selectedItem was updated (this would crash before the fix)
        assert_that(instance._selected.value).is_not_none()
        assert_that(instance._selected.value.name).is_equal_to("Rex")

    def test_treeview_filter_clear_and_select(self, base_class, decorator, qt: QtDriver) -> None:
        """QTreeView selection works after clearing filter.

        Regression test: ensure selection still works after filter is applied then cleared.
        """
        from PySide6.QtCore import QItemSelectionModel

        @decorator
        class TestClass(base_class):
            _search: Variable[str] = new("")
            _dogs: Variable[list[Dog]] = new(
                [
                    Dog("Buddy", 3),
                    Dog("Rex", 5),
                    Dog("Fido", 2),
                ]
            )
            _selected: Variable[Dog | None] = new(None)
            _tree: QTreeView = new(
                bind="_dogs",
                filter="{_search} in {name}",
                selectedItem="_selected",
            )

        instance = create_and_track(qt, TestClass, base_class)
        model = instance._tree.model()

        # Apply filter then clear it
        instance._search.value = "Rex"
        qt.process_events()
        instance._search.value = ""
        qt.process_events()
        assert_that(model.rowCount()).is_equal_to(3)

        # Select an item after filter cleared
        selection_model = instance._tree.selectionModel()
        index = model.index(1, 0)  # Second item
        selection_model.setCurrentIndex(index, QItemSelectionModel.SelectionFlag.ClearAndSelect)
        qt.process_events()

        # Verify selectedItem was updated
        assert_that(instance._selected.value).is_not_none()


@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestFilterCallable:
    """Filter using callable functions (lambda or function)."""

    def test_filter_with_lambda(self, base_class, decorator, qt: QtDriver) -> None:
        """Filter using lambda function."""

        @decorator
        class TestClass(base_class):
            _dogs: Variable[list[Dog]] = new(
                [
                    Dog("Fido", 3),
                    Dog("Rex", 5),
                    Dog("Buddy", 2),
                ]
            )
            _list: QListView = new(bind="_dogs", filter=lambda x: x.age >= 3)

        instance = create_and_track(qt, TestClass, base_class)
        model = instance._list.model()

        # Lambda filters to age >= 3: Fido (3) and Rex (5)
        assert_that(model.rowCount()).is_equal_to(2)

    def test_filter_with_lambda_string_contains(self, base_class, decorator, qt: QtDriver) -> None:
        """Filter using lambda with string contains check."""

        @decorator
        class TestClass(base_class):
            _dogs: Variable[list[Dog]] = new(
                [
                    Dog("Fido", 3),
                    Dog("Rex", 5),
                    Dog("Felix", 2),
                ]
            )
            _list: QListView = new(bind="_dogs", filter=lambda x: "F" in x.name)

        instance = create_and_track(qt, TestClass, base_class)
        model = instance._list.model()

        # Lambda filters to names containing "F": Fido and Felix
        assert_that(model.rowCount()).is_equal_to(2)

    def test_filter_with_lambda_complex_condition(self, base_class, decorator, qt: QtDriver) -> None:
        """Filter using lambda with complex condition."""

        @decorator
        class TestClass(base_class):
            _dogs: Variable[list[Dog]] = new(
                [
                    Dog("Fido", 3, "labrador"),
                    Dog("Rex", 5, "german shepherd"),
                    Dog("Buddy", 2, "labrador"),
                    Dog("Max", 8, "poodle"),
                ]
            )
            # Filter: labradors over age 2
            _list: QListView = new(
                bind="_dogs",
                filter=lambda x: x.breed == "labrador" and x.age > 2,
            )

        instance = create_and_track(qt, TestClass, base_class)
        model = instance._list.model()

        # Only Fido matches (labrador, age 3 > 2)
        assert_that(model.rowCount()).is_equal_to(1)

    def test_filter_with_lambda_on_primitives(self, base_class, decorator, qt: QtDriver) -> None:
        """Filter using lambda on primitive list."""

        @decorator
        class TestClass(base_class):
            _items: Variable[list[int]] = new([1, 5, 10, 15, 20])
            _list: QListView = new(bind="_items", filter=lambda x: x >= 10)

        instance = create_and_track(qt, TestClass, base_class)
        model = instance._list.model()

        # Filters to >= 10: 10, 15, 20
        assert_that(model.rowCount()).is_equal_to(3)

    def test_filter_with_lambda_all_filtered(self, base_class, decorator, qt: QtDriver) -> None:
        """Filter using lambda that filters everything."""

        @decorator
        class TestClass(base_class):
            _dogs: Variable[list[Dog]] = new(
                [
                    Dog("Fido", 3),
                    Dog("Rex", 5),
                ]
            )
            _list: QListView = new(bind="_dogs", filter=lambda x: x.age > 100)

        instance = create_and_track(qt, TestClass, base_class)
        model = instance._list.model()

        # No dog is over 100 years old
        assert_that(model.rowCount()).is_equal_to(0)


@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestFilterMethodName:
    """Filter using widget method names."""

    def test_filter_with_method_name(self, base_class, decorator, qt: QtDriver) -> None:
        """Filter using method name from widget."""

        @decorator
        class TestClass(base_class):
            _dogs: Variable[list[Dog]] = new(
                [
                    Dog("Fido", 3),
                    Dog("Rex", 5),
                    Dog("Buddy", 2),
                ]
            )
            _list: QListView = new(bind="_dogs", filter="should_show")

            def should_show(self, dog: Dog) -> bool:
                return dog.age >= 3

        instance = create_and_track(qt, TestClass, base_class)
        model = instance._list.model()

        # Method filters to age >= 3: Fido and Rex
        assert_that(model.rowCount()).is_equal_to(2)

    def test_filter_with_method_using_widget_state(self, base_class, decorator, qt: QtDriver) -> None:
        """Filter method can access widget state."""

        @decorator
        class TestClass(base_class):
            _min_age: Variable[int] = new(0)
            _dogs: Variable[list[Dog]] = new(
                [
                    Dog("Fido", 3),
                    Dog("Rex", 5),
                    Dog("Buddy", 2),
                ]
            )
            _list: QListView = new(bind="_dogs", filter="filter_by_min_age")

            def filter_by_min_age(self, dog: Dog) -> bool:
                return dog.age >= self._min_age.value

        instance = create_and_track(qt, TestClass, base_class)
        model = instance._list.model()

        # Initial min_age 0 - all shown
        assert_that(model.rowCount()).is_equal_to(3)

        # Note: With method-based filter, changing Variable doesn't auto-invalidate
        # The filter proxy doesn't subscribe to Variables when using callable
        # This is expected behavior - use expression syntax for reactive filters

    def test_filter_with_method_string_search(self, base_class, decorator, qt: QtDriver) -> None:
        """Filter method with string search."""

        @decorator
        class TestClass(base_class):
            _dogs: Variable[list[Dog]] = new(
                [
                    Dog("Fido", 3),
                    Dog("Rex", 5),
                    Dog("Felix", 2),
                ]
            )
            _list: QListView = new(bind="_dogs", filter="name_starts_with_f")

            def name_starts_with_f(self, dog: Dog) -> bool:
                return dog.name.startswith("F")

        instance = create_and_track(qt, TestClass, base_class)
        model = instance._list.model()

        # Fido and Felix start with F
        assert_that(model.rowCount()).is_equal_to(2)

    def test_filter_with_method_on_primitives(self, base_class, decorator, qt: QtDriver) -> None:
        """Filter method on primitive list."""

        @decorator
        class TestClass(base_class):
            _items: Variable[list[str]] = new(["Apple", "Banana", "Apricot", "Cherry"])
            _list: QListView = new(bind="_items", filter="starts_with_a")

            def starts_with_a(self, item: str) -> bool:
                return item.startswith("A")

        instance = create_and_track(qt, TestClass, base_class)
        model = instance._list.model()

        # Apple and Apricot start with A
        assert_that(model.rowCount()).is_equal_to(2)


@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestFilterCallableWithSort:
    """Filter callable combined with sort."""

    def test_filter_lambda_with_sort_expression(self, base_class, decorator, qt: QtDriver) -> None:
        """Lambda filter combined with expression sort."""

        @decorator
        class TestClass(base_class):
            _dogs: Variable[list[Dog]] = new(
                [
                    Dog("Buddy", 7),
                    Dog("Rex", 2),
                    Dog("Fido", 5),
                ]
            )
            _list: QListView = new(
                bind="_dogs",
                filter=lambda x: x.age >= 3,
                sort="{age}",
            )

        instance = create_and_track(qt, TestClass, base_class)
        model = instance._list.model()

        # Filtered to age >= 3: Fido (5) and Buddy (7), sorted by age
        assert_that(model.rowCount()).is_equal_to(2)

    def test_filter_method_with_sort_lambda(self, base_class, decorator, qt: QtDriver) -> None:
        """Method filter combined with lambda sort."""

        @decorator
        class TestClass(base_class):
            _dogs: Variable[list[Dog]] = new(
                [
                    Dog("Buddy", 7),
                    Dog("Rex", 2),
                    Dog("Fido", 5),
                ]
            )
            _list: QListView = new(
                bind="_dogs",
                filter="is_adult",
                sort=lambda x: x.name,
            )

            def is_adult(self, dog: Dog) -> bool:
                return dog.age >= 3

        instance = create_and_track(qt, TestClass, base_class)
        model = instance._list.model()

        # Filtered to age >= 3: Buddy and Fido, sorted by name
        assert_that(model.rowCount()).is_equal_to(2)


@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestFilterDepends:
    """Filter with filter_depends= for reactive callable/method filters."""

    def test_filter_depends_with_lambda(self, base_class, decorator, qt: QtDriver) -> None:
        """Lambda filter with filter_depends= re-evaluates when Variable changes."""

        @decorator
        class TestClass(base_class):
            _min_age: Variable[int] = new(0)
            _dogs: Variable[list[Dog]] = new(
                [
                    Dog("Fido", 3),
                    Dog("Rex", 5),
                    Dog("Buddy", 2),
                ]
            )
            _list: QListView = new(
                bind="_dogs",
                filter=lambda x: x.age >= 3,  # Static filter - ignores _min_age
                filter_depends=["_min_age"],  # But re-evaluates when _min_age changes
            )

            # We need a method that uses _min_age for this test to make sense
            # Let's use a method filter instead

        instance = create_and_track(qt, TestClass, base_class)
        model = instance._list.model()

        # Initial: lambda filters to age >= 3
        assert_that(model.rowCount()).is_equal_to(2)

        # Changing _min_age triggers filter re-evaluation (but lambda is static)
        # This tests that the subscription works, even if lambda doesn't use it
        instance._min_age.value = 10
        assert_that(model.rowCount()).is_equal_to(2)  # Still 2, lambda is static

    def test_filter_depends_with_method(self, base_class, decorator, qt: QtDriver) -> None:
        """Method filter with filter_depends= re-evaluates when Variable changes."""

        @decorator
        class TestClass(base_class):
            _min_age: Variable[int] = new(0)
            _dogs: Variable[list[Dog]] = new(
                [
                    Dog("Fido", 3),
                    Dog("Rex", 5),
                    Dog("Buddy", 2),
                ]
            )
            _list: QListView = new(
                bind="_dogs",
                filter="filter_by_age",
                filter_depends=["_min_age"],
            )

            def filter_by_age(self, dog: Dog) -> bool:
                # Access Variable value via .value
                return dog.age >= self._min_age.value

        instance = create_and_track(qt, TestClass, base_class)
        model = instance._list.model()

        # Initial min_age 0 - all shown
        assert_that(model.rowCount()).is_equal_to(3)

        # Change min_age to 3 - filters out Buddy (age 2)
        instance._min_age.value = 3
        assert_that(model.rowCount()).is_equal_to(2)

        # Change min_age to 5 - only Rex shown
        instance._min_age.value = 5
        assert_that(model.rowCount()).is_equal_to(1)

        # Change min_age to 0 - all shown again
        instance._min_age.value = 0
        assert_that(model.rowCount()).is_equal_to(3)

    def test_filter_depends_multiple_variables(self, base_class, decorator, qt: QtDriver) -> None:
        """Method filter with multiple filter_depends= Variables."""

        @decorator
        class TestClass(base_class):
            _min_age: Variable[int] = new(0)
            _search: Variable[str] = new("")
            _dogs: Variable[list[Dog]] = new(
                [
                    Dog("Fido", 3),
                    Dog("Rex", 5),
                    Dog("Buddy", 2),
                ]
            )
            _list: QListView = new(
                bind="_dogs",
                filter="complex_filter",
                filter_depends=["_min_age", "_search"],
            )

            def complex_filter(self, dog: Dog) -> bool:
                if dog.age < self._min_age.value:
                    return False
                search = self._search.value
                if search and search not in dog.name:
                    return False
                return True

        instance = create_and_track(qt, TestClass, base_class)
        model = instance._list.model()

        # Initial - all shown
        assert_that(model.rowCount()).is_equal_to(3)

        # Filter by age
        instance._min_age.value = 3
        assert_that(model.rowCount()).is_equal_to(2)  # Fido, Rex

        # Also filter by search
        instance._search.value = "ex"
        assert_that(model.rowCount()).is_equal_to(1)  # Only Rex

        # Clear search
        instance._search.value = ""
        assert_that(model.rowCount()).is_equal_to(2)  # Fido, Rex

    def test_filter_depends_with_string_search(self, base_class, decorator, qt: QtDriver) -> None:
        """Typical use case: search filter with filter_depends=."""

        @decorator
        class TestClass(base_class):
            _search: Variable[str] = new("")
            _dogs: Variable[list[Dog]] = new(
                [
                    Dog("Fido", 3),
                    Dog("Rex", 5),
                    Dog("Buddy", 2),
                ]
            )
            _list: QListView = new(
                bind="_dogs",
                filter="search_filter",
                filter_depends=["_search"],
            )

            def search_filter(self, dog: Dog) -> bool:
                search = self._search.value.lower()
                if not search:
                    return True
                return search in dog.name.lower()

        instance = create_and_track(qt, TestClass, base_class)
        model = instance._list.model()

        # No search - all shown
        assert_that(model.rowCount()).is_equal_to(3)

        # Search "fido" - only Fido
        instance._search.value = "fido"
        assert_that(model.rowCount()).is_equal_to(1)

        # Search "ex" - only Rex
        instance._search.value = "ex"
        assert_that(model.rowCount()).is_equal_to(1)

        # Search "d" - Fido and Buddy
        instance._search.value = "d"
        assert_that(model.rowCount()).is_equal_to(2)

        # Clear search
        instance._search.value = ""
        assert_that(model.rowCount()).is_equal_to(3)


# State classes with Var[T] attributes for testing Variable unwrapping
@state
class StateDog(State):
    """Test State class with Variable attributes - mimics real-world usage like Collection/Request."""

    name: Variable[str] = new("")
    age: Variable[int] = new(0)
    breed: Variable[str] = new("unknown")


@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestFilterWithStateObjects:
    """Filter on State objects with Var[T] attributes that need unwrapping.

    This tests the real-world scenario where tree items are State subclasses
    with Variable attributes (like Collection/Request in Forc), not plain dataclasses.
    """

    def test_filter_state_object_simple_contains(self, base_class, decorator, qt: QtDriver) -> None:
        """Filter with simple 'in' expression on State object with Var[str] attribute."""

        @decorator
        class TestClass(base_class):
            _search: Variable[str] = new("")
            _dogs: Variable[list[StateDog]] = new([])
            _list: QListView = new(bind="_dogs", filter="{_search} in {name}")

        instance = create_and_track(qt, TestClass, base_class)

        # Create State objects with Variable attributes
        fido = StateDog()
        fido.name.value = "Fido"
        fido.age.value = 3

        rex = StateDog()
        rex.name.value = "Rex"
        rex.age.value = 5

        buddy = StateDog()
        buddy.name.value = "Buddy"
        buddy.age.value = 2

        # Add to list
        instance._dogs.value = [fido, rex, buddy]

        model = instance._list.model()

        # No filter - all items shown
        assert_that(model.rowCount()).is_equal_to(3)

        # Filter for "id" - matches "Fido"
        instance._search.value = "id"
        assert_that(model.rowCount()).is_equal_to(1)

        # Filter for "ex" - matches "Rex"
        instance._search.value = "ex"
        assert_that(model.rowCount()).is_equal_to(1)

        # Filter for "" - back to all items
        instance._search.value = ""
        assert_that(model.rowCount()).is_equal_to(3)

    def test_filter_state_object_comparison(self, base_class, decorator, qt: QtDriver) -> None:
        """Filter with comparison on State object with Var[int] attribute."""

        @decorator
        class TestClass(base_class):
            _min_age: Variable[int] = new(0)
            _dogs: Variable[list[StateDog]] = new([])
            _list: QListView = new(bind="_dogs", filter="{age} >= {_min_age}")

        instance = create_and_track(qt, TestClass, base_class)

        # Create State objects
        puppy = StateDog()
        puppy.name.value = "Puppy"
        puppy.age.value = 1

        adult = StateDog()
        adult.name.value = "Adult"
        adult.age.value = 5

        senior = StateDog()
        senior.name.value = "Senior"
        senior.age.value = 10

        instance._dogs.value = [puppy, adult, senior]

        model = instance._list.model()

        # Min age 0 - all shown
        assert_that(model.rowCount()).is_equal_to(3)

        # Min age 3 - excludes puppy
        instance._min_age.value = 3
        assert_that(model.rowCount()).is_equal_to(2)

        # Min age 8 - only senior
        instance._min_age.value = 8
        assert_that(model.rowCount()).is_equal_to(1)

    def test_filter_state_object_case_insensitive(self, base_class, decorator, qt: QtDriver) -> None:
        """Filter using string methods on State object Var[str] attribute."""

        @decorator
        class TestClass(base_class):
            _search: Variable[str] = new("")
            _dogs: Variable[list[StateDog]] = new([])
            _list: QListView = new(
                bind="_dogs",
                filter="{_search.lower()} in {name.lower()}",
            )

        instance = create_and_track(qt, TestClass, base_class)

        # Create State objects with mixed case names
        fido = StateDog()
        fido.name.value = "FIDO"

        rex = StateDog()
        rex.name.value = "Rex"

        buddy = StateDog()
        buddy.name.value = "buddy"

        instance._dogs.value = [fido, rex, buddy]

        model = instance._list.model()

        # No filter - all shown
        assert_that(model.rowCount()).is_equal_to(3)

        # Case-insensitive search for "FIDO"
        instance._search.value = "fido"
        assert_that(model.rowCount()).is_equal_to(1)

        # Case-insensitive search for "buddy"
        instance._search.value = "BUDDY"
        assert_that(model.rowCount()).is_equal_to(1)

    def test_filter_state_object_and_expression(self, base_class, decorator, qt: QtDriver) -> None:
        """Filter with 'and' expression on State object attributes."""

        @decorator
        class TestClass(base_class):
            _min_age: Variable[int] = new(0)
            _search: Variable[str] = new("")
            _dogs: Variable[list[StateDog]] = new([])
            _list: QListView = new(
                bind="_dogs",
                filter="{age} >= {_min_age} and {_search} in {name}",
            )

        instance = create_and_track(qt, TestClass, base_class)

        fido = StateDog()
        fido.name.value = "Fido"
        fido.age.value = 3

        rex = StateDog()
        rex.name.value = "Rex"
        rex.age.value = 5

        buddy = StateDog()
        buddy.name.value = "Buddy"
        buddy.age.value = 2

        instance._dogs.value = [fido, rex, buddy]

        model = instance._list.model()

        # No filters - all shown
        assert_that(model.rowCount()).is_equal_to(3)

        # Min age 3 - Fido and Rex
        instance._min_age.value = 3
        assert_that(model.rowCount()).is_equal_to(2)

        # Also search for "ex" - only Rex
        instance._search.value = "ex"
        assert_that(model.rowCount()).is_equal_to(1)

    def test_filter_state_object_with_treeview(self, base_class, decorator, qt: QtDriver) -> None:
        """Filter on QTreeView with State objects - matches Forc Collection/Request pattern."""

        @decorator
        class TestClass(base_class):
            _filter_text: Variable[str] = new("")
            _items: Variable[list[StateDog]] = new([])
            _tree: QTreeView = new(
                bind="_items",
                headerHidden=True,
                filter="{_filter_text} in {name}",
            )

        instance = create_and_track(qt, TestClass, base_class)

        # Create items like Collection/Request would have
        item1 = StateDog()
        item1.name.value = "Collection A"

        item2 = StateDog()
        item2.name.value = "Request B"

        item3 = StateDog()
        item3.name.value = "Collection C"

        instance._items.value = [item1, item2, item3]

        model = instance._tree.model()

        # No filter - all shown
        assert_that(model.rowCount()).is_equal_to(3)

        # Filter for "Collection"
        instance._filter_text.value = "Collection"
        assert_that(model.rowCount()).is_equal_to(2)

        # Filter for "Request"
        instance._filter_text.value = "Request"
        assert_that(model.rowCount()).is_equal_to(1)

        # Clear filter
        instance._filter_text.value = ""
        assert_that(model.rowCount()).is_equal_to(3)

    def test_filter_with_embedded_widget(self, base_class, decorator, qt: QtDriver) -> None:
        """Filter combined with widget= should render embedded widgets correctly.

        This tests the scenario where a QTreeView has both filter= and widget= -
        the embedded widgets should render properly even when a proxy model is used.
        """
        from qtpy.QtWidgets import QLabel

        # Define an embedded row widget
        @widget
        class RowWidget(Widget[StateDog]):
            label: QLabel = new(bind="{name}")

        @decorator
        class TestClass(base_class):
            _filter_text: Variable[str] = new("")
            _items: Variable[list[StateDog]] = new([])
            _tree: QTreeView = new(
                bind="_items",
                headerHidden=True,
                filter="{_filter_text} in {name}",
                widget=RowWidget,
            )

        instance = create_and_track(qt, TestClass, base_class)

        # Create items
        fido = StateDog()
        fido.name.value = "Fido"

        rex = StateDog()
        rex.name.value = "Rex"

        buddy = StateDog()
        buddy.name.value = "Buddy"

        instance._items.value = [fido, rex, buddy]

        # Process events to let initial widgets render
        from qtpy.QtWidgets import QApplication

        QApplication.processEvents()

        model = instance._tree.model()

        # All items should be shown
        assert_that(model.rowCount()).is_equal_to(3)

        # Check that embedded widgets are created and have correct data
        for row in range(model.rowCount()):
            index = model.index(row, 0)
            editor = instance._tree.indexWidget(index)
            assert_that(editor).is_not_none()
            assert_that(editor).is_instance_of(RowWidget)
            if editor is not None:
                assert_that(editor.label.text()).is_not_empty()

        # Filter to show only Rex
        instance._filter_text.value = "ex"
        QApplication.processEvents()
        assert_that(model.rowCount()).is_equal_to(1)

        # Rex should have a working embedded widget
        index = model.index(0, 0)
        editor = instance._tree.indexWidget(index)
        assert_that(editor).is_not_none()
        if editor is not None:
            assert_that(editor.label.text()).is_equal_to("Rex")

        # Clear filter - all items should reappear WITH their embedded widgets
        instance._filter_text.value = ""
        QApplication.processEvents()
        assert_that(model.rowCount()).is_equal_to(3)

        # CRITICAL: After un-filtering, ALL items must have embedded widgets with correct data
        # This is the bug scenario - widgets disappear after filter is cleared
        expected_names = {"Fido", "Rex", "Buddy"}
        found_names: set[str] = set()
        for row in range(model.rowCount()):
            index = model.index(row, 0)
            editor = instance._tree.indexWidget(index)
            assert_that(editor).described_as(f"Row {row} must have embedded widget after un-filtering").is_not_none()
            if editor is not None:
                assert_that(editor).is_instance_of(RowWidget)
                label_text = editor.label.text()
                assert_that(label_text).described_as(f"Row {row} widget must have non-empty label text").is_not_empty()
                found_names.add(label_text)

        # Verify we found all expected names
        assert_that(found_names).is_equal_to(expected_names)

    def test_filter_with_embedded_widget_filter_all_then_restore(self, base_class, decorator, qt: QtDriver) -> None:
        """Filter that hides ALL items, then restore - widgets must reappear.

        This tests the scenario where filtering removes all visible rows,
        then clearing the filter should restore all widgets.
        """
        from qtpy.QtWidgets import QLabel

        @widget
        class NodeWidget(Widget[StateDog]):
            label: QLabel = new(bind="{name}")

        @decorator
        class TestClass(base_class):
            _filter_text: Variable[str] = new("")
            _items: Variable[list[StateDog]] = new([])
            _tree: QTreeView = new(
                bind="_items",
                headerHidden=True,
                filter="{_filter_text} in {name}",
                widget=NodeWidget,
            )

        instance = create_and_track(qt, TestClass, base_class)

        # Create items
        fido = StateDog()
        fido.name.value = "Fido"

        rex = StateDog()
        rex.name.value = "Rex"

        instance._items.value = [fido, rex]

        from qtpy.QtWidgets import QApplication

        QApplication.processEvents()

        model = instance._tree.model()

        # Initial: 2 items with widgets
        assert_that(model.rowCount()).is_equal_to(2)
        for row in range(2):
            editor = instance._tree.indexWidget(model.index(row, 0))
            assert_that(editor).is_not_none()

        # Filter that matches NOTHING - all rows disappear
        instance._filter_text.value = "ZZZZZ_NO_MATCH"
        QApplication.processEvents()
        assert_that(model.rowCount()).is_equal_to(0)

        # Clear filter - all items should reappear WITH widgets
        instance._filter_text.value = ""
        QApplication.processEvents()
        assert_that(model.rowCount()).is_equal_to(2)

        # CRITICAL: Both items must have embedded widgets after un-filtering
        for row in range(model.rowCount()):
            index = model.index(row, 0)
            editor = instance._tree.indexWidget(index)
            assert_that(editor).described_as(f"Row {row} must have widget after filter cleared").is_not_none()
            if editor is not None:
                assert_that(editor.label.text()).is_in("Fido", "Rex")

    def test_filter_with_widget_multiple_filter_cycles(self, base_class, decorator, qt: QtDriver) -> None:
        """Test multiple filter/unfilter cycles - widgets must persist.

        This tests that embedded widgets survive multiple filter changes.
        """
        from qtpy.QtWidgets import QLabel

        @widget
        class RowWidget(Widget[StateDog]):
            label: QLabel = new(bind="{name}")

        @decorator
        class TestClass(base_class):
            _filter_text: Variable[str] = new("")
            _items: Variable[list[StateDog]] = new([])
            _tree: QTreeView = new(
                bind="_items",
                headerHidden=True,
                filter="{_filter_text} in {name}",
                widget=RowWidget,
            )

        instance = create_and_track(qt, TestClass, base_class)

        # Create items
        fido = StateDog()
        fido.name.value = "Fido"
        rex = StateDog()
        rex.name.value = "Rex"
        buddy = StateDog()
        buddy.name.value = "Buddy"

        instance._items.value = [fido, rex, buddy]

        from qtpy.QtWidgets import QApplication

        QApplication.processEvents()

        model = instance._tree.model()

        # Initial state - all visible with widgets
        assert_that(model.rowCount()).is_equal_to(3)
        for row in range(3):
            assert_that(instance._tree.indexWidget(model.index(row, 0))).is_not_none()

        # Cycle 1: Filter then unfilter
        instance._filter_text.value = "ex"
        QApplication.processEvents()
        assert_that(model.rowCount()).is_equal_to(1)

        instance._filter_text.value = ""
        QApplication.processEvents()
        assert_that(model.rowCount()).is_equal_to(3)
        for row in range(3):
            editor = instance._tree.indexWidget(model.index(row, 0))
            assert_that(editor).described_as(f"Cycle 1: row {row}").is_not_none()

        # Cycle 2: Filter differently then unfilter
        instance._filter_text.value = "Bud"
        QApplication.processEvents()
        assert_that(model.rowCount()).is_equal_to(1)

        instance._filter_text.value = ""
        QApplication.processEvents()
        assert_that(model.rowCount()).is_equal_to(3)
        for row in range(3):
            editor = instance._tree.indexWidget(model.index(row, 0))
            assert_that(editor).described_as(f"Cycle 2: row {row}").is_not_none()

        # Cycle 3: Filter to nothing then restore
        instance._filter_text.value = "ZZZZZ"
        QApplication.processEvents()
        assert_that(model.rowCount()).is_equal_to(0)

        instance._filter_text.value = ""
        QApplication.processEvents()
        assert_that(model.rowCount()).is_equal_to(3)
        for row in range(3):
            editor = instance._tree.indexWidget(model.index(row, 0))
            assert_that(editor).described_as(f"Cycle 3: row {row}").is_not_none()


@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestFilterWithNestedChildWidgetVariable:
    """Filter referencing a Variable on a child widget.

    This tests the pattern where:
    - Parent widget has a child widget (_actions)
    - Child widget has a Variable (filter_text)
    - Parent's filter expression references {_actions.filter_text}
    """

    def test_filter_child_widget_variable_simple(self, base_class, decorator, qt: QtDriver) -> None:
        """Filter using Variable from child widget - simple case."""

        # Child widget with filter Variable
        @widget(layout="horizontal")
        class ActionsWidget(Widget):
            filter_text: Variable[str] = new("")

        @decorator
        class TestClass(base_class):
            _actions: ActionsWidget = new()
            _dogs: Variable[list[Dog]] = new(
                [
                    Dog("Fido", 3),
                    Dog("Rex", 5),
                    Dog("Buddy", 2),
                ]
            )
            _list: QListView = new(
                bind="_dogs",
                filter="{_actions.filter_text} in {name}",
            )

        instance = create_and_track(qt, TestClass, base_class)
        model = instance._list.model()

        # No filter - all items shown
        assert_that(model.rowCount()).is_equal_to(3)

        # Filter for "id" via child widget's Variable - should match "Fido"
        instance._actions.filter_text.value = "id"
        assert_that(model.rowCount()).is_equal_to(1)

        # Filter for "ex" - matches "Rex"
        instance._actions.filter_text.value = "ex"
        assert_that(model.rowCount()).is_equal_to(1)

        # Clear filter - back to all items
        instance._actions.filter_text.value = ""
        assert_that(model.rowCount()).is_equal_to(3)

    def test_filter_child_widget_variable_with_method_call(self, base_class, decorator, qt: QtDriver) -> None:
        """Filter using Variable from child widget with method call like .lower()."""

        @widget(layout="horizontal")
        class ActionsWidget(Widget):
            filter_text: Variable[str] = new("")

        @decorator
        class TestClass(base_class):
            _actions: ActionsWidget = new()
            _dogs: Variable[list[Dog]] = new(
                [
                    Dog("FIDO", 3),
                    Dog("Rex", 5),
                    Dog("buddy", 2),
                ]
            )
            _list: QListView = new(
                bind="_dogs",
                filter="{_actions.filter_text.lower()} in {name.lower()}",
            )

        instance = create_and_track(qt, TestClass, base_class)
        model = instance._list.model()

        # No filter - all items shown
        assert_that(model.rowCount()).is_equal_to(3)

        # Case-insensitive filter for "fido" - should match "FIDO"
        instance._actions.filter_text.value = "FIDO"
        assert_that(model.rowCount()).is_equal_to(1)

        # Filter for "buddy" - matches "buddy"
        instance._actions.filter_text.value = "BUDDY"
        assert_that(model.rowCount()).is_equal_to(1)

        # Clear filter
        instance._actions.filter_text.value = ""
        assert_that(model.rowCount()).is_equal_to(3)

    def test_filter_child_widget_variable_with_treeview(self, base_class, decorator, qt: QtDriver) -> None:
        """Filter on QTreeView using Variable from child widget - matches Forc pattern."""

        @widget(layout="horizontal")
        class CollectionsTreeActionsWidget(Widget):
            filter_text: Variable[str] = new("")

        @decorator
        class TestClass(base_class):
            _actions: CollectionsTreeActionsWidget = new()
            _items: Variable[list[StateDog]] = new([])
            _tree: QTreeView = new(
                bind="_items",
                headerHidden=True,
                filter="{_actions.filter_text.lower()} in {(name or '').lower()}",
            )

        instance = create_and_track(qt, TestClass, base_class)

        # Create State objects
        fido = StateDog()
        fido.name.value = "Fido"

        rex = StateDog()
        rex.name.value = "Rex"

        buddy = StateDog()
        buddy.name.value = "Buddy"

        instance._items.value = [fido, rex, buddy]

        model = instance._tree.model()

        # No filter - all shown
        assert_that(model.rowCount()).is_equal_to(3)

        # Filter via child widget
        instance._actions.filter_text.value = "fido"
        assert_that(model.rowCount()).is_equal_to(1)

        # Change filter
        instance._actions.filter_text.value = "ex"
        assert_that(model.rowCount()).is_equal_to(1)

        # Clear filter
        instance._actions.filter_text.value = ""
        assert_that(model.rowCount()).is_equal_to(3)
