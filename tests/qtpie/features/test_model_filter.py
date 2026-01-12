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

from qtpie import Variable, new
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
