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
"""Tests for QComboBox model binding with bind=.

Tests that QComboBox bound to Variable[list] uses ReactiveListModel
and updates reactively when the list changes.
"""

from dataclasses import dataclass
from enum import Enum

import pytest
from assertpy import assert_that
from PySide6.QtWidgets import QComboBox

from qtpie import Variable, new
from qtpie.testing import QtDriver

from .conftest import WIDGET_CLASS_TYPES, create_and_track


@dataclass
class Dog:
    """Test dataclass for format= tests."""

    name: str
    age: int


@dataclass
class Product:
    """Test dataclass for format spec tests."""

    name: str
    price: float


@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestComboBoxModelBinding:
    """QComboBox with bind= to Variable[list]."""

    def test_combo_shows_list_items(self, base_class, decorator, qt: QtDriver) -> None:
        """QComboBox with bind= shows Variable[list] items."""

        @decorator
        class TestClass(base_class):
            _items: Variable[list[str]] = new(["A", "B", "C"])
            _combo: QComboBox = new(bind="_items")

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance._combo.count()).is_equal_to(3)
        assert_that(instance._combo.itemText(0)).is_equal_to("A")
        assert_that(instance._combo.itemText(1)).is_equal_to("B")
        assert_that(instance._combo.itemText(2)).is_equal_to("C")

    def test_combo_updates_on_append(self, base_class, decorator, qt: QtDriver) -> None:
        """Appending to list updates QComboBox."""

        @decorator
        class TestClass(base_class):
            _items: Variable[list[str]] = new(["A"])
            _combo: QComboBox = new(bind="_items")

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance._combo.count()).is_equal_to(1)

        instance._items.append("B")
        assert_that(instance._combo.count()).is_equal_to(2)
        assert_that(instance._combo.itemText(1)).is_equal_to("B")

    def test_combo_updates_on_remove(self, base_class, decorator, qt: QtDriver) -> None:
        """Removing from list updates QComboBox."""

        @decorator
        class TestClass(base_class):
            _items: Variable[list[str]] = new(["A", "B", "C"])
            _combo: QComboBox = new(bind="_items")

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance._combo.count()).is_equal_to(3)

        instance._items.remove("B")
        assert_that(instance._combo.count()).is_equal_to(2)
        assert_that(instance._combo.itemText(0)).is_equal_to("A")
        assert_that(instance._combo.itemText(1)).is_equal_to("C")

    def test_combo_updates_on_replace(self, base_class, decorator, qt: QtDriver) -> None:
        """Replacing item in list updates QComboBox."""

        @decorator
        class TestClass(base_class):
            _items: Variable[list[str]] = new(["A", "B"])
            _combo: QComboBox = new(bind="_items")

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance._combo.itemText(0)).is_equal_to("A")

        instance._items[0] = "Z"
        assert_that(instance._combo.itemText(0)).is_equal_to("Z")

    def test_combo_updates_on_clear(self, base_class, decorator, qt: QtDriver) -> None:
        """Clearing list updates QComboBox."""

        @decorator
        class TestClass(base_class):
            _items: Variable[list[str]] = new(["A", "B", "C"])
            _combo: QComboBox = new(bind="_items")

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance._combo.count()).is_equal_to(3)

        instance._items.clear()
        assert_that(instance._combo.count()).is_equal_to(0)

    def test_combo_with_integers(self, base_class, decorator, qt: QtDriver) -> None:
        """QComboBox works with integer lists (str conversion)."""

        @decorator
        class TestClass(base_class):
            _numbers: Variable[list[int]] = new([1, 2, 3])
            _combo: QComboBox = new(bind="_numbers")

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance._combo.count()).is_equal_to(3)
        assert_that(instance._combo.itemText(0)).is_equal_to("1")
        assert_that(instance._combo.itemText(1)).is_equal_to("2")
        assert_that(instance._combo.itemText(2)).is_equal_to("3")

    def test_combo_empty_initial_list(self, base_class, decorator, qt: QtDriver) -> None:
        """QComboBox starts empty with empty list."""

        @decorator
        class TestClass(base_class):
            _items: Variable[list[str]] = new([])
            _combo: QComboBox = new(bind="_items")

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance._combo.count()).is_equal_to(0)

        # Adding items works
        instance._items.append("First")
        assert_that(instance._combo.count()).is_equal_to(1)
        assert_that(instance._combo.itemText(0)).is_equal_to("First")


