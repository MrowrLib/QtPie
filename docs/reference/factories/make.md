# make()

The `make()` factory function creates widget instances as dataclass field defaults. It provides a clean, declarative syntax for instantiating widgets with their initial values, properties, signal connections, and bindings.

## Why make()?

Without `make()`, you would need verbose `field(default_factory=...)` syntax:

```python
from dataclasses import field
from qtpy.QtWidgets import QLabel

# Verbose
label: QLabel = field(default_factory=lambda: QLabel("Hello"))
```

With `make()`, it's much cleaner:

```python
from qtpie import make
from qtpy.QtWidgets import QLabel

# Clean
label: QLabel = make(QLabel, "Hello")
```

## Basic Usage

### Creating a Simple Widget

```python
from qtpie import widget, make
from qtpy.QtWidgets import QLabel, QWidget

@widget
class MyWidget(QWidget):
    label: QLabel = make(QLabel)
```

### Passing Constructor Arguments

```python
from qtpie import widget, make
from qtpy.QtWidgets import QLabel, QWidget

@widget
class MyWidget(QWidget):
    label: QLabel = make(QLabel, "Hello World")
```

The positional arguments after the class type are passed directly to the widget's constructor.

### Setting Properties

Any keyword arguments that aren't signal connections are set as properties on the widget:

```python
from qtpie import widget, make
from qtpy.QtWidgets import QLineEdit, QWidget

@widget
class MyWidget(QWidget):
    edit: QLineEdit = make(QLineEdit, placeholderText="Enter name")
```

This is equivalent to:

```python
edit = QLineEdit()
edit.setPlaceholderText("Enter name")
```

## Signal Connections

### Connecting to Methods by Name

Pass signal names as keyword arguments with string values to connect them to methods:

```python
from qtpie import widget, make
from qtpy.QtWidgets import QPushButton, QWidget

@widget
class MyWidget(QWidget):
    button: QPushButton = make(QPushButton, "Click", clicked="on_click")
    click_count: int = 0

    def on_click(self) -> None:
        self.click_count += 1
```

### Connecting to Lambda Functions

You can also connect signals to callable objects like lambda functions:

```python
from qtpie import widget, make
from qtpy.QtWidgets import QPushButton, QWidget

@widget
class MyWidget(QWidget):
    button: QPushButton = make(QPushButton, "Click", clicked=lambda: print("Clicked!"))
```

### Multiple Signal Connections

Connect multiple signals by passing multiple keyword arguments:

```python
from qtpie import widget, make
from qtpy.QtWidgets import QSlider, QWidget

@widget
class MyWidget(QWidget):
    slider: QSlider = make(
        QSlider,
        valueChanged="on_value_changed",
        sliderReleased="on_released",
    )
    value_changes: int = 0
    releases: int = 0

    def on_value_changed(self, value: int) -> None:
        self.value_changes += 1

    def on_released(self) -> None:
        self.releases += 1
```

## Data Binding

The `bind` parameter connects a widget to a data source, automatically keeping them in sync.

### Basic Binding

Bind a widget to a proxy field:

```python
from dataclasses import dataclass
from qtpie import widget, make, Widget
from qtpy.QtWidgets import QLineEdit, QWidget
from observant import ObservableProxy

@dataclass
class Person:
    name: str = ""

@widget
class Editor(QWidget, Widget[Person]):
    name_edit: QLineEdit = make(QLineEdit, bind="proxy.name")
```

When `proxy.name` changes, the widget updates. When the user edits the widget, `proxy.name` updates.

### Short Form Binding

When using `Widget[T]`, you can omit `"proxy."` prefix:

```python
from dataclasses import dataclass
from qtpie import widget, make, Widget
from qtpy.QtWidgets import QLineEdit, QSpinBox, QWidget

@dataclass
class Person:
    name: str = ""
    age: int = 0

@widget
class Editor(QWidget, Widget[Person]):
    name_edit: QLineEdit = make(QLineEdit, bind="name")  # Short form!
    age_spin: QSpinBox = make(QSpinBox, bind="age")      # Short form!
```

