# QtPie Drafting Summary

This document catalogs **all ideas** from the various QtPie drafts, providing detailed descriptions, code examples, pros/cons, and file references. This serves as the foundation for building the final, unified QtPie library.

---

## Table of Contents

1. [Philosophy & Goals](#philosophy--goals)
2. [Core Decorators](#core-decorators)
   - [@widget](#widget-decorator)
   - [@widget_class](#widget_class-decorator)
   - [@window](#window-decorator)
   - [@menu](#menu-decorator)
   - [@action](#action-decorator)
   - [@entry_point](#entry_point-decorator)
3. [Widget Factory Functions](#widget-factory-functions)
   - [make()](#make)
   - [make_widget()](#make_widget)
   - [make_later()](#make_later)
   - [make_form_row()](#make_form_row)
   - [grid_item()](#grid_item)
4. [Data Binding System](#data-binding-system)
   - [Observable Integration](#observable-integration)
   - [Binding Registry](#binding-registry)
   - [Two-Way Binding](#two-way-binding)
   - [Nested Path Binding](#nested-path-binding)
5. [Styling System](#styling-system)
   - [CSS Classes on Widgets](#css-classes-on-widgets)
   - [Object Names for QSS](#object-names-for-qss)
   - [SCSS Compilation & Live Reload](#scss-compilation--live-reload)
6. [Layout System](#layout-system)
   - [Automatic Layout Population](#automatic-layout-population)
   - [Grid Layout with GridPosition](#grid-layout-with-gridposition)
   - [Form Layout Support](#form-layout-support)
   - [Stretch Support](#stretch-support)
7. [Signal & Event Handling](#signal--event-handling)
   - [Signal Connection in make()](#signal-connection-in-make)
   - [Signal Typing Utilities](#signal-typing-utilities)
8. [Application Infrastructure](#application-infrastructure)
   - [App Class](#app-class)
   - [run_app()](#run_app)
   - [Development Mode](#development-mode)
9. [Dock System](#dock-system)
   - [TabbedDocksMainWindow](#tabbeddocksmainwindow)
   - [DockManager](#dockmanager)
   - [DockTitleBar](#docktitlebar)
10. [Utility Functions](#utility-functions)
    - [Colored SVG](#colored-svg)
    - [Screen Centering](#screen-centering)
    - [File Utilities](#file-utilities)
11. [Pre-built Widgets](#pre-built-widgets)
    - [FilterableDropdown](#filterabledropdown)
    - [AutoHeightTextEdit](#autoheighttextedit)
12. [Metadata & Configuration](#metadata--configuration)
    - [WidgetFactoryProperties](#widgetfactoryproperties)
    - [Global Configuration](#global-configuration)
    - [Field Metadata vs Qt Properties](#field-metadata-vs-qt-properties)
13. [Base Classes & Mixins](#base-classes--mixins)
    - [Widget](#widget-base-class)
    - [ModelWidget](#modelwidget)
    - [WidgetModel](#widgetmodel)
    - [Action](#action-base-class)
14. [Comprehensive Feature Matrix](#comprehensive-feature-matrix)
15. [Recommendations for Final Implementation](#recommendations-for-final-implementation)

---

## Philosophy & Goals

QtPie aims to bring **declarative, dataclass-based UI development** to Qt/PySide6, inspired by:

- **Ruby DSLs** - Convention over configuration, minimal boilerplate
- **React/Vue** - Declarative component definitions, reactive data binding
- **Web CSS** - Class-based styling with familiar patterns
- **Modern Python** - Dataclasses, type hints, generics

**Core Principles:**

1. **Declarative over Imperative** - Define what widgets exist, not how to create them
2. **Zero Boilerplate Layouts** - Child widgets auto-populate parent layouts
3. **Reactive Data Binding** - Model changes reflect in UI automatically
4. **Type Safety** - Full type hints for IDE support and static analysis
5. **Familiar Styling** - CSS classes, SCSS compilation, hot reload

---

## Core Decorators

### @widget Decorator

**Purpose:** Transform a class into a Qt widget with automatic dataclass conversion, layout setup, and lifecycle hooks.

**Files:**
- `DRAFT/more_recent_drafting/qtpie/qtpie/decorators/widget.py`
- `DRAFT/other_drafting/qtpie/widget.py`
- `DRAFT/drafting/qtpie/decorators/widget.py`

**Signature:**
```python
@widget(
    name: str | None = None,              # Object name for QSS
    classes: list[str] | None = None,     # CSS-like classes
    layout: "horizontal" | "vertical" | "form" | "grid" | "none" | type[QLayout] = "vertical",
    add_widgets_to_layout: bool = True,   # Auto-add child widgets
    width: int | None = None,             # Fixed width
    height: int | None = None,            # Fixed height
)
```

**Example:**
```python
@widget(name="AnimalEditor", classes=["card", "shadow"], layout="vertical")
class AnimalWidget(QWidget, ModelWidget[Animal]):
    txt_name: QLineEdit = make(QLineEdit, bind="name")
    txt_species: QLineEdit = make(QLineEdit, bind="species")
    btn_save: QPushButton = make(QPushButton, "Save", clicked="on_save")

    def setup(self) -> None:
        """Called after widget initialization."""
        print("Widget ready!")

    def on_save(self) -> None:
        print(f"Saving {self.model.value.name}")
```

**Lifecycle Hooks (called in order):**
1. `setup()` - General initialization
2. `setup_values()` - Set initial values
3. `setup_bindings()` - Configure data bindings
4. `setup_layout(layout)` - Customize layout
5. `setup_box_layout(layout)` - Customize box layout specifically
6. `setup_styles()` - Apply dynamic styles
7. `setup_events()` - Set up event handlers
8. `setup_signals()` - Connect signals

**Pros:**
- Dramatically reduces boilerplate
- Consistent initialization order
- Type-safe with `@dataclass_transform()`
- Automatic layout population

**Cons:**
- Magic can be confusing for Qt newcomers
- Order of field declaration matters for layout
- Debugging initialization issues can be tricky

---

### @widget_class Decorator

**Purpose:** Like `@widget` but for classes that are already dataclasses or shouldn't be converted.

**File:** `DRAFT/drafting/qtpie/decorators/widget.py`

**Example:**
```python
@widget_class(layout="horizontal")
class ExistingWidget(QWidget):
    def __init__(self):
        super().__init__()
        # Custom init logic
```

**Pros:**
- Works with existing class hierarchies
- More control over initialization

**Cons:**
- Less magic = more manual setup
- Two decorators to remember

**Recommendation:** Consider unifying into a single `@widget` that auto-detects the situation.

---

### @window Decorator

**Purpose:** Transform a class into a `QMainWindow` with title, icon, size, and automatic menu bar setup.

**Files:**
- `DRAFT/more_recent_drafting/qtpie/qtpie/decorators/window.py`
- `DRAFT/other_drafting/qtpie/window.py`

**Signature:**
```python
@window(
    name: str | None = None,
    classes: list[str] | None = None,
    title: str | None = None,
    icon: str | None = None,          # Path to icon file
    size: tuple[int, int] | None = None,
)
```

**Example:**
```python
@window(title="Animal Manager", icon=":/icons/app.png", size=(800, 600))
class MainWindow(QMainWindow, Widget):
    central_widget: AnimalWidget = make(AnimalWidget)
    file_menu: FileMenu = make(FileMenu)
    edit_menu: EditMenu = make(EditMenu)

    def setup(self) -> None:
        self.statusBar().showMessage("Ready")
```

**Features:**
- Auto-sets `central_widget` if field exists
- Auto-adds `QMenu` fields to menu bar
- Same lifecycle hooks as `@widget`

**Pros:**
- Consistent with `@widget` pattern
- Menus declared as fields, auto-registered

**Cons:**
- Limited to `QMainWindow` (no `QDialog` variant yet)

---

### @menu Decorator

**Purpose:** Transform a class into a `QMenu` with automatic action/submenu registration.

**File:** `DRAFT/other_drafting/qtpie/menu.py`

**Signature:**
```python
@menu(text: str | None = None)
```

**Example:**
```python
@menu("File")
class FileMenu(QMenu):
    new_action: NewAction = make(NewAction)
    open_action: OpenAction = make(OpenAction)
    _separator1: QAction = make(lambda: QAction())  # Separator
    recent_menu: RecentFilesMenu = make(RecentFilesMenu)
    _separator2: QAction = make(lambda: QAction())
    exit_action: ExitAction = make(ExitAction)
```

**Features:**
- Child `QAction` fields auto-added via `addAction()`
- Child `QMenu` fields auto-added via `addMenu()`
- Preserves field order for menu item order

**Pros:**
- Declarative menu definition
- Nested menus as nested classes
- Type-safe action references

**Cons:**
- Separators require workaround (dummy actions)
- No built-in support for dynamic menus

**Recommendation:** Add `separator()` helper or `_separator` field type detection.

---

### @action Decorator

**Purpose:** Transform a class into a `QAction` with shortcut, tooltip, and icon.

**File:** `DRAFT/other_drafting/qtpie/action.py`

**Signature:**
```python
@action(
    text: str | None = None,
    shortcut: str | None = None,
    tooltip: str | None = None,
    icon: QPixmap | QIcon | QStyle.StandardPixmap | str | None = None,
)
```

**Example:**
```python
@action("Open File", shortcut="Ctrl+O", tooltip="Open an existing file", icon=QStyle.StandardPixmap.SP_DialogOpenButton)
class OpenAction(QAction, Action):
    def action(self, checked: bool) -> None:
        file_path, _ = QFileDialog.getOpenFileName(None, "Open File")
        if file_path:
            self.parent().open_file(file_path)
```

**Icon Sources:**
- `str` - File path, loaded as `QIcon`
- `QPixmap` / `QIcon` - Used directly
- `QStyle.StandardPixmap` - System icon from app style

**Pros:**
- Declarative action definition
- Multiple icon source types
- Auto-connects to `action()` method

**Cons:**
- Requires `Action` base class mixin
- Icon loading happens at init time

---

### @entry_point Decorator

**Purpose:** Wrap a function to auto-create `QApplication` and run the event loop.

**File:** `DRAFT/drafting/examples/experiments/entry_point_decorator_test.py`

**Example:**
```python
@entry_point
def main():
    label = QLabel("Hello, World!")
    label.setWindowTitle("Simple App")
    label.show()

if __name__ == "__main__":
    main()
```

**Pros:**
- Great for quick scripts and examples
- Reduces boilerplate for simple apps

**Cons:**
- Limited control over `QApplication` configuration
- Not suitable for complex apps

**Recommendation:** Add optional parameters for app name, dark mode, etc.

---

## Widget Factory Functions

### make()

**Purpose:** Create widget instances as dataclass field defaults with optional binding and signal connections.

**Files:**
- `DRAFT/more_recent_drafting/qtpie/qtpie/factories/make.py`
- `DRAFT/drafting/qtpie/factories/dataclass_factories/make.py`
- `DRAFT/drafting/qtpie/factories/attribute_factories/make.py`

**Signature:**
```python
def make(
    class_type: Callable[..., T],
    *args: Any,
    bind: str | None = None,           # Model path to bind
    bind_prop: str | None = None,      # Widget property (defaults by type)
    **kwargs: Any,                      # Passed to constructor OR signal connections
) -> T
```

**Examples:**
```python
# Basic widget creation
label: QLabel = make(QLabel, "Hello World")

# With binding to model
txt_name: QLineEdit = make(QLineEdit, bind="name")

# With nested path binding (optional chaining)
txt_city: QLineEdit = make(QLineEdit, bind="address?.city")

# With signal connections (string = method name)
btn_save: QPushButton = make(QPushButton, "Save", clicked="on_save_clicked")

# With signal connections (lambda)
btn_cancel: QPushButton = make(QPushButton, "Cancel", clicked=lambda: print("Cancelled"))

# With widget properties
slider: QSlider = make(QSlider, Qt.Orientation.Horizontal, minimum=0, maximum=100, value=50)

# Combined
txt_age: QLineEdit = make(
    QLineEdit,
    bind="age",
    placeholderText="Enter age",
    textChanged="on_age_changed"
)
```

**How Signal Detection Works:**
- If a kwarg value is a `str` or `callable`, it's treated as a potential signal connection
- At widget init time, the decorator checks if the attribute has a `.connect()` method
- If yes, it's a signal - connect it
- If no, it's a property - set it via setter method

**Pros:**
- Very concise syntax
- Combines creation, binding, and signals in one call
- Type-safe (returns `T`)

**Cons:**
- Signal detection heuristic can be wrong (string properties vs signal names)
- "Type lie" - returns `field()` at runtime but claims to return `T`

---

### make_widget()

**Purpose:** Like `make()` but with explicit CSS class support.

**File:** `DRAFT/more_recent_drafting/qtpie/qtpie/factories/make_widget.py`

**Signature:**
```python
def make_widget(
    widget_class: type[W],
    widget_options: str | list[str] | tuple[str, list[str]] | None = None,
    *args: Any,
    bind: str | None = None,
    bind_prop: str | None = None,
    **kwargs: Any,
) -> W
```

**Widget Options:**
- `str` - Object name only: `"myButton"`
- `list[str]` - Classes only: `["btn-primary", "large"]`
- `tuple[str, list[str]]` - Both: `("myButton", ["btn-primary"])`

**Example:**
```python
btn_save: QPushButton = make_widget(
    QPushButton,
    ("saveBtn", ["btn-primary", "btn-large"]),
    "Save Changes",
    clicked="on_save"
)
```

**Pros:**
- Explicit class support
- Clear separation of styling from behavior

**Cons:**
- More verbose than `make()`
- Tuple syntax can be confusing

---

### Tuple Syntax Variant (DRAFT/drafting)

**File:** `DRAFT/drafting/qtpie/factories/attribute_factories/make.py`

An alternative `make()` that accepts tuples:

```python
# Type only
btn: QPushButton = make(QPushButton, "Click")

# Type + object name
btn: QPushButton = make((QPushButton, "myButton"), "Click")

# Type + classes
btn: QPushButton = make((QPushButton, ["btn-primary"]), "Click")

# Type + name + classes
btn: QPushButton = make((QPushButton, "myButton", ["btn-primary"]), "Click")
```

**Pros:**
- Compact inline styling

**Cons:**
- Less readable
- Type hints harder to express

---

### make_later()

**Purpose:** Deferred widget creation - useful for widgets that need parent context.

**Referenced in:** `DRAFT/other_drafting/qtpie/__init__.py`

**Note:** Implementation not found in drafts. Likely creates a factory that's called later.

---

### make_form_row()

**Purpose:** Create a widget for use in a `QFormLayout` with a label.

**Files:**
- `DRAFT/more_recent_drafting/qtpie/qtpie/factories/make_widget.py`
- `DRAFT/other_drafting/qtpie/make_widget.py`

**Signature:**
```python
def make_form_row(
    form_field_name: str,     # Label text
    widget_class: type[W],
    *args: Any,
    **kwargs: Any,
) -> W
```

**Example:**
```python
@widget(layout="form")
class UserForm(QWidget, Widget):
    txt_name: QLineEdit = make_form_row("Name:", QLineEdit)
    txt_email: QLineEdit = make_form_row("Email:", QLineEdit)
    cmb_role: QComboBox = make_form_row("Role:", QComboBox)
```

**How it works:**
- Sets `form_field_name` as a Qt property on the widget
- When the `@widget` decorator processes the layout, it reads this property
- Uses it as the label in `QFormLayout.addRow(label, widget)`

---

### grid_item()

**Purpose:** Create a widget with explicit grid position for `QGridLayout`.

**Files:**
- `DRAFT/drafting/qtpie/factories/attribute_factories/grid_item.py`
- `DRAFT/drafting/qtpie/factories/dataclass_factories/grid_item.py`

**GridPosition:**
```python
@dataclass(frozen=True)
class GridPosition:
    row: int
    col: int
    rowspan: int = 1
    colspan: int = 1
```

**Example:**
```python
@widget(layout="grid")
class CalculatorWidget(QWidget, Widget):
    display: QLineEdit = grid_item(GridPosition(0, 0, colspan=4), QLineEdit)
    btn_7: QPushButton = grid_item(GridPosition(1, 0), QPushButton, "7")
    btn_8: QPushButton = grid_item(GridPosition(1, 1), QPushButton, "8")
    btn_9: QPushButton = grid_item(GridPosition(1, 2), QPushButton, "9")
    btn_div: QPushButton = grid_item(GridPosition(1, 3), QPushButton, "/")
    # ... etc
```

**Pros:**
- Explicit positioning
- Supports row/column spans
- Clean declarative syntax

**Cons:**
- Verbose for simple grids
- Position values can get out of sync with visual layout

---

## Data Binding System

### Observable Integration

**Purpose:** Connect Qt widgets to reactive data models via the `observant` library.

**Files:**
- `DRAFT/more_recent_drafting/qtpie/qtpie/types.py` - `WidgetModel`, `ModelWidget`
- `DRAFT/more_recent_drafting/qtpie/qtpie/bindings/bind.py`
- `C:/Code/mrowr/MrowrLib/observant.py/observant/` - The reactive library

**Core Classes:**

```python
class WidgetModel(Generic[T]):
    """Wraps a data object with an ObservableProxy."""

    def __init__(self, obj: T):
        self._object = obj
        self._proxy = ObservableProxy(self._object, sync=True)

    @property
    def value(self) -> T:
        """The underlying data object."""
        return self._object

    @property
    def proxy(self) -> ObservableProxy[T]:
        """The reactive proxy for binding."""
        return self._proxy


class ModelWidget(Widget, Generic[T]):
    """Base class for widgets bound to a model."""
    _bound_widget_model: WidgetModel[T] | None = None

    @property
    def model(self) -> WidgetModel[T] | None:
        return self._bound_widget_model

    def set_model(self, model: T) -> None:
        self._bound_widget_model = WidgetModel(model)
        self._auto_bind_fields()  # Auto-bind fields with bind= metadata
        self.setup_model(self._bound_widget_model)
```

**Usage:**
```python
@dataclass
class User:
    name: str
    email: str
    age: int = 0

@widget
class UserEditor(QWidget, ModelWidget[User]):
    txt_name: QLineEdit = make(QLineEdit, bind="name")
    txt_email: QLineEdit = make(QLineEdit, bind="email")

    def setup_model(self, model: WidgetModel[User]) -> None:
        print(f"Editing user: {model.value.name}")

# Usage
editor = UserEditor()
editor.set_model(User(name="Alice", email="alice@example.com"))
```

---

### Binding Registry

**Purpose:** Register how to bind different widget types to observables.

**Files:**
- `DRAFT/more_recent_drafting/qtpie/qtpie/bindings/registry.py`
- `DRAFT/other_drafting/qtpie/bindings.py`

**Signature:**
```python
def register_binding(
    widget_type: type[TWidget],
    property: str,
    *,
    signal: str | None = None,        # Signal that fires on change
    getter: Callable[[TWidget], TValue] | None = None,
    setter: Callable[[TWidget, TValue], None] | None = None,
    value_type: type[TValue] = str,
    default: bool = False,            # Make this the default prop for widget type
) -> None
```

**Example:**
```python
# Built-in registrations
register_binding(
    QLineEdit,
    "text",
    setter=lambda w, v: w.setText(str(v)),
    getter=lambda w: w.text(),
    signal="textChanged",
)

register_binding(
    QSlider,
    "value",
    setter=lambda w, v: w.setValue(int(v)),
    getter=lambda w: w.value(),
    signal="valueChanged",
    default=True,  # "value" is the default for QSlider
)

# Custom widget registration
register_binding(
    MyCustomWidget,
    "data",
    setter=lambda w, v: w.setData(v),
    getter=lambda w: w.getData(),
    signal="dataChanged",
    default=True,
)
```

**Default Bindings Provided:**
- `QLineEdit.text`
- `QLabel.text` (one-way, no signal)
- `QTextEdit.text`
- `QPlainTextEdit.text`
- `QComboBox.text` (currentText)

---

### Two-Way Binding

**Purpose:** Automatically sync widget ↔ model in both directions.

**File:** `DRAFT/more_recent_drafting/qtpie/qtpie/bindings/bind.py`

**How it works:**
```python
def bind(observable: IObservable[TValue], widget: QWidget, prop: str = "text") -> None:
    adapter = get_binding_registry().get(widget, prop)

    lock = False  # Prevent infinite loops

    def update_model(value: TValue) -> None:
        nonlocal lock
        if not lock:
            lock = True
            observable.set(value)
            lock = False

    def update_ui(value: TValue) -> None:
        nonlocal lock
        if not lock:
            lock = True
            adapter.apply_value(widget, value)
            lock = False

    # Widget → Model
    adapter.listen_to_change(widget, update_model)

    # Model → Widget
    observable.on_change(update_ui)

    # Initial sync
    update_ui(observable.get())
```

**Pros:**
- Automatic bidirectional sync
- Lock prevents infinite loops
- Initial value sync

**Cons:**
- No batching of rapid changes
- Memory leak potential if not cleaned up

---

### Nested Path Binding

**Purpose:** Bind to deeply nested properties with optional chaining.

**File:** `DRAFT/more_recent_drafting/qtpie/qtpie/types.py` (uses `ObservableProxy.observable_for_path()`)

**Syntax:**
```python
# Simple nesting
txt_city: QLineEdit = make(QLineEdit, bind="address.city")

# Optional chaining (won't error if address is None)
txt_city: QLineEdit = make(QLineEdit, bind="address?.city")

# Deep nesting
txt_zip: QLineEdit = make(QLineEdit, bind="user?.address?.zip_code")
```

**How it works:**
- Parses path into segments: `"address?.city"` → `[("address", True), ("city", False)]`
- Creates nested `ObservableProxy` for each level
- Subscribes to parent changes to update when structure changes
- Returns `None` if any optional segment is `None`

**Pros:**
- Elegant nested data binding
- Safe navigation with `?.`
- Reactive to parent object changes

**Cons:**
- Complex implementation
- Performance overhead for deep paths
- Debugging can be difficult

---

## Styling System

### CSS Classes on Widgets

**Purpose:** Add/remove CSS-like classes on Qt widgets for QSS styling.

**Files:**
- `DRAFT/more_recent_drafting/qtpie/qtpie/styles/style_class.py`
- `DRAFT/other_drafting/qtpie/styles.py`
- `DRAFT/drafting/qtpie/styles/classes.py`

**Implementation:**
Classes are stored as a Qt dynamic property named `"class"`:

```python
class QtStyleClass:
    @staticmethod
    def get_classes(obj: QObject) -> list[str]:
        classes = obj.property("class")
        return classes if isinstance(classes, list) else []

    @staticmethod
    def set_classes(obj: QObject, classes: list[str]) -> None:
        obj.setProperty("class", classes)
        if isinstance(obj, QWidget):
            obj.style().unpolish(obj)
            obj.style().polish(obj)  # Reapply styles

    @staticmethod
    def add_class(obj: QObject, class_name: str) -> None: ...

    @staticmethod
    def remove_class(obj: QObject, class_name: str) -> None: ...

    @staticmethod
    def toggle_class(obj: QObject, class_name: str) -> None: ...

    @staticmethod
    def replace_class(obj: QObject, old: str, new: str) -> None: ...

    @staticmethod
    def has_class(obj: QObject, class_name: str) -> bool: ...
```

**QSS Usage:**
```scss
/* Target widgets with class "primary" */
QPushButton[class~="primary"] {
    background-color: #007bff;
    color: white;
}

/* Target widgets with class "danger" */
QPushButton[class~="danger"] {
    background-color: #dc3545;
}

/* Multiple classes */
QWidget[class~="card"][class~="shadow"] {
    border: 1px solid #ddd;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}
```

**Widget Base Class Methods:**
```python
class Widget:
    def add_class(self, class_name: str) -> None: ...
    def remove_class(self, class_name: str) -> None: ...
    def toggle_class(self, class_name: str) -> None: ...
    def replace_class(self, old: str, new: str) -> None: ...
```

**Pros:**
- Familiar CSS-like pattern
- Dynamic class changes reapply styles
- Multiple classes per widget

**Cons:**
- QSS attribute selector syntax is verbose (`[class~="name"]`)
- Performance cost of unpolish/polish on every change

---

### Object Names for QSS

**Purpose:** Use Qt object names for #id-style selectors in QSS.

**Automatic Naming:**
```python
@widget(name="UserEditor")  # Explicit
class UserEditor(QWidget, Widget): ...

@widget  # Auto-generates name from class
class AnimalWidget(QWidget, Widget):  # objectName = "Animal" (strips "Widget" suffix)
    pass
```

**QSS Usage:**
```scss
#UserEditor {
    background-color: white;
}

#saveButton {
    font-weight: bold;
}
```

---

### SCSS Compilation & Live Reload

**Purpose:** Write styles in SCSS, compile to QSS, hot-reload during development.

**Files:**
- `DRAFT/more_recent_drafting/qtpie/qtpie/styles/stylesheet.py`
- `DRAFT/other_drafting/qtpie/styles.py`

**Configuration:**
```python
app = App(name="My App", dark_mode=True)
app.set_styles(
    watch=True,                    # Enable live reload
    scss_path="./styles.scss",     # Main SCSS file
    qss_path="./styles.qss",       # Output QSS file
    watch_folders=["./themes"],    # Additional folders to watch
)
```

**How it works:**
```python
@dataclass
class StylesheetWatcher:
    app: QApplication
    config: StyleConfiguration
    _qss_watcher: QFileSystemWatcher

    def __post_init__(self):
        self._qss_watcher.fileChanged.connect(self._on_file_change)
        self._qss_watcher.addPath(self.config.scss_path)

    def _on_file_change(self):
        qss = self._rebuild_qss()
        write_file(self.config.qss_path, qss)
        self.app.setStyleSheet(qss)

    def _rebuild_qss(self) -> str:
        # Compile SCSS to CSS
        qss = sass.compile(filename=self.config.scss_path)

        # Transform data-attributes: [data-state="active"] → [state="active"]
        qss = re.sub(r"\[([^\]]+)=", self._attribute_replacer, qss)

        return f"/* Generated - DO NOT EDIT */\n\n{qss}"
```

**SCSS Features Supported:**
- Variables: `$primary-color: #007bff;`
- Nesting: `QPushButton { &:hover { ... } }`
- Imports: `@import "variables";`
- Mixins: `@mixin card { ... }`

**Pros:**
- Real SCSS with variables, nesting, mixins
- Live reload for rapid iteration
- Compiled output for production

**Cons:**
- Requires `sass` or `scss` Python package
- Some CSS features don't work in QSS
- File watcher can miss rapid changes

---

## Layout System

### Automatic Layout Population

**Purpose:** Child widgets declared as fields are automatically added to the parent's layout.

**How it works:**
```python
# In @widget decorator's __init__:
if add_widgets_to_layout:
    type_hints = get_type_hints(self.__class__)
    for field in fields(self.__class__):
        if field.name.startswith("_"):
            continue  # Skip private fields

        field_type = type_hints.get(field.name)
        if isinstance(field_type, type) and issubclass(field_type, QWidget):
            widget_instance = getattr(self, field.name)
            if _box_layout is not None:
                _box_layout.addWidget(widget_instance)
            elif isinstance(_layout, QFormLayout):
                label = widget_instance.property("form_field_name")
                _layout.addRow(label, widget_instance)
            elif isinstance(_layout, QGridLayout):
                # Use GridPosition from metadata
                ...
```

**Field Order = Layout Order:**
```python
@widget(layout="vertical")
class MyWidget(QWidget, Widget):
    header: QLabel = make(QLabel, "Header")      # Added first (top)
    content: QTextEdit = make(QTextEdit)          # Added second (middle)
    footer: QPushButton = make(QPushButton, "OK") # Added third (bottom)
```

**Skipping Fields:**
- Prefix with `_` to exclude from layout: `_helper: QTimer = make(QTimer)`
- Exception: `_stretch` fields add stretch to box layouts

---

### Grid Layout with GridPosition

**Purpose:** Explicit row/column positioning for grid layouts.

**File:** `DRAFT/drafting/qtpie/factories/grid_position.py`

```python
@dataclass(frozen=True)
class GridPosition:
    row: int
    col: int
    rowspan: int = 1
    colspan: int = 1
```

**Example:**
```python
@widget(layout="grid")
class LoginForm(QWidget, Widget):
    lbl_user: QLabel = grid_item(GridPosition(0, 0), QLabel, "Username:")
    txt_user: QLineEdit = grid_item(GridPosition(0, 1), QLineEdit)

    lbl_pass: QLabel = grid_item(GridPosition(1, 0), QLabel, "Password:")
    txt_pass: QLineEdit = grid_item(GridPosition(1, 1), QLineEdit)

    btn_login: QPushButton = grid_item(
        GridPosition(2, 0, colspan=2),  # Spans both columns
        QPushButton, "Login"
    )
```

---

### Form Layout Support

**Purpose:** Automatic label-widget pairs for forms.

**Two approaches:**

**1. Using `make_form_row()`:**
```python
@widget(layout="form")
class UserForm(QWidget, Widget):
    txt_name: QLineEdit = make_form_row("Name:", QLineEdit)
    txt_email: QLineEdit = make_form_row("Email:", QLineEdit)
```

**2. Using object name as label:**
```python
@widget(layout="form")
class UserForm(QWidget, Widget):
    Name: QLineEdit = make(QLineEdit)   # Object name "Name" becomes label
    Email: QLineEdit = make(QLineEdit)  # Object name "Email" becomes label
```

**Auto-adds "form" class:**
```python
if layout == "form":
    QtStyleClass.add_class(self, "form")
```

---

### Stretch Support

**Purpose:** Add stretch/spacers to box layouts.

**Convention:** Fields starting with `_stretch` are treated as stretch values:

```python
@widget(layout="vertical")
class MyWidget(QWidget, Widget):
    header: QLabel = make(QLabel, "Header")
    _stretch1: int = 1                        # Adds stretch(1)
    content: QTextEdit = make(QTextEdit)
    _stretch2: int = 0                        # Adds stretch(0) - just a spacer
    footer: QPushButton = make(QPushButton, "OK")
```

**Implementation:**
```python
elif issubclass(field_type, int) and field.name.startswith("_stretch"):
    stretch = getattr(self, field.name, 0)
    if _box_layout is not None:
        _box_layout.addStretch(stretch)
```

---

## Signal & Event Handling

### Signal Connection in make()

**Purpose:** Connect Qt signals to methods directly in `make()` calls.

**File:** `DRAFT/more_recent_drafting/qtpie/qtpie/decorators/widget.py`

**Syntax:**
```python
# Method name as string
btn: QPushButton = make(QPushButton, "Click", clicked="on_button_clicked")

# Lambda function
btn: QPushButton = make(QPushButton, "Click", clicked=lambda: print("Clicked!"))

# Multiple signals
slider: QSlider = make(
    QSlider,
    valueChanged="on_value_changed",
    sliderReleased="on_slider_released"
)
```

**How it works:**
```python
# In make():
for key, value in kwargs.items():
    if isinstance(value, str) or callable(value):
        potential_signals[key] = value  # Might be signal or property
    else:
        widget_kwargs[key] = value  # Definitely a property

# In @widget __init__:
for attr_name, handler in potential_signals.items():
    attr = getattr(widget_instance, attr_name, None)
    if attr is not None and hasattr(attr, "connect"):
        # It's a signal
        if isinstance(handler, str):
            method = getattr(self, handler)
            attr.connect(method)
        elif callable(handler):
            attr.connect(handler)
    else:
        # It's a property - try to set it
        setter = getattr(widget_instance, f"set{attr_name[0].upper()}{attr_name[1:]}", None)
        if setter:
            setter(handler)
```

**Pros:**
- Very concise
- Keeps signal connections near widget definition
- Supports both method names and lambdas

**Cons:**
- Heuristic can fail (string properties vs signals)
- Error messages may be confusing if method not found

---

### Signal Typing Utilities

**Purpose:** Help type checkers understand Qt signal connections.

**File:** `DRAFT/other_drafting/qtpie/signal_typing.py`

**Protocols:**
```python
class BoolSignalHandler(Protocol):
    def __call__(self, checked: bool) -> None: ...

class VoidSignalHandler(Protocol):
    def __call__(self) -> None: ...

class IntSignalHandler(Protocol):
    def __call__(self, value: int) -> None: ...
```

**Cast Helpers:**
```python
def as_bool_handler(func: Callable[[bool], None]) -> BoolSignalHandler:
    return cast(BoolSignalHandler, func)

def as_void_handler(func: Callable[[], None]) -> VoidSignalHandler:
    return cast(VoidSignalHandler, func)

def as_int_handler(func: Callable[[int], None]) -> IntSignalHandler:
    return cast(IntSignalHandler, func)
```

**Usage:**
```python
# Without helper - Pylance may complain
button.clicked.connect(lambda checked: self.on_click(checked))

# With helper - Pylance is happy
button.clicked.connect(as_bool_handler(lambda checked: self.on_click(checked)))

# For void signals
timer.timeout.connect(as_void_handler(self.on_timeout))
```

**Pros:**
- Satisfies strict type checkers
- Self-documenting signal signatures

**Cons:**
- Extra verbosity
- Might hide real type errors

---

## Application Infrastructure

### App Class

**Purpose:** Extended `QApplication` with convenience features.

**File:** `DRAFT/more_recent_drafting/qtpie/qtpie/app.py`

```python
class App(QApplication):
    def __init__(
        self,
        name: str = "Application",
        version: str = "1.0.0",
        light_mode: bool = False,
        dark_mode: bool = False,
        styles: StyleConfiguration | None = None,
    ) -> None:
        if dark_mode:
            os.environ["QT_QPA_PLATFORM"] = "windows:darkmode=2"
        elif light_mode:
            os.environ["QT_QPA_PLATFORM"] = "windows:darkmode=0"

        super().__init__()
        self.setApplicationName(name)
        self.setApplicationVersion(version)
        self._styles = styles or StyleConfiguration()

    def set_styles(
        self,
        watch: bool = False,
        scss_path: str | None = None,
        qss_path: str | None = None,
        qss_resource: str | None = None,
        watch_folders: list[str] | None = None,
    ) -> None:
        self._styles = StyleConfiguration(...)

    def run(self) -> None:
        run_app(self, styles=self._styles)
```

**Usage:**
```python
app = App(name="Animal Manager", version="1.0.0", dark_mode=True)
app.set_styles(watch=True, scss_path="./styles.scss", qss_path="./styles.qss")

window = MainWindow()
window.show()
app.run()
```

---

### run_app()

**Purpose:** Start the application event loop with async support.

**Files:**
- `DRAFT/more_recent_drafting/qtpie/qtpie/startup.py`
- `DRAFT/other_drafting/qtpie/run_app.py`

```python
import asyncio
import qasync

app_close_event = asyncio.Event()

def run_app(
    app: QApplication,
    styles: StyleConfiguration | None = None,
) -> None:
    if styles:
        if styles.watch:
            watch_qss(app, config=styles)
        elif styles.qss_resource_path:
            app.setStyleSheet(read_file(styles.qss_resource_path))

    app.aboutToQuit.connect(app_close_event.set)
    event_loop = qasync.QEventLoop(app)
    asyncio.set_event_loop(event_loop)
    with event_loop:
        event_loop.run_until_complete(app_close_event.wait())
```

**Features:**
- Integrates Qt event loop with asyncio via `qasync`
- Enables `async/await` in Qt applications
- Proper cleanup on quit

---

### Development Mode

**Purpose:** Different behavior for development vs production.

**File:** `DRAFT/other_drafting/qtpie/run_app.py`

```python
def run_app(
    app: QApplication,
    development_mode: bool = False,
    styles_qss_resource: str | None = None,      # Production: embedded resource
    styles_qss_local_path: str | None = None,    # Development: local file
    main_scss_local_path: str | None = None,     # Development: SCSS source
) -> None:
    if development_mode:
        if main_scss_local_path and styles_qss_local_path:
            watch_qss(app, main_scss=main_scss_local_path, out_qss=styles_qss_local_path)
    else:
        if styles_qss_resource:
            app.setStyleSheet(read_file(styles_qss_resource))
```

**Usage:**
```python
run_app(
    app,
    development_mode=os.environ.get("DEV_MODE") == "1",
    styles_qss_resource=":/styles/app.qss",
    styles_qss_local_path="./build/styles.qss",
    main_scss_local_path="./src/styles/main.scss",
)
```

---

## Dock System

### TabbedDocksMainWindow

**Purpose:** A `QMainWindow` subclass with enhanced docking features.

**File:** `DRAFT/other_drafting/qtpie/tabbed_docks_main_window.py`

**Features:**
- Tab-based dock organization with closable/movable tabs
- Drag-to-undock: drag a tab outside the tab bar to float it
- Auto-hide title bars when docks are tabified
- Proper title bar restoration when undocked

```python
class TabbedDocksMainWindow(QMainWindow):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._docked_widgets: list[QDockWidget] = []
        self.setDockNestingEnabled(True)
        self.setTabPosition(Qt.DockWidgetArea.AllDockWidgetAreas, QTabWidget.TabPosition.North)

    def dock(
        self,
        widget: QWidget,
        area: Qt.DockWidgetArea,
        title: str | None = None,
        allowed_areas: Qt.DockWidgetArea = Qt.DockWidgetArea.AllDockWidgetAreas,
        features: QDockWidget.DockWidgetFeature = ...,
    ) -> QDockWidget:
        dock = self._make_dock(widget, title, allowed_areas, features)
        self.addDockWidget(area, dock)
        return dock

    def hide_titlebar(self, dock_widget: QDockWidget) -> None:
        hidden = QWidget()
        hidden.setFixedHeight(0)
        dock_widget.setTitleBarWidget(hidden)

    def show_titlebar(self, dock_widget: QDockWidget) -> None:
        dock_widget.setTitleBarWidget(None)
```

**Drag-to-undock implementation:**
```python
def eventFilter(self, watched: QObject, event: QEvent) -> bool:
    if isinstance(watched, QTabBar):
        if event.type() == QEvent.Type.MouseMove:
            mouse_event = cast(QMouseEvent, event)
            margin = 50
            padded = tab_bar.rect().adjusted(-margin, -margin, margin, margin)
            if not padded.contains(mouse_event.pos()):
                self._undock_tab(self._drag_tab_text)
```

---

### DockManager

**Purpose:** Composition-based dock management (vs inheritance).

**File:** `DRAFT/other_drafting/dock_manager.py`

```python
class IDockManager(ABC):
    @abstractmethod
    def dock(self, widget, area, title=None, ...) -> QDockWidget: ...
    @abstractmethod
    def hide_titlebar(self, dock_widget) -> None: ...
    @abstractmethod
    def show_titlebar(self, dock_widget) -> None: ...
    @abstractmethod
    def get_docked_widgets(self) -> list[QDockWidget]: ...

@dataclass
class DockManager(IDockManager):
    main_window: QMainWindow
    docked_widgets: list[QDockWidget] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.main_window.setDockNestingEnabled(True)
        self.main_window.setTabPosition(...)

def get_dock_manager(main_window: QMainWindow) -> IDockManager:
    return DockManager(main_window)
```

**Usage:**
```python
class MyMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.dock_manager = get_dock_manager(self)

        self.dock_manager.dock(EditorWidget(), Qt.DockWidgetArea.LeftDockWidgetArea)
        self.dock_manager.dock(PropertiesWidget(), Qt.DockWidgetArea.RightDockWidgetArea)
```

**Pros:**
- Doesn't require inheritance
- Clear interface
- Testable

**Cons:**
- Requires forwarding event methods

---

### DockTitleBar

**Purpose:** Custom title bar for floating docks with Windows 11-style behavior.

**File:** `DRAFT/other_drafting/qtpie/widgets/dock_title_bar.py`

**Features:**
- Double-click maximizes/restores floating dock
- Drag to move
- Windows 11-style close button (red on hover)
- Syncs with dock's window title

```python
class DockTitleBar(QWidget):
    close_requested = Signal()

    def __init__(self, dock_widget: QDockWidget, parent=None):
        super().__init__(parent)
        self._dock_widget = dock_widget
        self._is_maximized = False
        self._normal_geometry = None

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._toggle_maximize()

    def _toggle_maximize(self):
        if self._is_maximized:
            self._dock_widget.setGeometry(self._normal_geometry)
            self._is_maximized = False
        else:
            self._normal_geometry = self._dock_widget.geometry()
            screen = self._dock_widget.screen()
            self._dock_widget.setGeometry(screen.availableGeometry())
            self._is_maximized = True
```

---

## Utility Functions

### Colored SVG

**Purpose:** Load SVG files and replace `currentColor` with a specific color.

**File:** `DRAFT/other_drafting/qtpie/svg.py`

```python
def colored_svg(svg_path: str, color: QColor, size: QSize) -> QPixmap:
    svg_data = read_file(svg_path)

    # Replace 'currentColor' with hex color
    color_hex = color.name(QColor.NameFormat.HexRgb)
    svg_data = svg_data.replace("currentColor", color_hex)

    # Render to pixmap
    renderer = QSvgRenderer(QByteArray(svg_data.encode("utf-8")))
    pixmap = QPixmap(size)
    pixmap.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pixmap)
    renderer.render(painter)
    painter.end()

    return pixmap
```

**Usage:**
```python
# For themeable icons that respect app color scheme
icon = colored_svg(":/icons/save.svg", QColor("#ffffff"), QSize(24, 24))
button.setIcon(QIcon(icon))

# Or use palette colors
icon = colored_svg(":/icons/save.svg", palette.color(QPalette.ColorRole.Text), QSize(24, 24))
```

**Pros:**
- Single SVG works with any color scheme
- Runtime color changes
- Standard SVG `currentColor` convention

**Cons:**
- Requires SVGs using `currentColor`
- Re-renders on every call (consider caching)

---

### Screen Centering

**Purpose:** Center a widget on its screen.

**File:** `DRAFT/other_drafting/qtpie/screen.py`

```python
def center_on_screen(widget: QWidget):
    screen = widget.screen()
    screen_geometry = screen.geometry()
    window_geometry = widget.geometry()

    x = screen_geometry.x() + (screen_geometry.width() - window_geometry.width()) // 2
    y = screen_geometry.y() + (screen_geometry.height() - window_geometry.height()) // 2

    widget.setGeometry(x, y, window_geometry.width(), window_geometry.height())
```

**Usage:**
```python
window = MainWindow()
window.show()
center_on_screen(window)
```

---

### File Utilities

**Purpose:** Simple file read/write helpers.

**File:** `DRAFT/more_recent_drafting/qtpie/qtpie/files.py` (referenced but not shown)

```python
def read_file(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def write_file(path: str, content: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
```

---

## Pre-built Widgets

### FilterableDropdown

**Purpose:** A searchable dropdown with popup list.

**File:** `DRAFT/other_drafting/qtpie/widgets/filterable_dropdown.py`

**Features:**
- Type to filter options
- Keyboard navigation (Up/Down/Enter/Escape)
- Popup closes on outside click
- Popup shows on focus

```python
@widget(classes=["filterable-dropdown"])
class FilterableDropdown(QWidget, Widget):
    line_edit: QLineEdit = make(QLineEdit)

    _model: QStringListModel = make(QStringListModel)
    _proxy: QSortFilterProxyModel = make(QSortFilterProxyModel)
    _popup_frame: QFrame = make(QFrame)
    _list_view: QListView = make(QListView)
    _current_index: int = 0

    def set_items(self, items: list[str]) -> None:
        self._model.setStringList(items)

    def set_placeholder_text(self, text: str) -> None:
        self.line_edit.setPlaceholderText(text)
```

**Usage:**
```python
dropdown = FilterableDropdown()
dropdown.set_items(["Apple", "Banana", "Cherry", "Date", "Elderberry"])
dropdown.set_placeholder_text("Search fruits...")
```

---

### AutoHeightTextEdit

**Purpose:** A text edit that grows with content.

**File:** `DRAFT/other_drafting/qtpie/widgets/auto_height_text_edit.py`

```python
@widget(layout="none", classes=["text-edit"])
class AutoHeightTextEdit(QTextEdit, Widget):
    def setup(self) -> None:
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.document().setDocumentMargin(0)
        self.document().contentsChanged.connect(self._adjust_height)
        self._adjust_height()

    def _adjust_height(self) -> None:
        text = self.toPlainText()
        font_metrics = QFontMetrics(self.font())
        line_height = font_metrics.height()
        visible_lines = text.count("\n") + 1 if text else 1
        margins = self.contentsMargins().top() + self.contentsMargins().bottom()
        height = (visible_lines * line_height) + margins
        self.setFixedHeight(height)
```

---

## Metadata & Configuration

### WidgetFactoryProperties

**Purpose:** Store styling/layout metadata on widgets via Qt properties.

**File:** `DRAFT/drafting/qtpie/factories/widget_factory_properties.py`

```python
WIDGET_FACTORY_PROPERTIES_PROPERTY_NAME = "widgetFactoryProperties"

@dataclass(frozen=True)
class WidgetFactoryProperties:
    object_name: str | None = None
    class_names: list[str] | None = None
    form_field_label: str | None = None
    grid_position: GridPosition | None = None

    @staticmethod
    def set(obj: QObject, properties: WidgetFactoryProperties) -> None:
        obj.setProperty(WIDGET_FACTORY_PROPERTIES_PROPERTY_NAME, properties)

    @staticmethod
    def get(obj: QObject) -> WidgetFactoryProperties | None:
        return obj.property(WIDGET_FACTORY_PROPERTIES_PROPERTY_NAME)
```

**Comparison with Field Metadata:**

| Approach | WidgetFactoryProperties | Field Metadata |
|----------|------------------------|----------------|
| Storage | Qt property on widget | dataclass field metadata |
| Access | Any code with widget reference | Only during @widget init |
| Non-dataclass widgets | ✅ Works | ❌ Doesn't work |
| Type safety | Less (dynamic property) | More (typed dict) |

---

### Global Configuration

**Purpose:** Configure QtPie behavior globally.

**File:** `DRAFT/drafting/qtpie/config.py`

```python
@dataclass
class QtPieConfiguration:
    all_decorators_dataclass_transformer: bool = True
    widget_decorator_dataclass_transformer: bool | None = None

_qtpie_configuration = QtPieConfiguration()

def qtpie_configuration() -> QtPieConfiguration:
    return _qtpie_configuration

def configure_qtpie(
    *,
    widget_decorator_dataclass_transformer: bool | None = None,
    all_decorators_dataclass_transformer: bool | None = None,
) -> None:
    config = qtpie_configuration()
    if widget_decorator_dataclass_transformer is not None:
        config.widget_decorator_dataclass_transformer = widget_decorator_dataclass_transformer
    # ... etc
```

**Potential settings:**
- `dataclass_transformer` - Whether `@widget` applies `@dataclass`
- `default_layout` - Default layout type
- `auto_object_names` - Whether to auto-generate object names
- `strip_widget_suffix` - Whether to strip "Widget" from auto-generated names

---

## Base Classes & Mixins

### Widget Base Class

**Purpose:** Provide lifecycle hooks and utility methods for all widgets.

**File:** `DRAFT/more_recent_drafting/qtpie/qtpie/types.py`

```python
class Widget:
    # Lifecycle hooks (override in subclasses)
    def setup(self) -> None: pass
    def setup_values(self) -> None: pass
    def setup_bindings(self) -> None: pass
    def setup_layout(self, layout: QLayout) -> None: pass
    def setup_box_layout(self, layout: QBoxLayout) -> None: pass
    def setup_styles(self) -> None: pass
    def setup_events(self) -> None: pass
    def setup_signals(self) -> None: pass

    # Utility methods
    def add_class(self, class_name: str) -> None: ...
    def remove_class(self, class_name: str) -> None: ...
    def toggle_class(self, class_name: str) -> None: ...
    def replace_class(self, old: str, new: str) -> None: ...

    def add_widget(self, widget: QWidget) -> None:
        """Add widget to this widget's layout."""
        ...

    def remove_widget(self, widget: QWidget) -> None:
        """Remove widget from this widget's layout."""
        ...
```

---

### ModelWidget

**Purpose:** Base class for widgets that display/edit a data model.

```python
@dataclass
class ModelWidget(Widget, Generic[T]):
    _bound_widget_model: WidgetModel[T] | None = None

    @property
    def model(self) -> WidgetModel[T] | None:
        return self._bound_widget_model

    def set_model(self, model: T) -> None:
        self._bound_widget_model = WidgetModel(model)
        self._auto_bind_fields()
        self.setup_model(self._bound_widget_model)

    def setup_model(self, model: WidgetModel[T]) -> None:
        """Override to react to model changes."""
        pass

    def teardown_model(self, model: WidgetModel[T]) -> None:
        """Override to clean up when model is removed."""
        pass

    def reset_model(self) -> None:
        self._bound_widget_model = None
```

---

### WidgetModel

**Purpose:** Wrap a data object with reactive proxy.

```python
class WidgetModel(Generic[T]):
    def __init__(self, obj: T):
        self._object = obj
        self._proxy = ObservableProxy(self._object, sync=True)

    @property
    def value(self) -> T:
        """The raw data object."""
        return self._object

    @property
    def proxy(self) -> ObservableProxy[T]:
        """Reactive proxy for bindings."""
        return self._proxy
```

---

### Action Base Class

**Purpose:** Base class for action classes used with `@action`.

```python
class Action:
    def action(self, checked: bool) -> None:
        """Override to define action behavior."""
        pass
```

---

## Comprehensive Feature Matrix

| Feature | other_drafting | more_recent_drafting | drafting |
|---------|---------------|---------------------|----------|
| **Decorators** | | | |
| `@widget` | ✅ | ✅ | ✅ |
| `@widget_class` | ❌ | ❌ | ✅ |
| `@window` | ✅ | ✅ | ❌ |
| `@menu` | ✅ | ❌ | ❌ |
| `@action` | ✅ | ❌ | ❌ |
| `@entry_point` | ❌ | ❌ | ✅ |
| **Factories** | | | |
| `make()` | ✅ | ✅ | ✅ |
| `make_widget()` | ✅ | ✅ | ❌ |
| `make_form_row()` | ✅ | ✅ | ✅ |
| `grid_item()` | ❌ | ❌ | ✅ |
| Tuple syntax | ❌ | ❌ | ✅ |
| **Data Binding** | | | |
| Observable integration | ✅ (basic) | ✅ (full) | ❌ |
| Binding registry | ✅ | ✅ | ❌ |
| `bind=` in make() | ❌ | ✅ | ❌ |
| Nested path binding | ❌ | ✅ | ❌ |
| Optional chaining (`?.`) | ❌ | ✅ | ❌ |
| **Layout** | | | |
| Horizontal/Vertical | ✅ | ✅ | ✅ |
| Form layout | ✅ | ✅ | ✅ |
| Grid layout | ❌ | ❌ | ✅ |
| Auto-population | ✅ | ✅ | ✅ |
| Stretch support | ✅ | ✅ | ❌ |
| **Styling** | | | |
| CSS classes | ✅ | ✅ | ✅ |
| Object names | ✅ | ✅ | ✅ |
| SCSS compilation | ✅ | ✅ | ❌ |
| Live reload | ✅ | ✅ | ❌ |
| **Signals** | | | |
| Signal in make() | ❌ | ✅ | ❌ |
| Signal typing utils | ✅ | ❌ | ❌ |
| **Infrastructure** | | | |
| App class | ❌ | ✅ | ❌ |
| run_app() | ✅ | ✅ | ❌ |
| Async support | ✅ | ✅ | ❌ |
| Development mode | ✅ | ❌ | ❌ |
| **Dock System** | | | |
| TabbedDocksMainWindow | ✅ | ❌ | ❌ |
| DockManager | ✅ | ❌ | ❌ |
| DockTitleBar | ✅ | ❌ | ❌ |
| **Utilities** | | | |
| Colored SVG | ✅ | ❌ | ❌ |
| Screen centering | ✅ | ❌ | ❌ |
| **Widgets** | | | |
| FilterableDropdown | ✅ | ❌ | ❌ |
| AutoHeightTextEdit | ✅ | ❌ | ❌ |
| **Metadata** | | | |
| WidgetFactoryProperties | ❌ | ❌ | ✅ |
| Field metadata | ❌ | ✅ | ❌ |
| Global config | ❌ | ❌ | ✅ |
| **Dependencies** | | | |
| Uses `attrs` | ✅ | ❌ | ❌ |
| Uses `observant` | ✅ | ✅ | ❌ |
| Uses `qasync` | ✅ | ✅ | ❌ |

---

## Recommendations for Final Implementation

### Must Have (Core)

1. **`@widget` decorator** - Unified version that handles dataclass/non-dataclass
2. **`@window` decorator** - For main windows
3. **`make()` factory** - With binding AND signal connection
4. **CSS classes system** - `QtStyleClass` with all methods
5. **Binding registry** - With default bindings for common widgets
6. **SCSS compilation** - With live reload option
7. **`Widget` base class** - With lifecycle hooks
8. **`ModelWidget` base class** - With reactive binding support

### Should Have (Important)

1. **`@menu` and `@action` decorators** - Declarative menus
2. **Grid layout support** - With `GridPosition`
3. **Form layout support** - With `make_form_row()`
4. **Signal typing utilities** - For type safety
5. **`App` class** - With dark mode, styling config
6. **Nested path binding** - With optional chaining
7. **Global configuration** - For customization

### Nice to Have (Polish)

1. **Dock system** - TabbedDocksMainWindow, DockManager
2. **Pre-built widgets** - FilterableDropdown, AutoHeightTextEdit
3. **Colored SVG utility** - For themeable icons
4. **Screen utilities** - Centering, etc.
5. **`@entry_point`** - For quick scripts
6. **Development mode** - Explicit dev vs prod

### Architecture Decisions

1. **Use standard `dataclasses`** not `attrs` - More common, less dependency
2. **Use field metadata** for binding info - Better type safety
3. **Also support Qt properties** for non-dataclass widgets
4. **Single `@widget` decorator** - Auto-detect dataclass situation
5. **Async-first with `qasync`** - Modern Python patterns
6. **Test-driven development** - Start with tests for each feature

### File Structure Suggestion

```
qtpie/
├── __init__.py
├── app.py                    # App class, run_app
├── decorators/
│   ├── __init__.py
│   ├── widget.py             # @widget
│   ├── window.py             # @window
│   ├── menu.py               # @menu
│   └── action.py             # @action
├── factories/
│   ├── __init__.py
│   ├── make.py               # make(), make_later()
│   ├── make_widget.py        # make_widget(), make_form_row()
│   └── grid.py               # grid_item(), GridPosition
├── bindings/
│   ├── __init__.py
│   ├── registry.py           # BindingRegistry, register_binding()
│   ├── bind.py               # bind()
│   └── defaults.py           # Default bindings
├── styles/
│   ├── __init__.py
│   ├── classes.py            # QtStyleClass
│   └── scss.py               # SCSS compilation, watcher
├── types/
│   ├── __init__.py
│   ├── widget.py             # Widget base class
│   ├── model_widget.py       # ModelWidget, WidgetModel
│   └── action.py             # Action base class
├── signals/
│   ├── __init__.py
│   └── typing.py             # Signal typing utilities
├── utils/
│   ├── __init__.py
│   ├── svg.py                # colored_svg()
│   ├── screen.py             # center_on_screen()
│   └── files.py              # read_file(), write_file()
├── docks/
│   ├── __init__.py
│   ├── tabbed_main_window.py
│   ├── manager.py
│   └── title_bar.py
└── widgets/
    ├── __init__.py
    ├── filterable_dropdown.py
    └── auto_height_text_edit.py
```

---

*This document serves as the comprehensive reference for building the final QtPie library. Each feature has been analyzed for its merits and potential issues. The next step is to implement these features with proper test coverage, starting with the core decorators and factories.*
