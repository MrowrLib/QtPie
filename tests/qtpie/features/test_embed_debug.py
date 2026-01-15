# pyright: reportPrivateUsage=false
# pyright: reportAttributeAccessIssue=false
# pyright: reportUnknownVariableType=false
# pyright: reportUnknownMemberType=false
"""Debug test for embed column detection."""

from dataclasses import dataclass, field

from PySide6.QtWidgets import QLabel, QTableView

from qtpie import Variable, Widget, new, widget
from qtpie.testing import QtDriver


@dataclass
class KeyValue:
    key: str
    value: str


@dataclass
class Request:
    """A request with query params - mimics user's real structure."""

    name: str = ""
    query_params: list[KeyValue] = field(default_factory=list)


@widget
class SomeWidget(Widget[KeyValue]):
    _label: QLabel = new("HELLO")


@widget
class SomeWidgetNoRecord(Widget):
    """Widget without record type - just plain HELLO label."""

    _label: QLabel = new("HELLO")


def test_table_model_has_3_columns(qt: QtDriver) -> None:
    """Check that the model has 3 columns."""

    @widget
    class TestWidget(Widget):
        _items: Variable[list[KeyValue]] = new([KeyValue("a", "b"), KeyValue("c", "d")])
        table: QTableView = new(bind="_items", columns=["key", "value", SomeWidget])

    w = TestWidget()
    qt.track(w)
    qt.process_events()

    model = w.table.model()
    print(f"\nrowCount: {model.rowCount()}")
    print(f"columnCount: {model.columnCount()}")

    assert model.rowCount() == 2
    assert model.columnCount() == 3


def test_table_delegate_is_set(qt: QtDriver) -> None:
    """Check that delegate is set for widget column."""

    @widget
    class TestWidget(Widget):
        _items: Variable[list[KeyValue]] = new([KeyValue("a", "b")])
        table: QTableView = new(bind="_items", columns=["key", "value", SomeWidget])

    w = TestWidget()
    qt.track(w)
    qt.process_events()

    # Check delegate for column 2
    delegate = w.table.itemDelegateForColumn(2)
    print(f"\ndelegate for column 2: {delegate}")
    print(f"delegate type: {type(delegate)}")

    from qtpie.delegates import QtPieWidgetDelegate

    assert isinstance(delegate, QtPieWidgetDelegate)


def test_table_persistent_editor_opened(qt: QtDriver) -> None:
    """Check that persistent editor is opened for widget column."""

    @widget
    class TestWidget(Widget):
        _items: Variable[list[KeyValue]] = new([KeyValue("a", "b")])
        table: QTableView = new(bind="_items", columns=["key", "value", SomeWidget])

    w = TestWidget()
    qt.track(w)
    qt.process_events()

    model = w.table.model()

    # Check if persistent editor exists for row 0, column 2
    index = model.index(0, 2)
    editor = w.table.indexWidget(index)
    print(f"\nindex widget for (0, 2): {editor}")
    print(f"index widget type: {type(editor)}")

    # The editor should be our SomeWidget
    assert editor is not None, "No persistent editor found for widget column"


def test_table_with_record_binding(qt: QtDriver) -> None:
    """Test table bound through record.field path - matches user's real use case."""

    @widget(record=Request("test", [KeyValue("a", "b"), KeyValue("c", "d")]))
    class ParamsTabContent(Widget[Request]):
        table: QTableView = new(bind="record.query_params", columns=["key", "value", SomeWidget])

    w = ParamsTabContent()
    qt.track(w)
    qt.process_events()

    model = w.table.model()
    print(f"\n[record binding] rowCount: {model.rowCount()}")
    print(f"[record binding] columnCount: {model.columnCount()}")

    assert model.rowCount() == 2, "Model should have 2 rows"
    assert model.columnCount() == 3, "Model should have 3 columns (key, value, widget)"

    # Check delegate for column 2
    delegate = w.table.itemDelegateForColumn(2)
    print(f"[record binding] delegate for column 2: {delegate}")

    from qtpie.delegates import QtPieWidgetDelegate

    assert isinstance(delegate, QtPieWidgetDelegate), "Delegate should be QtPieWidgetDelegate"

    # Check if persistent editor exists for row 0, column 2
    index = model.index(0, 2)
    editor = w.table.indexWidget(index)
    print(f"[record binding] index widget for (0, 2): {editor}")

    assert editor is not None, "No persistent editor found for widget column"


def test_widget_is_visible_and_has_size(qt: QtDriver) -> None:
    """Check that the embedded widget has proper size and visibility."""

    @widget
    class TestWidget(Widget):
        _items: Variable[list[KeyValue]] = new([KeyValue("a", "b")])
        table: QTableView = new(bind="_items", columns=["key", "value", SomeWidget])

    w = TestWidget()
    w.resize(400, 300)  # Give it some size
    w.show()
    qt.track(w)
    qt.process_events()

    model = w.table.model()
    index = model.index(0, 2)
    editor = w.table.indexWidget(index)

    assert editor is not None
    assert editor._label.text() == "HELLO", f"Expected 'HELLO' but got '{editor._label.text()}'"


def test_widget_without_record_has_text(qt: QtDriver) -> None:
    """Check that embedded widget without record type shows text."""

    @widget
    class TestWidget(Widget):
        _items: Variable[list[KeyValue]] = new([KeyValue("a", "b")])
        table: QTableView = new(bind="_items", columns=["key", "value", SomeWidgetNoRecord])

    w = TestWidget()
    w.resize(400, 300)
    w.show()
    qt.track(w)
    qt.process_events()

    model = w.table.model()
    index = model.index(0, 2)
    editor = w.table.indexWidget(index)

    print(f"\n[no record] Widget: {editor}")
    label = editor._label
    print(f"[no record] Label text: '{label.text()}'")

    assert label.text() == "HELLO", f"Expected 'HELLO' but got '{label.text()}'"
