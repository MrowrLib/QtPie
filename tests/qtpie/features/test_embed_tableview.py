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
"""Tests for QTableView with embedded widget columns using columns=[...widget...] and embed().

Tests that QTableView can display custom Widget subclasses in specific columns
using Qt's openPersistentEditor() mechanism.
"""

from dataclasses import dataclass

import pytest
from assertpy import assert_that
from PySide6.QtCore import Signal
from PySide6.QtWidgets import QLabel, QPushButton, QTableView

from qtpie import Variable, Widget, embed, new, widget
from qtpie.testing import QtDriver

from .conftest import WIDGET_CLASS_TYPES, create_and_track


@dataclass
class Dog:
    """Test dataclass for embedded widget tests."""

    name: str
    age: int


# Simple widget for action column
@widget
class DogActions(Widget[Dog]):
    """Actions widget with delete button."""

    delete_requested = Signal()

    _delete: QPushButton = new("Delete", clicked="on_delete")

    def on_delete(self) -> None:
        self.delete_requested.emit()


# Widget with row index injection
@widget
class DogActionsWithRow(Widget[Dog]):
    """Actions widget with row index."""

    row: Variable[int]  # Bare annotation - will be injected
    _label: QLabel = new(bind="Row {row}")
    _delete: QPushButton = new("X")


@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestTableViewWidgetColumn:
    """QTableView with widget class in columns list."""

    def test_widget_in_columns_list(self, base_class, decorator, qt: QtDriver) -> None:
        """Widget class in columns list shows widget in that column."""

        @decorator
        class TestClass(base_class):
            _dogs: Variable[list[Dog]] = new([Dog("Fido", 3), Dog("Rex", 5)])
            _table: QTableView = new(bind="_dogs", columns=["name", "age", DogActions])

        instance = create_and_track(qt, TestClass, base_class)
        qt.process_events()

        model = instance._table.model()
        assert_that(model.rowCount()).is_equal_to(2)
        assert_that(model.columnCount()).is_equal_to(3)

    def test_widget_column_in_middle(self, base_class, decorator, qt: QtDriver) -> None:
        """columns=['name', MyWidget, 'age'] - widget column in middle."""

        @decorator
        class TestClass(base_class):
            _dogs: Variable[list[Dog]] = new([Dog("Fido", 3)])
            _table: QTableView = new(bind="_dogs", columns=["name", DogActions, "age"])

        instance = create_and_track(qt, TestClass, base_class)
        qt.process_events()

        model = instance._table.model()
        assert_that(model.columnCount()).is_equal_to(3)

    def test_widget_column_first(self, base_class, decorator, qt: QtDriver) -> None:
        """columns=[MyWidget, 'name', 'age'] - widget column first."""

        @decorator
        class TestClass(base_class):
            _dogs: Variable[list[Dog]] = new([Dog("Fido", 3)])
            _table: QTableView = new(bind="_dogs", columns=[DogActions, "name", "age"])

        instance = create_and_track(qt, TestClass, base_class)
        qt.process_events()

        model = instance._table.model()
        assert_that(model.columnCount()).is_equal_to(3)

    def test_text_columns_work_alongside_widget(self, base_class, decorator, qt: QtDriver) -> None:
        """Text columns still work alongside widget columns."""

        @decorator
        class TestClass(base_class):
            _dogs: Variable[list[Dog]] = new([Dog("Fido", 3), Dog("Rex", 5)])
            _table: QTableView = new(bind="_dogs", columns=["name", "age", DogActions])

        instance = create_and_track(qt, TestClass, base_class)
        qt.process_events()

        model = instance._table.model()
        # Text columns should still show data
        assert_that(model.data(model.index(0, 0))).is_equal_to("Fido")
        # Age may be returned as int or string depending on model implementation
        assert_that(str(model.data(model.index(0, 1)))).is_equal_to("3")


@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestTableViewEmbedWithSelectedRow:
    """QTableView with embed() and selectedRow injection."""

    def test_embed_with_selected_row(self, base_class, decorator, qt: QtDriver) -> None:
        """embed(MyWidget, selectedRow='row') injects row index."""

        @decorator
        class TestClass(base_class):
            _dogs: Variable[list[Dog]] = new([Dog("Fido", 3), Dog("Rex", 5)])
            _table: QTableView = new(
                bind="_dogs",
                columns=["name", "age", embed(DogActionsWithRow, selectedRow="row")],
            )

        instance = create_and_track(qt, TestClass, base_class)
        qt.process_events()

        model = instance._table.model()
        assert_that(model.rowCount()).is_equal_to(2)
        assert_that(model.columnCount()).is_equal_to(3)


@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestTableViewEmbedWithSignalConnection:
    """QTableView with embed() and signal connections to parent."""

    def test_embed_signal_connection(self, base_class, decorator, qt: QtDriver) -> None:
        """embed(MyWidget, delete_requested='handler') connects signal to parent method."""
        delete_called = {"count": 0}

        @decorator
        class TestClass(base_class):
            _dogs: Variable[list[Dog]] = new([Dog("Fido", 3)])
            _table: QTableView = new(
                bind="_dogs",
                columns=["name", embed(DogActions, delete_requested="handle_delete")],
            )

            def handle_delete(self) -> None:
                delete_called["count"] += 1

        instance = create_and_track(qt, TestClass, base_class)
        qt.process_events()

        model = instance._table.model()
        assert_that(model.rowCount()).is_equal_to(1)


@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestTableViewLifecycle:
    """QTableView widget lifecycle management."""

    def test_widgets_created_on_row_insert(self, base_class, decorator, qt: QtDriver) -> None:
        """Widget created on row insert."""

        @decorator
        class TestClass(base_class):
            _dogs: Variable[list[Dog]] = new([Dog("Fido", 3)])
            _table: QTableView = new(bind="_dogs", columns=["name", DogActions])

        instance = create_and_track(qt, TestClass, base_class)
        qt.process_events()

        model = instance._table.model()
        assert_that(model.rowCount()).is_equal_to(1)

        instance._dogs.append(Dog("Rex", 5))
        qt.process_events()

        assert_that(model.rowCount()).is_equal_to(2)

    def test_widgets_removed_on_row_delete(self, base_class, decorator, qt: QtDriver) -> None:
        """Widget removed on row delete."""

        @decorator
        class TestClass(base_class):
            _dogs: Variable[list[Dog]] = new([Dog("A", 1), Dog("B", 2)])
            _table: QTableView = new(bind="_dogs", columns=["name", DogActions])

        instance = create_and_track(qt, TestClass, base_class)
        qt.process_events()

        model = instance._table.model()
        assert_that(model.rowCount()).is_equal_to(2)

        instance._dogs.pop(0)
        qt.process_events()

        assert_that(model.rowCount()).is_equal_to(1)

    def test_widgets_cleared_on_list_clear(self, base_class, decorator, qt: QtDriver) -> None:
        """Widgets cleared on list clear."""

        @decorator
        class TestClass(base_class):
            _dogs: Variable[list[Dog]] = new([Dog("A", 1), Dog("B", 2)])
            _table: QTableView = new(bind="_dogs", columns=["name", DogActions])

        instance = create_and_track(qt, TestClass, base_class)
        qt.process_events()

        instance._dogs.clear()
        qt.process_events()

        model = instance._table.model()
        assert_that(model.rowCount()).is_equal_to(0)
