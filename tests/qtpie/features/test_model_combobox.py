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
# pyright: reportUnknownVariableType=false
"""Tests for QComboBox model binding with bind=.

Tests that QComboBox bound to Variable[list] uses ReactiveListModel
and updates reactively when the list changes.
"""

from dataclasses import dataclass, field
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


@dataclass
class ComboWorkspace:
    """Workspace for testing nested selectedItem/selectedIndex bindings."""

    name: str
    items: list[Dog] = field(default_factory=list)
    selected_item: Dog | None = None
    selected_index: int = -1


class TestComboBoxSelectedItemNestedPath:
    """Test selectedItem=/selectedIndex= with nested paths like 'workspace?.selected_item'.

    This tests the same bugs found in QTreeView, QTableView, and QListView:
    1. Bug 1: ObservableProxy not handled in variable resolution
    2. Bug 2: Root variable subscription missing for nested paths
    3. Bug 3: Initial value not synced to widget when Variable has a value
    """

    def test_selectedItem_syncs_initial_value_when_workspace_not_none(self, qt: QtDriver) -> None:
        """selectedItem= with nested path syncs initial value when workspace starts non-None."""
        from qtpie import Widget, widget

        dog_a = Dog("Fido", 3)
        dog_b = Dog("Rex", 5)

        initial_workspace = ComboWorkspace(
            name="Test",
            items=[dog_a, dog_b],
            selected_item=dog_b,  # Pre-select dog B
        )

        @widget
        class TestWidget(Widget):
            workspace: Variable[ComboWorkspace | None] = new(initial_workspace)
            _combo: QComboBox = new(
                bind="workspace?.items",
                format="{name}",
                selectedItem="workspace?.selected_item",
            )

        instance = TestWidget()
        qt.track(instance)
        instance.show()
        qt.process_events()

        # Initial selection should be dog_b (index 1)
        assert_that(instance._combo.currentIndex()).is_equal_to(1)
        assert_that(instance._combo.currentText()).is_equal_to("Rex")

    def test_selectedItem_syncs_when_root_variable_changes_from_none(self, qt: QtDriver) -> None:
        """selectedItem= with nested path should sync when root changes from None."""
        from qtpie import Widget, widget

        dog_a = Dog("Fido", 3)
        dog_b = Dog("Rex", 5)
        dog_c = Dog("Max", 2)

        @widget
        class TestWidget(Widget):
            workspace: Variable[ComboWorkspace | None] = new(None)
            _combo: QComboBox = new(
                bind="workspace?.items",
                format="{name}",
                selectedItem="workspace?.selected_item",
            )

        instance = TestWidget()
        qt.track(instance)
        instance.show()
        qt.process_events()

        # Initially no workspace, combo should be empty
        assert_that(instance._combo.count()).is_equal_to(0)

        # Create workspace with items and a pre-selected item
        workspace = ComboWorkspace(
            name="Test Workspace",
            items=[dog_a, dog_b, dog_c],
            selected_item=dog_b,
        )

        instance.workspace.value = workspace
        qt.process_events()

        # Combo should now have items
        assert_that(instance._combo.count()).is_equal_to(3)

        # Selection should be synced to dog_b (index 1)
        assert_that(instance._combo.currentIndex()).is_equal_to(1)
        assert_that(instance._combo.currentText()).is_equal_to("Rex")

    def test_selectedIndex_syncs_initial_value_when_workspace_not_none(self, qt: QtDriver) -> None:
        """selectedIndex= with nested path syncs initial value when workspace starts non-None."""
        from qtpie import Widget, widget

        dog_a = Dog("Fido", 3)
        dog_b = Dog("Rex", 5)

        initial_workspace = ComboWorkspace(
            name="Test",
            items=[dog_a, dog_b],
            selected_index=1,  # Pre-select index 1
        )

        @widget
        class TestWidget(Widget):
            workspace: Variable[ComboWorkspace | None] = new(initial_workspace)
            _combo: QComboBox = new(
                bind="workspace?.items",
                format="{name}",
                selectedIndex="workspace?.selected_index",
            )

        instance = TestWidget()
        qt.track(instance)
        instance.show()
        qt.process_events()

        # Initial selection should be index 1
        assert_that(instance._combo.currentIndex()).is_equal_to(1)
        assert_that(instance._combo.currentText()).is_equal_to("Rex")

    def test_selectedIndex_syncs_when_root_variable_changes_from_none(self, qt: QtDriver) -> None:
        """selectedIndex= with nested path should sync when root changes from None."""
        from qtpie import Widget, widget

        dog_a = Dog("Fido", 3)
        dog_b = Dog("Rex", 5)

        @widget
        class TestWidget(Widget):
            workspace: Variable[ComboWorkspace | None] = new(None)
            _combo: QComboBox = new(
                bind="workspace?.items",
                format="{name}",
                selectedIndex="workspace?.selected_index",
            )

        instance = TestWidget()
        qt.track(instance)
        instance.show()
        qt.process_events()

        # Create workspace with items and a pre-selected index
        workspace = ComboWorkspace(
            name="Test",
            items=[dog_a, dog_b],
            selected_index=1,
        )

        instance.workspace.value = workspace
        qt.process_events()

        # Selection should be synced to index 1
        assert_that(instance._combo.currentIndex()).is_equal_to(1)
        assert_that(instance._combo.currentText()).is_equal_to("Rex")


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
        # Note: record.body_type returns the actual value (RecordVariable unwraps Observable)
        instance._combo.setCurrentIndex(1)  # MEDIUM
        assert_that(instance.record.body_type).is_equal_to(Priority.MEDIUM)

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
        assert_that(instance.record.auth.type.get()).is_equal_to(Priority.MEDIUM)

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

    def test_record_dict_via_child_widget_binding(self, base_class, decorator, qt: QtDriver) -> None:
        """Child Widget[Response] with QComboBox bind='headers' works."""
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


