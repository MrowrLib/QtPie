# @widget

The `@widget` decorator configures a `Widget` class with declarative layout, styling, and Qt property bindings.

## Signature

```python
@widget(
    cls: type[Widget] | None = None,
    *,
    layout: LayoutType = "vertical",
    margins: int | tuple[int, int, int, int] | None = None,
    auto_bind: bool = True,
    name: str | None = None,
    classes: list[str] | None = None,
    title: str | None = None,
    record: Any | None = None,
    stylesheet: str | None = None,
    **kwargs: Any,
) -> type[Widget] | Callable[[type[Widget]], type[Widget]]
```

## Parameters

### layout

**Type:** `"vertical" | "horizontal" | "form" | "grid" | None`
**Default:** `"vertical"`

The layout type for child widgets.

- `"vertical"` - `QVBoxLayout` (default)
- `"horizontal"` - `QHBoxLayout`
- `"form"` - `QFormLayout` (requires `label=` on fields)
- `"grid"` - `QGridLayout` (requires `grid=` on fields)
- `None` - No layout

```python
@widget
class DefaultLayout(Widget):
    # Vertical by default
    _label: QLabel = new("Top")
    _button: QPushButton = new("Bottom")

@widget(layout="horizontal")
class HorizontalLayout(Widget):
    _left: QLabel = new("Left")
    _right: QLabel = new("Right")

@widget(layout=None)
class NoLayout(Widget):
    # Manually position widgets
    _label: QLabel = new("Free-floating")
```

### margins

**Type:** `int | tuple[int, int, int, int] | None`
**Default:** `None`

Layout margins. Pass an `int` to apply to all sides, or a tuple for `(left, top, right, bottom)`.

```python
@widget(margins=20)
class UniformMargins(Widget):
    # 20px on all sides
    _label: QLabel = new("Content")

@widget(margins=(10, 5, 10, 5))
class CustomMargins(Widget):
    # 10px left/right, 5px top/bottom
    _label: QLabel = new("Content")
```

### auto_bind

**Type:** `bool`
**Default:** `True`

Whether to automatically bind QWidget fields to matching Variables or record fields by stripping underscore prefixes.

```python
@widget
class AutoBindEnabled(Widget):
    _name: Variable[str] = new("Alice")
    # This QLineEdit auto-binds to _name (looks for "name" field)
    name: QLineEdit = new()

@widget(auto_bind=False)
class AutoBindDisabled(Widget):
    _name: Variable[str] = new("Bob")
    # No auto-binding - must use bind= explicitly
    name: QLineEdit = new(bind="_name")
```

With `Widget[T]` record types:

```python
@dataclass
class Person:
    name: str = ""
    age: int = 0

@widget
class PersonEditor(Widget[Person]):
    # Auto-binds to record.name and record.age
    name: QLineEdit = new()
    age: QSpinBox = new()

@widget(auto_bind=False)
class PersonEditorManual(Widget[Person]):
    # Must bind explicitly
    name: QLineEdit = new(bind="name")
    age: QSpinBox = new(bind="age")
```

### name

**Type:** `str | None`
**Default:** `None` (uses class name)

Sets the widget's `objectName` for QSS/styling.

```python
@widget(name="main-panel")
class MyWidget(Widget):
    pass

w = MyWidget()
assert w.objectName() == "main-panel"
```

Without `name=`, the objectName defaults to the class name:

```python
@widget
class Dashboard(Widget):
    pass

w = Dashboard()
assert w.objectName() == "Dashboard"
```

### classes

**Type:** `list[str] | None`
**Default:** `None`

CSS classes for styling. Works with QtPie's styling system.

```python
@widget(classes=["card", "elevated"])
class Card(Widget):
    _title: QLabel = new("Card Title")

# Apply stylesheet with class selectors
app.setStyleSheet("""
.card {
    background: white;
    border-radius: 8px;
}
.elevated {
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}
""")
```

### title

**Type:** `str | None`
**Default:** `None`

Convenience alias for `windowTitle`. Calls `setWindowTitle()` on the widget.

```python
@widget(title="My Application")
class MainWidget(Widget):
    pass

# Equivalent to:
@widget(windowTitle="My Application")
class MainWidget(Widget):
    pass

w = MainWidget()
assert w.windowTitle() == "My Application"
```

### record

**Type:** `Any | None`
**Default:** `None`

Initial value for `Widget[T]` record. Sets the record in `__init__` before `__setup__` is called.

```python
@dataclass
class User:
    username: str = ""
    email: str = ""

@widget(record=User("admin", "admin@example.com"))
class UserEditor(Widget[User]):
    username: QLineEdit = new()
    email: QLineEdit = new()

    def __setup__(self) -> None:
        # Record is already set
        print(self.record.username)  # "admin"
```

Useful for types without default constructors:

```python
@dataclass
class Config:
    host: str
    port: int

@widget(record=Config("localhost", 8080))
class ConfigEditor(Widget[Config]):
    host: QLineEdit = new()
    port: QSpinBox = new()
```

### stylesheet

