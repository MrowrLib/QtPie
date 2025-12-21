# Hello World - Your First QtPie App

Let's build a Qt app, step by step, from the simplest possible widget to a reactive counter.

## Step 1: Just a Label

The simplest QtPie app is a function that returns a widget:

```python
from qtpie import entry_point
from qtpy.QtWidgets import QLabel


@entry_point
def main():
    return QLabel("Hello, World!")
```

Save this as `hello.py` and run it:

```bash
python hello.py
```

That's it. A window appears with "Hello, World!". No `QApplication`, no `if __name__ == "__main__"`, no boilerplate.

**What `@entry_point` does:**
- Creates a `QApplication` instance
- Calls your function to get a widget
- Shows the widget in a window
- Runs the event loop

## Step 2: A Widget Class with a Button

Let's make a real widget with multiple children:

```python
from qtpie import entry_point, make, widget
from qtpy.QtWidgets import QLabel, QPushButton, QWidget


@entry_point
@widget
class MyWidget(QWidget):
    text: QLabel = make(QLabel, "Hello, World!")
    button: QPushButton = make(QPushButton, "Click Me", clicked="on_click")

    def on_click(self):
        self.text.setText("Button Clicked!")
```

Run it, click the button. The label updates.

**What `@widget` does:**
- Calls `super().__init__()` for you
- Creates a vertical layout automatically
- Adds `text` and `button` to the layout in declaration order
- Sets the widget's `objectName` to `"MyWidget"`

**What `make()` does:**
- Creates widget instances: `make(QLabel, "Hello")` → `QLabel("Hello")`
- Connects signals: `clicked="on_click"` → `button.clicked.connect(self.on_click)`
- The field name becomes the widget's `objectName` (useful for styling)

### No More Boilerplate

Compare to plain PySide6:

```python
# Plain PySide6 - lots of ceremony
class MyWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName("MyWidget")

        layout = QVBoxLayout(self)

        self.text = QLabel("Hello, World!")
        self.text.setObjectName("text")
        layout.addWidget(self.text)

        self.button = QPushButton("Click Me")
        self.button.setObjectName("button")
        self.button.clicked.connect(self.on_click)
        layout.addWidget(self.button)

    def on_click(self):
        self.text.setText("Button Clicked!")


if __name__ == "__main__":
    app = QApplication([])
    window = MyWidget()
    window.show()
    app.exec()
```

**35 lines** of boilerplate vs **12 lines** of intent.

## Step 3: Add State

Right now, clicking the button just sets static text. Let's add a counter:

```python
from qtpie import entry_point, make, widget
from qtpy.QtWidgets import QLabel, QPushButton, QWidget


@entry_point
@widget
class Counter(QWidget):
    label: QLabel = make(QLabel, "Count: 0")
    button: QPushButton = make(QPushButton, "Add", clicked="increment")
    count: int = 0

    def increment(self):
        self.count += 1
        self.label.setText(f"Count: {self.count}")
```

This works, but notice we're still manually updating the label with `setText()`. We can do better.

## Step 4: Reactive State with `state()`

Here's where QtPie shines. Use `state()` to create reactive state, and `bind=` to connect widgets:

```python
from qtpie import entry_point, make, state, widget
from qtpy.QtWidgets import QLabel, QPushButton, QWidget


@entry_point
@widget
class Counter(QWidget):
    count: int = state(0)
    label: QLabel = make(QLabel, bind="Count: {count}")
    button: QPushButton = make(QPushButton, "Add", clicked="increment")

    def increment(self):
        self.count += 1
```

**That's it.** No manual `setText()`. When `self.count` changes, the label updates automatically.

**What `state()` does:**
- Creates a reactive field: `count: int = state(0)` starts at `0`
- When you assign `self.count = 42`, it notifies all bound widgets
- Widgets bound with `bind="count"` update automatically

**What `bind=` does:**
- `bind="count"` → binds to `self.count`
- `bind="Count: {count}"` → format string, updates to "Count: 0", "Count: 1", etc.
- `bind="{count * 2}"` → expressions work too: `0`, `2`, `4`, `6`...

### Two-Way Binding

Binding works both ways for input widgets:

```python
from qtpie import entry_point, make, state, widget
from qtpy.QtWidgets import QLabel, QLineEdit, QWidget


@entry_point
@widget
class Greeter(QWidget):
    name: str = state("")
    name_input: QLineEdit = make(QLineEdit, bind="name")
    greeting: QLabel = make(QLabel, bind="Hello, {name}!")
```

- Type in the input → `self.name` updates → label updates
- Change `self.name` in code → input updates

### Advanced: Multiple Variables in Bindings

```python
from qtpie import entry_point, make, state, widget
from qtpy.QtWidgets import QLabel, QSpinBox, QWidget


@entry_point
@widget
class Calculator(QWidget):
    a: int = state(10)
    b: int = state(20)
    spin_a: QSpinBox = make(QSpinBox, bind="a")
    spin_b: QSpinBox = make(QSpinBox, bind="b")
    result: QLabel = make(QLabel, bind="{a} + {b} = {a + b}")
```

Change either spinbox → both state fields update → result recalculates automatically.

---

## Complete Example: The Counter

Here's the canonical QtPie example - the "Hello World" of reactive frameworks:

```python
from qtpie import entry_point, make, state, widget
from qtpy.QtWidgets import QLabel, QPushButton, QWidget


@entry_point
@widget
class Counter(QWidget):
    count: int = state(0)
    label: QLabel = make(QLabel, bind="Count: {count}")
    button: QPushButton = make(QPushButton, "Add", clicked="increment")

    def increment(self):
        self.count += 1
```

**12 lines. Zero boilerplate. Fully reactive.**

Compare to plain PySide6:

```python
from qtpy.QtWidgets import QApplication, QLabel, QPushButton, QVBoxLayout, QWidget


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

**35 lines** vs **12 lines**. Same functionality.

---

## What's Next?

Now that you've built your first QtPie app, explore:

- **[Key Concepts](concepts.md)** - Deeper dive into `@widget`, `make()`, and `state()`
- **[Layouts](../basics/layouts.md)** - Horizontal, form, and grid layouts
- **[Signals](../basics/signals.md)** - More ways to connect signals
- **[Reactive State](../data/state.md)** - Full power of `state()` and binding
- **[Styling](../basics/styling.md)** - CSS classes and themes

Or jump straight to the [Examples](../examples.md) for real-world patterns.
