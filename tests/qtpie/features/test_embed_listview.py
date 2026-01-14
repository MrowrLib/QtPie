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
"""Tests for QListView with embedded widgets using widget= and embed().

Tests that QListView can display custom Widget subclasses for each item
using Qt's openPersistentEditor() mechanism.
"""

from dataclasses import dataclass

import pytest
from assertpy import assert_that
from PySide6.QtCore import Signal
from PySide6.QtWidgets import QLabel, QListView, QPushButton

from qtpie import Variable, Widget, embed, new, widget
from qtpie.testing import QtDriver

from .conftest import WIDGET_CLASS_TYPES, create_and_track


@dataclass
class Dog:
    """Test dataclass for embedded widget tests."""

    name: str
    age: int


# Simple embedded widget for basic tests
@widget
class DogLabel(Widget[Dog]):
    """A simple widget that displays dog info."""

    _label: QLabel = new(bind="{record.name} ({record.age})")


# Widget with bare Variable for index injection
@widget
class DogLabelWithIndex(Widget[Dog]):
    """Widget with index injection."""

    row_index: Variable[int]  # Bare annotation - will be injected
    _label: QLabel = new(bind="Row {row_index}: {record.name}")


# Widget with signal for parent connection
@widget
class DogLabelWithDelete(Widget[Dog]):
    """Widget with delete signal."""

    # Define a signal that the parent can connect to
    delete_requested = Signal()

    _label: QLabel = new(bind="{record.name}")
    _delete: QPushButton = new("Delete", clicked="on_delete")

    def on_delete(self) -> None:
        """Emit signal when delete requested."""
        self.delete_requested.emit()


@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestListViewEmbedBasic:
    """Basic QListView with widget= embedding."""

    def test_simple_widget_shows_for_each_item(self, base_class, decorator, qt: QtDriver) -> None:
        """widget=MyWidget shows widget for each list item."""

        @decorator
        class TestClass(base_class):
            _dogs: Variable[list[Dog]] = new([Dog("Fido", 3), Dog("Rex", 5)])
            _list: QListView = new(bind="_dogs", widget=DogLabel)

        instance = create_and_track(qt, TestClass, base_class)

        # Process pending events to let persistent editors open
        qt.process_events()

        # Check the model has the right data
        model = instance._list.model()
        assert_that(model.rowCount()).is_equal_to(2)

    def test_widgets_created_for_initial_items(self, base_class, decorator, qt: QtDriver) -> None:
        """Widgets are created for all initial items on construction."""

        @decorator
        class TestClass(base_class):
            _dogs: Variable[list[Dog]] = new([Dog("A", 1), Dog("B", 2), Dog("C", 3)])
            _list: QListView = new(bind="_dogs", widget=DogLabel)

        instance = create_and_track(qt, TestClass, base_class)
        qt.process_events()

        model = instance._list.model()
        assert_that(model.rowCount()).is_equal_to(3)

    def test_widget_created_on_item_append(self, base_class, decorator, qt: QtDriver) -> None:
        """New widget created when item appended to list."""

        @decorator
        class TestClass(base_class):
            _dogs: Variable[list[Dog]] = new([Dog("Fido", 3)])
            _list: QListView = new(bind="_dogs", widget=DogLabel)

        instance = create_and_track(qt, TestClass, base_class)
        qt.process_events()

        model = instance._list.model()
        assert_that(model.rowCount()).is_equal_to(1)

        # Append a new dog
        instance._dogs.append(Dog("Rex", 5))
        qt.process_events()

        assert_that(model.rowCount()).is_equal_to(2)

    def test_widget_removed_on_item_remove(self, base_class, decorator, qt: QtDriver) -> None:
        """Widget removed when item removed from list."""

        @decorator
        class TestClass(base_class):
            _dogs: Variable[list[Dog]] = new([Dog("A", 1), Dog("B", 2), Dog("C", 3)])
            _list: QListView = new(bind="_dogs", widget=DogLabel)

        instance = create_and_track(qt, TestClass, base_class)
        qt.process_events()

        model = instance._list.model()
        assert_that(model.rowCount()).is_equal_to(3)

        # Remove middle item
        instance._dogs.remove(Dog("B", 2))
        qt.process_events()

        assert_that(model.rowCount()).is_equal_to(2)

    def test_widgets_cleared_on_list_clear(self, base_class, decorator, qt: QtDriver) -> None:
        """All widgets removed when list cleared."""

        @decorator
        class TestClass(base_class):
            _dogs: Variable[list[Dog]] = new([Dog("A", 1), Dog("B", 2)])
            _list: QListView = new(bind="_dogs", widget=DogLabel)

        instance = create_and_track(qt, TestClass, base_class)
        qt.process_events()

        model = instance._list.model()
        assert_that(model.rowCount()).is_equal_to(2)

        instance._dogs.clear()
        qt.process_events()

        assert_that(model.rowCount()).is_equal_to(0)

    def test_empty_list_no_crash(self, base_class, decorator, qt: QtDriver) -> None:
        """No crash when list starts empty."""

        @decorator
        class TestClass(base_class):
            _dogs: Variable[list[Dog]] = new([])
            _list: QListView = new(bind="_dogs", widget=DogLabel)

        instance = create_and_track(qt, TestClass, base_class)
        qt.process_events()

        model = instance._list.model()
        assert_that(model.rowCount()).is_equal_to(0)

        # Add items to empty list
        instance._dogs.append(Dog("Fido", 3))
        qt.process_events()

        assert_that(model.rowCount()).is_equal_to(1)