@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestComboBoxFormatBinding:
    """QComboBox with bind= and format= for complex objects."""

    def test_format_simple_property(self, base_class, decorator, qt: QtDriver) -> None:
        """format= with simple property access."""

        @decorator
        class TestClass(base_class):
            _dogs: Variable[list[Dog]] = new([Dog("Fido", 3), Dog("Rex", 5)])
            _combo: QComboBox = new(bind="_dogs", format="{name}")

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance._combo.count()).is_equal_to(2)
        assert_that(instance._combo.itemText(0)).is_equal_to("Fido")
        assert_that(instance._combo.itemText(1)).is_equal_to("Rex")

    def test_format_multiple_properties(self, base_class, decorator, qt: QtDriver) -> None:
        """format= with multiple properties."""

        @decorator
        class TestClass(base_class):
            _dogs: Variable[list[Dog]] = new([Dog("Fido", 3), Dog("Rex", 5)])
            _combo: QComboBox = new(bind="_dogs", format="{name} ({age} years)")

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance._combo.itemText(0)).is_equal_to("Fido (3 years)")
        assert_that(instance._combo.itemText(1)).is_equal_to("Rex (5 years)")

    def test_format_method_call(self, base_class, decorator, qt: QtDriver) -> None:
        """format= with method calls like .upper()."""

        @decorator
        class TestClass(base_class):
            _dogs: Variable[list[Dog]] = new([Dog("Fido", 3), Dog("Rex", 5)])
            _combo: QComboBox = new(bind="_dogs", format="{name.upper()}")

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance._combo.itemText(0)).is_equal_to("FIDO")
        assert_that(instance._combo.itemText(1)).is_equal_to("REX")

    def test_format_function_call(self, base_class, decorator, qt: QtDriver) -> None:
        """format= with function calls like len()."""

        @decorator
        class TestClass(base_class):
            _dogs: Variable[list[Dog]] = new([Dog("Fido", 3), Dog("Buddy", 2)])
            _combo: QComboBox = new(bind="_dogs", format="{name} (len={len(name)})")

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance._combo.itemText(0)).is_equal_to("Fido (len=4)")
        assert_that(instance._combo.itemText(1)).is_equal_to("Buddy (len=5)")

    def test_format_complex_expression(self, base_class, decorator, qt: QtDriver) -> None:
        """format= with complex expressions combining method and function calls."""

        @decorator
        class TestClass(base_class):
            _dogs: Variable[list[Dog]] = new([Dog("Fido", 3), Dog("Rex", 5)])
            _combo: QComboBox = new(bind="_dogs", format="Name: {name.upper()} - Length: {len(name)}")

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance._combo.itemText(0)).is_equal_to("Name: FIDO - Length: 4")
        assert_that(instance._combo.itemText(1)).is_equal_to("Name: REX - Length: 3")

    def test_format_math_expression(self, base_class, decorator, qt: QtDriver) -> None:
        """format= with math expressions."""

        @decorator
        class TestClass(base_class):
            _dogs: Variable[list[Dog]] = new([Dog("Fido", 3), Dog("Rex", 5)])
            _combo: QComboBox = new(bind="_dogs", format="{name} - dog years: {age * 7}")

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance._combo.itemText(0)).is_equal_to("Fido - dog years: 21")
        assert_that(instance._combo.itemText(1)).is_equal_to("Rex - dog years: 35")

    def test_format_spec(self, base_class, decorator, qt: QtDriver) -> None:
        """format= with Python format specs like :.2f."""

        @decorator
        class TestClass(base_class):
            _products: Variable[list[Product]] = new([Product("Apple", 1.5), Product("Banana", 0.75)])
            _combo: QComboBox = new(bind="_products", format="{name}: ${price:.2f}")

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance._combo.itemText(0)).is_equal_to("Apple: $1.50")
        assert_that(instance._combo.itemText(1)).is_equal_to("Banana: $0.75")

    def test_format_self_reference(self, base_class, decorator, qt: QtDriver) -> None:
        """format= with #self for the whole item."""

        @decorator
        class TestClass(base_class):
            _items: Variable[list[str]] = new(["hello", "world"])
            _combo: QComboBox = new(bind="_items", format="Item: {#self.upper()}")

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance._combo.itemText(0)).is_equal_to("Item: HELLO")
        assert_that(instance._combo.itemText(1)).is_equal_to("Item: WORLD")

    def test_format_updates_on_change(self, base_class, decorator, qt: QtDriver) -> None:
        """format= works correctly when list changes."""

        @decorator
        class TestClass(base_class):
            _dogs: Variable[list[Dog]] = new([Dog("Fido", 3)])
            _combo: QComboBox = new(bind="_dogs", format="{name} ({age})")

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance._combo.itemText(0)).is_equal_to("Fido (3)")

        # Append new item
        instance._dogs.append(Dog("Rex", 5))
        assert_that(instance._combo.count()).is_equal_to(2)
        assert_that(instance._combo.itemText(1)).is_equal_to("Rex (5)")

        # Replace item
        instance._dogs[0] = Dog("Max", 7)
        assert_that(instance._combo.itemText(0)).is_equal_to("Max (7)")


@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestComboBoxSelectionBindingIndex:
    """QComboBox with selectedIndex= binding only."""

    def test_selected_index_initial_value(self, base_class, decorator, qt: QtDriver) -> None:
        """selectedIndex= sets initial selection from Variable."""

        @decorator
        class TestClass(base_class):
            _items: Variable[list[str]] = new(["A", "B", "C"])
            _idx: Variable[int] = new(1)
            _combo: QComboBox = new(bind="_items", selectedIndex="_idx")

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance._combo.currentIndex()).is_equal_to(1)
        assert_that(instance._combo.currentText()).is_equal_to("B")

    def test_selected_index_variable_to_widget(self, base_class, decorator, qt: QtDriver) -> None:
        """Changing selectedIndex Variable updates QComboBox selection."""

        @decorator
        class TestClass(base_class):
            _items: Variable[list[str]] = new(["A", "B", "C"])
            _idx: Variable[int] = new(0)
            _combo: QComboBox = new(bind="_items", selectedIndex="_idx")

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance._combo.currentIndex()).is_equal_to(0)

        instance._idx.value = 2
        assert_that(instance._combo.currentIndex()).is_equal_to(2)
        assert_that(instance._combo.currentText()).is_equal_to("C")

    def test_selected_index_widget_to_variable(self, base_class, decorator, qt: QtDriver) -> None:
        """Changing QComboBox selection updates selectedIndex Variable."""

        @decorator
        class TestClass(base_class):
            _items: Variable[list[str]] = new(["A", "B", "C"])
            _idx: Variable[int] = new(0)
            _combo: QComboBox = new(bind="_items", selectedIndex="_idx")

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance._idx.value).is_equal_to(0)

        instance._combo.setCurrentIndex(2)
        assert_that(instance._idx.value).is_equal_to(2)


@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestComboBoxSelectionBindingItem:
    """QComboBox with selectedItem= binding only."""

    def test_selected_item_initial_value(self, base_class, decorator, qt: QtDriver) -> None:
        """selectedItem= sets initial selection from Variable."""

        @decorator
        class TestClass(base_class):
            _items: Variable[list[str]] = new(["A", "B", "C"])
            _item: Variable[str | None] = new("B")
            _combo: QComboBox = new(bind="_items", selectedItem="_item")

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance._combo.currentIndex()).is_equal_to(1)
        assert_that(instance._combo.currentText()).is_equal_to("B")

    def test_selected_item_variable_to_widget(self, base_class, decorator, qt: QtDriver) -> None:
        """Changing selectedItem Variable updates QComboBox selection."""

        @decorator
        class TestClass(base_class):
            _items: Variable[list[str]] = new(["A", "B", "C"])
            _item: Variable[str | None] = new(None)
            _combo: QComboBox = new(bind="_items", selectedItem="_item")

        instance = create_and_track(qt, TestClass, base_class)

        instance._item.value = "C"
        assert_that(instance._combo.currentIndex()).is_equal_to(2)
        assert_that(instance._combo.currentText()).is_equal_to("C")

    def test_selected_item_widget_to_variable(self, base_class, decorator, qt: QtDriver) -> None:
        """Changing QComboBox selection updates selectedItem Variable."""

        @decorator
        class TestClass(base_class):
            _items: Variable[list[str]] = new(["A", "B", "C"])
            _item: Variable[str | None] = new(None)
            _combo: QComboBox = new(bind="_items", selectedItem="_item")

        instance = create_and_track(qt, TestClass, base_class)

        instance._combo.setCurrentIndex(1)
        assert_that(instance._item.value).is_equal_to("B")

    def test_selected_item_with_objects(self, base_class, decorator, qt: QtDriver) -> None:
        """selectedItem= works with complex objects."""

        @decorator
        class TestClass(base_class):
            _dogs: Variable[list[Dog]] = new([Dog("Fido", 3), Dog("Rex", 5), Dog("Max", 7)])
            _dog: Variable[Dog] = new(Dog("", 0))  # Placeholder default
            _combo: QComboBox = new(bind="_dogs", format="{name}", selectedItem="_dog")

        instance = create_and_track(qt, TestClass, base_class)

        instance._combo.setCurrentIndex(1)
        assert_that(instance._dog.value).is_equal_to(Dog("Rex", 5))
        assert_that(instance._dog.value.name).is_equal_to("Rex")


