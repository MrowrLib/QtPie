# Key Concepts

Understanding these core concepts will help you get the most out of QtPie.

## Declarative UI

QtPie uses a **declarative** approach: you describe what your UI should look like, not how to build it.

```python
@widget
class MyWidget(Widget):
    label: QLabel = new("Hello")      # Declare a label
    button: QPushButton = new("Click") # Declare a button
```

QtPie handles:

- Creating the widgets
- Setting up the layout
- Adding widgets to the layout
- Calling `show()` when needed

## The `new()` Factory

`new()` is the universal factory for declaring fields:

```python
# Widget with constructor args
label: QLabel = new("Hello World")

# Widget with properties
button: QPushButton = new("Click", enabled=False, toolTip="Click me")

# Widget with signal connection
btn: QPushButton = new("Save", clicked="on_save")

# Variable with default value
count: Variable[int] = new(0)

# Variable with widget (chained call)
name: Variable[str, QLineEdit] = new("default")(placeholderText="Enter name")
```

## Variable[T] - Reactive State

`Variable[T]` holds reactive state. When changed, bound widgets update automatically.

```python
_count: Variable[int] = new(0)

# Access the value
print(self._count.value)

# Set the value
self._count.value = 42

# Or use operators directly
self._count += 1
```

### Variable[T, W] - State + Widget

`Variable[T, W]` creates both a variable AND a bound widget:

```python
_name: Variable[str, QLineEdit] = new("default")

# Access the variable value
print(self._name.value)

# Access the widget
self._name.widget.setFocus()
```

The widget is automatically bound - editing the QLineEdit updates the variable, and vice versa.

## Data Binding with `bind=`

The `bind=` parameter creates reactive bindings:

```python
# Simple binding
label: QLabel = new(bind="{_name}")

# With format string
label: QLabel = new(bind="Hello, {_name}!")

# With expressions
label: QLabel = new(bind="Total: {_price * _quantity}")

# With method calls
label: QLabel = new(bind="Upper: {_name.upper()}")
```

Bindings are reactive - they update when any referenced variable changes.

## Widget[T] - Record Types

`Widget[T]` binds a dataclass to a widget:

```python
from dataclasses import dataclass

@dataclass
class Person:
    name: str = ""
    age: int = 0

@widget(record=Person("Alice", 30))
class PersonEditor(Widget[Person]):
    name: QLineEdit = new()  # Auto-binds to record.name
    age: QLineEdit = new()   # Auto-binds to record.age
```

Access the record:

```python
def save(self) -> None:
    person = self.record  # ObservableProxy[Person]
    print(f"{person.name} is {person.age}")
```

## Layouts

QtPie supports multiple layout types:

```python
@widget(layout="vertical")    # Default - QVBoxLayout
class VBox(Widget): ...

@widget(layout="horizontal")  # QHBoxLayout
class HBox(Widget): ...

@widget(layout="form")        # QFormLayout
class Form(Widget):
    name: QLineEdit = new(label="Name:")

@widget(layout="grid")        # QGridLayout
class Grid(Widget):
    a: QLabel = new("A", grid=(0, 0))
    b: QLabel = new("B", grid=(0, 1))
```

## Signal Connections

Connect signals declaratively:

```python
# Connect to method by name
button: QPushButton = new("Click", clicked="on_click")

# Connect to lambda
button: QPushButton = new("Click", clicked=lambda: print("Clicked!"))

def on_click(self) -> None:
    print("Button clicked!")
```

## The `__setup__` Hook

For initialization after all fields are ready:

```python
@widget
class MyWidget(Widget):
    label: QLabel = new("Hello")

    def __setup__(self) -> None:
        # Called after all fields are initialized
        # Layout is ready, widgets exist
        self.label.setText("Setup complete!")
```

## Decorators

| Decorator     | Purpose                           |
| ------------- | --------------------------------- |
| `@widget`     | Transform class into QtPie widget |
| `@window`     | Transform class into QMainWindow  |
| `@menu`       | Define a menu for window menu bar |
| `@action`     | Define a QAction                  |
| `@slot`       | Mark async method as slot         |
| `@entrypoint` | Make widget runnable as app       |

## Validation

Add validators to check field values:

```python
def __setup__(self) -> None:
    self.add_validator("name", "required",
        lambda v: None if v else "Name is required")

def on_submit(self) -> None:
    if self.is_valid:
        self.save()
    else:
        print(self.validation_error_messages)
```

## Dirty Tracking

Track whether fields have changed:

```python
def on_save(self) -> None:
    if self.view_model.is_dirty:
        self.save()
        self.view_model.reset_dirty()
```

## Next Steps

- [Widgets](../basics/widgets.md) - Complete widget documentation
- [Variables](../state/variables.md) - Full Variable API
- [Bindings](../state/bindings.md) - Data binding details
- [Validation](../data/validation.md) - Validation system