# =============================================================================
# Signal Handler Multiple Fire Bug Investigation
# =============================================================================


class TestComboBoxSignalHandlerMultipleFires:
    """Investigate bug where currentIndexChanged fires multiple times.

    User reported that with this setup:
    - QComboBox bound to Enum
    - selectedItem= bound to optional nested record field (auth?.location)
    - currentIndexChanged signal connected to handler

    The handler fires 3 times when user changes selection once.
    """

    def test_enum_combo_with_nested_selection_and_signal_handler(self, qt: QtDriver) -> None:
        """Reproduce: Enum combo + selectedItem='auth?.location' + currentIndexChanged handler."""
        from qtpie import Widget, widget

        class ApiKeyLocation(Enum):
            HEADER = "header"
            QUERY = "query"

        API_KEY_LOCATION_LABELS = {
            ApiKeyLocation.HEADER: "Header",
            ApiKeyLocation.QUERY: "Query Parameter",
        }

        @dataclass
        class ApiKeyAuth:
            location: ApiKeyLocation = ApiKeyLocation.HEADER

        @dataclass
        class Request:
            auth: ApiKeyAuth | None = None

        # Track how many times the handler is called
        call_count = {"value": 0}

        @widget(record=Request(auth=ApiKeyAuth(location=ApiKeyLocation.HEADER)))
        class TestWidget(Widget[Request]):
            _combo: QComboBox = new(
                bind=ApiKeyLocation,
                format=API_KEY_LOCATION_LABELS.get,
                selectedItem="auth?.location",
                currentIndexChanged="_on_location_changed",
            )

            def _on_location_changed(self) -> None:
                call_count["value"] += 1

        instance = TestWidget()
        qt.track(instance)
        instance.show()

        # Reset count after initial setup (setup may trigger the signal)
        initial_count = call_count["value"]
        call_count["value"] = 0

        # User changes selection from HEADER (index 0) to QUERY (index 1)
        instance._combo.setCurrentIndex(1)

        # BUG: This should be 1, but user reports it fires 3 times
        print(f"Initial setup fired {initial_count} times")
        print(f"After setCurrentIndex(1), handler fired {call_count['value']} times")

        # Assert it should only fire once
        assert_that(call_count["value"]).is_equal_to(1)

    def test_enum_combo_with_simple_variable_selection(self, qt: QtDriver) -> None:
        """Control test: Enum combo + selectedItem='_location' (simple Variable)."""
        from qtpie import Widget, widget

        class ApiKeyLocation(Enum):
            HEADER = "header"
            QUERY = "query"

        call_count = {"value": 0}

        @widget
        class TestWidget(Widget):
            _location: Variable[ApiKeyLocation] = new(ApiKeyLocation.HEADER)
            _combo: QComboBox = new(
                bind=ApiKeyLocation,
                selectedItem="_location",
                currentIndexChanged="_on_location_changed",
            )

            def _on_location_changed(self) -> None:
                call_count["value"] += 1

        instance = TestWidget()
        qt.track(instance)
        instance.show()

        # Reset count after initial setup
        call_count["value"] = 0

        # User changes selection
        instance._combo.setCurrentIndex(1)

        print(f"Simple Variable: handler fired {call_count['value']} times")
        assert_that(call_count["value"]).is_equal_to(1)

    def test_enum_combo_no_selection_binding(self, qt: QtDriver) -> None:
        """Control test: Enum combo with NO selectedItem= binding."""
        from qtpie import Widget, widget

        class ApiKeyLocation(Enum):
            HEADER = "header"
            QUERY = "query"

        call_count = {"value": 0}

        @widget
        class TestWidget(Widget):
            _combo: QComboBox = new(
                bind=ApiKeyLocation,
                currentIndexChanged="_on_location_changed",
            )

            def _on_location_changed(self) -> None:
                call_count["value"] += 1

        instance = TestWidget()
        qt.track(instance)
        instance.show()

        # Reset count after initial setup
        call_count["value"] = 0

        # User changes selection
        instance._combo.setCurrentIndex(1)

        print(f"No selection binding: handler fired {call_count['value']} times")
        assert_that(call_count["value"]).is_equal_to(1)

    def test_enum_combo_with_visible_binding(self, qt: QtDriver) -> None:
        """Test: Enum combo + selectedItem + visible= binding (closer to user's setup)."""
        from PySide6.QtWidgets import QLabel

        from qtpie import Widget, widget

        class AuthType(Enum):
            NONE = "none"
            API_KEY = "api_key"
            BEARER = "bearer"

        class ApiKeyLocation(Enum):
            HEADER = "header"
            QUERY = "query"

        API_KEY_LOCATION_LABELS = {
            ApiKeyLocation.HEADER: "Header",
            ApiKeyLocation.QUERY: "Query Parameter",
        }

        @dataclass
        class ApiKeyAuth:
            location: ApiKeyLocation = ApiKeyLocation.HEADER

        @dataclass
        class Request:
            auth_type: AuthType = AuthType.API_KEY
            auth: ApiKeyAuth | None = None

        call_count = {"value": 0}

        @widget(record=Request(auth_type=AuthType.API_KEY, auth=ApiKeyAuth(location=ApiKeyLocation.HEADER)))
        class TestWidget(Widget[Request]):
            _label: QLabel = new("Auth Type:")
            _auth_type_combo: QComboBox = new(bind=AuthType, selectedItem="auth_type")

            _location_label: QLabel = new(
                "Location:",
                visible="{auth_type == AuthType.API_KEY}",
            )
            _location_combo: QComboBox = new(
                bind=ApiKeyLocation,
                format=API_KEY_LOCATION_LABELS.get,
                selectedItem="auth?.location",
                visible="{auth_type == AuthType.API_KEY}",
                currentIndexChanged="_on_location_changed",
            )

            def _on_location_changed(self) -> None:
                call_count["value"] += 1
                print(f"  Handler called! Count now: {call_count['value']}")

        instance = TestWidget()
        qt.track(instance)
        instance.show()

        # Reset count after initial setup
        initial_count = call_count["value"]
        call_count["value"] = 0

        print(f"Initial setup fired {initial_count} times")

        # User changes location selection
        print("Changing location from HEADER to QUERY...")
        instance._location_combo.setCurrentIndex(1)

        print(f"After setCurrentIndex(1), handler fired {call_count['value']} times")
        assert_that(call_count["value"]).is_equal_to(1)

    def test_enum_combo_full_user_scenario(self, qt: QtDriver) -> None:
        """Full reproduction of user's scenario with format= and all bindings."""
        from PySide6.QtWidgets import QFormLayout, QLineEdit

        from qtpie import Widget, widget

        class AuthType(Enum):
            NONE = "none"
            API_KEY = "api_key"
            BEARER = "bearer"
            BASIC = "basic"

        class ApiKeyLocation(Enum):
            HEADER = "header"
            QUERY = "query"

        API_KEY_LOCATION_LABELS = {
            ApiKeyLocation.HEADER: "Header",
            ApiKeyLocation.QUERY: "Query Parameter",
        }

        AUTH_TYPE_LABELS = {
            AuthType.NONE: "None",
            AuthType.API_KEY: "API Key",
            AuthType.BEARER: "Bearer Token",
            AuthType.BASIC: "Basic Auth",
        }

        @dataclass
        class ApiKeyAuth:
            type: AuthType = AuthType.API_KEY
            location: ApiKeyLocation = ApiKeyLocation.HEADER
            key: str = "X-API-Key"
            value: str = ""

        @dataclass
        class BasicAuth:
            type: AuthType = AuthType.BASIC
            username: str = ""
            password: str = ""

        @dataclass
        class BearerAuth:
            type: AuthType = AuthType.BEARER
            token: str = ""

        @dataclass
        class Request:
            name: str = "Test Request"
            auth: ApiKeyAuth | BasicAuth | BearerAuth | None = None

        call_count = {"value": 0}
        call_locations: list[str] = []

        @widget(record=Request(auth=ApiKeyAuth()))
        class TestWidget(Widget[Request]):
            _auth_fields_layout: QFormLayout

            # Auth type selector - THIS binds to auth?.type
            _auth_type: QComboBox = new(
                bind=AuthType,
                format=AUTH_TYPE_LABELS.get,
                selectedItem="auth?.type",
            )

            # Basic Auth fields
            _basic_username: QLineEdit = new(
                bind="auth?.username",
                layout="_auth_fields_layout",
                label="Username:",
                visible="{auth?.type == AuthType.BASIC}",
            )
            _basic_password: QLineEdit = new(
                bind="auth?.password",
                layout="_auth_fields_layout",
                label="Password:",
                visible="{auth?.type == AuthType.BASIC}",
            )

            # Bearer Auth fields
            _bearer_token: QLineEdit = new(
                bind="auth?.token",
                layout="_auth_fields_layout",
                label="Token:",
                visible="{auth?.type == AuthType.BEARER}",
            )

            # API Key Auth fields
            _api_key_key: QLineEdit = new(
                bind="auth?.key",
                layout="_auth_fields_layout",
                label="Key:",
                visible="{auth?.type == AuthType.API_KEY}",
            )
            _api_key_value: QLineEdit = new(
                bind="auth?.value",
                layout="_auth_fields_layout",
                label="Value:",
                visible="{auth?.type == AuthType.API_KEY}",
            )
            _api_key_location: QComboBox = new(
                bind=ApiKeyLocation,
                format=API_KEY_LOCATION_LABELS.get,
                layout="_auth_fields_layout",
                label="Location:",
                selectedItem="auth?.location",
                visible="{auth?.type == AuthType.API_KEY}",
                currentIndexChanged="_on_api_key_location_changed",
            )

            def _on_api_key_location_changed(self) -> None:
                call_count["value"] += 1
                # Try to access record like the user does
                if self.record.auth is not None and isinstance(self.record_value.auth, ApiKeyAuth):
                    loc = self.record_value.auth.location
                    call_locations.append(str(loc))
                    print(f"  Handler #{call_count['value']}: API Key location = {loc}")

        instance = TestWidget()
        qt.track(instance)
        instance.show()

        # Reset count after initial setup
        initial_count = call_count["value"]
        call_count["value"] = 0
        call_locations.clear()

        print(f"Initial setup fired {initial_count} times")

        # User changes location selection
        print("Changing location from HEADER (0) to QUERY (1)...")
        instance._api_key_location.setCurrentIndex(1)

        print(f"After setCurrentIndex(1), handler fired {call_count['value']} times")
        print(f"Call locations: {call_locations}")

        # This is the bug - should be 1, user reports 3
        assert_that(call_count["value"]).is_equal_to(1)

    def test_enum_combo_embedded_in_parent_widget(self, qt: QtDriver) -> None:
        """Test: Widget embedded in parent with Variable binding to record."""
        from PySide6.QtWidgets import QFormLayout, QLabel, QLineEdit

        from qtpie import Widget, widget

        class AuthType(Enum):
            NONE = "none"
            API_KEY = "api_key"
            BEARER = "bearer"

        class ApiKeyLocation(Enum):
            HEADER = "header"
            QUERY = "query"

        API_KEY_LOCATION_LABELS = {
            ApiKeyLocation.HEADER: "Header",
            ApiKeyLocation.QUERY: "Query Parameter",
        }

        AUTH_TYPE_LABELS = {
            AuthType.NONE: "None",
            AuthType.API_KEY: "API Key",
            AuthType.BEARER: "Bearer Token",
        }

        @dataclass
        class ApiKeyAuth:
            type: AuthType = AuthType.API_KEY
            location: ApiKeyLocation = ApiKeyLocation.HEADER
            key: str = "X-API-Key"
            value: str = ""

        @dataclass
        class Request:
            name: str = "Test Request"
            auth: ApiKeyAuth | None = None

        call_count = {"value": 0}

        # Child widget that edits auth
        @widget(title="Auth")
        class AuthTabContent(Widget[Request]):
            _auth_fields_layout: QFormLayout

            _auth_type: QComboBox = new(
                bind=AuthType,
                format=AUTH_TYPE_LABELS.get,
                selectedItem="auth?.type",
            )

            _api_key_key: QLineEdit = new(
                bind="auth?.key",
                layout="_auth_fields_layout",
                label="Key:",
                visible="{auth?.type == AuthType.API_KEY}",
            )
            _api_key_value: QLineEdit = new(
                bind="auth?.value",
                layout="_auth_fields_layout",
                label="Value:",
                visible="{auth?.type == AuthType.API_KEY}",
            )
            _api_key_location: QComboBox = new(
                bind=ApiKeyLocation,
                format=API_KEY_LOCATION_LABELS.get,
                layout="_auth_fields_layout",
                label="Location:",
                selectedItem="auth?.location",
                visible="{auth?.type == AuthType.API_KEY}",
                currentIndexChanged="_on_api_key_location_changed",
            )

            def _on_api_key_location_changed(self) -> None:
                call_count["value"] += 1
                print(f"  Handler #{call_count['value']} fired")

        # Parent widget that holds the request
        @widget
        class ParentWidget(Widget):
            _request: Variable[Request] = new(Request(auth=ApiKeyAuth()))
            _auth_tab: AuthTabContent = new(bind="_request")
            _name_label: QLabel = new(bind="Name: {_request.name}")

        instance = ParentWidget()
        qt.track(instance)
        instance.show()

        # Reset count after initial setup
        initial_count = call_count["value"]
        call_count["value"] = 0

        print(f"Initial setup fired {initial_count} times")

        # User changes location selection on the child widget
        print("Changing location from HEADER (0) to QUERY (1)...")
        instance._auth_tab._api_key_location.setCurrentIndex(1)

        print(f"After setCurrentIndex(1), handler fired {call_count['value']} times")

        # Should be 1
        assert_that(call_count["value"]).is_equal_to(1)

    def test_signal_handler_sees_updated_value(self, qt: QtDriver) -> None:
        """Verify that user's signal handler sees the UPDATED value, not the old one."""
        from qtpie import Widget, widget

        class Priority(Enum):
            LOW = "low"
            MEDIUM = "medium"
            HIGH = "high"

        seen_values: list[Priority] = []

        @widget
        class TestWidget(Widget):
            _priority: Variable[Priority] = new(Priority.LOW)
            _combo: QComboBox = new(
                bind=Priority,
                selectedItem="_priority",
                currentIndexChanged="_on_changed",
            )

            def _on_changed(self) -> None:
                # What value does the handler see?
                seen_values.append(self._priority.value)

        instance = TestWidget()
        qt.track(instance)
        instance.show()

        seen_values.clear()

        # Change from LOW (0) to HIGH (2)
        instance._combo.setCurrentIndex(2)

        # Handler should see HIGH (the updated value)
        assert_that(seen_values).is_equal_to([Priority.HIGH])

    def test_combo_in_tab_widget_signal_fires_once(self, qt: QtDriver) -> None:
        """Test that signal handler fires once when combo is in a tab widget.

        BUG: When a Widget[T] is added via tabs=, _propagate_record_to_child calls
        apply_auto_bindings AGAIN after the widget was already initialized. This causes
        the selection binding's signal handler to be connected multiple times.
        """
        from PySide6.QtWidgets import QTabWidget

        from qtpie import Widget, widget

        class Priority(Enum):
            LOW = "low"
            MEDIUM = "medium"
            HIGH = "high"

        @dataclass
        class Settings:
            priority: Priority = Priority.LOW

        call_count = {"value": 0}

        @widget(title="Settings")
        class SettingsTab(Widget[Settings]):
            _combo: QComboBox = new(
                bind=Priority,
                selectedItem="priority",
                currentIndexChanged="_on_changed",
            )

            def _on_changed(self) -> None:
                call_count["value"] += 1
                print(f"  Tab handler #{call_count['value']} fired")

        @widget(record=Settings(priority=Priority.LOW))
        class ParentWidget(Widget[Settings]):
            _tabs: QTabWidget = new(tabs=[SettingsTab])

        instance = ParentWidget()
        qt.track(instance)
        instance.show()

        # Reset count after initial setup
        initial_count = call_count["value"]
        call_count["value"] = 0

        print(f"Initial setup fired {initial_count} times")

        # Get the settings tab
        settings_tab = instance._tabs.widget(0)
        assert_that(settings_tab).is_instance_of(SettingsTab)

        # User changes selection
        print("Changing priority from LOW (0) to HIGH (2)...")
        settings_tab._combo.setCurrentIndex(2)

        print(f"After setCurrentIndex(2), handler fired {call_count['value']} times")

        # BUG: This fires multiple times because apply_auto_bindings is called twice:
        # 1. During SettingsTab.__init__
        # 2. Again in _propagate_record_to_child
        assert_that(call_count["value"]).is_equal_to(1)

    def test_combo_deeply_nested_in_tab_widget(self, qt: QtDriver) -> None:
        """Test: Deeply nested Widget[T] structure like Forc.

        Structure: ParentWidget[Request] -> ChildWidget[Request] -> QTabWidget -> GrandchildTab[Request]
        This matches Forc's: RequestWidget -> RequestEditorWidget -> QTabWidget -> AuthTabContent
        """
        from PySide6.QtWidgets import QTabWidget

        from qtpie import Widget, widget

        class Priority(Enum):
            LOW = "low"
            MEDIUM = "medium"
            HIGH = "high"

        @dataclass
        class Settings:
            priority: Priority = Priority.LOW

        call_count = {"value": 0}
        init_count = {"value": 0}

        @widget(title="Settings Tab")
        class GrandchildTab(Widget[Settings]):
            """The deepest widget - like AuthTabContent."""

            _combo: QComboBox = new(
                bind=Priority,
                selectedItem="priority",
                currentIndexChanged="_on_changed",
            )

            def __init__(self, *args, **kwargs) -> None:  # type: ignore[no-untyped-def]
                init_count["value"] += 1
                print(f"  GrandchildTab init #{init_count['value']}")
                super().__init__(*args, **kwargs)

            def _on_changed(self) -> None:
                call_count["value"] += 1
                print(f"  Handler #{call_count['value']} fired")

        @widget
        class ChildWidget(Widget[Settings]):
            """Middle widget - like RequestEditorWidget."""

            _tabs: QTabWidget = new(tabs=[GrandchildTab])

        @widget(record=Settings(priority=Priority.LOW))
        class ParentWidget(Widget[Settings]):
            """Top-level widget - like RequestWidget."""

            _child: ChildWidget

        print("\nCreating ParentWidget...")
        instance = ParentWidget()
        qt.track(instance)
        instance.show()

        print(f"GrandchildTab was initialized {init_count['value']} times")
        print(f"Initial handler fires: {call_count['value']}")

        # Reset count
        initial_calls = call_count["value"]
        call_count["value"] = 0

        # Get the deeply nested combo
        grandchild = instance._child._tabs.widget(0)
        assert_that(grandchild).is_instance_of(GrandchildTab)

        # Change selection
        print("\nChanging priority from LOW (0) to HIGH (2)...")
        grandchild._combo.setCurrentIndex(2)

        print(f"Handler fired {call_count['value']} times after change")
        print(f"(Initial setup fired {initial_calls} times)")

        # Should only fire once
        assert_that(call_count["value"]).is_equal_to(1)