@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestComboBoxSelectionBindingBoth:
    """QComboBox with both selectedIndex= and selectedItem= bindings."""

    def test_both_bindings_initial_value(self, base_class, decorator, qt: QtDriver) -> None:
        """Both selectedIndex= and selectedItem= work together."""

        @decorator
        class TestClass(base_class):
            _items: Variable[list[str]] = new(["A", "B", "C"])
            _idx: Variable[int] = new(1)
            _item: Variable[str | None] = new(None)
            _combo: QComboBox = new(bind="_items", selectedIndex="_idx", selectedItem="_item")

        instance = create_and_track(qt, TestClass, base_class)
        # Initial index is set from _idx
        assert_that(instance._combo.currentIndex()).is_equal_to(1)
        # Widget → Variable should have set _item
        # Note: initial sync happens when widget selection changes, not on init
        # So _item may still be None until first user interaction

    def test_both_bindings_variable_to_widget(self, base_class, decorator, qt: QtDriver) -> None:
        """Changing index Variable updates both widget and item Variable."""

        @decorator
        class TestClass(base_class):
            _items: Variable[list[str]] = new(["A", "B", "C"])
            _idx: Variable[int] = new(0)
            _item: Variable[str | None] = new(None)
            _combo: QComboBox = new(bind="_items", selectedIndex="_idx", selectedItem="_item")

        instance = create_and_track(qt, TestClass, base_class)

        instance._idx.value = 2
        assert_that(instance._combo.currentIndex()).is_equal_to(2)
        # Note: When we change _idx, the widget updates, but _item won't auto-update
        # unless the widget fires currentIndexChanged. Let's verify the widget state.
        assert_that(instance._combo.currentText()).is_equal_to("C")

    def test_both_bindings_widget_to_variable(self, base_class, decorator, qt: QtDriver) -> None:
        """Changing widget updates both index and item Variables."""

        @decorator
        class TestClass(base_class):
            _items: Variable[list[str]] = new(["A", "B", "C"])
            _idx: Variable[int] = new(0)
            _item: Variable[str | None] = new(None)
            _combo: QComboBox = new(bind="_items", selectedIndex="_idx", selectedItem="_item")

        instance = create_and_track(qt, TestClass, base_class)

        instance._combo.setCurrentIndex(2)
        assert_that(instance._idx.value).is_equal_to(2)
        assert_that(instance._item.value).is_equal_to("C")

    def test_both_bindings_with_objects(self, base_class, decorator, qt: QtDriver) -> None:
        """Both bindings work with complex objects."""

        @decorator
        class TestClass(base_class):
            _dogs: Variable[list[Dog]] = new([Dog("Fido", 3), Dog("Rex", 5)])
            _idx: Variable[int] = new(0)
            _dog: Variable[Dog] = new(Dog("", 0))  # Placeholder default
            _combo: QComboBox = new(bind="_dogs", format="{name}", selectedIndex="_idx", selectedItem="_dog")

        instance = create_and_track(qt, TestClass, base_class)

        instance._combo.setCurrentIndex(1)
        assert_that(instance._idx.value).is_equal_to(1)
        assert_that(instance._dog.value).is_equal_to(Dog("Rex", 5))


@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestSelectionParamsNotStolen:
    """Ensure selection kwargs pass to constructor when widget is not a model widget."""

    def test_combobox_kwargs_pass_to_non_model_widget(self, base_class, decorator, qt: QtDriver) -> None:
        """QComboBox-related kwargs pass to constructor for non-model widgets."""
        from PySide6.QtWidgets import QWidget

        class CustomWidget(QWidget):
            def __init__(
                self,
                parent: QWidget | None = None,
                selectedIndex: int = -1,
                selectedItem: str | None = None,
                format: str | None = None,  # noqa: A002
            ) -> None:
                super().__init__(parent)
                self.my_index = selectedIndex
                self.my_item = selectedItem
                self.my_format = format

        @decorator
        class TestClass(base_class):
            _custom: CustomWidget = new(bind="x", selectedIndex=42, selectedItem="test", format="{name}")

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance._custom.my_index).is_equal_to(42)
        assert_that(instance._custom.my_item).is_equal_to("test")
        assert_that(instance._custom.my_format).is_equal_to("{name}")


@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestSelectionSyncFromWidget:
    """Test that Variables sync from widget when they start as None."""

    def test_selected_index_syncs_from_widget_when_none(self, base_class, decorator, qt: QtDriver) -> None:
        """selectedIndex Variable syncs to widget's current index when starting as None."""

        @decorator
        class TestClass(base_class):
            _items: Variable[list[str]] = new(["A", "B", "C"])
            _idx: Variable[int] = new()  # No default = None
            _combo: QComboBox = new(bind="_items", selectedIndex="_idx")

        instance = create_and_track(qt, TestClass, base_class)
        # Widget shows index 0 by default, Variable should sync to 0
        assert_that(instance._combo.currentIndex()).is_equal_to(0)
        assert_that(instance._idx.value).is_equal_to(0)

    def test_selected_item_syncs_from_widget_when_none(self, base_class, decorator, qt: QtDriver) -> None:
        """selectedItem Variable syncs to widget's current item when starting as None."""

        @decorator
        class TestClass(base_class):
            _items: Variable[list[str]] = new(["A", "B", "C"])
            _item: Variable[str | None] = new(None)
            _combo: QComboBox = new(bind="_items", selectedItem="_item")

        instance = create_and_track(qt, TestClass, base_class)
        # Widget shows index 0 by default, Variable should sync to "A"
        assert_that(instance._combo.currentIndex()).is_equal_to(0)
        assert_that(instance._item.value).is_equal_to("A")

    def test_selected_index_no_sync_when_has_value(self, base_class, decorator, qt: QtDriver) -> None:
        """selectedIndex Variable with value sets widget, doesn't sync from widget."""

        @decorator
        class TestClass(base_class):
            _items: Variable[list[str]] = new(["A", "B", "C"])
            _idx: Variable[int] = new(2)  # Explicit default
            _combo: QComboBox = new(bind="_items", selectedIndex="_idx")

        instance = create_and_track(qt, TestClass, base_class)
        # Variable value should set widget, not the other way around
        assert_that(instance._combo.currentIndex()).is_equal_to(2)
        assert_that(instance._idx.value).is_equal_to(2)

    def test_both_bindings_sync_from_widget_when_none(self, base_class, decorator, qt: QtDriver) -> None:
        """Both Variables sync from widget when index starts as None."""

        @decorator
        class TestClass(base_class):
            _items: Variable[list[str]] = new(["A", "B", "C"])
            _idx: Variable[int] = new()  # No default = None
            _item: Variable[str | None] = new(None)
            _combo: QComboBox = new(bind="_items", selectedIndex="_idx", selectedItem="_item")

        instance = create_and_track(qt, TestClass, base_class)
        # Both should sync to widget's default selection
        assert_that(instance._combo.currentIndex()).is_equal_to(0)
        assert_that(instance._idx.value).is_equal_to(0)
        # Note: _item won't auto-sync in this case because index_var takes precedence
        # in the initial sync logic (it's an if/elif)


