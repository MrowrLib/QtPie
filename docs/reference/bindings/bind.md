# bind()

The `bind()` function creates manual two-way bindings between observables and Qt widgets. This is a low-level function - most users should use the `bind` parameter in `make()` instead.

## When to Use bind()

You typically don't need `bind()` directly. Use it when:

- Creating bindings outside of `@widget` classes
- Building custom binding logic
- Manually managing observable connections

For normal widget binding, use `make()` with the `bind` parameter:

```python
from qtpie import widget, make
from qtpy.QtWidgets import QLineEdit, QWidget

@widget
class Editor(QWidget):
    name: QLineEdit = make(QLineEdit, bind="name")  # Preferred!
```

This page documents the low-level `bind()` function for advanced usage.

## Basic Usage

### Simple Manual Binding

```python
from dataclasses import dataclass
from observant import ObservableProxy
from qtpie import bind
from qtpy.QtWidgets import QLineEdit

@dataclass
class Model:
    name: str = "Test"

proxy = ObservableProxy(Model(), sync=True)
edit = QLineEdit()

# Manual binding
bind(proxy.observable(str, "name"), edit)
```

Now changes flow both ways:
- `proxy.observable(str, "name").set("Updated")` → widget shows "Updated"
- User types "New" → `proxy.name` becomes "New"

### Default Property

Each widget type has a default property that `bind()` uses automatically:

```python
from qtpie import bind
from qtpy.QtWidgets import QLineEdit, QSpinBox, QCheckBox

# Uses "text" for QLineEdit
bind(name_observable, line_edit)

# Uses "value" for QSpinBox
bind(age_observable, spin_box)

# Uses "checked" for QCheckBox
bind(active_observable, check_box)
```

### Explicit Property

Specify a different property with the `prop` parameter:

```python
from dataclasses import dataclass
from observant import ObservableProxy
from qtpie import bind
from qtpy.QtWidgets import QComboBox

@dataclass
class Model:
    selected: str = "Option A"

proxy = ObservableProxy(Model(), sync=True)
combo = QComboBox()
combo.addItems(["Option A", "Option B", "Option C"])

# Bind to currentText instead of default (currentIndex)
bind(proxy.observable(str, "selected"), combo, "currentText")
```

## Widget Bindings

### Input Widgets (Two-Way)

Input widgets support bidirectional binding:

```python
from dataclasses import dataclass
from observant import ObservableProxy
from qtpie import bind
from qtpy.QtWidgets import QLineEdit, QSpinBox, QCheckBox

@dataclass
class Person:
    name: str = ""
    age: int = 0
    active: bool = False

proxy = ObservableProxy(Person(), sync=True)

name_edit = QLineEdit()
age_spin = QSpinBox()
active_check = QCheckBox()

bind(proxy.observable(str, "name"), name_edit)
bind(proxy.observable(int, "age"), age_spin)
bind(proxy.observable(bool, "active"), active_check)
```

Changes flow both ways:
- Model → Widget: Observable changes update the widget
- Widget → Model: User input updates the observable

### Display Widgets (One-Way)

Some widgets only support model → widget binding (read-only):

```python
from dataclasses import dataclass
from observant import ObservableProxy
from qtpie import bind
from qtpy.QtWidgets import QLabel, QProgressBar

@dataclass
class Status:
    message: str = "Ready"
    progress: int = 0

proxy = ObservableProxy(Status(), sync=True)

label = QLabel()
bar = QProgressBar()

bind(proxy.observable(str, "message"), label)
bind(proxy.observable(int, "progress"), bar)

# Only model → widget works
proxy.observable(str, "message").set("Loading...")  # Updates label
proxy.observable(int, "progress").set(50)  # Updates progress bar
```

## Built-in Widget Support

QtPie includes bindings for many common Qt widgets:

### Text Widgets

| Widget | Default Property | Bidirectional |
|--------|------------------|---------------|
| QLineEdit | `text` | Yes |
| QTextEdit | `text` | Yes |
| QPlainTextEdit | `text` | Yes |
| QLabel | `text` | No (read-only) |

### Numeric Widgets

| Widget | Default Property | Bidirectional |
|--------|------------------|---------------|
| QSpinBox | `value` | Yes |
| QDoubleSpinBox | `value` | Yes |
| QSlider | `value` | Yes |
| QDial | `value` | Yes |
| QProgressBar | `value` | No (read-only) |

### Selection Widgets

| Widget | Default Property | Bidirectional |
|--------|------------------|---------------|
| QCheckBox | `checked` | Yes |
| QRadioButton | `checked` | Yes |
| QComboBox | `currentText` | Yes |
| QListWidget | `currentRow` | Yes |

