# List Widget Binding in QtPie

Documentation of list widget binding patterns from `test_list_widget_binding.py`.

## Basic List Binding

Bind a `list[QWidget]` to a `Variable[list[T]]` to create a reactive widget repeater. One widget is created per list item.

```python
@widget
class MyWidget(Widget):
    items: Variable[list[str]] = new(["Hello", "World"])
    labels: list[QLabel] = new(bind="items")
```

The `labels` field becomes a `WidgetRepeater` containing one `QLabel` per item.

## Reactive List Operations

List mutations automatically update widgets:

```python
# Adding items creates new widgets
w.items.append("new item")

# Removing items removes widgets
w.items.remove("item to remove")
```

## Layout Integration

List widgets integrate into the parent layout in field order:

```python
@widget
class MyWidget(Widget):
    header: QLabel = new("Header")
    items: Variable[list[str]] = new(["a", "b"])
    labels: list[QLabel] = new(bind="items")
    footer: QLabel = new("Footer")
```

Layout order: header → repeater → footer.

## Excluding from Layout

Use `layout=False` to create a repeater without adding it to the parent layout:

```python
labels: list[QLabel] = new(bind="items", layout=False)
```

## Widget Constructor Arguments

Pass kwargs to configure each repeated widget:

```python
labels: list[QLabel] = new(bind="items", styleSheet="color: red;")
# or using the alias:
labels: list[QLabel] = new(bind="items", stylesheet="color: blue;")
```

## Binding to Validation Error Messages

### Per-Variable Validation

Bind to a Variable's validation errors:

```python
@widget
class MyWidget(Widget):
    text: Variable[str] = new("")
    errors: list[QLabel] = new(bind="text.validation_error_messages")

    def __setup__(self) -> None:
        self.text.add_validator("required", lambda v: "Required" if not v else None)
```

### Widget-Level Aggregated Validation

Bind to all validation errors across the widget:

```python
@widget
class MyWidget(Widget):
    text1: Variable[str] = new("")
    text2: Variable[str] = new("")
    errors: list[QLabel] = new(bind="validation_error_messages")

    def __setup__(self) -> None:
        self.text1.add_validator("req1", lambda v: "Text1 required" if not v else None)
        self.text2.add_validator("req2", lambda v: "Text2 required" if not v else None)
```

## List-Like Access to Repeated Widgets

The repeater supports standard list operations:

```python
# Index access (positive and negative)
w.labels[0].text()   # First widget
w.labels[-1].text()  # Last widget

# Length
len(w.labels)

# Iteration
for label in w.labels:
    print(label.text())
```

## Modifying Widgets in Setup

Access and modify individual widgets in `__setup__`:

```python
@widget
class MyWidget(Widget):
    items: Variable[list[str]] = new(["first", "second"])
    labels: list[QLabel] = new(bind="items")

    def __setup__(self) -> None:
        self.labels[0].setStyleSheet("color: red;")
        self.labels[1].setStyleSheet("color: blue;")
```
