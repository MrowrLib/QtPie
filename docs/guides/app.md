# App

The `@app` decorator creates a custom `QApplication` subclass with all of QtPie's declarative features. It's the most full-featured way to build an application - supporting widgets, menu bars, system tray, and everything else.

```python
from PySide6.QtWidgets import QLabel, QPushButton
from PySide6.QtGui import QAction
from qtpie import App, Variable, new, app, entrypoint

@entrypoint
@app
class MyApp(App):
    _count: Variable[int] = new(0)
    _label: QLabel = new(bind="Count: {_count}")
    _button: QPushButton = new("Increment", clicked="on_click")

    def on_click(self) -> None:
        self._count += 1
```

## Why Use @app?

`App` gives you everything:

- **All `Widget` features** - Variables, bindings, validation, dirty tracking
- **All `Window` features** - Menu bar, central widget, layouts
- **QApplication subclass** - Full control over the application instance
- **System tray support** - Add `QAction` fields for tray menu items

You don't *need* `@app` - any `@widget` or `@window` works as an application with `@entrypoint`. But `App` is there when you want the full package.

## @app Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `show` | `bool` | `True` | Show the window on startup |
| `window` | `bool` | `True` | Create a window (False for tray-only) |
| `system_tray` | `bool` | `True` | Enable system tray icon |
| `minimize_to_tray` | `bool` | `True` | Closing window hides to tray instead of quitting |
| `icon` | `str \| QIcon \| QPixmap \| StandardPixmap` | `None` | Sets both window and tray icon |
| `window_icon` | `str \| QIcon \| QPixmap \| StandardPixmap` | `None` | Window icon only (overrides `icon`) |
| `tray_icon` | `str \| QIcon \| QPixmap \| StandardPixmap` | `None` | Tray icon only (overrides `icon`) |
| `record` | `T` | `None` | Bind a dataclass record |

## Basic App

```python
@entrypoint
@app
class MyApp(App):
    _name: Variable[str] = new("")
    _label: QLabel = new(bind="Hello, {_name}!")
    _input: QLineEdit = new(bind="_name")
    _button: QPushButton = new("Greet", clicked="on_greet")

    def on_greet(self) -> None:
        print(f"Hello, {self._name.value}!")
```

## Icons

Set icons for the window and/or system tray:

```python
from PySide6.QtWidgets import QStyle
from PySide6.QtGui import QIcon

# Use a standard Qt icon
@app(icon=QStyle.StandardPixmap.SP_ComputerIcon)

# Use a QRC resource path
@app(icon=":/icons/app.png")

# Use a file path
@app(icon="path/to/icon.png")

# Use a QIcon
@app(icon=QIcon("path/to/icon.png"))

# Set window and tray icons separately
@app(
    window_icon="path/to/window.png",
    tray_icon=QStyle.StandardPixmap.SP_MessageBoxInformation
)
```

The `icon` parameter sets both window and tray icons. Use `window_icon` and `tray_icon` to set them separately.

## System Tray

Add `QAction` fields to create system tray menu items. An `icon` is required for the tray to appear:

```python
from PySide6.QtWidgets import QLabel, QStyle
from PySide6.QtGui import QAction
from qtpie import App, new, app, entrypoint

@entrypoint
@app(icon=QStyle.StandardPixmap.SP_ComputerIcon)
class MyApp(App):
    # Window content
    _label: QLabel = new("Main content")

    # Tray menu actions
    show_action: QAction = new("Show Window", triggered="on_show")
    quit_action: QAction = new("Quit", triggered="quit")

    def on_show(self) -> None:
        self.show()
```

### Tray-Only App

```python
from PySide6.QtWidgets import QStyle
from PySide6.QtGui import QAction
from qtpie import App, new, app, entrypoint

@entrypoint
@app(icon=QStyle.StandardPixmap.SP_MessageBoxInformation)
class TrayApp(App):
    notify_action: QAction = new("Notify", triggered="on_notify")
    quit_action: QAction = new("Quit", triggered="quit")

    def on_notify(self) -> None:
        print("Notification!")
```

No widget fields means no window is created - it's tray-only automatically. Use `window=False` only if you have widget fields but still want tray-only.

### Menu Separators

```python
from PySide6.QtWidgets import QStyle
from PySide6.QtGui import QAction
from qtpie import App, new, app, entrypoint
from qtpie.menu import Separator

@entrypoint
@app(icon=QStyle.StandardPixmap.SP_ComputerIcon)
class TrayApp(App):
    action1: QAction = new("First")
    ___: Separator  # Menu separator
    action2: QAction = new("Second")
```