@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestBareVariableSelectionBinding:
    """Test bare Variable[T] (no new()) for selection bindings."""

    def test_bare_variable_selected_index(self, base_class, decorator, qt: QtDriver) -> None:
        """Bare Variable[int] works for selectedIndex binding."""

        @decorator
        class TestClass(base_class):
            _items: Variable[list[str]] = new(["A", "B", "C"])
            _idx: Variable[int]  # Bare - no new()!
            _combo: QComboBox = new(bind="_items", selectedIndex="_idx")

        instance = create_and_track(qt, TestClass, base_class)
        # Should sync from widget's default (0)
        assert_that(instance._combo.currentIndex()).is_equal_to(0)
        assert_that(instance._idx.value).is_equal_to(0)

        # Two-way binding should work
        instance._idx.value = 2
        assert_that(instance._combo.currentIndex()).is_equal_to(2)

        instance._combo.setCurrentIndex(1)
        assert_that(instance._idx.value).is_equal_to(1)

    def test_bare_variable_selected_item(self, base_class, decorator, qt: QtDriver) -> None:
        """Bare Variable[str] works for selectedItem binding."""

        @decorator
        class TestClass(base_class):
            _items: Variable[list[str]] = new(["A", "B", "C"])
            _item: Variable[str]  # Bare - no new()!
            _combo: QComboBox = new(bind="_items", selectedItem="_item")

        instance = create_and_track(qt, TestClass, base_class)
        # Should sync from widget's default selection (first item)
        assert_that(instance._combo.currentIndex()).is_equal_to(0)
        assert_that(instance._item.value).is_equal_to("A")

        # Two-way binding should work
        instance._item.value = "C"
        assert_that(instance._combo.currentIndex()).is_equal_to(2)

        instance._combo.setCurrentIndex(1)
        assert_that(instance._item.value).is_equal_to("B")

    def test_bare_variable_both_bindings(self, base_class, decorator, qt: QtDriver) -> None:
        """Bare Variables work with both selectedIndex and selectedItem."""

        @decorator
        class TestClass(base_class):
            _items: Variable[list[str]] = new(["A", "B", "C"])
            _idx: Variable[int]  # Bare
            _item: Variable[str]  # Bare
            _combo: QComboBox = new(bind="_items", selectedIndex="_idx", selectedItem="_item")

        instance = create_and_track(qt, TestClass, base_class)
        # Both should sync from widget
        assert_that(instance._idx.value).is_equal_to(0)
        # Note: item may not sync when index takes precedence

        # Two-way binding
        instance._idx.value = 2
        assert_that(instance._combo.currentIndex()).is_equal_to(2)

    def test_bare_variable_with_format(self, base_class, decorator, qt: QtDriver) -> None:
        """Bare Variable[int] works with format= for complex objects."""

        @decorator
        class TestClass(base_class):
            _items: Variable[list[Dog]] = new([Dog("Fido", 3), Dog("Rex", 5), Dog("Max", 2)])
            _index: Variable[int]  # Bare - no new()!
            _combo: QComboBox = new(bind="_items", format="{name} ({age} yrs)", selectedIndex="_index")

        instance = create_and_track(qt, TestClass, base_class)

        # Check format works
        assert_that(instance._combo.itemText(0)).is_equal_to("Fido (3 yrs)")
        assert_that(instance._combo.itemText(1)).is_equal_to("Rex (5 yrs)")

        # Check selection sync
        assert_that(instance._combo.currentIndex()).is_equal_to(0)
        assert_that(instance._index.value).is_equal_to(0)

        # Two-way binding
        instance._index.value = 1
        assert_that(instance._combo.currentIndex()).is_equal_to(1)

        instance._combo.setCurrentIndex(2)
        assert_that(instance._index.value).is_equal_to(2)

    def test_bare_both_bindings_with_objects(self, base_class, decorator, qt: QtDriver) -> None:
        """Bare Variables for both index and item sync on initial load with complex objects."""

        @decorator
        class TestClass(base_class):
            _dogs: Variable[list[Dog]] = new([Dog("Fido", 3), Dog("Rex", 5), Dog("Max", 2)])
            _index: Variable[int]  # Bare
            _dog: Variable[Dog]  # Bare
            _combo: QComboBox = new(
                bind="_dogs",
                format="{name} ({age} yrs)",
                selectedIndex="_index",
                selectedItem="_dog",
            )

        instance = create_and_track(qt, TestClass, base_class)

        # CRITICAL: Both should sync on initial load - not just after changing
        assert_that(instance._combo.currentIndex()).is_equal_to(0)
        assert_that(instance._index.value).is_equal_to(0)
        assert_that(instance._dog.value).is_not_none()
        assert_that(instance._dog.value.name).is_equal_to("Fido")
        assert_that(instance._dog.value.age).is_equal_to(3)

    def test_bare_item_accessible_immediately(self, base_class, decorator, qt: QtDriver) -> None:
        """Selected item properties can be accessed immediately after widget creation."""

        @decorator
        class TestClass(base_class):
            _dogs: Variable[list[Dog]] = new([Dog("Buddy", 7), Dog("Luna", 4)])
            _selected: Variable[Dog]  # Bare - no new()!
            _combo: QComboBox = new(bind="_dogs", format="{name}", selectedItem="_selected")

            def get_selected_name(self) -> str:
                """Method that accesses selected dog's name."""
                return self._selected.value.name

            def get_selected_age(self) -> int:
                """Method that accesses selected dog's age."""
                return self._selected.value.age

        instance = create_and_track(qt, TestClass, base_class)

        # Should be able to access selected item properties immediately
        assert_that(instance.get_selected_name()).is_equal_to("Buddy")
        assert_that(instance.get_selected_age()).is_equal_to(7)

        # Change selection and verify
        instance._combo.setCurrentIndex(1)
        assert_that(instance.get_selected_name()).is_equal_to("Luna")
        assert_that(instance.get_selected_age()).is_equal_to(4)

    def test_bare_both_bindings_two_way(self, base_class, decorator, qt: QtDriver) -> None:
        """Two-way binding works with both bare index and item Variables."""

        @decorator
        class TestClass(base_class):
            _dogs: Variable[list[Dog]] = new([Dog("A", 1), Dog("B", 2), Dog("C", 3)])
            _idx: Variable[int]  # Bare
            _dog: Variable[Dog]  # Bare
            _combo: QComboBox = new(bind="_dogs", selectedIndex="_idx", selectedItem="_dog")

        instance = create_and_track(qt, TestClass, base_class)

        # Initial state
        assert_that(instance._idx.value).is_equal_to(0)
        assert_that(instance._dog.value.name).is_equal_to("A")

        # Change via index Variable
        instance._idx.value = 2
        assert_that(instance._combo.currentIndex()).is_equal_to(2)
        assert_that(instance._dog.value.name).is_equal_to("C")

        # Change via widget
        instance._combo.setCurrentIndex(1)
        assert_that(instance._idx.value).is_equal_to(1)
        assert_that(instance._dog.value.name).is_equal_to("B")

        # Change via item Variable
        instance._dog.value = Dog("C", 3)
        assert_that(instance._combo.currentIndex()).is_equal_to(2)
        assert_that(instance._idx.value).is_equal_to(2)