# =============================================================================
# Issue Reproduction: selectedItem Dirty State Across Selections
# =============================================================================


@dataclass
class EditablePerson:
    """Editable person for dirty state testing."""

    name: str
    age: int


@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestComboBoxSelectedItemDirtyStateAcrossSelections:
    """Test that dirty state is tracked correctly when combo selection changes.

    The key scenario: if you have two items and you:
    1. Select item 1
    2. Modify item 1 via selectedItem (dirty = true)
    3. Select item 2
    4. What is _selected.is_dirty?

    It SHOULD be false (item 2 is clean) but if dirty state is per-Variable
    rather than per-proxy, it might incorrectly show dirty.
    """

    def test_dirty_state_resets_when_selecting_clean_item(self, base_class, decorator, qt: QtDriver) -> None:
        """Switching selection to a clean item should show is_dirty=false."""

        @decorator
        class TestClass(base_class):
            _people: Variable[list[EditablePerson]] = new([EditablePerson("Alice", 30), EditablePerson("Bob", 25)])
            _selected: Variable[EditablePerson | None] = new(None)
            _combo: QComboBox = new(bind="_people", format="{name}", selectedItem="_selected")

        instance = create_and_track(qt, TestClass, base_class)
        qt.process_events()

        # First item is auto-selected
        assert_that(instance._selected.value).is_not_none()
        assert_that(instance._selected.value.name).is_equal_to("Alice")

        # Modify the first item
        instance._selected.name = "Alice Modified"  # type: ignore[attr-defined]
        qt.process_events()

        # Should be dirty now
        assert_that(instance._selected.is_dirty.get()).is_true()

        # Select second item (Bob, which is clean)
        instance._combo.setCurrentIndex(1)
        qt.process_events()

        # Now _selected points to Bob
        assert_that(instance._selected.value.name).is_equal_to("Bob")

        # EXPECTED: Since Bob is clean, is_dirty should be false
        # This WILL FAIL if dirty state is tracked per-Variable rather than per-item
        assert_that(instance._selected.is_dirty.get()).is_false()

    def test_dirty_state_persists_for_modified_item(self, base_class, decorator, qt: QtDriver) -> None:
        """Going back to a modified item should show is_dirty=true."""

        @decorator
        class TestClass(base_class):
            _people: Variable[list[EditablePerson]] = new([EditablePerson("Alice", 30), EditablePerson("Bob", 25)])
            _selected: Variable[EditablePerson | None] = new(None)
            _combo: QComboBox = new(bind="_people", format="{name}", selectedItem="_selected")

        instance = create_and_track(qt, TestClass, base_class)
        qt.process_events()

        # First item is auto-selected
        assert_that(instance._selected.value.name).is_equal_to("Alice")
        instance._selected.name = "Alice Modified"  # type: ignore[attr-defined]
        qt.process_events()
        assert_that(instance._selected.is_dirty.get()).is_true()

        # Select second item
        instance._combo.setCurrentIndex(1)
        qt.process_events()

        # Select first item again
        instance._combo.setCurrentIndex(0)
        qt.process_events()

        # EXPECTED: First item (Alice Modified) is still dirty
        # This test checks if dirty state is remembered per-item
        assert_that(instance._selected.value.name).is_equal_to("Alice Modified")
        assert_that(instance._selected.is_dirty.get()).is_true()


