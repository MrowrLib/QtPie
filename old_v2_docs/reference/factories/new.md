# new()

The `new()` factory function is the core mechanism for declaratively defining fields in QtPie widgets and windows. It stores configuration for deferred instantiation, allowing QtPie to process fields during widget initialization.

## Signature

```python
def new(*args: Any, **kwargs: Any) -> NewField
```

## Basic Usage

### Widget Fields

Positional arguments are passed directly to the widget constructor:

```python
from qtpie import Widget, new, widget
from qtpy.QtWidgets import QLabel, QPushButton

@widget
class MyWidget(Widget):
    label: QLabel = new("Hello, World!")
    button: QPushButton = new("Click Me")
```

### Non-Widget Fields

The `new()` factory also works with non-QWidget types, passing all arguments to the constructor:

```python
from dataclasses import dataclass

@dataclass
class Config:
    name: str
    port: int

@widget
class MyWidget(Widget):
    config: Config = new(name="localhost", port=8080)
    label: QLabel = new("Ready")
```

## Special QtPie Parameters

These parameters are intercepted by QtPie and NOT passed to the widget constructor:

### bind

Binds a widget to a Variable or format expression:

```python
@widget
class Example(Widget):
    _name: Variable[str] = new("")
    _count: Variable[int] = new(0)

    # Simple binding
    display: QLabel = new(bind="_name")

    # Format expression
    status: QLabel = new(bind="Count: {_count}")
```

### name

Sets the widget's `objectName` property (used for QSS selectors):

```python
@widget
class Example(Widget):
    # objectName will be "main-title"
    title: QLabel = new("Welcome", name="main-title")

    # Without name=, objectName defaults to field name ("subtitle")
    subtitle: QLabel = new("Subtitle text")
```

### classes

Applies CSS classes to the widget:

```python
@widget
class Example(Widget):
    title: QLabel = new("Important", classes=["header", "bold"])
    warning: QLabel = new("Warning!", classes=["error"])
```

### layout

Controls whether the widget is added to the parent's layout:

```python
@widget
class Example(Widget):
    visible: QLabel = new("In layout")

    # Widget exists but not added to layout (useful for overlays, popups)
    hidden: QLabel = new("Not in layout", layout=False)
```

### label

For form layouts, provides the label text:

```python
@widget(layout="form")
class Form(Widget):
    name: QLineEdit = new(label="Name:")
    email: QLineEdit = new(label="Email:")
    age: QSpinBox = new(label="Age:")
```

### grid

For grid layouts, specifies position as `(row, col)` or `(row, col, rowspan, colspan)`:

```python
@widget(layout="grid")
class Grid(Widget):
    # Single cell
    top_left: QLabel = new("A", grid=(0, 0))
    top_right: QLabel = new("B", grid=(0, 1))

    # Spanning multiple cells (row=1, col=0, rowspan=1, colspan=2)
    bottom: QLabel = new("Spans 2 columns", grid=(1, 0, 1, 2))
```

### visible

Reactive visibility control with variable reference or expression:

```python
@widget
class Example(Widget):
    _is_logged_in: Variable[bool] = new(False)
    _item_count: Variable[int] = new(0)

    # Simple variable binding
    login_panel: QWidget = new(visible="_is_logged_in")

    # Expression binding
    empty_state: QLabel = new("No items", visible="{_item_count == 0}")
```

### enabled

Reactive enabled state control:

```python
@widget
class Example(Widget):
    _has_selection: Variable[bool] = new(False)
    _name: Variable[str] = new("")

    # Simple binding
    delete_btn: QPushButton = new("Delete", enabled="_has_selection")

    # Expression binding
    submit_btn: QPushButton = new("Submit", enabled="{len(_name) > 0}")
```

## Signal Connections

Any keyword argument matching a signal name on the widget type will be connected automatically:

```python
@widget
class Example(Widget):
    # Connect to method by name
    save_btn: QPushButton = new("Save", clicked="on_save")

    # Connect to lambda
    cancel_btn: QPushButton = new("Cancel", clicked=lambda: print("Cancelled"))

    # Multiple signals
    text_input: QLineEdit = new(
        textChanged="on_text_changed",
        returnPressed="on_submit"
    )

    def on_save(self) -> None:
        print("Saving...")

    def on_text_changed(self, text: str) -> None:
        print(f"Text changed: {text}")

    def on_submit(self) -> None:
        print("Submitted")
```

