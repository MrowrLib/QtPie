# List Widget Binding Tests

## Basic List Widget Binding

Creates a `WidgetRepeater` that reactively syncs widgets with a list Variable. Adding/removing items from the source list automatically creates/removes widgets.

```python
@widget
class MyWidget(Widget):
    items: Variable[list[str]] = new(["Hello", "World"])
    labels: list[QLabel] = new(bind="items")

w = qt.track(MyWidget())
assert_that(w.labels.layout().count()).is_equal_to(2)
assert_that(w.labels.layout().itemAt(0).widget().text()).is_equal_to("Hello")

# Add an item
w.items.append("b")
assert_that(w.labels.layout().count()).is_equal_to(2)
```

## Binding to Validation Error Messages

Bind a list widget to `Variable.validation_error_messages` to display errors reactively.

```python
@widget
class MyWidget(Widget):
    text: Variable[str] = new("")
    text_input: QLineEdit = new(bind="text")
    errors: list[QLabel] = new(bind="text.validation_error_messages")

    def __setup__(self) -> None:
        self.text.add_validator("required", lambda v: "Required" if not v else None)

w = qt.track(MyWidget())
assert_that(w.errors.layout().count()).is_equal_to(1)

# Enter text - should become valid
w.text_input.setText("hello")
assert_that(w.errors.layout().count()).is_equal_to(0)
```

## Binding to Widget-Level Validation

Bind to `validation_error_messages` (without a variable prefix) to show all validation errors from all fields in the widget.

```python
@widget
class MyWidget(Widget):
    text1: Variable[str] = new("")
    text2: Variable[str] = new("")
    errors: list[QLabel] = new(bind="validation_error_messages")

    def __setup__(self) -> None:
        self.text1.add_validator("req1", lambda v: "Text1 required" if not v else None)
        self.text2.add_validator("req2", lambda v: "Text2 required" if not v else None)

w = qt.track(MyWidget())
assert_that(w.errors.layout().count()).is_equal_to(2)
```

## Widget Constructor Arguments

Pass kwargs to `new()` to forward them to each created widget's constructor.

```python
@widget
class MyWidget(Widget):
    items: Variable[list[str]] = new(["test"])
    labels: list[QLabel] = new(bind="items", styleSheet="color: red;")

w = qt.track(MyWidget())
label = w.labels.layout().itemAt(0).widget()
assert_that(label.styleSheet()).is_equal_to("color: red;")
```

## List Interface

`WidgetRepeater` implements list-like interface: indexing (positive/negative), `len()`, and iteration.

```python
@widget
class MyWidget(Widget):
    items: Variable[list[str]] = new(["a", "b", "c"])
    labels: list[QLabel] = new(bind="items")

w = qt.track(MyWidget())
assert_that(w.labels[0].text()).is_equal_to("a")
assert_that(w.labels[-1].text()).is_equal_to("c")
assert_that(len(w.labels)).is_equal_to(3)

texts = [label.text() for label in w.labels]
assert_that(texts).is_equal_to(["a", "b", "c"])
```

## Layout Placement

`WidgetRepeater` is added to parent layout by default. Use `layout=False` to exclude it.

```python
@widget
class MyWidget(Widget):
    header: QLabel = new("Header")
    items: Variable[list[str]] = new(["a", "b"])
    labels: list[QLabel] = new(bind="items", layout=False)
    footer: QLabel = new("Footer")

w = qt.track(MyWidget())
layout = w.layout()

# Should only have header and footer
assert_that(layout.count()).is_equal_to(2)
assert_that(layout.itemAt(0).widget()).is_equal_to(w.header)
assert_that(layout.itemAt(1).widget()).is_equal_to(w.footer)
```

## Error Handling

`list[QWidget]` requires `bind=` parameter and the bound path must resolve to a list.

```python
# Missing bind= raises ValueError
@widget
class MyWidget(Widget):
    labels: list[QLabel] = new()

# Binding to non-list raises TypeError
@widget
class MyWidget(Widget):
    name: Variable[str] = new("hello")
    labels: list[QLabel] = new(bind="name")
```