These automatically expand to `"proxy.name"` and `"proxy.age"`.

### Nested Property Binding

Bind to nested object properties:

```python
from dataclasses import dataclass
from qtpie import widget, make, Widget
from qtpy.QtWidgets import QLineEdit, QWidget

@dataclass
class Address:
    city: str = ""

@dataclass
class Person:
    address: Address

@widget
class Editor(QWidget, Widget[Person]):
    city_edit: QLineEdit = make(QLineEdit, bind="address.city")  # Nested!
```

### Optional Chaining

Use `?.` for optional properties that might be None:

```python
from dataclasses import dataclass
from qtpie import widget, make, Widget
from qtpy.QtWidgets import QLineEdit, QWidget

@dataclass
class Owner:
    name: str = ""

@dataclass
class Pet:
    owner: Owner | None = None

@widget
class Editor(QWidget, Widget[Pet]):
    owner_edit: QLineEdit = make(QLineEdit, bind="owner?.name")  # Optional!
```

If `owner` is None, the widget is disabled and cleared. When `owner` becomes non-None, the widget re-enables and shows the name.

### Format Expression Binding

For read-only widgets like labels, use format expressions:

```python
from qtpie import widget, make, state
from qtpy.QtWidgets import QLabel, QWidget

@widget
class Counter(QWidget):
    count: int = state(0)
    label: QLabel = make(QLabel, bind="Count: {count}")
```

The label automatically updates when `count` changes.

#### Multiple Fields

```python
from qtpie import widget, make, state
from qtpy.QtWidgets import QLabel, QWidget

@widget
class NameDisplay(QWidget):
    first: str = state("John")
    last: str = state("Doe")
    label: QLabel = make(QLabel, bind="{first} {last}")
```

#### Expressions

```python
from qtpie import widget, make, state
from qtpy.QtWidgets import QLabel, QWidget

@widget
class Calculator(QWidget):
    count: int = state(5)
    label: QLabel = make(QLabel, bind="{count + 5}")  # Displays: 10
```

#### Format Specs

```python
from qtpie import widget, make, state
from qtpy.QtWidgets import QLabel, QWidget

@widget
class PriceDisplay(QWidget):
    price: float = state(19.99)
    label: QLabel = make(QLabel, bind="Total: ${price * 1.1:.2f}")  # $21.99
```

#### Method Calls

```python
from qtpie import widget, make, state
from qtpy.QtWidgets import QLabel, QWidget

@widget
class NameDisplay(QWidget):
    name: str = state("hello")
    label: QLabel = make(QLabel, bind="{name.upper()}")  # HELLO
```

See [Format Expressions](../../data/format.md) for more details.

### Custom Property Binding

By default, `make()` binds to the standard property for each widget type (e.g., `text` for QLineEdit, `value` for QSpinBox). Use `bind_prop` to bind to a different property:

```python
from dataclasses import dataclass
from qtpie import widget, make, Widget
from qtpy.QtWidgets import QComboBox, QWidget
from observant import ObservableProxy

@dataclass
class Model:
    selected: str = "Option A"

@widget
class Editor(QWidget, Widget[Model]):
    combo: QComboBox = make(
        QComboBox,
        bind="proxy.selected",
        bind_prop="currentText"  # Custom property!
    )
```

## Form Layouts

Use `form_label` to create labeled rows in form layouts:

```python
from qtpie import widget, make
from qtpy.QtWidgets import QLineEdit, QSpinBox, QWidget

@widget(layout="form")
class PersonForm(QWidget):
    name: QLineEdit = make(QLineEdit, form_label="Full Name")
    email: QLineEdit = make(QLineEdit, form_label="Email")
    age: QSpinBox = make(QSpinBox, form_label="Age")
```

This creates a form with labels on the left and input fields on the right.

See [Form Layouts](../../guides/forms.md) for more details.

## Grid Layouts

Use `grid` to position widgets in a grid layout:

```python
from qtpie import widget, make
from qtpy.QtWidgets import QPushButton, QWidget

@widget(layout="grid")
class ButtonGrid(QWidget):
    btn_00: QPushButton = make(QPushButton, "00", grid=(0, 0))
    btn_01: QPushButton = make(QPushButton, "01", grid=(0, 1))
    btn_10: QPushButton = make(QPushButton, "10", grid=(1, 0))
    btn_11: QPushButton = make(QPushButton, "11", grid=(1, 1))
```

The `grid` parameter accepts:
- `(row, col)` - Position in the grid
- `(row, col, rowspan, colspan)` - Position with spanning

### Grid Spanning

```python
from qtpie import widget, make
from qtpy.QtWidgets import QLineEdit, QPushButton, QWidget

@widget(layout="grid")
class Calculator(QWidget):
    display: QLineEdit = make(QLineEdit, grid=(0, 0, 1, 4))  # spans 4 columns
    btn_7: QPushButton = make(QPushButton, "7", grid=(1, 0))
    btn_8: QPushButton = make(QPushButton, "8", grid=(1, 1))
    btn_9: QPushButton = make(QPushButton, "9", grid=(1, 2))
    btn_plus: QPushButton = make(QPushButton, "+", grid=(1, 3, 2, 1))  # spans 2 rows
```

See [Grid Layouts](../../guides/grids.md) for more details.

## Built-in Widget Bindings

QtPie includes default property bindings for many common Qt widgets:

| Widget | Default Property | Description |
|--------|------------------|-------------|
| QLineEdit | `text` | Single-line text input |
| QTextEdit | `plainText` | Multi-line text input |
| QPlainTextEdit | `plainText` | Plain text editor |
| QLabel | `text` | Text display (read-only) |
| QSpinBox | `value` | Integer spinner |
| QDoubleSpinBox | `value` | Float spinner |
| QCheckBox | `checked` | Boolean checkbox |
| QRadioButton | `checked` | Boolean radio button |
| QSlider | `value` | Integer slider |
| QDial | `value` | Integer dial |
| QProgressBar | `value` | Progress indicator |
| QComboBox | `currentIndex` | Dropdown selection |
| QDateEdit | `date` | Date picker |
| QTimeEdit | `time` | Time picker |
| QDateTimeEdit | `dateTime` | Date/time picker |
| QFontComboBox | `currentFont` | Font selector |
| QKeySequenceEdit | `keySequence` | Keyboard shortcut editor |
| QListWidget | `currentRow` | List selection |

These defaults are used when you specify `bind=` without `bind_prop=`.

## API Reference

```python
def make[T](
    class_type: Callable[..., T],
    *args: Any,
    form_label: str | None = None,
    grid: GridTuple | None = None,
    bind: str | None = None,
    bind_prop: str | None = None,
    **kwargs: Any,
) -> T
```

### Parameters

- **class_type**: The widget class to instantiate (e.g., `QLabel`, `QPushButton`)
- **\*args**: Positional arguments passed to the widget's constructor
- **form_label**: Label text for form layouts. Creates a labeled row in form layout
- **grid**: Position in grid layout as `(row, col)` or `(row, col, rowspan, colspan)`
- **bind**: Path to bind to, e.g., `"name"`, `"proxy.name"`, `"dog?.owner.name"`, or format expression like `"Count: {count}"`
- **bind_prop**: Explicit property name to bind. If None, uses the default for the widget type
- **\*\*kwargs**: Keyword arguments - string or callable values are treated as signal connections, others are set as widget properties

### Returns

At type-check time, returns `T` (the widget type). At runtime, returns a dataclass field with a factory function that creates the widget.

## See Also

- [@widget](../decorators/widget.md) - Widget decorator that processes `make()` fields
- [make_later()](make-later.md) - Deferred initialization for fields that depend on other fields
- [state()](state.md) - Reactive state fields that trigger automatic updates
- [bind()](../bindings/bind.md) - Manual binding function
- [Widget[T]](../bindings/widget-base.md) - Base class for model-bound widgets
- [Format Expressions](../../data/format.md) - Advanced binding with format strings
- [Form Layouts](../../guides/forms.md) - Using `form_label` parameter
- [Grid Layouts](../../guides/grids.md) - Using `grid` parameter
