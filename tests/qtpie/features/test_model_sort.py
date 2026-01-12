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
# pyright: reportUnknownVariableType=false
# pyright: reportUnknownLambdaType=false
# pyright: reportMissingTypeArgument=false
"""Tests for model widget sort= support.

Tests expression-based sorting on QListView, QComboBox, QTableView, QTreeView.

Sort syntax:
- sort="{age}"         - sort by expression result
- sort="method_name"   - call widget method
- sort=lambda x: x.age - direct callable
"""

from dataclasses import dataclass
from typing import Self

import pytest
from assertpy import assert_that
from PySide6.QtWidgets import QComboBox, QListView, QTableView, QTreeView
from qtpy.QtCore import Qt

from qtpie import Variable, new
from qtpie.testing import QtDriver

from .conftest import WIDGET_CLASS_TYPES, create_and_track


@dataclass
class Dog:
    """Test dataclass for sort tests."""

    name: str
    age: int


@dataclass
class Person:
    """Test dataclass for sort tests."""

    name: str
    score: float


class ReverseString:
    """Helper class for reverse string sorting."""

    def __init__(self, s: str):
        self.s = s

    def __lt__(self, other: Self) -> bool:
        return self.s > other.s  # Reversed!


def get_sorted_items(model) -> list:
    """Get items from model in display order."""
    items = []
    for i in range(model.rowCount()):
        idx = model.index(i, 0)
        item = model.data(idx, Qt.ItemDataRole.UserRole)
        items.append(item)
    return items


@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestSortExpression:
    """Sort using expression strings like {age}."""

    def test_sort_by_int_attribute(self, base_class, decorator, qt: QtDriver) -> None:
        """Sort by integer attribute ascending."""

        @decorator
        class TestClass(base_class):
            _dogs: Variable[list[Dog]] = new(
                [
                    Dog("Buddy", 7),
                    Dog("Rex", 2),
                    Dog("Fido", 5),
                ]
            )
            _list: QListView = new(bind="_dogs", sort="{age}")

        instance = create_and_track(qt, TestClass, base_class)
        items = get_sorted_items(instance._list.model())

        # Should be sorted by age ascending: 2, 5, 7
        assert_that(items[0].name).is_equal_to("Rex")
        assert_that(items[1].name).is_equal_to("Fido")
        assert_that(items[2].name).is_equal_to("Buddy")

    def test_sort_by_string_attribute(self, base_class, decorator, qt: QtDriver) -> None:
        """Sort by string attribute alphabetically."""

        @decorator
        class TestClass(base_class):
            _dogs: Variable[list[Dog]] = new(
                [
                    Dog("Buddy", 7),
                    Dog("Rex", 2),
                    Dog("Fido", 5),
                ]
            )
            _list: QListView = new(bind="_dogs", sort="{name}")

        instance = create_and_track(qt, TestClass, base_class)
        items = get_sorted_items(instance._list.model())

        # Should be sorted alphabetically: Buddy, Fido, Rex
        assert_that(items[0].name).is_equal_to("Buddy")
        assert_that(items[1].name).is_equal_to("Fido")
        assert_that(items[2].name).is_equal_to("Rex")

    def test_sort_by_float_attribute(self, base_class, decorator, qt: QtDriver) -> None:
        """Sort by float attribute."""

        @decorator
        class TestClass(base_class):
            _people: Variable[list[Person]] = new(
                [
                    Person("Alice", 85.5),
                    Person("Bob", 92.0),
                    Person("Charlie", 78.3),
                ]
            )
            _list: QListView = new(bind="_people", sort="{score}")

        instance = create_and_track(qt, TestClass, base_class)
        items = get_sorted_items(instance._list.model())

        # Should be sorted by score: 78.3, 85.5, 92.0
        assert_that(items[0].name).is_equal_to("Charlie")
        assert_that(items[1].name).is_equal_to("Alice")
        assert_that(items[2].name).is_equal_to("Bob")

    def test_sort_by_negative_expression(self, base_class, decorator, qt: QtDriver) -> None:
        """Sort by negative value (descending)."""

        @decorator
        class TestClass(base_class):
            _dogs: Variable[list[Dog]] = new(
                [
                    Dog("Buddy", 7),
                    Dog("Rex", 2),
                    Dog("Fido", 5),
                ]
            )
            _list: QListView = new(bind="_dogs", sort="{-age}")

        instance = create_and_track(qt, TestClass, base_class)
        items = get_sorted_items(instance._list.model())

        # Should be sorted descending: 7, 5, 2
        assert_that(items[0].name).is_equal_to("Buddy")
        assert_that(items[1].name).is_equal_to("Fido")
        assert_that(items[2].name).is_equal_to("Rex")

    def test_sort_by_length_expression(self, base_class, decorator, qt: QtDriver) -> None:
        """Sort by computed length."""

        @decorator
        class TestClass(base_class):
            _dogs: Variable[list[Dog]] = new(
                [
                    Dog("Buddy", 7),  # len 5
                    Dog("Rex", 2),  # len 3
                    Dog("Fido", 5),  # len 4
                ]
            )
            _list: QListView = new(bind="_dogs", sort="{len(name)}")

        instance = create_and_track(qt, TestClass, base_class)
        items = get_sorted_items(instance._list.model())

        # Should be sorted by name length: 3, 4, 5
        assert_that(items[0].name).is_equal_to("Rex")
        assert_that(items[1].name).is_equal_to("Fido")
        assert_that(items[2].name).is_equal_to("Buddy")


