# pyright: reportMissingTypeArgument=false
# pyright: reportPrivateUsage=false
"""Tests for WidgetRepeater signal connections to parent handlers."""

from dataclasses import dataclass

import pytest
from assertpy import assert_that
from qtpy.QtCore import Signal
from qtpy.QtWidgets import QLabel, QPushButton

from qtpie import Variable, Widget, new, widget
from qtpie.testing import QtDriver


@dataclass
class TodoItem:
    """Simple dataclass for testing."""

    text: str
    done: bool = False


@widget
class TodoRow(Widget[TodoItem]):
    """Child widget with a custom signal."""

    on_delete = Signal()
    on_edit = Signal(str)  # Signal with argument

    label: QLabel = new(bind="{text}")
    delete_btn: QPushButton = new("X", clicked="on_delete")


class TestWidgetRepeaterSignals:
    """Test signal connections from child widgets in WidgetRepeater."""

    def test_basic_signal_connection(self, qt: QtDriver) -> None:
        """Basic signal connection passes signal args by default."""
        deleted_indices: list[int] = []

        @widget
        class TodoApp(Widget):
            _items: Variable[list[TodoItem]] = new([TodoItem("Task 1"), TodoItem("Task 2")])
            _todo_list: list[TodoRow] = new(bind="_items", on_delete="on_item_deleted")

            def on_item_deleted(self) -> None:
                # Default: no args passed (signal has no args)
                deleted_indices.append(-1)

        app = qt.track(TodoApp())
        assert_that(len(app._todo_list)).is_equal_to(2)

        # Click delete on first item
        app._todo_list[0].delete_btn.click()

        assert_that(deleted_indices).is_equal_to([-1])

    def test_signal_with_index_placeholder(self, qt: QtDriver) -> None:
        """Signal connection with #index passes the item index."""
        deleted_indices: list[int] = []

        @widget
        class TodoApp(Widget):
            _items: list[TodoItem] = [TodoItem("Task 1"), TodoItem("Task 2")]
            _todo_list: list[TodoRow] = new(bind="_items", on_delete="on_item_deleted(#index)")

            def on_item_deleted(self, index: int) -> None:
                deleted_indices.append(index)

        app = qt.track(TodoApp())

        # Click delete on second item (index 1)
        app._todo_list[1].delete_btn.click()
        assert_that(deleted_indices).is_equal_to([1])

        # Click delete on first item (index 0)
        app._todo_list[0].delete_btn.click()
        assert_that(deleted_indices).is_equal_to([1, 0])

    def test_signal_with_value_placeholder(self, qt: QtDriver) -> None:
        """Signal connection with #value passes the item value."""
        deleted_items: list[TodoItem] = []

        @widget
        class TodoApp(Widget):
            _items: list[TodoItem] = [TodoItem("Task 1"), TodoItem("Task 2")]
            _todo_list: list[TodoRow] = new(bind="_items", on_delete="on_item_deleted(#value)")

            def on_item_deleted(self, item: TodoItem) -> None:
                deleted_items.append(item)

        app = qt.track(TodoApp())

        # Click delete on second item
        app._todo_list[1].delete_btn.click()

        assert_that(len(deleted_items)).is_equal_to(1)
        assert_that(deleted_items[0].text).is_equal_to("Task 2")

    def test_signal_with_widget_placeholder(self, qt: QtDriver) -> None:
        """Signal connection with #widget passes the child widget."""
        deleted_widgets: list[TodoRow] = []

        @widget
        class TodoApp(Widget):
            _items: list[TodoItem] = [TodoItem("Task 1"), TodoItem("Task 2")]
            _todo_list: list[TodoRow] = new(bind="_items", on_delete="on_item_deleted(#widget)")

            def on_item_deleted(self, widget: TodoRow) -> None:
                deleted_widgets.append(widget)

        app = qt.track(TodoApp())

        # Click delete on first item
        app._todo_list[0].delete_btn.click()

        assert_that(len(deleted_widgets)).is_equal_to(1)
        assert_that(deleted_widgets[0]).is_same_as(app._todo_list[0])

    def test_signal_with_multiple_placeholders(self, qt: QtDriver) -> None:
        """Signal connection with multiple placeholders."""
        received_args: list[tuple[TodoItem, int]] = []

        @widget
        class TodoApp(Widget):
            _items: list[TodoItem] = [TodoItem("Task 1"), TodoItem("Task 2")]
            _todo_list: list[TodoRow] = new(bind="_items", on_delete="on_item_deleted(#value, #index)")

            def on_item_deleted(self, item: TodoItem, index: int) -> None:
                received_args.append((item, index))

        app = qt.track(TodoApp())

        # Click delete on second item
        app._todo_list[1].delete_btn.click()

        assert_that(len(received_args)).is_equal_to(1)
        assert_that(received_args[0][0].text).is_equal_to("Task 2")
        assert_that(received_args[0][1]).is_equal_to(1)

    def test_signal_with_no_args(self, qt: QtDriver) -> None:
        """Signal connection with empty parens passes nothing."""
        call_count = 0

        @widget
        class TodoApp(Widget):
            _items: list[TodoItem] = [TodoItem("Task 1")]
            _todo_list: list[TodoRow] = new(bind="_items", on_delete="on_item_deleted()")

            def on_item_deleted(self) -> None:
                nonlocal call_count
                call_count += 1

        app = qt.track(TodoApp())
        app._todo_list[0].delete_btn.click()

        assert_that(call_count).is_equal_to(1)

    def test_index_updates_after_removal(self, qt: QtDriver) -> None:
        """Index placeholder reflects current index after list modifications."""
        deleted_indices: list[int] = []

        @widget
        class TodoApp(Widget):
            _items: list[TodoItem] = [TodoItem("A"), TodoItem("B"), TodoItem("C")]
            _todo_list: list[TodoRow] = new(bind="_items", on_delete="on_item_deleted(#index)")

            def on_item_deleted(self, index: int) -> None:
                deleted_indices.append(index)
                # Remove the item (this should update indices for remaining items)
                del self._items[index]

        app = qt.track(TodoApp())

        # Delete item at index 0 ("A")
        app._todo_list[0].delete_btn.click()
        assert_that(deleted_indices).is_equal_to([0])
        assert_that(len(app._items)).is_equal_to(2)

        # Now "B" is at index 0, "C" is at index 1
        # Delete what's now at index 0 ("B")
        app._todo_list[0].delete_btn.click()
        assert_that(deleted_indices).is_equal_to([0, 0])
        assert_that(len(app._items)).is_equal_to(1)
        assert_that(app._items[0].text).is_equal_to("C")

    def test_signal_with_args_placeholder(self, qt: QtDriver) -> None:
        """Signal connection with #args spreads signal's own arguments."""
        received_args: list[tuple[int, int]] = []

        @dataclass
        class EditItem:
            name: str

        @widget
        class EditRow(Widget[EditItem]):
            value_changed = Signal(int)
            label: QLabel = new(bind="{name}")
            btn: QPushButton = new("Change", clicked="emit_change")

            def emit_change(self) -> None:
                self.value_changed.emit(42)

        @widget
        class App(Widget):
            _items: list[EditItem] = [EditItem("a"), EditItem("b")]
            _rows: list[EditRow] = new(bind="_items", value_changed="on_change(#index, #args)")

            def on_change(self, index: int, signal_value: int) -> None:
                received_args.append((index, signal_value))

        app = qt.track(App())
        app._rows[1].btn.click()

        assert_that(received_args).is_equal_to([(1, 42)])

    def test_invalid_handler_raises(self, qt: QtDriver) -> None:
        """Connecting to nonexistent handler raises AttributeError."""

        @widget
        class TodoApp(Widget):
            _items: list[TodoItem] = [TodoItem("Task")]
            _todo_list: list[TodoRow] = new(bind="_items", on_delete="nonexistent_handler")

        with pytest.raises(AttributeError, match="nonexistent_handler"):
            qt.track(TodoApp())

    def test_callable_handler(self, qt: QtDriver) -> None:
        """Direct callable handler works."""
        call_count = 0

        def handler() -> None:
            nonlocal call_count
            call_count += 1

        @widget
        class TodoApp(Widget):
            _items: list[TodoItem] = [TodoItem("Task")]
            _todo_list: list[TodoRow] = new(bind="_items", on_delete=handler)

        app = qt.track(TodoApp())
        app._todo_list[0].delete_btn.click()

        assert_that(call_count).is_equal_to(1)