## Widget Properties

Any keyword argument matching a `setXxx()` method on the widget type will be applied:

```python
@widget
class Example(Widget):
    label: QLabel = new(
        "Text",
        toolTip="This is a tooltip",
        styleSheet="color: red;",
        minimumWidth=200
    )

    button: QPushButton = new(
        "Click",
        enabled=False,
        toolTip="Disabled button"
    )
```

### Convenience Aliases

QtPie provides lowercase aliases for common properties:

```python
@widget
class Example(Widget):
    # These are equivalent
    label1: QLabel = new("Hello", title="Window")
    label2: QLabel = new("World", windowTitle="Window")

    # stylesheet -> styleSheet
    styled: QLabel = new("Styled", stylesheet="color: blue;")

    # tooltip -> toolTip
    help: QLabel = new("?", tooltip="Help text")
```

## Variable[T, W] Chained Call Syntax

For `Variable[T, W]` fields, use chained calls to configure both the Variable and the widget:

```python
from qtpy.QtWidgets import QLineEdit, QSpinBox

@widget
class Example(Widget):
    # First call: Variable default value
    # Second call: Widget constructor kwargs
    _name: Variable[str, QLineEdit] = new("default")(
        placeholderText="Enter name...",
        maxLength=50
    )

    _age: Variable[int, QSpinBox] = new(0)(
        minimum=0,
        maximum=120,
        suffix=" years"
    )

    # Access the widget via .widget property
    def focus_name(self) -> None:
        self._name.widget.setFocus()
```

### Layout Parameters in Chained Calls

For `Variable[T, W]` fields, layout parameters go in the second call:

```python
@widget(layout="form")
class Form(Widget):
    # label= goes in the widget kwargs (second call)
    _name: Variable[str, QLineEdit] = new("")(label="Name:")
    _email: Variable[str, QLineEdit] = new("")(label="Email:")

@widget(layout="grid")
class Grid(Widget):
    # grid= goes in the widget kwargs (second call)
    _value: Variable[int, QSpinBox] = new(10)(grid=(0, 0))
    _display: Variable[str, QLabel] = new("Hello")(grid=(0, 1))
```

## List Widget Bindings

Define reactive widget lists that sync with a list Variable:

```python
@widget
class TodoList(Widget):
    _items: Variable[list[str]] = new(["Task 1", "Task 2"])

    # Creates one QLabel per item, auto-syncs on list changes
    labels: list[QLabel] = new(bind="_items")

    def add_item(self, text: str) -> None:
        self._items.append(text)  # Automatically creates new QLabel
```

### Custom Format for List Items

Use the `format=` parameter to customize how list items are displayed:

```python
@widget
class NumberList(Widget):
    _numbers: Variable[list[int]] = new([1, 2, 3])

    # {#index} - item index
    # {#self} - item value
    labels: list[QLabel] = new(
        bind="_numbers",
        format="Item {#index}: {#self}"
    )
    # Output: "Item 0: 1", "Item 1: 2", "Item 2: 3"
```

### Dict Widget Bindings

Bind to dictionary Variables with key/value placeholders:

```python
@widget
class ScoreBoard(Widget):
    _scores: Variable[dict[str, int]] = new({"Alice": 100, "Bob": 85})

    # {#key} - dict key
    # {#value} - dict value
    labels: list[QLabel] = new(
        bind="_scores",
        format="{#key}: {#value} points"
    )
    # Output: "Alice: 100 points", "Bob: 85 points"
```

## How new() Works with Different Field Types

### QWidget Types

For QWidget subclasses, `new()`:
1. Stores constructor args/kwargs
2. Extracts QtPie special params (`bind=`, `name=`, `classes=`, `layout=`, `label=`, `grid=`, `visible=`, `enabled=`)
3. Extracts signal connections (kwargs matching signal names)
4. Extracts widget properties (kwargs matching `setXxx()` methods)
5. Instantiates the widget during widget initialization
6. Applies objectName, CSS classes, property bindings, and signal connections