@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestSortCallable:
    """Sort using callable functions."""

    def test_sort_with_lambda(self, base_class, decorator, qt: QtDriver) -> None:
        """Sort using lambda function."""

        @decorator
        class TestClass(base_class):
            _dogs: Variable[list[Dog]] = new(
                [
                    Dog("Buddy", 7),
                    Dog("Rex", 2),
                    Dog("Fido", 5),
                ]
            )
            _list: QListView = new(bind="_dogs", sort=lambda x: x.age)

        instance = create_and_track(qt, TestClass, base_class)
        items = get_sorted_items(instance._list.model())

        # Should be sorted by age
        assert_that(items[0].name).is_equal_to("Rex")
        assert_that(items[1].name).is_equal_to("Fido")
        assert_that(items[2].name).is_equal_to("Buddy")

    def test_sort_with_lambda_tuple(self, base_class, decorator, qt: QtDriver) -> None:
        """Sort using lambda returning tuple (secondary sort)."""

        @decorator
        class TestClass(base_class):
            _dogs: Variable[list[Dog]] = new(
                [
                    Dog("Buddy", 5),
                    Dog("Rex", 5),
                    Dog("Fido", 5),
                ]
            )
            _list: QListView = new(bind="_dogs", sort=lambda x: (x.age, x.name))

        instance = create_and_track(qt, TestClass, base_class)
        items = get_sorted_items(instance._list.model())

        # Same age, so sorted by name
        assert_that(items[0].name).is_equal_to("Buddy")
        assert_that(items[1].name).is_equal_to("Fido")
        assert_that(items[2].name).is_equal_to("Rex")

    def test_sort_with_lambda_descending(self, base_class, decorator, qt: QtDriver) -> None:
        """Sort descending using lambda with negation."""

        @decorator
        class TestClass(base_class):
            _dogs: Variable[list[Dog]] = new(
                [
                    Dog("Buddy", 7),
                    Dog("Rex", 2),
                    Dog("Fido", 5),
                ]
            )
            _list: QListView = new(bind="_dogs", sort=lambda x: -x.age)

        instance = create_and_track(qt, TestClass, base_class)
        items = get_sorted_items(instance._list.model())

        # Should be sorted descending
        assert_that(items[0].name).is_equal_to("Buddy")
        assert_that(items[1].name).is_equal_to("Fido")
        assert_that(items[2].name).is_equal_to("Rex")


@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestSortMethodName:
    """Sort using widget method names."""

    def test_sort_with_method_name(self, base_class, decorator, qt: QtDriver) -> None:
        """Sort using method name from widget."""

        @decorator
        class TestClass(base_class):
            _dogs: Variable[list[Dog]] = new(
                [
                    Dog("Buddy", 7),
                    Dog("Rex", 2),
                    Dog("Fido", 5),
                ]
            )
            _list: QListView = new(bind="_dogs", sort="get_sort_key")

            def get_sort_key(self, dog: Dog) -> int:
                return dog.age

        instance = create_and_track(qt, TestClass, base_class)
        items = get_sorted_items(instance._list.model())

        # Should be sorted by age via method
        assert_that(items[0].name).is_equal_to("Rex")
        assert_that(items[1].name).is_equal_to("Fido")
        assert_that(items[2].name).is_equal_to("Buddy")

    def test_sort_with_method_descending(self, base_class, decorator, qt: QtDriver) -> None:
        """Sort descending using method."""

        @decorator
        class TestClass(base_class):
            _dogs: Variable[list[Dog]] = new(
                [
                    Dog("Buddy", 7),
                    Dog("Rex", 2),
                    Dog("Fido", 5),
                ]
            )
            _list: QListView = new(bind="_dogs", sort="sort_key_descending")

            def sort_key_descending(self, dog: Dog) -> int:
                return -dog.age

        instance = create_and_track(qt, TestClass, base_class)
        items = get_sorted_items(instance._list.model())

        # Should be sorted descending
        assert_that(items[0].name).is_equal_to("Buddy")
        assert_that(items[1].name).is_equal_to("Fido")
        assert_that(items[2].name).is_equal_to("Rex")


