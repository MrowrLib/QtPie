# QtPie App and AppBase Usage Patterns

This document describes the usage patterns for `App` and `AppBase` classes in QtPie, extracted from `test_app.py`.

---

## App Class (QApplication Wrapper)

The `App` class extends `QApplication` with QtPie enhancements.

### Basic App Instance

```python
from qtpie import App

# App is a QApplication with added methods
app = App()
app.run()  # Run the event loop
app.run_async()  # Run with async support
```

### Loading Stylesheets

```python
app.load_stylesheet("path/to/style.qss")
```

### Dark/Light Mode

```python
app.enable_dark_mode()
app.enable_light_mode()
```

---

## AppBase Class (Declarative App Container)

`AppBase` is the primary way to create declarative Qt applications. Use the `@app` decorator.

### Basic AppBase

```python
from qtpie import AppBase, app, new

@app(show=False, system_tray=False)
class MyApp(AppBase):
    pass
```

### Decorator Options

| Option | Default | Description |
|--------|---------|-------------|
| `show` | `True` | Show window on creation |
| `system_tray` | `True` | Enable system tray support |
| `window` | auto | Create auto-window (auto-detected from widget fields) |
| `title` | class name | Window title |
| `icon` | None | Shared icon for window and tray |
| `window_icon` | None | Window-specific icon (overrides `icon`) |
| `tray_icon` | None | Tray-specific icon (overrides `icon`) |
| `minimize_to_tray` | `True` | Hide to tray on window close |
| `org` | None | Organization name (for QSettings) |
| `app_name` | None | Application name (for QSettings) |
| `stylesheet` | None | QSS stylesheet string |
| `style` | None | Qt style (e.g., "Fusion") |

---

## Variable Fields

### Basic Variable

```python
@app(show=False, system_tray=False)
class MyApp(AppBase):
    _count: Variable[int] = new(0)
    _name: Variable[str] = new("default")
```

### Variable with Widget (Variable[T, W])

```python
@app(show=False, system_tray=False, window=False)
class MyApp(AppBase):
    _name: Variable[str, QLineEdit] = new("")
    # Access: instance._name.value (str), instance._name.widget (QLineEdit)
```

---

## Reactive Bindings

### Simple Variable Binding

```python
_name: Variable[str] = new("Alice")
_label: QLabel = new(bind="{_name}")
```

### Expression Binding

```python
_x: Variable[int] = new(10)
_y: Variable[int] = new(5)
_label: QLabel = new(bind="{_x + _y}")  # "15"
```

### Method Call Binding

```python
_name: Variable[str] = new("hello")
_label: QLabel = new(bind="{_name.upper()}")  # "HELLO"
```

### Built-in Function Binding

```python
_text: Variable[str] = new("hello")
_label: QLabel = new(bind="Length: {len(_text)}")  # "Length: 5"
```

### Format Spec Binding

```python
_price: Variable[float] = new(19.99)
_label: QLabel = new(bind="${_price:.2f}")  # "$19.99"
```

### Multiple Variables in Binding

```python
_first: Variable[str] = new("John")
_last: Variable[str] = new("Doe")
_label: QLabel = new(bind="{_first} {_last}")  # "John Doe"
```

---

## Special Placeholders

### #self Placeholder (Variable's Value)

```python
_name: Variable[str, QLabel] = new("hello")(bind="Value: {#self}")
_upper: Variable[str, QLabel] = new("hello")(bind="{#self.upper()}")
```

### #var Placeholder (Alias for Variable Value)

```python
_count: Variable[int, QLabel] = new(10)(bind="Double: {#var * 2}")
```

### #widget Placeholder (Parent Instance)

```python
title: str = "My App"
_label: QLabel = new(bind="{#widget.title}")
```

### #window Placeholder (Alias for #widget)

```python
_label: QLabel = new(bind="{#window.get_greeting()}")
```

### #app Placeholder (QApplication Instance)

```python
_label: QLabel = new(bind="{#app.applicationName()}")
_version: QLabel = new(bind="Version: {#app.applicationVersion()}")
```

---

## List Bindings

### Basic List Binding

```python
_items: Variable[list[str]] = new(["A", "B", "C"])
_labels: list[QLabel] = new(bind="_items")
```

### List with Format String

```python
_nums: Variable[list[int]] = new([1, 2, 3])
_labels: list[QLabel] = new(bind="_nums", format="Value: {#self}")
```

### List with #index Placeholder

```python
_items: Variable[list[str]] = new(["X", "Y"])
_labels: list[QLabel] = new(bind="_items", format="#{#index}: {#self}")
# "#0: X", "#1: Y"
```

---

## Dict Bindings

### Dict with #key and #value

```python
_scores: Variable[dict[str, int]] = new({"Alice": 100, "Bob": 85})
_labels: list[QLabel] = new(bind="_scores", format="{#key}: {#value}")
```

---

## Property Bindings (visible=, enabled=)

### Variable Binding

```python
_show: Variable[bool] = new(False)
_panel: QLabel = new("Hidden", visible="_show")
```

### Expression Binding