**Type:** `str | None`
**Default:** `None`

Convenience alias for `styleSheet`. Calls `setStyleSheet()` on the widget.

```python
@widget(stylesheet="background-color: #f0f0f0;")
class StyledWidget(Widget):
    _label: QLabel = new("Content")

# Equivalent to:
@widget(styleSheet="background-color: #f0f0f0;")
class StyledWidget(Widget):
    _label: QLabel = new("Content")
```

### **kwargs

**Type:** `Any`

Additional Qt properties applied via `setXXX()` methods. The decorator converts `propName` to `setPropName` and calls it with the value.

```python
@widget(
    minimumWidth=400,
    minimumHeight=300,
    toolTip="Main application window"
)
class AppWindow(Widget):
    pass

w = AppWindow()
assert w.minimumWidth() == 400
assert w.minimumHeight() == 300
assert w.toolTip() == "Main application window"
```

Common properties:

```python
@widget(
    windowTitle="My App",
    minimumSize=(800, 600),
    maximumSize=(1920, 1080),
    enabled=True,
    visible=True,
    toolTip="Description",
    whatsThis="Extended help",
    focusPolicy=Qt.FocusPolicy.StrongFocus,
)
class ConfiguredWidget(Widget):
    pass
```

## Layout Types

### Vertical Layout (Default)

Stacks widgets top-to-bottom using `QVBoxLayout`.

```python
@widget  # layout="vertical" is default
class VerticalStack(Widget):
    _header: QLabel = new("Header")
    _content: QLabel = new("Content")
    _footer: QLabel = new("Footer")
```

### Horizontal Layout

Arranges widgets left-to-right using `QHBoxLayout`.

```python
@widget(layout="horizontal")
class Toolbar(Widget):
    _new: QPushButton = new("New")
    _open: QPushButton = new("Open")
    _save: QPushButton = new("Save")
```

### Form Layout

Two-column layout with labels on the left, fields on the right. Requires `label=` parameter on each field.

```python
@widget(layout="form")
class ContactForm(Widget):
    name: QLineEdit = new(label="Full Name")
    email: QLineEdit = new(label="Email Address")
    phone: QLineEdit = new(label="Phone Number")
```

Without `label=`, raises `TypeError`:

```python
@widget(layout="form")
class InvalidForm(Widget):
    name: QLineEdit = new()  # Error: requires label=
```

### Grid Layout

Arranges widgets in a grid. Requires `grid=` parameter specifying `(row, col)` or `(row, col, rowspan, colspan)`.

```python
@widget(layout="grid")
class Calculator(Widget):
    display: QLineEdit = new(grid=(0, 0, 1, 4))  # Spans 4 columns
    btn_7: QPushButton = new("7", grid=(1, 0))
    btn_8: QPushButton = new("8", grid=(1, 1))
    btn_9: QPushButton = new("9", grid=(1, 2))
    btn_div: QPushButton = new("/", grid=(1, 3))
```

Without `grid=`, raises `TypeError`:

```python
@widget(layout="grid")
class InvalidGrid(Widget):
    btn: QPushButton = new("Click")  # Error: requires grid=
```

### No Layout

Set `layout=None` to manually position widgets.

```python
@widget(layout=None)
class CustomPositioned(Widget):
    _label: QLabel = new("Manual")

    def __setup__(self) -> None:
        self._label.move(100, 50)
        self._label.resize(200, 30)
```

## Styling with name= and classes=

### Widget-Level Styling

```python
@widget(
    name="dashboard",
    classes=["primary", "with-shadow"]
)
class Dashboard(Widget):
    _title: QLabel = new("Dashboard")
```

Access via QSS:

```css
#dashboard {
    background: white;
}
.primary {
    border: 2px solid blue;
}
.with-shadow {
    box-shadow: 0 4px 8px rgba(0,0,0,0.2);
}
```

### Field-Level Styling

Apply `name=` and `classes=` to individual fields:

```python
@widget
class StyledForm(Widget):
    _title: QLabel = new(
        "Welcome",
        name="page-title",
        classes=["header", "large"]
    )
    _submit: QPushButton = new(
        "Submit",
        name="submit-btn",
        classes=["btn", "btn-primary"]
    )
```

### Default Object Names

Without explicit `name=`, widgets get sensible defaults:

```python
@widget
class AutoNamed(Widget):
    _button: QPushButton = new("Click")

w = AutoNamed()
assert w.objectName() == "AutoNamed"      # Widget uses class name
assert w._button.objectName() == "_button"  # Field uses field name
```

## Reactive Properties

Decorator properties support reactive bindings using format strings with `{}`.

```python
@widget(windowTitle="{_app_name} - {_filename}")
class Editor(Widget):
    _app_name: Variable[str] = new("MyEditor")
    _filename: Variable[str] = new("untitled.txt")

    def open_file(self, name: str) -> None:
        self._filename.value = name
        # Window title automatically updates to "MyEditor - document.txt"
```

Works with any Qt property:

```python
@widget(
    windowTitle="{_count} items selected",
    toolTip="Total: {_count}"
)
class ItemCounter(Widget):
    _count: Variable[int] = new(0)
```

## Widget[T] Record Types

Use `Widget[T]` to bind a widget to a data model.

### Basic Record Type

```python
@dataclass
class Settings:
    theme: str = "light"
    font_size: int = 12

@widget
class SettingsPanel(Widget[Settings]):
    # Auto-binds to record.theme and record.font_size
    theme: QComboBox = new()
    font_size: QSpinBox = new()

    def __setup__(self) -> None:
        # Access record in setup
        self.record.theme = "dark"
        print(self.record.font_size)  # 12
```

### With Initial Value

```python
@widget(record=Settings("dark", 14))
class SettingsPanel(Widget[Settings]):
    theme: QComboBox = new()
    font_size: QSpinBox = new()

w = SettingsPanel()
assert w.record.theme == "dark"
assert w.record.font_size == 14
```

### Record State Access

Use `record_state` to access the `RecordVariable` wrapper for dirty tracking and observables:

```python
@widget
class PersonEditor(Widget[Person]):
    name: QLineEdit = new()
    age: QSpinBox = new()

    def save(self) -> None:
        if self.record_state.is_dirty.get():
            # Get the actual value
            person = self.record_state.value
            db.save(person)
            # Mark as clean
            self.record_state.reset_dirty()
```

## Examples

### Simple Widget

```python
@widget
class HelloWorld(Widget):
    _label: QLabel = new("Hello, World!")
    _button: QPushButton = new("Click Me", clicked="on_click")

    def on_click(self) -> None:
        print("Button clicked!")
```

### Form Layout with Validation

```python
@widget(layout="form", margins=20)
class LoginForm(Widget):
    _username: Variable[str] = new("")
    _password: Variable[str] = new("")

    username: QLineEdit = new(label="Username")
    password: QLineEdit = new(label="Password")
    submit: QPushButton = new("Login", clicked="on_submit")

    def __setup__(self) -> None:
        self.add_validator(
            "_username",
            "required",
            lambda v: None if v else "Username required"
        )
        self.add_validator(
            "_password",
            "min_length",
            lambda v: None if len(v) >= 8 else "Min 8 characters"
        )

    def on_submit(self) -> None:
        if self.is_valid:
            print(f"Logging in: {self._username.value}")
```

### Grid Layout Calculator

```python
@widget(layout="grid", title="Calculator")
class Calculator(Widget):
    _display: QLineEdit = new(grid=(0, 0, 1, 4))

    _btn_7: QPushButton = new("7", grid=(1, 0))
    _btn_8: QPushButton = new("8", grid=(1, 1))
    _btn_9: QPushButton = new("9", grid=(1, 2))
    _btn_div: QPushButton = new("/", grid=(1, 3))

    _btn_4: QPushButton = new("4", grid=(2, 0))
    _btn_5: QPushButton = new("5", grid=(2, 1))
    _btn_6: QPushButton = new("6", grid=(2, 2))
    _btn_mul: QPushButton = new("*", grid=(2, 3))
```

### Styled Card Widget

```python
@widget(
    name="card",
    classes=["elevated", "rounded"],
    stylesheet="""
        #card {
            background: white;
            border-radius: 8px;
            padding: 16px;
        }
        .elevated {
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
    """,
    minimumWidth=300,
)
class Card(Widget):
    _title: QLabel = new("Card Title", classes=["card-title"])
    _content: QLabel = new("Card content goes here.")
    _action: QPushButton = new("Action", classes=["btn-primary"])
```

### Record-Based Editor

```python
@dataclass
class BlogPost:
    title: str = ""
    content: str = ""
    published: bool = False

@widget(
    layout="form",
    record=BlogPost("My First Post", "Hello world!", False)
)
class PostEditor(Widget[BlogPost]):
    title: QLineEdit = new(label="Title")
    content: QTextEdit = new(label="Content")
    published: QCheckBox = new(label="Published")
    save: QPushButton = new("Save", clicked="on_save")

    def on_save(self) -> None:
        if self.record_state.is_dirty.get():
            post = self.record_state.value
            database.save(post)
            self.record_state.reset_dirty()
```

### Reactive Window Title

```python
@widget(
    windowTitle="{_app_name} - {_doc_name} {'*' if _modified else ''}",
    minimumWidth=800,
    minimumHeight=600,
)
class DocumentEditor(Widget):
    _app_name: Variable[str] = new("TextEdit")
    _doc_name: Variable[str] = new("Untitled")
    _modified: Variable[bool] = new(False)

    _text: QTextEdit = new()

    def __setup__(self) -> None:
        self._text.textChanged.connect(self._on_text_changed)

    def _on_text_changed(self) -> None:
        self._modified.value = True
```

## See Also

- [new() - Field Factory](../factories/new.md)
- [Variable - Reactive State](../core/variable.md)
- [Widget - Base Class](../core/widget.md)
- [Layout System](../../guides/layouts.md)
- [Styling Guide](../../guides/styling.md)