@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestSortWithFilter:
    """Sort combined with filter."""

    def test_sort_and_filter_together(self, base_class, decorator, qt: QtDriver) -> None:
        """Sort and filter can be used together."""

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
            _list: QListView = new(
                bind="_dogs",
                filter="{age} >= {_min_age}",
                sort="{age}",
            )

        instance = create_and_track(qt, TestClass, base_class)
        items = get_sorted_items(instance._list.model())

        # All items shown, sorted by age
        assert_that(len(items)).is_equal_to(3)
        assert_that(items[0].name).is_equal_to("Rex")

        # Filter to age >= 5
        instance._min_age.value = 5
        items = get_sorted_items(instance._list.model())
        assert_that(len(items)).is_equal_to(2)
        # Remaining items still sorted
        assert_that(items[0].name).is_equal_to("Fido")
        assert_that(items[1].name).is_equal_to("Buddy")


@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestSortWithComboBox:
    """Sort on QComboBox."""

    def test_combobox_sorted(self, base_class, decorator, qt: QtDriver) -> None:
        """QComboBox items are sorted."""

        @decorator
        class TestClass(base_class):
            _items: Variable[list[str]] = new(["Cherry", "Apple", "Banana"])
            _combo: QComboBox = new(bind="_items", sort="{#self}")

        instance = create_and_track(qt, TestClass, base_class)
        items = get_sorted_items(instance._combo.model())

        # Should be sorted alphabetically
        assert_that(items[0]).is_equal_to("Apple")
        assert_that(items[1]).is_equal_to("Banana")
        assert_that(items[2]).is_equal_to("Cherry")


@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestSortMultipleColumnsExpression:
    """Sort by multiple columns using expression syntax."""

    def test_sort_by_two_columns_expression(self, base_class, decorator, qt: QtDriver) -> None:
        """Sort by two columns using tuple expression - primary then secondary."""

        @decorator
        class TestClass(base_class):
            _dogs: Variable[list[Dog]] = new(
                [
                    Dog("Buddy", 5),
                    Dog("Rex", 5),
                    Dog("Fido", 3),
                    Dog("Max", 5),
                ]
            )
            # Sort by age first, then by name using tuple expression
            _list: QListView = new(bind="_dogs", sort="{(age, name)}")

        instance = create_and_track(qt, TestClass, base_class)
        items = get_sorted_items(instance._list.model())

        # Fido (age 3) first, then age 5 sorted by name: Buddy, Max, Rex
        assert_that(items[0].name).is_equal_to("Fido")  # age 3
        assert_that(items[1].name).is_equal_to("Buddy")  # age 5, name B
        assert_that(items[2].name).is_equal_to("Max")  # age 5, name M
        assert_that(items[3].name).is_equal_to("Rex")  # age 5, name R

    def test_sort_by_two_numeric_columns_second_descending_expression(self, base_class, decorator, qt: QtDriver) -> None:
        """Sort by two numeric columns using expression - first ascending, second descending."""

        @dataclass
        class Student:
            name: str
            grade: int  # 1-12
            score: int  # 0-100

        @decorator
        class TestClass(base_class):
            _students: Variable[list[Student]] = new(
                [
                    Student("Alice", 10, 85),
                    Student("Bob", 10, 92),
                    Student("Charlie", 9, 78),
                    Student("Diana", 10, 88),
                ]
            )
            # Sort by grade ascending, then by score descending using -score
            _list: QListView = new(bind="_students", sort="{(grade, -score)}")

        instance = create_and_track(qt, TestClass, base_class)
        items = get_sorted_items(instance._list.model())

        # Grade 9 first (Charlie), then grade 10 sorted by score DESC: Bob(92), Diana(88), Alice(85)
        assert_that(items[0].name).is_equal_to("Charlie")  # grade 9
        assert_that(items[1].name).is_equal_to("Bob")  # grade 10, score 92
        assert_that(items[2].name).is_equal_to("Diana")  # grade 10, score 88
        assert_that(items[3].name).is_equal_to("Alice")  # grade 10, score 85