# =============================================================================
# selectedText= Binding Tests - Match by display text (format= output)
# =============================================================================


@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestComboBoxSelectedTextBinding:
    """QComboBox with selectedText= binding - matches by display text.

    This binding matches the Variable[str] against the formatted display text
    shown in the combobox, rather than matching the item object directly.

    Use case: When you have a list of objects with a format= template but want
    to bind selection to a simple string (like Environment.name).
    """

    def test_selected_text_initial_value(self, base_class, decorator, qt: QtDriver) -> None:
        """selectedText= sets initial selection from Variable matching display text."""

        @decorator
        class TestClass(base_class):
            _dogs: Variable[list[Dog]] = new([Dog("Fido", 3), Dog("Rex", 5), Dog("Max", 7)])
            _name: Variable[str] = new("Rex")  # Match by display text
            _combo: QComboBox = new(bind="_dogs", format="{name}", selectedText="_name")

        instance = create_and_track(qt, TestClass, base_class)
        # "Rex" should match the second item
        assert_that(instance._combo.currentIndex()).is_equal_to(1)
        assert_that(instance._combo.currentText()).is_equal_to("Rex")

    def test_selected_text_variable_to_widget(self, base_class, decorator, qt: QtDriver) -> None:
        """Changing selectedText Variable updates QComboBox selection."""

        @decorator
        class TestClass(base_class):
            _dogs: Variable[list[Dog]] = new([Dog("Fido", 3), Dog("Rex", 5), Dog("Max", 7)])
            _name: Variable[str] = new("Fido")
            _combo: QComboBox = new(bind="_dogs", format="{name}", selectedText="_name")

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance._combo.currentIndex()).is_equal_to(0)

        instance._name.value = "Max"
        assert_that(instance._combo.currentIndex()).is_equal_to(2)
        assert_that(instance._combo.currentText()).is_equal_to("Max")

    def test_selected_text_widget_to_variable(self, base_class, decorator, qt: QtDriver) -> None:
        """Changing QComboBox selection updates selectedText Variable."""

        @decorator
        class TestClass(base_class):
            _dogs: Variable[list[Dog]] = new([Dog("Fido", 3), Dog("Rex", 5)])
            _name: Variable[str | None] = new(None)
            _combo: QComboBox = new(bind="_dogs", format="{name}", selectedText="_name")

        instance = create_and_track(qt, TestClass, base_class)
        # Initial sync sets the display text
        assert_that(instance._name.value).is_equal_to("Fido")

        instance._combo.setCurrentIndex(1)
        assert_that(instance._name.value).is_equal_to("Rex")

    def test_selected_text_with_complex_format(self, base_class, decorator, qt: QtDriver) -> None:
        """selectedText= works with complex format expressions."""

        @decorator
        class TestClass(base_class):
            _dogs: Variable[list[Dog]] = new([Dog("Fido", 3), Dog("Rex", 5)])
            _text: Variable[str | None] = new("Fido (3 years)")
            _combo: QComboBox = new(bind="_dogs", format="{name} ({age} years)", selectedText="_text")

        instance = create_and_track(qt, TestClass, base_class)
        # Should match "Fido (3 years)" which is the first item
        assert_that(instance._combo.currentIndex()).is_equal_to(0)

        instance._combo.setCurrentIndex(1)
        assert_that(instance._text.value).is_equal_to("Rex (5 years)")

    def test_selected_text_with_string_list(self, base_class, decorator, qt: QtDriver) -> None:
        """selectedText= works with simple string lists (no format needed)."""

        @decorator
        class TestClass(base_class):
            _options: Variable[list[str]] = new(["Development", "Production", "Staging"])
            _env: Variable[str] = new("Production")
            _combo: QComboBox = new(bind="_options", selectedText="_env")

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance._combo.currentIndex()).is_equal_to(1)
        assert_that(instance._combo.currentText()).is_equal_to("Production")

        instance._env.value = "Staging"
        assert_that(instance._combo.currentIndex()).is_equal_to(2)

    def test_selected_text_bare_variable_syncs(self, base_class, decorator, qt: QtDriver) -> None:
        """Bare Variable[str] syncs from widget on init."""

        @decorator
        class TestClass(base_class):
            _dogs: Variable[list[Dog]] = new([Dog("Fido", 3), Dog("Rex", 5)])
            _name: Variable[str]  # Bare - no new()!
            _combo: QComboBox = new(bind="_dogs", format="{name}", selectedText="_name")

        instance = create_and_track(qt, TestClass, base_class)
        # Should sync to first item's display text
        assert_that(instance._name.value).is_equal_to("Fido")

    def test_selected_text_with_selected_index(self, base_class, decorator, qt: QtDriver) -> None:
        """selectedText= and selectedIndex= work together."""

        @decorator
        class TestClass(base_class):
            _dogs: Variable[list[Dog]] = new([Dog("Fido", 3), Dog("Rex", 5)])
            _idx: Variable[int] = new(1)
            _name: Variable[str] = new("")
            _combo: QComboBox = new(bind="_dogs", format="{name}", selectedIndex="_idx", selectedText="_name")

        instance = create_and_track(qt, TestClass, base_class)
        # Index binding takes precedence for initial selection
        assert_that(instance._combo.currentIndex()).is_equal_to(1)
        # But text should sync
        assert_that(instance._name.value).is_equal_to("Rex")

        # Changing selection updates both
        instance._combo.setCurrentIndex(0)
        assert_that(instance._idx.value).is_equal_to(0)
        assert_that(instance._name.value).is_equal_to("Fido")

    def test_selected_text_with_selected_item(self, base_class, decorator, qt: QtDriver) -> None:
        """selectedText= and selectedItem= work together."""

        @decorator
        class TestClass(base_class):
            _dogs: Variable[list[Dog]] = new([Dog("Fido", 3), Dog("Rex", 5)])
            _dog: Variable[Dog | None] = new(None)
            _name: Variable[str] = new("")
            _combo: QComboBox = new(bind="_dogs", format="{name}", selectedItem="_dog", selectedText="_name")

        instance = create_and_track(qt, TestClass, base_class)
        # Initial sync happens
        assert_that(instance._combo.currentIndex()).is_equal_to(0)
        assert_that(instance._dog.value).is_not_none()
        assert_that(instance._name.value).is_equal_to("Fido")

        # Changing selection updates both
        instance._combo.setCurrentIndex(1)
        assert_that(instance._dog.value.name).is_equal_to("Rex")
        assert_that(instance._name.value).is_equal_to("Rex")

    def test_selected_text_no_match_keeps_current(self, base_class, decorator, qt: QtDriver) -> None:
        """Setting selectedText to non-matching value doesn't change selection."""

        @decorator
        class TestClass(base_class):
            _dogs: Variable[list[Dog]] = new([Dog("Fido", 3), Dog("Rex", 5)])
            _name: Variable[str] = new("Fido")
            _combo: QComboBox = new(bind="_dogs", format="{name}", selectedText="_name")

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance._combo.currentIndex()).is_equal_to(0)

        # Setting to non-matching value - widget should stay as is
        instance._name.value = "NonExistent"
        # Selection doesn't change when no match found
        assert_that(instance._combo.currentIndex()).is_equal_to(0)

    def test_selected_text_syncs_when_items_added_later(self, base_class, decorator, qt: QtDriver) -> None:
        """selectedText= syncs correctly when items are added after widget creation."""

        @decorator
        class TestClass(base_class):
            _dogs: Variable[list[Dog]] = new([])  # Start empty!
            _name: Variable[str] = new("Rex")  # Already set to "Rex"
            _combo: QComboBox = new(bind="_dogs", format="{name}", selectedText="_name")

        instance = create_and_track(qt, TestClass, base_class)

        # Initially empty, no selection possible
        assert_that(instance._combo.count()).is_equal_to(0)

        # Add items - "Rex" should now be auto-selected
        instance._dogs.append(Dog("Fido", 3))
        instance._dogs.append(Dog("Rex", 5))
        instance._dogs.append(Dog("Max", 7))

        # Should have selected "Rex" (index 1)
        assert_that(instance._combo.count()).is_equal_to(3)
        assert_that(instance._combo.currentIndex()).is_equal_to(1)
        assert_that(instance._combo.currentText()).is_equal_to("Rex")