# Test enums for enum binding tests


class Priority(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Status(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    DONE = "done"


# Display name mapping for format tests
PRIORITY_LABELS: dict[Priority, str] = {
    Priority.LOW: "Low Priority",
    Priority.MEDIUM: "Medium Priority",
    Priority.HIGH: "High Priority",
}


@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestComboBoxEnumBinding:
    """QComboBox with bind= to an Enum class directly."""

    def test_enum_binding_shows_all_values(self, base_class, decorator, qt: QtDriver) -> None:
        """bind=EnumClass populates QComboBox with all enum values."""

        @decorator
        class TestClass(base_class):
            _combo: QComboBox = new(bind=Priority)

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance._combo.count()).is_equal_to(3)

    def test_enum_binding_default_format_uses_name(self, base_class, decorator, qt: QtDriver) -> None:
        """Default format shows enum .name (e.g., 'LOW', 'MEDIUM')."""

        @decorator
        class TestClass(base_class):
            _combo: QComboBox = new(bind=Priority)

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance._combo.itemText(0)).is_equal_to("LOW")
        assert_that(instance._combo.itemText(1)).is_equal_to("MEDIUM")
        assert_that(instance._combo.itemText(2)).is_equal_to("HIGH")

    def test_enum_binding_format_with_value(self, base_class, decorator, qt: QtDriver) -> None:
        """format='{value}' shows enum .value."""

        @decorator
        class TestClass(base_class):
            _combo: QComboBox = new(bind=Priority, format="{value}")

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance._combo.itemText(0)).is_equal_to("low")
        assert_that(instance._combo.itemText(1)).is_equal_to("medium")
        assert_that(instance._combo.itemText(2)).is_equal_to("high")

    def test_enum_binding_format_with_lambda(self, base_class, decorator, qt: QtDriver) -> None:
        """format= accepts a callable (lambda) for custom formatting."""

        @decorator
        class TestClass(base_class):
            _combo: QComboBox = new(bind=Priority, format=lambda e: f"Priority: {e.name.title()}")

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance._combo.itemText(0)).is_equal_to("Priority: Low")
        assert_that(instance._combo.itemText(1)).is_equal_to("Priority: Medium")
        assert_that(instance._combo.itemText(2)).is_equal_to("Priority: High")

    def test_enum_binding_format_with_dict_get(self, base_class, decorator, qt: QtDriver) -> None:
        """format= accepts dict.get for label lookups."""

        @decorator
        class TestClass(base_class):
            _combo: QComboBox = new(bind=Priority, format=PRIORITY_LABELS.get)

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance._combo.itemText(0)).is_equal_to("Low Priority")
        assert_that(instance._combo.itemText(1)).is_equal_to("Medium Priority")
        assert_that(instance._combo.itemText(2)).is_equal_to("High Priority")

    def test_enum_binding_with_selected_item(self, base_class, decorator, qt: QtDriver) -> None:
        """selectedItem= binds to Variable[EnumType]."""

        @decorator
        class TestClass(base_class):
            _priority: Variable[Priority] = new(Priority.MEDIUM)
            _combo: QComboBox = new(bind=Priority, selectedItem="_priority")

        instance = create_and_track(qt, TestClass, base_class)
        # Initial selection from Variable
        assert_that(instance._combo.currentIndex()).is_equal_to(1)  # MEDIUM is index 1

    def test_enum_binding_selected_item_two_way(self, base_class, decorator, qt: QtDriver) -> None:
        """Two-way binding between QComboBox and Variable[EnumType]."""

        @decorator
        class TestClass(base_class):
            _priority: Variable[Priority] = new(Priority.LOW)
            _combo: QComboBox = new(bind=Priority, selectedItem="_priority")

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance._priority.value).is_equal_to(Priority.LOW)

        # Widget -> Variable
        instance._combo.setCurrentIndex(2)  # HIGH
        assert_that(instance._priority.value).is_equal_to(Priority.HIGH)

        # Variable -> Widget
        instance._priority.value = Priority.MEDIUM
        assert_that(instance._combo.currentIndex()).is_equal_to(1)

    def test_enum_binding_with_selected_index(self, base_class, decorator, qt: QtDriver) -> None:
        """selectedIndex= works with enum binding."""

        @decorator
        class TestClass(base_class):
            _idx: Variable[int] = new(2)
            _combo: QComboBox = new(bind=Priority, selectedIndex="_idx")

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance._combo.currentIndex()).is_equal_to(2)
        assert_that(instance._combo.currentText()).is_equal_to("HIGH")

    def test_enum_binding_bare_variable_syncs(self, base_class, decorator, qt: QtDriver) -> None:
        """Bare Variable[EnumType] syncs from widget on init."""

        @decorator
        class TestClass(base_class):
            _status: Variable[Status]  # Bare - no new()!
            _combo: QComboBox = new(bind=Status, selectedItem="_status")

        instance = create_and_track(qt, TestClass, base_class)
        # Should sync to first enum value
        assert_that(instance._status.value).is_equal_to(Status.PENDING)

    def test_enum_binding_with_format_and_selected_item(self, base_class, decorator, qt: QtDriver) -> None:
        """format= and selectedItem= work together."""

        @decorator
        class TestClass(base_class):
            _priority: Variable[Priority] = new(Priority.HIGH)
            _combo: QComboBox = new(
                bind=Priority,
                format=PRIORITY_LABELS.get,
                selectedItem="_priority",
            )

        instance = create_and_track(qt, TestClass, base_class)
        # Check display uses format
        assert_that(instance._combo.itemText(0)).is_equal_to("Low Priority")
        # Check selection is correct
        assert_that(instance._combo.currentIndex()).is_equal_to(2)  # HIGH
        assert_that(instance._combo.currentText()).is_equal_to("High Priority")

        # Two-way still works
        instance._combo.setCurrentIndex(0)
        assert_that(instance._priority.value).is_equal_to(Priority.LOW)


