# @window

Decorator for creating declarative `QMainWindow` subclasses with automatic layout management and menu bar integration.

## Signature

```python
@window(
    title: str | None = None,
    *,
    layout: Literal["vertical", "horizontal", "form", "grid", None] = "vertical",
    margins: int | tuple[int, int, int, int] | None = None,
    record: T | None = None,
    # Plus any QMainWindow property
    **kwargs
) -> type[Window[T]]
```

## Parameters

### Core Parameters

**`title`** (alias for `windowTitle`)
- Window title text
- Can be a format string referencing Variables: `title="{_filename} - Editor"`
- Default: No title set

**`layout`**
- Layout type for central widget
- Options: `"vertical"`, `"horizontal"`, `"form"`, `"grid"`, `None`
- Default: `"vertical"` (creates `QVBoxLayout`)
- When `None`, no layout is created on the central widget

**`margins`**
- Central widget layout margins
- `int`: Same margin on all sides
- `tuple[int, int, int, int]`: (left, top, right, bottom)
- Default: Qt default margins

**`record`**
- Initial record value for `Window[T]`
- Sets `self.record` immediately, available in `__setup__`
- Enables automatic field binding to record properties
- Example: `record=Person("Alice", 30)`

### Qt Property Parameters

Any `QMainWindow` property can be set via `setXXX()`:

```python
@window(
    windowTitle="My App",      # setWindowTitle()
    minimumWidth=800,           # setMinimumWidth()
    minimumHeight=600,          # setMinimumHeight()
    styleSheet="...",          # setStyleSheet()
)
```

**Common property aliases:**
- `title` → `windowTitle`
- `stylesheet` → `styleSheet`

### Styling Parameters

**`name`**
- Sets `objectName` via `setObjectName()`
- Default: Class name (e.g., `"MainWindow"`)
- Used for CSS selectors: `#MainWindow { ... }`

**`classes`**
- CSS class names as a list
- Stored in dynamic property `"class"`
- Example: `classes=["dark-theme", "main-window"]`

## Behavior

### Automatic Central Widget

1. Creates a central widget with the specified layout type
2. Adds all widget fields (non-menu, non-Variable-only) to the layout
3. Respects field declaration order

Exception: If a field named `central_widget` exists, it becomes the central widget directly (no automatic layout).

### Automatic Menu Bar

1. Finds all `QMenu` typed fields
2. Adds them to the menu bar via `addMenu()` in declaration order
3. Menus are not added to the central widget layout

### Field Exclusions

Fields are NOT added to the central widget layout if:
- They are `QMenu` instances (go to menu bar)
- They have `layout=False` in `new()`
- They are Variable-only (no widget)
- They are underscore-prefixed and Variable-only

### Initialization Order

1. `QMainWindow.__init__()` called
2. All field descriptors initialized
3. Menus added to menu bar
4. Widgets added to central widget layout
5. Properties applied (`setXXX()` calls)
6. `__setup__()` hook called (if defined)

## Reactive Properties

Decorator parameters support format string bindings:

```python
@window(title="{_filename} - {_app_name}")
class MyWindow(Window):
    _filename: Variable[str] = new("untitled.txt")
    _app_name: Variable[str] = new("MyApp")
```

When any referenced Variable changes, the property updates automatically.

## Usage with Window[T]

For record-based windows:

```python
@dataclass
class Person:
    name: str
    age: int

@window(record=Person("Alice", 30))
class PersonEditor(Window[Person]):
    name: QLineEdit = new()  # Auto-binds to record.name
    age: QLineEdit = new()   # Auto-binds to record.age
```

The `record=` parameter:
- Sets `self.record` to the provided value
- Enables field auto-binding by name
- Makes record accessible in `__setup__`
- Enables dirty tracking via `self.record_state`

## Examples

### Basic Window

```python
@window
class MainWindow(Window):
    label: QLabel = new("Hello, World!")
    button: QPushButton = new("Click Me")
```

### With Properties

```python
@window(
    title="Text Editor",
    minimumWidth=800,
    minimumHeight=600,
    stylesheet="QMainWindow { background: #f0f0f0; }"
)
class EditorWindow(Window):
    editor: QTextEdit = new()
```

### With Menus

```python
@menu("&File")
class FileMenu(QMenu):
    new_action: QAction = new("&New", shortcut="Ctrl+N")
    exit_action: QAction = new("E&xit")

@window(title="My App")
class MainWindow(Window):
    file_menu: FileMenu = new()
    content: QLabel = new("Content area")
```

### Horizontal Layout

```python
@window(layout="horizontal")
class HorizontalWindow(Window):
    left_panel: QWidget = new()
    right_panel: QWidget = new()
```

### Form Layout

```python
@window(layout="form")
class SettingsWindow(Window):
    username: QLineEdit = new(label="Username:")
    password: QLineEdit = new(label="Password:")
```

### Grid Layout

```python
@window(layout="grid")
class GridWindow(Window):
    top_left: QLabel = new("TL", grid=(0, 0))
    top_right: QLabel = new("TR", grid=(0, 1))
    bottom: QLabel = new("Bottom", grid=(1, 0, 1, 2))  # Spans 2 columns
```

### Custom Margins

```python
@window(margins=20)  # All sides
class Window1(Window):
    pass

@window(margins=(10, 20, 10, 20))  # left, top, right, bottom
class Window2(Window):
    pass
```

### Explicit Central Widget

```python
@window
class CustomCentralWindow(Window):
    central_widget: MyCustomWidget = new()
    # Other widgets exist but are not added to any layout
    other: QLabel = new("Not in layout")
```

### With Record and Reactive Title

```python
@dataclass
class Document:
    filename: str = "untitled.txt"

@window(
    title="{filename} - Editor",
    record=Document()
)
class DocumentEditor(Window[Document]):
    # Title updates when filename changes
    pass
```

### Excluding Widgets from Layout

```python
@window
class MainWindow(Window):
    visible: QLabel = new("In layout")
    hidden: QLabel = new("Not in layout", layout=False)
```

## Required

The `@window` decorator is required. Instantiating a `Window` subclass without it raises `TypeError`:

```python
class MainWindow(Window):  # Missing @window
    pass

MainWindow()  # TypeError: MainWindow must be decorated with @window
```

## See Also

- [Window class reference](../classes/window.md)
- [Windows & Menus guide](../../guides/windows-menus.md)
- [@menu decorator](./menu.md)
- [@widget decorator](./widget.md)