### Date/Time Widgets

| Widget | Default Property | Bidirectional |
|--------|------------------|---------------|
| QDateEdit | `date` | Yes |
| QTimeEdit | `time` | Yes |
| QDateTimeEdit | `dateTime` | Yes |

### Other Widgets

| Widget | Default Property | Bidirectional |
|--------|------------------|---------------|
| QFontComboBox | `currentFont` | Yes |
| QKeySequenceEdit | `keySequence` | Yes |

## Multiple Widgets, Same Observable

Multiple widgets can bind to the same observable:

```python
from dataclasses import dataclass
from observant import ObservableProxy
from qtpie import bind
from qtpy.QtWidgets import QLineEdit, QLabel

@dataclass
class Model:
    name: str = ""

proxy = ObservableProxy(Model(), sync=True)

edit1 = QLineEdit()
edit2 = QLineEdit()
label = QLabel()

name_obs = proxy.observable(str, "name")
bind(name_obs, edit1)
bind(name_obs, edit2)
bind(name_obs, label)
```

All three widgets stay synchronized:
- User types "Alice" in edit1 → edit2 and label show "Alice"
- User types "Bob" in edit2 → edit1 and label show "Bob"
- `proxy.observable(str, "name").set("Charlie")` → all three show "Charlie"

## Advanced Features

### No Infinite Loops

`bind()` automatically prevents infinite update loops:

```python
from dataclasses import dataclass
from observant import ObservableProxy
from qtpie import bind
from qtpy.QtWidgets import QSpinBox

@dataclass
class Counter:
    value: int = 0

proxy = ObservableProxy(Counter(), sync=True)
spin = QSpinBox()

bind(proxy.observable(int, "value"), spin)

# These don't cause infinite loops:
spin.setValue(10)  # Updates observable once
proxy.observable(int, "value").set(20)  # Updates widget once
```

### Initial Sync

When you call `bind()`, it immediately syncs the current observable value to the widget:

```python
from dataclasses import dataclass
from observant import ObservableProxy
from qtpie import bind
from qtpy.QtWidgets import QLineEdit

@dataclass
class Model:
    name: str = "Alice"

proxy = ObservableProxy(Model(), sync=True)
edit = QLineEdit()

# Before binding, widget is empty
assert edit.text() == ""

# After binding, widget shows current value
bind(proxy.observable(str, "name"), edit)
assert edit.text() == "Alice"
```

## Prefer make() Over bind()

In most cases, use the `bind` parameter in `make()` instead of calling `bind()` directly:

### Instead of This

```python
from dataclasses import dataclass
from qtpie import widget, make, bind, Widget
from qtpy.QtWidgets import QLineEdit, QWidget

@dataclass
class Dog:
    name: str = ""

@widget
class DogEditor(QWidget, Widget[Dog]):
    name_edit: QLineEdit = make(QLineEdit)

    def setup_bindings(self) -> None:
        # Manual binding - verbose!
        bind(self.model_observable_proxy.observable(str, "name"), self.name_edit)
```

### Do This

```python
from dataclasses import dataclass
from qtpie import widget, make, Widget
from qtpy.QtWidgets import QLineEdit, QWidget

@dataclass
class Dog:
    name: str = ""

@widget
class DogEditor(QWidget, Widget[Dog]):
    # Short form - clean and simple!
    name_edit: QLineEdit = make(QLineEdit, bind="name")
```

Much cleaner! The `Widget[Dog]` base class creates the `model_observable_proxy` automatically, and `bind="name"` expands to `bind="model_observable_proxy.name"` behind the scenes.

## API Reference

```python
def bind(
    observable: IObservable[Any],
    widget: QObject,
    prop: str | None = None,
) -> None
```

### Parameters

- **observable**: The observable to bind (from `ObservableProxy`)
- **widget**: The Qt widget to bind to
- **prop**: The widget property name. If `None`, uses the default for the widget type

### Returns

None. The function sets up the binding as a side effect.

### Raises

- **ValueError**: If no binding is registered for the widget type and property combination

## See Also

- [make()](../factories/make.md) - Preferred way to create bindings with `bind` parameter
- [register_binding()](register.md) - Register custom widget bindings
- [Widget[T]](widget-base.md) - Base class that auto-creates `model_observable_proxy` for model editing
- [Reactive State](../../data/state.md) - Reactive state with `state()` function
- [Model Widgets](../../data/model-widgets.md) - Using `Widget[T]` for forms