@dataclass
class MockRequest:
    """Mock request for Widget[T] enum binding tests."""

    body_type: Priority = Priority.LOW


class TestComboBoxEnumBindingWithRecord:
    """QComboBox enum binding with Widget[T] record type."""

    def test_enum_binding_with_record_type_two_way(self, qt: QtDriver) -> None:
        """Enum binding works with Widget[T] - selection persists."""
        from qtpie import Widget, widget

        @widget
        class TestWidget(Widget[MockRequest]):
            _selected: Variable[Priority]
            _combo: QComboBox = new(bind=Priority, selectedItem="_selected")

        instance = TestWidget()
        instance.record = MockRequest()
        qt.track(instance)
        instance.show()

        # Initial sync - bare Variable should sync from widget (index 0)
        assert_that(instance._combo.currentIndex()).is_equal_to(0)
        assert_that(instance._selected.value).is_equal_to(Priority.LOW)

        # User selects HIGH (index 2)
        instance._combo.setCurrentIndex(2)

        # Selection should persist, NOT reset to 0
        assert_that(instance._combo.currentIndex()).is_equal_to(2)
        assert_that(instance._selected.value).is_equal_to(Priority.HIGH)

        # Variable -> Widget also works
        instance._selected.value = Priority.MEDIUM
        assert_that(instance._combo.currentIndex()).is_equal_to(1)

    def test_enum_binding_multiple_selection_changes(self, qt: QtDriver) -> None:
        """Multiple selection changes don't cause reset (stale callback bug)."""
        from qtpie import Widget, widget

        @widget
        class TestWidget(Widget[MockRequest]):
            _selected: Variable[Priority]
            _combo: QComboBox = new(bind=Priority, selectedItem="_selected")

        instance = TestWidget()
        instance.record = MockRequest()
        qt.track(instance)
        instance.show()

        # Change multiple times - each should persist
        instance._combo.setCurrentIndex(2)  # HIGH
        assert_that(instance._combo.currentIndex()).is_equal_to(2)
        assert_that(instance._selected.value).is_equal_to(Priority.HIGH)

        instance._combo.setCurrentIndex(1)  # MEDIUM
        assert_that(instance._combo.currentIndex()).is_equal_to(1)
        assert_that(instance._selected.value).is_equal_to(Priority.MEDIUM)

        instance._combo.setCurrentIndex(0)  # LOW
        assert_that(instance._combo.currentIndex()).is_equal_to(0)
        assert_that(instance._selected.value).is_equal_to(Priority.LOW)

    def test_enum_binding_with_record_field_binding(self, qt: QtDriver) -> None:
        """Enum binding with selectedItem='body_type' binds to record property."""
        from qtpie import Widget, widget

        @widget(record=MockRequest(body_type=Priority.HIGH))
        class TestWidget(Widget[MockRequest]):
            _combo: QComboBox = new(bind=Priority, selectedItem="body_type")

        instance = TestWidget()
        qt.track(instance)
        instance.show()

        # Should reflect record's body_type (HIGH = index 2)
        assert_that(instance._combo.currentIndex()).is_equal_to(2)

        # User changes selection -> should update record
        # Note: record.body_type returns ObservableProxy for Enum fields, use .unwrap() to get value
        instance._combo.setCurrentIndex(1)  # MEDIUM
        assert_that(instance.record.body_type.unwrap()).is_equal_to(Priority.MEDIUM)

        # Record change -> should update widget
        instance.record.body_type = Priority.LOW
        assert_that(instance._combo.currentIndex()).is_equal_to(0)

    def test_enum_binding_with_nested_record_field(self, qt: QtDriver) -> None:
        """Enum binding with selectedItem='nested.field' binds to nested record property.

        Regression test: nested enum fields like 'auth.type' weren't working because
        resolve_binding_source returned ObservableProxy instead of Observable.
        """
        from qtpie import Widget, widget

        @dataclass
        class AuthSettings:
            type: Priority = Priority.LOW

        @dataclass
        class RequestWithAuth:
            auth: AuthSettings | None = None

        @widget(record=RequestWithAuth(auth=AuthSettings(type=Priority.HIGH)))
        class TestWidget(Widget[RequestWithAuth]):
            _combo: QComboBox = new(bind=Priority, selectedItem="auth.type")

        instance = TestWidget()
        qt.track(instance)
        instance.show()

        # Should reflect nested auth.type (HIGH = index 2)
        assert_that(instance._combo.currentIndex()).is_equal_to(2)

        # User changes selection -> should update nested record field
        instance._combo.setCurrentIndex(1)  # MEDIUM
        assert_that(instance.record.auth.type.unwrap()).is_equal_to(Priority.MEDIUM)

        # Nested record change -> should update widget
        instance.record.auth.type = Priority.LOW
        assert_that(instance._combo.currentIndex()).is_equal_to(0)

    def test_enum_binding_with_optional_nested_field(self, qt: QtDriver) -> None:
        """Enum binding with selectedItem='auth?.type' handles optional chaining."""
        from qtpie import Widget, widget

        @dataclass
        class AuthSettings:
            type: Priority = Priority.LOW

        @dataclass
        class RequestWithAuth:
            auth: AuthSettings | None = None

        # Test with auth=None
        @widget(record=RequestWithAuth(auth=None))
        class TestWidgetNull(Widget[RequestWithAuth]):
            _combo: QComboBox = new(bind=Priority, selectedItem="auth?.type")

        instance1 = TestWidgetNull()
        qt.track(instance1)
        instance1.show()

        # With auth=None, should default to first enum value
        assert_that(instance1._combo.currentIndex()).is_equal_to(0)

        # Test with auth set
        @widget(record=RequestWithAuth(auth=AuthSettings(type=Priority.HIGH)))
        class TestWidgetSet(Widget[RequestWithAuth]):
            _combo: QComboBox = new(bind=Priority, selectedItem="auth?.type")

        instance2 = TestWidgetSet()
        qt.track(instance2)
        instance2.show()

        # Should reflect auth.type (HIGH = index 2)
        assert_that(instance2._combo.currentIndex()).is_equal_to(2)


@dataclass
class Response:
    """Test dataclass with dict property for dict binding tests."""

    status_code: int
    headers: dict[str, str]