@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestComboBoxSelectedTextObservable:
    """QComboBox with selectedText= binding using Observable[str] instead of Variable[str]."""

    def test_selected_text_observable_initial_value(self, base_class, decorator, qt: QtDriver) -> None:
        """selectedText= works with Observable[str] for initial selection."""
        from observant import Observable

        @decorator
        class TestClass(base_class):
            _dogs: Variable[list[Dog]] = new([Dog("Fido", 3), Dog("Rex", 5), Dog("Max", 7)])
            _name: Observable[str] = new("Rex")
            _combo: QComboBox = new(bind="_dogs", format="{name}", selectedText="_name")

        instance = create_and_track(qt, TestClass, base_class)
        # "Rex" should match the second item
        assert_that(instance._combo.currentIndex()).is_equal_to(1)
        assert_that(instance._combo.currentText()).is_equal_to("Rex")

    def test_selected_text_observable_variable_to_widget(self, base_class, decorator, qt: QtDriver) -> None:
        """Changing Observable[str] updates QComboBox selection."""
        from observant import Observable

        @decorator
        class TestClass(base_class):
            _dogs: Variable[list[Dog]] = new([Dog("Fido", 3), Dog("Rex", 5), Dog("Max", 7)])
            _name: Observable[str] = new("Fido")
            _combo: QComboBox = new(bind="_dogs", format="{name}", selectedText="_name")

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance._combo.currentIndex()).is_equal_to(0)

        instance._name.set("Max")
        assert_that(instance._combo.currentIndex()).is_equal_to(2)
        assert_that(instance._combo.currentText()).is_equal_to("Max")

    def test_selected_text_observable_widget_to_variable(self, base_class, decorator, qt: QtDriver) -> None:
        """Changing QComboBox selection updates Observable[str]."""
        from observant import Observable

        @decorator
        class TestClass(base_class):
            _dogs: Variable[list[Dog]] = new([Dog("Fido", 3), Dog("Rex", 5)])
            _name: Observable[str] = new("")
            _combo: QComboBox = new(bind="_dogs", format="{name}", selectedText="_name")

        instance = create_and_track(qt, TestClass, base_class)
        # Initial sync sets the display text
        assert_that(instance._name.get()).is_equal_to("Fido")

        instance._combo.setCurrentIndex(1)
        assert_that(instance._name.get()).is_equal_to("Rex")
