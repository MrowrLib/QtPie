# List Widget Binding

## Basic List Binding

Create a repeating list of widgets bound to a `Variable[list[T]]`. The list automatically syncs when items are added or removed.

```python
@widget
class MyWidget(Widget):
    items: Variable[list[str]] = new(["Hello", "World"])
    labels: list[QLabel] = new(bind="items")
```

```python
# Add an item
w.items.append("b")
assert_that(w.labels.layout().count()).is_equal_to(2)

# Remove an item
w.items.remove("b")
assert_that(w.labels.layout().count()).is_equal_to(1)
```

## Validation Error Display

Bind a list of labels to validation error messages. Labels automatically appear/disappear as validation state changes.

```python
@widget
class MyWidget(Widget):
    text: Variable[str] = new("")
    text_input: QLineEdit = new(bind="text")
    errors: list[QLabel] = new(bind="text.validation_error_messages")

    def __setup__(self) -> None:
        self.text.add_validator("required", lambda v: "Required" if not v else None)
```

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

## Widget Configuration

Pass constructor kwargs to configure all generated widgets.

```python
@widget
class MyWidget(Widget):
    items: Variable[list[str]] = new(["test"])
    labels: list[QLabel] = new(bind="items", styleSheet="color: red;")
```

## Layout Control

Exclude repeater from parent layout with `layout=False`.

```python
@widget
class MyWidget(Widget):
    header: QLabel = new("Header")
    items: Variable[list[str]] = new(["a", "b"])
    labels: list[QLabel] = new(bind="items", layout=False)
    footer: QLabel = new("Footer")
```

## List Interface

Access and iterate over generated widgets using standard list operations.

```python
assert_that(w.labels[0].text()).is_equal_to("a")
assert_that(w.labels[-1].text()).is_equal_to("c")
assert_that(len(w.labels)).is_equal_to(3)

texts = [label.text() for label in w.labels]
```

```python
def __setup__(self) -> None:
    self.labels[0].setStyleSheet("color: red;")
    self.labels[1].setStyleSheet("color: blue;")
```