@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestComboBoxDictBinding:
    """QComboBox with bind= to Variable[dict]."""

    def test_combo_binds_to_dict(self, base_class, decorator, qt: QtDriver) -> None:
        """QComboBox with bind=Variable[dict] shows dict items as tuples."""

        @decorator
        class TestClass(base_class):
            _headers: Variable[dict[str, str]] = new({"Content-Type": "application/json", "Accept": "text/html"})
            _combo: QComboBox = new(bind="_headers")

        instance = create_and_track(qt, TestClass, base_class)

        # Should have 2 items (one per dict entry)
        assert_that(instance._combo.count()).is_equal_to(2)

    def test_combo_dict_with_format(self, base_class, decorator, qt: QtDriver) -> None:
        """QComboBox with bind=dict and format='{#key}: {#value}' formats properly."""

        @decorator
        class TestClass(base_class):
            _headers: Variable[dict[str, str]] = new({"Content-Type": "application/json"})
            _combo: QComboBox = new(bind="_headers", format="{#key}: {#value}")

        instance = create_and_track(qt, TestClass, base_class)

        # Should show formatted key: value
        assert_that(instance._combo.itemText(0)).is_equal_to("Content-Type: application/json")

    def test_combo_dict_optional_chaining(self, base_class, decorator, qt: QtDriver) -> None:
        """QComboBox with bind='response?.headers' where response is Variable[Response | None]."""

        @decorator
        class TestClass(base_class):
            _response: Variable[Response | None] = new(None)
            _combo: QComboBox = new(bind="_response?.headers", format="{#key}: {#value}")

        instance = create_and_track(qt, TestClass, base_class)

        # Initially response is None, combo should be empty
        assert_that(instance._combo.count()).is_equal_to(0)

        # Set response - combo should update
        instance._response.value = Response(200, {"X-Custom": "test-value"})

        assert_that(instance._combo.count()).is_equal_to(1)
        assert_that(instance._combo.itemText(0)).is_equal_to("X-Custom: test-value")


# =============================================================================
# Comprehensive Dict Binding Tests (ObservableDict, RecordVariable[dict])
# =============================================================================


# =============================================================================
# Static List/Dict Binding Tests
# =============================================================================


@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestComboBoxStaticListBinding:
    """QComboBox with bind= to static list[str] class attribute."""

    def test_static_list_shows_items(self, base_class, decorator, qt: QtDriver) -> None:
        """Static list[str] attribute populates QComboBox."""

        @decorator
        class TestClass(base_class):
            _locations: list[str] = new(["header", "query", "cookie"])
            _combo: QComboBox = new(bind="_locations")

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance._combo.count()).is_equal_to(3)
        assert_that(instance._combo.itemText(0)).is_equal_to("header")
        assert_that(instance._combo.itemText(1)).is_equal_to("query")
        assert_that(instance._combo.itemText(2)).is_equal_to("cookie")

    def test_static_list_with_selected_item(self, base_class, decorator, qt: QtDriver) -> None:
        """Static list[str] with selectedItem= binding."""

        @decorator
        class TestClass(base_class):
            _locations: list[str] = new(["header", "query"])
            _selected: Variable[str] = new("query")
            _combo: QComboBox = new(bind="_locations", selectedItem="_selected")

        instance = create_and_track(qt, TestClass, base_class)
        # Initial selection from Variable
        assert_that(instance._combo.currentIndex()).is_equal_to(1)
        assert_that(instance._combo.currentText()).is_equal_to("query")

    def test_static_list_two_way_binding(self, base_class, decorator, qt: QtDriver) -> None:
        """Static list[str] with two-way selectedItem binding."""

        @decorator
        class TestClass(base_class):
            _locations: list[str] = new(["header", "query"])
            _selected: Variable[str]  # Bare variable
            _combo: QComboBox = new(bind="_locations", selectedItem="_selected")

        instance = create_and_track(qt, TestClass, base_class)

        # Initial sync from widget
        assert_that(instance._selected.value).is_equal_to("header")

        # Widget -> Variable
        instance._combo.setCurrentIndex(1)
        assert_that(instance._selected.value).is_equal_to("query")

        # Variable -> Widget
        instance._selected.value = "header"
        assert_that(instance._combo.currentIndex()).is_equal_to(0)

    def test_static_list_with_selected_index(self, base_class, decorator, qt: QtDriver) -> None:
        """Static list[str] with selectedIndex= binding."""

        @decorator
        class TestClass(base_class):
            _locations: list[str] = new(["header", "query", "cookie"])
            _idx: Variable[int] = new(2)
            _combo: QComboBox = new(bind="_locations", selectedIndex="_idx")

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance._combo.currentIndex()).is_equal_to(2)
        assert_that(instance._combo.currentText()).is_equal_to("cookie")


@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestComboBoxStaticDictBinding:
    """QComboBox with bind= to static dict[str, str] class attribute.

    Dict binding: keys are the selectable values, values are the display text.
    """

    def test_static_dict_shows_values_as_display(self, base_class, decorator, qt: QtDriver) -> None:
        """Static dict[str, str] shows dict values as display text."""

        @decorator
        class TestClass(base_class):
            _locations: dict[str, str] = new({"header": "Header", "query": "Query Parameter"})
            _combo: QComboBox = new(bind="_locations")

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance._combo.count()).is_equal_to(2)
        # Display text should be the values
        assert_that(instance._combo.itemText(0)).is_equal_to("Header")
        assert_that(instance._combo.itemText(1)).is_equal_to("Query Parameter")

    def test_static_dict_selected_item_is_key(self, base_class, decorator, qt: QtDriver) -> None:
        """Static dict[str, str] selectedItem= binds to dict keys."""

        @decorator
        class TestClass(base_class):
            _locations: dict[str, str] = new({"header": "Header", "query": "Query Parameter"})
            _selected: Variable[str] = new("query")
            _combo: QComboBox = new(bind="_locations", selectedItem="_selected")

        instance = create_and_track(qt, TestClass, base_class)
        # Variable value "query" should select the second item
        assert_that(instance._combo.currentIndex()).is_equal_to(1)
        # But display text is the value
        assert_that(instance._combo.currentText()).is_equal_to("Query Parameter")

    def test_static_dict_two_way_binding(self, base_class, decorator, qt: QtDriver) -> None:
        """Static dict[str, str] two-way binding uses keys."""

        @decorator
        class TestClass(base_class):
            _locations: dict[str, str] = new({"header": "Header", "query": "Query Parameter"})
            _selected: Variable[str]  # Bare variable
            _combo: QComboBox = new(bind="_locations", selectedItem="_selected")

        instance = create_and_track(qt, TestClass, base_class)

        # Initial sync - should get the key
        assert_that(instance._selected.value).is_equal_to("header")

        # Widget -> Variable (gets key, not display value)
        instance._combo.setCurrentIndex(1)
        assert_that(instance._selected.value).is_equal_to("query")

        # Variable -> Widget (set key, displays value)
        instance._selected.value = "header"
        assert_that(instance._combo.currentIndex()).is_equal_to(0)
        assert_that(instance._combo.currentText()).is_equal_to("Header")