### Menu Sections

```python
from PySide6.QtWidgets import QStyle
from PySide6.QtGui import QAction
from qtpie import App, new, app, entrypoint
from qtpie.menu import Section, Separator

@entrypoint
@app(icon=QStyle.StandardPixmap.SP_ComputerIcon)
class TrayApp(App):
    ___file_section___: Section  # Shows as "File Section"
    open_action: QAction = new("Open")
    save_action: QAction = new("Save")

    ___: Separator

    quit_action: QAction = new("Quit")
```

!!! note
    Sections don't show up on Windows when using native Windows styling. To see them, use `@app(style="fusion")`.

### Using a Menu Class

For reusable tray menus, define a field named `system_tray` with a `Menu` subclass:

```python
from PySide6.QtWidgets import QStyle
from PySide6.QtGui import QAction
from qtpie import App, Menu, new, app, entrypoint, menu

@menu
class TrayMenu(Menu):
    hello_action: QAction = new("Say Hello", triggered="on_hello")

    def on_hello(self) -> None:
        print("Hello from tray!")

@entrypoint
@app(icon=QStyle.StandardPixmap.SP_ComputerIcon)
class MyApp(App):
    system_tray: TrayMenu = new()
```

## All Widget Features

`App` supports everything `Widget` does:

### Variables

```python
@app
class MyApp(App):
    _name: Variable[str] = new("default")
    _count: Variable[int] = new(0)
```

### Variable[T, W] Inline Widgets

```python
@app
class MyApp(App):
    _username: Variable[str, QLineEdit] = new("")(placeholderText="Username")
```

### Format String Bindings

```python
@app
class MyApp(App):
    _name: Variable[str] = new("Alice")
    _label: QLabel = new(bind="Hello, {_name.upper()}!")

    _x: Variable[int] = new(10)
    _y: Variable[int] = new(5)
    _sum: QLabel = new(bind="{_x + _y}")

    _price: Variable[float] = new(19.99)
    _formatted: QLabel = new(bind="${_price:.2f}")
```

### Property Bindings

```python
@app
class MyApp(App):
    _show_panel: Variable[bool] = new(False)
    _panel: QLabel = new("Hidden panel", visible="_show_panel")

    _count: Variable[int] = new(0)
    _warning: QLabel = new("Low!", visible="{_count < 5}")
```

### List and Dict Bindings

```python
@app
class MyApp(App):
    _items: Variable[list[str]] = new(["A", "B", "C"])
    _labels: list[QLabel] = new(bind="_items")

    _scores: Variable[dict[str, int]] = new({"Alice": 100})
    _score_labels: list[QLabel] = new(bind="_scores", format="{#key}: {#value}")
```

### Signal Connections

```python
@app
class MyApp(App):
    _button: QPushButton = new("Click", clicked="on_click")

    def on_click(self) -> None:
        print("Clicked!")
```

## Record Types

Bind a dataclass to your app:

```python
from dataclasses import dataclass

@dataclass
class Settings:
    name: str = ""
    count: int = 0

@entrypoint
@app(record=Settings("test", 42))
class MyApp(App[Settings]):
    name: QLineEdit = new()  # Auto-binds to record.name
    count: QLineEdit = new()  # Auto-binds to record.count
```

## Validation

```python
@app
class MyApp(App):
    _name: Variable[str] = new("")

    def __setup__(self) -> None:
        self.add_validator("_name", "required", lambda v: None if v else "Required")
```

Access validation state:

- `is_valid` - `Observable[bool]`
- `validation_error_messages` - list of error strings
- `on_valid_changed(is_valid: bool)` - lifecycle hook

## Dirty Tracking

```python
@app
class MyApp(App):
    _count: Variable[int] = new(0)

    def on_dirty_changed(self, is_dirty: bool) -> None:
        print(f"Dirty: {is_dirty}")
```

Access dirty state:

- `is_dirty` - `Observable[bool]`
- `dirty_fields` - set of changed field names
- `reset_dirty()` - mark all fields as clean

## Lifecycle Hook

Use `__setup__()` for initialization after fields are created:

```python
@app
class MyApp(App):
    _count: Variable[int] = new(0)

    def __setup__(self) -> None:
        self._count.value = 100
        self.add_validator("_name", "req", lambda v: None if v else "Required")
```

## See Also

- [@entrypoint](entrypoint.md) - Running your application
- [Widgets](../basics/widgets.md) - Widget basics
- [Windows & Menus](windows-menus.md) - Main windows with menus
- [Validation](../data/validation.md) - Form validation
- [Dirty Tracking](../data/dirty-tracking.md) - Change detection