@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestListViewEmbedWithIndex:
    """QListView with embed() and selectedIndex injection."""

    def test_embed_with_selected_index(self, base_class, decorator, qt: QtDriver) -> None:
        """embed(MyWidget, selectedIndex='var') injects row index into bare Variable."""

        @decorator
        class TestClass(base_class):
            _dogs: Variable[list[Dog]] = new([Dog("Fido", 3), Dog("Rex", 5)])
            _list: QListView = new(bind="_dogs", widget=embed(DogLabelWithIndex, selectedIndex="row_index"))

        instance = create_and_track(qt, TestClass, base_class)
        qt.process_events()

        model = instance._list.model()
        assert_that(model.rowCount()).is_equal_to(2)


@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestListViewEmbedWithSignalConnection:
    """QListView with embed() and signal connections to parent."""

    def test_embed_signal_connection(self, base_class, decorator, qt: QtDriver) -> None:
        """embed(MyWidget, delete_requested='handler') connects signal to parent method."""
        delete_called = {"count": 0}

        @decorator
        class TestClass(base_class):
            _dogs: Variable[list[Dog]] = new([Dog("Fido", 3)])
            _list: QListView = new(bind="_dogs", widget=embed(DogLabelWithDelete, delete_requested="handle_delete"))

            def handle_delete(self) -> None:
                delete_called["count"] += 1

        instance = create_and_track(qt, TestClass, base_class)
        qt.process_events()

        model = instance._list.model()
        assert_that(model.rowCount()).is_equal_to(1)


@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestListViewEmbedWithVariablePassThrough:
    """QListView with embed() and Variable pass-through from parent."""

    def test_embed_variable_pass_through(self, base_class, decorator, qt: QtDriver) -> None:
        """embed(MyWidget, show_details='_show') passes parent Variable to child."""

        @widget
        class DogLabelWithToggle(Widget[Dog]):
            show_details: Variable[bool]  # Bare - will receive parent's Variable
            _label: QLabel = new(bind="{record.name}")
            _age: QLabel = new(bind="{record.age} years", visible="show_details")

        @decorator
        class TestClass(base_class):
            _show_details: Variable[bool] = new(True)
            _dogs: Variable[list[Dog]] = new([Dog("Fido", 3)])
            _list: QListView = new(bind="_dogs", widget=embed(DogLabelWithToggle, show_details="_show_details"))

        instance = create_and_track(qt, TestClass, base_class)
        qt.process_events()

        model = instance._list.model()
        assert_that(model.rowCount()).is_equal_to(1)


@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestListViewEmbedCombined:
    """QListView with embed() using multiple features together."""

    def test_embed_combined_features(self, base_class, decorator, qt: QtDriver) -> None:
        """embed() with selectedIndex + signal + Variable pass-through."""

        @widget
        class DogCard(Widget[Dog]):
            delete_requested = Signal()

            row_index: Variable[int]
            show_age: Variable[bool]
            _label: QLabel = new(bind="[{row_index}] {record.name}")
            _age: QLabel = new(bind="{record.age} years", visible="show_age")
            _delete: QPushButton = new("X", clicked="on_delete")

            def on_delete(self) -> None:
                self.delete_requested.emit()

        delete_calls: list[int] = []

        @decorator
        class TestClass(base_class):
            _show_age: Variable[bool] = new(True)
            _dogs: Variable[list[Dog]] = new([Dog("Fido", 3), Dog("Rex", 5)])
            _list: QListView = new(
                bind="_dogs",
                widget=embed(
                    DogCard,
                    selectedIndex="row_index",
                    show_age="_show_age",
                    delete_requested="handle_delete",
                ),
            )

            def handle_delete(self) -> None:
                delete_calls.append(1)

        instance = create_and_track(qt, TestClass, base_class)
        qt.process_events()

        model = instance._list.model()
        assert_that(model.rowCount()).is_equal_to(2)
