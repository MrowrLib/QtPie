# Hello World

Let's build your first QtPie application: a simple counter.

## The Complete App

Create a file called `counter.py`:

```python
from PySide6.QtWidgets import QLabel, QPushButton
from qtpie import Widget, Variable, new, widget, entrypoint

@entrypoint
@widget
class Counter(Widget):
    _count: Variable[int] = new(0)
    _label: QLabel = new(bind="Count: {_count}")
    _button: QPushButton = new("Increment", clicked="increment")

    def increment(self) -> None:
        self._count += 1

# That's it! Run with: python counter.py
```

Run it:

```bash
python counter.py
```

You'll see a window with a label showing "Count: 0" and a button. Click the button and the count increases.

## Breaking It Down

### The Imports

```python
from PySide6.QtWidgets import QLabel, QPushButton
from qtpie import Widget, Variable, new, widget, entrypoint
```

- Import Qt widgets you'll use directly from PySide6
- Import QtPie's core: `Widget`, `Variable`, `new`, `widget`, `entrypoint`

### The Decorators

```python
@entrypoint
@widget
class Counter(Widget):
```

- `@widget` transforms your class into a QtPie widget with automatic layout and field processing
- `@entrypoint` makes the class runnable as a standalone app (creates `QApplication`, shows window, runs event loop)

### Reactive State

```python
_count: Variable[int] = new(0)
```

- `Variable[int]` creates reactive integer state initialized to `0`
- Changes to `_count` automatically update any bound widgets
- The underscore prefix is convention for private state (not required)

### Data Binding

```python
_label: QLabel = new(bind="Count: {_count}")
```

- `bind=` creates a reactive binding
- `{_count}` is a placeholder that updates when `_count` changes
- The label text automatically updates - no manual `setText()` needed

### Signal Connections

```python
_button: QPushButton = new("Increment", clicked="increment")
```

- First argument `"Increment"` is the button text
- `clicked="increment"` connects the clicked signal to the `increment` method

### The Handler

```python
def increment(self) -> None:
    self._count += 1
```

- Just update the variable - the UI updates automatically
- You can use `+=` operator directly on Variables

## Adding More Features

### Multiple Variables

```python
@widget
class Calculator(Widget):
    _a: Variable[int] = new(0)
    _b: Variable[int] = new(0)
    _result: QLabel = new(bind="Sum: {_a + _b}")
```

Format expressions support math operations!

### Input Fields

```python
from PySide6.QtWidgets import QLineEdit

@widget
class Greeting(Widget):
    _name: Variable[str, QLineEdit] = new("")
    _greeting: QLabel = new(bind="Hello, {_name}!")
```

`Variable[str, QLineEdit]` creates both a reactive variable AND a widget that's automatically bound to it.

### Form Layout

```python
@widget(layout="form")
class PersonForm(Widget):
    _name: Variable[str, QLineEdit] = new("")(label="Name:")
    _email: Variable[str, QLineEdit] = new("")(label="Email:")
    _submit: QPushButton = new("Submit", clicked="on_submit")

    def on_submit(self) -> None:
        print(f"Submitted: {self._name.value}, {self._email.value}")
```

Use `layout="form"` and `label=` for clean form layouts.

## Next Steps

- [Key Concepts](concepts.md) - Deeper understanding of QtPie's model
- [Widgets](../basics/widgets.md) - Complete widget documentation
- [Variables](../state/variables.md) - Full Variable API