```python
@widget
class Example(Widget):
    button: QPushButton = new(
        "Click",                    # Positional arg -> QPushButton constructor
        clicked="on_click",         # Signal connection
        toolTip="Click here",       # Property (calls setToolTip)
        name="main-button",         # QtPie: objectName
        classes=["primary"],        # QtPie: CSS classes
        enabled="{_is_ready}"       # QtPie: reactive property binding
    )
```

### Variable[T] Types

For Variable types without a widget:
1. Creates an Observable, ObservableList, ObservableDict, or ObservableProxy based on the type `T`
2. Initializes with the default value from `new()`
3. No widget is created

```python
@widget
class Example(Widget):
    _count: Variable[int] = new(0)           # Observable[int]
    _items: Variable[list[str]] = new([])    # ObservableList[str]
    _config: Variable[Config] = new(Config()) # ObservableProxy[Config]
```

### Variable[T, W] Types

For Variable types with a widget type:
1. Creates the appropriate observable for `T`
2. Creates the widget of type `W`
3. Auto-binds the widget to the observable
4. Widget constructor args come from the chained call: `new(value)(widget_kwargs)`

```python
@widget
class Example(Widget):
    # Creates Observable[str] + QLineEdit, binds them together
    _name: Variable[str, QLineEdit] = new("default")(placeholderText="Name...")

    # Access the value
    def get_name(self) -> str:
        return self._name.value

    # Access the widget
    def focus_name(self) -> None:
        self._name.widget.setFocus()
```

### list[QWidget] Types

For list widget types:
1. Creates a WidgetRepeater or DictWidgetRepeater
2. Binds to a source Variable
3. Creates/destroys widgets automatically as the source changes
4. Requires `bind=` parameter

```python
@widget
class Example(Widget):
    _items: Variable[list[str]] = new(["A", "B", "C"])

    # Creates WidgetRepeater that manages QLabel widgets
    labels: list[QLabel] = new(
        bind="_items",           # Required: source Variable
        format="{#self}"         # Optional: format template
    )
```

### Non-QWidget Types

For any other type:
1. All args/kwargs are passed directly to the constructor
2. No QtPie special params are extracted (except for Variable types)
3. The object is instantiated and stored as a field

```python
@dataclass
class Config:
    host: str
    port: int

@widget
class Example(Widget):
    # Creates Config("localhost", 8080)
    config: Config = new(host="localhost", port=8080)

    # Even layout= and bind= pass through for non-QWidget types
    settings: dict = new(bind="some_value", layout=123)
```

## Complete Example

```python
from dataclasses import dataclass
from qtpie import Widget, Variable, new, widget
from qtpy.QtWidgets import QLabel, QLineEdit, QPushButton, QSpinBox

@dataclass
class Person:
    name: str
    age: int

@widget(layout="form")
class PersonEditor(Widget):
    # Variable with widget (chained syntax)
    _name: Variable[str, QLineEdit] = new("")(
        label="Name:",
        placeholderText="Enter name...",
        textChanged="on_name_changed"
    )

    # Variable with widget in grid
    _age: Variable[int, QSpinBox] = new(0)(
        label="Age:",
        minimum=0,
        maximum=120
    )

    # Regular widget with binding
    display: QLabel = new(
        bind="Name: {_name}, Age: {_age}",
        name="person-display",
        classes=["info"],
        stylesheet="font-weight: bold;"
    )

    # Button with signal connection
    save: QPushButton = new(
        "Save",
        clicked="on_save",
        enabled="{len(_name) > 0}",
        toolTip="Save person data"
    )

    def on_name_changed(self, text: str) -> None:
        print(f"Name changed to: {text}")

    def on_save(self) -> None:
        person = Person(self._name.value, self._age.value)
        print(f"Saving: {person}")
```

## See Also

- [Variable](../classes/variable.md) - Reactive state management
- [Widget](../classes/widget.md) - Base widget class
- [Bindings](../../guides/bindings.md) - Data binding system
- [Layout](../../guides/layouts.md) - Layout configuration
