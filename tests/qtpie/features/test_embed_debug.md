# Embedded Widget Columns in QTableView

This document describes how to embed custom QtPie widgets inside QTableView columns.

## Overview

QtPie allows embedding full Widget instances as table columns. The embedded widgets become persistent editors for each table row, enabling rich interactive UIs within tables.

## Basic Embedded Widget Column

Define a widget class and include it in the `columns=` list alongside field names.

```python
@widget
class SomeWidget(Widget[KeyValue]):
    _label: QLabel = new("HELLO")

@widget
class TestWidget(Widget):
    _items: Variable[list[KeyValue]] = new([KeyValue("a", "b")])
    table: QTableView = new(bind="_items", columns=["key", "value", SomeWidget])
```

The `columns=` list accepts:
- String field names (`"key"`, `"value"`) - rendered as text columns
- Widget classes (`SomeWidget`) - rendered as embedded widget columns

## Widget With Record Type

Embedded widgets can use `Widget[T]` with a record type matching the table's item type. The record is automatically bound per row.

```python
@widget
class SomeWidget(Widget[KeyValue]):
    _label: QLabel = new("HELLO")
```

## Widget Without Record Type

Plain widgets (no `[T]` type parameter) also work. They render identically for each row.

```python
@widget
class SomeWidgetNoRecord(Widget):
    _label: QLabel = new("HELLO")
```

## Binding Through Record Path

Tables can bind to nested record fields using dot notation.

```python
@widget(record=Request("test", [KeyValue("a", "b")]))
class ParamsTabContent(Widget[Request]):
    table: QTableView = new(bind="record.query_params", columns=["key", "value", SomeWidget])
```

## Delegate System

QtPie automatically assigns a `QtPieWidgetDelegate` to widget columns. This delegate:
- Creates widget instances for each row
- Opens persistent editors so widgets remain visible
- Manages widget lifecycle with the table

```python
from qtpie.delegates import QtPieWidgetDelegate

delegate = table.itemDelegateForColumn(2)
assert isinstance(delegate, QtPieWidgetDelegate)
```

## Accessing Embedded Widgets

Retrieve the embedded widget for a specific cell using Qt's `indexWidget()`.

```python
model = table.model()
index = model.index(0, 2)  # row 0, column 2 (widget column)
editor = table.indexWidget(index)
```

## Column Count

The model's column count includes both text and widget columns.

```python
# 2 text columns ("key", "value") + 1 widget column (SomeWidget) = 3
assert model.columnCount() == 3
```

## Testing Pattern

Use `QtDriver` to properly manage widget lifecycle in tests.

```python
def test_embedded_widget(qt: QtDriver) -> None:
    w = TestWidget()
    qt.track(w)
    qt.process_events()

    # Access and verify embedded widgets
    editor = w.table.indexWidget(model.index(0, 2))
    assert editor is not None
```