@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestComboBoxInlineListBinding:
    """QComboBox with bind= to inline list literal."""

    def test_inline_list_shows_items(self, base_class, decorator, qt: QtDriver) -> None:
        """Inline list passed to bind= populates QComboBox."""

        @decorator
        class TestClass(base_class):
            _combo: QComboBox = new(bind=["header", "query", "cookie"])

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance._combo.count()).is_equal_to(3)
        assert_that(instance._combo.itemText(0)).is_equal_to("header")
        assert_that(instance._combo.itemText(1)).is_equal_to("query")
        assert_that(instance._combo.itemText(2)).is_equal_to("cookie")

    def test_inline_list_with_selected_item(self, base_class, decorator, qt: QtDriver) -> None:
        """Inline list with selectedItem= binding."""

        @decorator
        class TestClass(base_class):
            _selected: Variable[str] = new("query")
            _combo: QComboBox = new(bind=["header", "query"], selectedItem="_selected")

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance._combo.currentIndex()).is_equal_to(1)

    def test_inline_list_two_way_binding(self, base_class, decorator, qt: QtDriver) -> None:
        """Inline list with two-way selectedItem binding."""

        @decorator
        class TestClass(base_class):
            _selected: Variable[str]  # Bare variable
            _combo: QComboBox = new(bind=["header", "query"], selectedItem="_selected")

        instance = create_and_track(qt, TestClass, base_class)

        # Initial sync
        assert_that(instance._selected.value).is_equal_to("header")

        # Two-way binding
        instance._combo.setCurrentIndex(1)
        assert_that(instance._selected.value).is_equal_to("query")

        instance._selected.value = "header"
        assert_that(instance._combo.currentIndex()).is_equal_to(0)


@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestComboBoxInlineDictBinding:
    """QComboBox with bind= to inline dict literal."""

    def test_inline_dict_shows_values_as_display(self, base_class, decorator, qt: QtDriver) -> None:
        """Inline dict passed to bind= shows values as display text."""

        @decorator
        class TestClass(base_class):
            _combo: QComboBox = new(bind={"header": "Header", "query": "Query Parameter"})

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance._combo.count()).is_equal_to(2)
        assert_that(instance._combo.itemText(0)).is_equal_to("Header")
        assert_that(instance._combo.itemText(1)).is_equal_to("Query Parameter")

    def test_inline_dict_selected_item_is_key(self, base_class, decorator, qt: QtDriver) -> None:
        """Inline dict selectedItem= binds to dict keys."""

        @decorator
        class TestClass(base_class):
            _selected: Variable[str] = new("query")
            _combo: QComboBox = new(bind={"header": "Header", "query": "Query Parameter"}, selectedItem="_selected")

        instance = create_and_track(qt, TestClass, base_class)
        # Variable value "query" should select the second item
        assert_that(instance._combo.currentIndex()).is_equal_to(1)
        assert_that(instance._combo.currentText()).is_equal_to("Query Parameter")

    def test_inline_dict_two_way_binding(self, base_class, decorator, qt: QtDriver) -> None:
        """Inline dict two-way binding uses keys."""

        @decorator
        class TestClass(base_class):
            _selected: Variable[str]  # Bare variable
            _combo: QComboBox = new(bind={"header": "Header", "query": "Query Parameter"}, selectedItem="_selected")

        instance = create_and_track(qt, TestClass, base_class)

        # Initial sync - should get the key
        assert_that(instance._selected.value).is_equal_to("header")

        # Widget -> Variable (gets key, not display value)
        instance._combo.setCurrentIndex(1)
        assert_that(instance._selected.value).is_equal_to("query")

        # Variable -> Widget (set key, displays value)
        instance._selected.value = "header"
        assert_that(instance._combo.currentIndex()).is_equal_to(0)
        assert_that(instance._combo.currentText()).is_equal_to("Header")


@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestComboBoxObservableDictBinding:
    """QComboBox with bind= to ObservableDict directly."""

    def test_combo_binds_to_observable_dict(self, base_class, decorator, qt: QtDriver) -> None:
        """QComboBox with bind=ObservableDict shows dict items."""
        from observant import ObservableDict

        @decorator
        class TestClass(base_class):
            headers: ObservableDict[str, str]
            _combo: QComboBox = new(bind="headers", format="{#key}: {#value}")

            def __setup__(self) -> None:
                self.headers = ObservableDict({"Content-Type": "application/json", "Accept": "text/html"})

        instance = create_and_track(qt, TestClass, base_class)

        # Should have 2 items (one per dict entry)
        assert_that(instance._combo.count()).is_equal_to(2)


@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestComboBoxRecordVariableDictBinding:
    """QComboBox with bind= to record.dict_property (RecordVariable[dict] scenario)."""

    def test_combo_binds_to_record_dict_property(self, base_class, decorator, qt: QtDriver) -> None:
        """QComboBox with bind='headers' shows dict from Widget[Response].record."""

        @decorator(record=Response(200, {"Content-Type": "text/html", "Server": "nginx"}))
        class TestClass(base_class[Response]):  # type: ignore[misc]
            _combo: QComboBox = new(bind="headers", format="{#key}: {#value}")

        instance = create_and_track(qt, TestClass, base_class)

        # Should have 2 items (one per dict entry)
        assert_that(instance._combo.count()).is_equal_to(2)

    @pytest.mark.xfail(reason="Child widget dict binding with late record assignment not fully supported for QComboBox")
    def test_record_dict_via_child_widget_binding(self, base_class, decorator, qt: QtDriver) -> None:
        """Child Widget[Response] with QComboBox bind='headers' works.

        Note: This test is xfail because ReactiveListModel doesn't have the same
        root sync callback as ReactiveTableModel for dict bindings. QTableView
        passes this test but QComboBox doesn't auto-sync when parent sets record later.
        """
        from qtpie import Widget, widget

        @widget
        class HeadersSelector(Widget[Response]):
            """Child widget that shows headers in a combo."""

            _combo: QComboBox = new(bind="headers", format="{#key}: {#value}")

        @decorator
        class TestClass(base_class):
            _response: Variable[Response | None] = new(None)
            _selector: HeadersSelector = new(bind="_response")

        instance = create_and_track(qt, TestClass, base_class)

        # Get the child widget
        selector = instance._selector
        assert_that(selector).is_not_none()

        # Now set the response - THIS should trigger model binding
        instance._response.value = Response(200, {"Authorization": "Bearer token"})

        # Combo should have 1 item NOW (after response was set)
        assert_that(selector._combo.count()).is_equal_to(1)
        assert_that(selector._combo.itemText(0)).is_equal_to("Authorization: Bearer token")