@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestSortMultipleColumnsLambda:
    """Sort by multiple columns using lambda (for comparison)."""

    def test_sort_by_two_columns(self, base_class, decorator, qt: QtDriver) -> None:
        """Sort by two columns - primary then secondary."""

        @decorator
        class TestClass(base_class):
            _dogs: Variable[list[Dog]] = new(
                [
                    Dog("Buddy", 5),
                    Dog("Rex", 5),
                    Dog("Fido", 3),
                    Dog("Max", 5),
                ]
            )
            # Sort by age first, then by name (both ascending)
            _list: QListView = new(bind="_dogs", sort=lambda x: (x.age, x.name))

        instance = create_and_track(qt, TestClass, base_class)
        items = get_sorted_items(instance._list.model())

        # Fido (age 3) first, then age 5 sorted by name: Buddy, Max, Rex
        assert_that(items[0].name).is_equal_to("Fido")  # age 3
        assert_that(items[1].name).is_equal_to("Buddy")  # age 5, name B
        assert_that(items[2].name).is_equal_to("Max")  # age 5, name M
        assert_that(items[3].name).is_equal_to("Rex")  # age 5, name R

    def test_sort_by_two_columns_second_descending(self, base_class, decorator, qt: QtDriver) -> None:
        """Sort by two columns - first ascending, second descending."""

        @decorator
        class TestClass(base_class):
            _dogs: Variable[list[Dog]] = new(
                [
                    Dog("Buddy", 5),
                    Dog("Rex", 5),
                    Dog("Fido", 3),
                    Dog("Max", 5),
                ]
            )
            # Sort by age ascending, then by name descending
            # For descending string sort, we reverse the string comparison
            _list: QListView = new(bind="_dogs", sort="get_sort_key")

            def get_sort_key(self, dog: Dog):
                # For descending string sort, use a helper class that reverses comparison
                return (dog.age, ReverseString(dog.name))

        instance = create_and_track(qt, TestClass, base_class)
        items = get_sorted_items(instance._list.model())

        # Fido (age 3) first, then age 5 sorted by name DESCENDING: Rex, Max, Buddy
        assert_that(items[0].name).is_equal_to("Fido")  # age 3
        assert_that(items[1].name).is_equal_to("Rex")  # age 5, name R (desc)
        assert_that(items[2].name).is_equal_to("Max")  # age 5, name M (desc)
        assert_that(items[3].name).is_equal_to("Buddy")  # age 5, name B (desc)

    def test_sort_by_two_numeric_columns_second_descending(self, base_class, decorator, qt: QtDriver) -> None:
        """Sort by two numeric columns - first ascending, second descending."""

        @dataclass
        class Student:
            name: str
            grade: int  # 1-12
            score: int  # 0-100

        @decorator
        class TestClass(base_class):
            _students: Variable[list[Student]] = new(
                [
                    Student("Alice", 10, 85),
                    Student("Bob", 10, 92),
                    Student("Charlie", 9, 78),
                    Student("Diana", 10, 88),
                ]
            )
            # Sort by grade ascending, then by score descending (highest first)
            _list: QListView = new(bind="_students", sort=lambda x: (x.grade, -x.score))

        instance = create_and_track(qt, TestClass, base_class)
        items = get_sorted_items(instance._list.model())

        # Grade 9 first (Charlie), then grade 10 sorted by score DESC: Bob(92), Diana(88), Alice(85)
        assert_that(items[0].name).is_equal_to("Charlie")  # grade 9
        assert_that(items[1].name).is_equal_to("Bob")  # grade 10, score 92
        assert_that(items[2].name).is_equal_to("Diana")  # grade 10, score 88
        assert_that(items[3].name).is_equal_to("Alice")  # grade 10, score 85


@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestSortPrimitives:
    """Sort primitive lists (strings, ints)."""

    def test_sort_string_list(self, base_class, decorator, qt: QtDriver) -> None:
        """Sort list of strings using #self."""

        @decorator
        class TestClass(base_class):
            _items: Variable[list[str]] = new(["Zebra", "Apple", "Mango"])
            _list: QListView = new(bind="_items", sort="{#self}")

        instance = create_and_track(qt, TestClass, base_class)
        items = get_sorted_items(instance._list.model())

        assert_that(items[0]).is_equal_to("Apple")
        assert_that(items[1]).is_equal_to("Mango")
        assert_that(items[2]).is_equal_to("Zebra")

    def test_sort_int_list(self, base_class, decorator, qt: QtDriver) -> None:
        """Sort list of integers."""

        @decorator
        class TestClass(base_class):
            _items: Variable[list[int]] = new([50, 10, 30])
            _list: QListView = new(bind="_items", sort="{#self}")

        instance = create_and_track(qt, TestClass, base_class)
        items = get_sorted_items(instance._list.model())

        assert_that(items[0]).is_equal_to(10)
        assert_that(items[1]).is_equal_to(30)
        assert_that(items[2]).is_equal_to(50)