```python
_count: Variable[int] = new(0)
_warning: QLabel = new("Low!", visible="{_count < 5}")
```

### Enabled with Expression

```python
_name: Variable[str] = new("")
_submit: QPushButton = new("Go", enabled="{len(_name) > 0}")
```

---

## Dirty Tracking

### Checking Dirty State

```python
instance.is_dirty.get()  # Returns bool
instance.dirty_fields  # Returns set of field names
instance.reset_dirty()  # Clear dirty state
```

### on_dirty_changed Hook

```python
@override
def on_dirty_changed(self, is_dirty: bool) -> None:
    self.save_btn.setEnabled(is_dirty)
```

---

## Validation

### Adding Validators

```python
instance.add_validator("_name", "required", lambda v: None if v else "Required")
```

### Checking Validation State

```python
instance.is_valid.get()  # Returns bool
instance.validation_error_messages.get()  # Returns list of error strings
```

### on_valid_changed Hook

```python
@override
def on_valid_changed(self, is_valid: bool) -> None:
    self.submit_btn.setEnabled(is_valid)
```

---

## Record Support (AppBase[T])

### Record from Decorator

```python
@dataclass
class Settings:
    name: str = ""
    count: int = 0

@app(show=False, system_tray=False, record=Settings("test", 42))
class MyApp(AppBase[Settings]):
    pass

instance = MyApp()
instance.record.name  # "test"
instance.record.count  # 42
```

### Auto-binding Fields to Record Properties

```python
@dataclass
class User:
    username: str = ""

@app(record=User("alice"))
class MyApp(AppBase[User]):
    username: QLineEdit = new()  # Auto-binds to record.username
```

### Passing Record to Child Menu

```python
@menu
class DogMenu(Menu):
    dog: Variable[Dog]

@app(record=Dog("Rover", 5))
class MyApp(AppBase[Dog]):
    dog_menu: DogMenu = new(dog="record")  # Shares app's record
```

---

## Signal Connections

### By Method Name

```python
_button: QPushButton = new("Click", clicked="on_click")

def on_click(self) -> None:
    print("Clicked!")
```

### By Lambda

```python
_button: QPushButton = new("Click", clicked=lambda: print("Clicked"))
```

---

## __setup__ Lifecycle Hook

```python
def __setup__(self) -> None:
    self._count.value = 100
    self.add_validator("_name", "req", lambda v: None if v else "Required")
```

---

## System Tray

### QAction Fields Create Tray Menu

```python
from qtpy.QtGui import QAction

@app(show=False, window=False)
class MyApp(AppBase):
    action1: QAction = new("First")
    action2: QAction = new("Second")
    # Automatically creates system tray with these actions
```

### Custom Tray Menu (system_tray field)

```python
@menu
class TrayMenu(Menu):
    action1: QAction = new("First Action")
    action2: QAction = new("Second Action")

@app(show=False)
class MyApp(AppBase):
    system_tray: TrayMenu = new()  # Used as tray context menu
```

### Separators and Sections in Tray

```python
from qtpie.menu import Separator, Section

@app(show=False, window=False)
class MyApp(AppBase):
    action1: QAction = new("First")
    ___: Separator
    action2: QAction = new("Second")
    ___my_section___: Section
    action3: QAction = new("Third")
```

### on_system_tray_activated Hook

```python
@override
def on_system_tray_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
    if reason == QSystemTrayIcon.ActivationReason.Trigger:
        self.show()
```

---

## Window Control

### Window Property

```python
instance.window  # Returns QMainWindow or None
instance.is_visible  # Returns bool
instance.hide()  # Hide the window
```

---

## Icon Configuration

### Shared Icon (window + tray)

```python
@app(icon=QIcon("app.png"))
class MyApp(AppBase): ...
```

### Separate Icons

```python
@app(icon=shared_icon, window_icon=window_icon, tray_icon=tray_icon)
class MyApp(AppBase): ...
```

### Icon from Standard Pixmap

```python
@app(icon=QStyle.StandardPixmap.SP_ComputerIcon)
class MyApp(AppBase): ...
```

### Icon from File Path

```python
@app(icon="path/to/icon.png")
class MyApp(AppBase): ...
```

---

## Title Configuration

### Static Title

```python
@app(title="My Application")
class MyApp(AppBase): ...
```

### Without Title (uses class name)

```python
@app(show=False)
class MyCustomApp(AppBase):  # Window title: "MyCustomApp"
    ...
```

---

## ref() for Deferred Binding Resolution

Use `ref()` when binding expressions reference fields that aren't yet bound:

```python
from qtpie import ref

@menu
class DogMenu(Menu):
    dog: Variable[Dog]
    dog_action: QAction = new(text=ref("{dog.name}"))

@app(record=Dog("Fido", 3))
class MyApp(AppBase[Dog]):
    dog_menu: DogMenu = new(dog="record")
```

---

## Custom Widget Props

Props are passed to setXxx() methods:

```python
@app(show=False, customProp="value")
class MyApp(AppBase):
    def setCustomProp(self, value: str) -> None:
        ...
```
