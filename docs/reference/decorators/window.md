# @window

The `@window` decorator transforms a class into a Qt main window with automatic setup and configuration.

## Basic Usage

```python
from qtpy.QtWidgets import QMainWindow
from qtpie import window

@window
class MyWindow(QMainWindow):
    pass
```

With parentheses and parameters:

```python
@window(title="My Application", size=(1024, 768))
class MyWindow(QMainWindow):
    pass
```

## Parameters

### title

**Type:** `str | None`
**Default:** `None`

Sets the window title.

```python
@window(title="My Application")
class MyWindow(QMainWindow):
    pass

# Window title will be "My Application"
```

Without a title parameter, the window title is empty.

### size

**Type:** `tuple[int, int] | None`
**Default:** `None`

Sets the window dimensions as `(width, height)`.

```python
@window(size=(800, 600))
class MyWindow(QMainWindow):
    pass

# Window will be 800 pixels wide, 600 pixels tall
```

### icon

**Type:** `str | None`
**Default:** `None`

Sets the window icon from a file path.

```python
@window(icon="/path/to/icon.png")
class MyWindow(QMainWindow):
    pass
```

Supports any image format that Qt can load (PNG, JPG, SVG, etc.).

### center

**Type:** `bool`
**Default:** `False`

Centers the window on the screen. Must be used with `size` parameter.

```python
@window(title="Centered", size=(400, 300), center=True)
class MyWindow(QMainWindow):
    pass

# Window will appear centered on screen
```

### name

**Type:** `str | None`
**Default:** `None` (auto-generated from class name)

Sets the widget's `objectName` for QSS styling.

```python
@window(name="MainAppWindow")
class MyWindow(QMainWindow):
    pass

# objectName is "MainAppWindow"
```

#### Auto-naming

If `name` is not provided, it's derived from the class name:

```python
@window
class SomeWindow(QMainWindow):
    pass

# objectName is "Some" (Window suffix stripped)

@window
class Editor(QMainWindow):
    pass

# objectName is "Editor" (no suffix to strip)
```

### classes

**Type:** `list[str] | None`
**Default:** `None`

Sets CSS-like classes for styling via QSS.

```python
@window(classes=["dark-theme", "main-window"])
class MyWindow(QMainWindow):
    pass

# Can be styled with QSS:
# QMainWindow[class~="dark-theme"] { ... }
```

The classes are stored as a Qt property named `"class"`:

```python
w = MyWindow()
classes = w.property("class")  # ["dark-theme", "main-window"]
```

## Central Widget

A field named `central_widget` is automatically set as the window's central widget:

```python
from qtpy.QtWidgets import QTextEdit
from qtpie import window, make

@window
class MyWindow(QMainWindow):
    central_widget: QTextEdit = make(QTextEdit)

# Equivalent to calling: self.setCentralWidget(self.central_widget)
```

The central widget receives all child content:

```python
from qtpy.QtWidgets import QLabel

@window
class MyWindow(QMainWindow):
    central_widget: QLabel = make(QLabel, "Hello from central!")

w = MyWindow()
assert w.centralWidget() is w.central_widget
assert w.central_widget.text() == "Hello from central!"
```

If no `central_widget` field exists, the window has no central widget (which is valid for QMainWindow).

## Menu Bar Integration

QMenu fields are automatically added to the window's menu bar:

```python
from dataclasses import field
from qtpy.QtWidgets import QMenu

@window
class MyWindow(QMainWindow):
    file_menu: QMenu = field(default_factory=lambda: QMenu("&File"))
    edit_menu: QMenu = field(default_factory=lambda: QMenu("&Edit"))

# Both menus appear in the menu bar
```

### Private Menus

Fields starting with `_` are NOT added to the menu bar:

```python
@window
class MyWindow(QMainWindow):
    _hidden_menu: QMenu = field(default_factory=lambda: QMenu("Hidden"))
    visible_menu: QMenu = field(default_factory=lambda: QMenu("Visible"))

# Only visible_menu appears in menu bar
```

## Lifecycle Hooks

These methods are called automatically during initialization if they exist:

1. `setup()`
2. `setup_values()`
3. `setup_bindings()`
4. `setup_styles()`
5. `setup_events()`
6. `setup_signals()`

```python
@window
class MyWindow(QMainWindow):
    central_widget: QLabel = make(QLabel, "Initial")

    def setup(self) -> None:
        # Called after fields are initialized
        self.central_widget.setText("Modified in setup")

    def setup_values(self) -> None:
        # Set initial values
        pass

    def setup_bindings(self) -> None:
        # Set up data bindings
        pass

    def setup_styles(self) -> None:
        # Apply styles
        pass

    def setup_events(self) -> None:
        # Install event filters
        pass

    def setup_signals(self) -> None:
        # Connect additional signals
        pass
```

All hooks have access to fully initialized child widgets.

## Signal Connections

Signals are connected via the `make()` factory:

```python
from qtpy.QtWidgets import QPushButton

@window
class MyWindow(QMainWindow):
    central_widget: QPushButton = make(QPushButton, "Click", clicked="on_click")

    def on_click(self) -> None:
        print("Button clicked!")
```

Both method names (strings) and lambdas work:

```python
@window
class MyWindow(QMainWindow):
    central_widget: QPushButton = make(
        QPushButton,
        "Click",
        clicked=lambda: print("Clicked!"),
    )
```

## Field Defaults

Fields can have default values:

```python
@window
class MyWindow(QMainWindow):
    count: int = 42
    name: str = "default"

w = MyWindow()
assert w.count == 42
assert w.name == "default"
```

Fields can be overridden via constructor kwargs:

```python
@window
class MyWindow(QMainWindow):
    count: int = 0

w = MyWindow(count=99)
assert w.count == 99
```

## Complete Example

```python
from dataclasses import field
from qtpy.QtWidgets import QMainWindow, QTextEdit, QMenu
from qtpie import window, make

@window(
    title="Text Editor",
    size=(1024, 768),
    icon="resources/app_icon.png",
    center=True,
    classes=["main-window"],
)
class EditorWindow(QMainWindow):
    # Central widget
    central_widget: QTextEdit = make(QTextEdit)

    # Menus
    file_menu: QMenu = field(default_factory=lambda: QMenu("&File"))
    edit_menu: QMenu = field(default_factory=lambda: QMenu("&Edit"))

    # Custom fields
    unsaved_changes: bool = False

    def setup(self) -> None:
        # Configure after initialization
        self.statusBar().showMessage("Ready")
        self.central_widget.textChanged.connect(self.mark_dirty)

    def mark_dirty(self) -> None:
        self.unsaved_changes = True
```

## See Also

- [@widget](widget.md) - For general widgets
- [@menu](menu.md) - For menu configuration
- [@action](action.md) - For menu actions
- [make()](../factories/make.md) - Widget factory
- [Windows & Menus Guide](../../guides/windows-menus.md) - Complete guide
