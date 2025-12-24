# ![Qt Pie](docs/images/QtPie%2064.png) Qt Pie

*Tasty way to build Qt apps*

```bash
pip install qtpie
```

**Declarative. Reactive. Delightful.**

```python
from qtpie import entrypoint, make, state, widget
from qtpy.QtWidgets import QLabel, QPushButton, QWidget


@entrypoint
@widget
class Counter(QWidget):

    # Tracked state - changes update the UI
    count: int = state(0)

    # Updates automatically when count changes
    label: QLabel = make(QLabel, bind="Count: {count}")

    # Calls increment() when clicked
    button: QPushButton = make(QPushButton, "+1", clicked="increment")

    def increment(self) -> None:
        self.count += 1
```

| Light mode | Dark mode |
|:--:|:--:|
| ![Light mode](docs/images/screenshots/hello-world-light-mode.png) | ![Dark mode](docs/images/screenshots/hello-world-dark-mode.png) |

Click the button. State changes. Label updates. That's it.

[Documentation →](https://mrowrlib.github.io/qtpie)

## Features

- **`state()`** - reactive variables that update the UI
- **`bind="{x}"`** - format expressions with auto-refresh
- **`clicked="method"`** - signal connections by name
- **`@widget`** - dataclass-style components with automatic layouts
- **`Widget[T]`** - type-safe model binding
- **SCSS hot reload** - style with CSS classes
- **Async support** - `async def` just works
- **pyright strict** - full type safety, no compromises

## Why QtPie?

Qt is powerful but verbose:

```python
# Plain Qt - 35 lines of boilerplate
class Counter(QWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName("Counter")
        self.count = 0

        layout = QVBoxLayout(self)

        self.label = QLabel("Count: 0")
        self.label.setObjectName("label")
        layout.addWidget(self.label)

        self.button = QPushButton("Add")
        self.button.setObjectName("button")
        self.button.clicked.connect(self.increment)
        layout.addWidget(self.button)

    def increment(self):
        self.count += 1
        self.label.setText(f"Count: {self.count}")


if __name__ == "__main__":
    app = QApplication([])
    window = Counter()
    window.show()
    app.exec()
```

vs QtPie - **12 lines**, fully reactive:

```python
@entrypoint
@widget
class Counter(QWidget):
    count: int = state(0)
    label: QLabel = make(QLabel, bind="Count: {count}")
    button: QPushButton = make(QPushButton, "+1", clicked="increment")

    def increment(self) -> None:
        self.count += 1
```

## Quick Examples

### Reactive State

```python
count: int = state(0)
label: QLabel = make(QLabel, bind="Count: {count}")

self.count += 1  # Label updates instantly
```

### Two-Way Binding

```python
@widget
class Greeter(QWidget):
    name: str = state("")
    name_input: QLineEdit = make(QLineEdit, bind="name")
    greeting: QLabel = make(QLabel, bind="Hello, {name}!")
```

Type in the input, greeting updates. Change `self.name`, input updates.

### Format Expressions

```python
bind="Count: {count}"
bind="{first} {last}"
bind="{name.upper()}"
bind="Total: ${price * 1.1:.2f}"
```

### Automatic Layouts

```python
@widget
class MyWidget(QWidget):
    top: QLabel = make(QLabel, "Top")
    middle: QLabel = make(QLabel, "Middle")
    bottom: QLabel = make(QLabel, "Bottom")

@widget(layout="form")
class MyForm(QWidget):
    name: QLineEdit = make(QLineEdit, form_label="Name:")
    email: QLineEdit = make(QLineEdit, form_label="Email:")
```

### Model Binding

```python
@dataclass
class Person:
    name: str = ""
    age: int = 0

@widget
class PersonEditor(QWidget, Widget[Person]):
    name: QLineEdit = make(QLineEdit)  # auto-binds to model.name
    age: QSpinBox = make(QSpinBox)      # auto-binds to model.age
```

### Full Qt Access

QtPie is a layer, not a cage. All of Qt is still there:

```python
@widget
class MyWidget(QWidget):
    label: QLabel = make(QLabel, "Hello")

    def setup(self) -> None:
        self.setWindowTitle("My App")
        self.label.setStyleSheet("color: red;")
```

## License

[`0BSD`](https://opensource.org/license/0bsd)

Use however, no attribution required.

```
BSD Zero Clause License (SPDX: 0BSD)

Permission to use, copy, modify, and/or distribute this software for any purpose
with or without fee is hereby granted.

THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES WITH
REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF MERCHANTABILITY AND
FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY SPECIAL, DIRECT,
INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING FROM LOSS
OF USE, DATA OR PROFITS, WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE OR OTHER
TORTIOUS ACTION, ARISING OUT OF OR IN CONNECTION WITH THE USE OR PERFORMANCE OF
THIS SOFTWARE.
```