@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestSortWithTableView:
    """Sort on QTableView."""

    def test_tableview_sorted_by_expression(self, base_class, decorator, qt: QtDriver) -> None:
        """QTableView items are sorted by expression."""

        @decorator
        class TestClass(base_class):
            _dogs: Variable[list[Dog]] = new(
                [
                    Dog("Buddy", 7),
                    Dog("Rex", 2),
                    Dog("Fido", 5),
                ]
            )
            _table: QTableView = new(bind="_dogs", sort="{age}")

        instance = create_and_track(qt, TestClass, base_class)
        items = get_sorted_items(instance._table.model())

        # Should be sorted by age ascending
        assert_that(items[0].name).is_equal_to("Rex")
        assert_that(items[1].name).is_equal_to("Fido")
        assert_that(items[2].name).is_equal_to("Buddy")

    def test_tableview_sorted_by_multiple_columns(self, base_class, decorator, qt: QtDriver) -> None:
        """QTableView sorted by multiple columns using tuple expression."""

        @decorator
        class TestClass(base_class):
            _dogs: Variable[list[Dog]] = new(
                [
                    Dog("Buddy", 5),
                    Dog("Rex", 5),
                    Dog("Fido", 3),
                ]
            )
            _table: QTableView = new(bind="_dogs", sort="{(age, name)}")

        instance = create_and_track(qt, TestClass, base_class)
        items = get_sorted_items(instance._table.model())

        # Fido (age 3) first, then age 5 sorted by name
        assert_that(items[0].name).is_equal_to("Fido")
        assert_that(items[1].name).is_equal_to("Buddy")
        assert_that(items[2].name).is_equal_to("Rex")

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
        items = get_sorted_items(instance._table.model())

        # All shown, sorted by age
        assert_that(len(items)).is_equal_to(3)
        assert_that(items[0].name).is_equal_to("Rex")

        # Filter to age >= 5
        instance._min_age.value = 5
        items = get_sorted_items(instance._table.model())
        assert_that(len(items)).is_equal_to(2)
        assert_that(items[0].name).is_equal_to("Fido")


@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestSortWithTreeView:
    """Sort on QTreeView."""

    def test_treeview_sorted_by_expression(self, base_class, decorator, qt: QtDriver) -> None:
        """QTreeView items are sorted by expression."""

        @decorator
        class TestClass(base_class):
            _dogs: Variable[list[Dog]] = new(
                [
                    Dog("Buddy", 7),
                    Dog("Rex", 2),
                    Dog("Fido", 5),
                ]
            )
            _tree: QTreeView = new(bind="_dogs", sort="{age}")

        instance = create_and_track(qt, TestClass, base_class)
        items = get_sorted_items(instance._tree.model())

        # Should be sorted by age ascending
        assert_that(items[0].name).is_equal_to("Rex")
        assert_that(items[1].name).is_equal_to("Fido")
        assert_that(items[2].name).is_equal_to("Buddy")

    def test_treeview_sorted_by_multiple_columns(self, base_class, decorator, qt: QtDriver) -> None:
        """QTreeView sorted by multiple columns using tuple expression."""

        @decorator
        class TestClass(base_class):
            _dogs: Variable[list[Dog]] = new(
                [
                    Dog("Buddy", 5),
                    Dog("Rex", 5),
                    Dog("Fido", 3),
                ]
            )
            _tree: QTreeView = new(bind="_dogs", sort="{(age, name)}")

        instance = create_and_track(qt, TestClass, base_class)
        items = get_sorted_items(instance._tree.model())

        # Fido (age 3) first, then age 5 sorted by name
        assert_that(items[0].name).is_equal_to("Fido")
        assert_that(items[1].name).is_equal_to("Buddy")
        assert_that(items[2].name).is_equal_to("Rex")

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
        items = get_sorted_items(instance._tree.model())

        # All shown, sorted by age
        assert_that(len(items)).is_equal_to(3)
        assert_that(items[0].name).is_equal_to("Rex")

        # Filter to age >= 5
        instance._min_age.value = 5
        items = get_sorted_items(instance._tree.model())
        assert_that(len(items)).is_equal_to(2)
        assert_that(items[0].name).is_equal_to("Fido")
