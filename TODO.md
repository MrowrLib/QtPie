# QtPie Development Roadmap

## Phase 1: Core Foundation ✅ COMPLETE

**Goal**: Establish the fundamental `@widget` decorator and `make()` factory.

### Accomplished

- [x] `@widget` decorator with `@dataclass_transform()` for type safety
- [x] `@widget` works with AND without parentheses
- [x] `layout` parameter: `"vertical"` | `"horizontal"` | `"none"`
- [x] Auto-add child QWidget fields to layout (in declaration order)
- [x] Skip `_private` fields from layout
- [x] `name` parameter for objectName (auto-generates from class name, strips "Widget" suffix)
- [x] `classes` parameter for CSS-like styling (stored as Qt property)
- [x] Lifecycle hooks: `setup()`, `setup_values()`, `setup_bindings()`, `setup_layout()`, `setup_styles()`, `setup_events()`, `setup_signals()`
- [x] `make()` factory function (cleaner than `field(default_factory=...)`)
- [x] `make()` positional args passed to constructor
- [x] `make()` kwargs: signals (string/callable) vs properties (other values)
- [x] Signal connections by method name string
- [x] Signal connections by lambda/callable
- [x] Python 3.13 type parameter syntax (`def widget[T](...)`)
- [x] 30 tests passing
- [x] 0 pyright errors (strict mode)
- [x] 0 ruff errors

### Files Created

```
lib/qtpie/
├── __init__.py
├── decorators/
│   ├── __init__.py
│   └── widget.py
└── factories/
    ├── __init__.py
    └── make.py

tests/unit/
├── __init__.py
├── test_widget_decorator.py
└── test_make_factory.py
```

---

## Phase 2: Layout Extensions ✅ COMPLETE

**Goal**: Add form and grid layout support for richer UI composition.

### Accomplished

- [x] `layout="form"` creates QFormLayout
- [x] `form_label` parameter in `make()` for form row labels
- [x] `layout="grid"` creates QGridLayout
- [x] `grid` parameter in `make()` for positioning: `(row, col)` or `(row, col, rowspan, colspan)`
- [x] `stretch()` factory for spacers in box layouts
- [x] Auto-add "form" class to form layout widgets

### API Design

```python
# Form Layout
@widget(layout="form")
class PersonForm(QWidget):
    name: QLineEdit = make(QLineEdit, form_label="Full Name")
    email: QLineEdit = make(QLineEdit, form_label="Email Address")
    age: QSpinBox = make(QSpinBox, form_label="Age")

# Grid Layout
@widget(layout="grid")
class Calculator(QWidget):
    display: QLineEdit = make(QLineEdit, grid=(0, 0, 1, 4))
    btn_7: QPushButton = make(QPushButton, "7", grid=(1, 0))
    btn_8: QPushButton = make(QPushButton, "8", grid=(1, 1))
    btn_9: QPushButton = make(QPushButton, "9", grid=(1, 2))
    btn_plus: QPushButton = make(QPushButton, "+", grid=(1, 3, 2, 1))  # spans 2 rows

# Stretch in Box Layouts
@widget(layout="vertical")
class ToolPanel(QWidget):
    toolbar: QWidget = make(QWidget)
    spacer: QSpacerItem = stretch(1)  # pushes content to bottom
    content: QWidget = make(QWidget)
```

---

## Phase 3: @window Decorator ✅ COMPLETE

**Goal**: Declarative QMainWindow with common window setup.

### Accomplished

- [x] `@window` decorator for QMainWindow subclasses
- [x] `@window` works with AND without parentheses
- [x] `title` parameter for window title
- [x] `size` parameter: `(width, height)`
- [x] `icon` parameter: path to icon file
- [x] `center` parameter: center on screen
- [x] Auto-set `central_widget` field as central widget
- [x] Auto-add QMenu fields to menu bar
- [x] Same lifecycle hooks as @widget
- [x] Auto-generate objectName (strips "Window" suffix)
- [x] 19 new tests (67 total)
- [x] 0 pyright errors (strict mode)
- [x] 0 ruff errors

### API Design

```python
@window(title="My Application", size=(1024, 768), center=True)
class MainWindow(QMainWindow):
    central_widget: QTextEdit = make(QTextEdit)
    file_menu: QMenu = field(default_factory=lambda: QMenu("&File"))

    def setup(self) -> None:
        self.statusBar().showMessage("Ready")
```

---

## Phase 4: @menu / @action Decorators ✅ COMPLETE

**Goal**: Declarative menu bars and actions.

### Accomplished

- [x] `@menu` decorator for QMenu subclasses
- [x] `@action` decorator for QAction subclasses
- [x] `@menu("&File")` - text as positional arg or keyword
- [x] `@action("&New")` - text as positional arg or keyword
- [x] Auto-text from class name (strips "Menu"/"Action" suffix)
- [x] `shortcut` parameter (string, QKeySequence, or StandardKey)
- [x] `tooltip` parameter (sets both toolTip and statusTip)
- [x] `icon` parameter (path, QIcon, or QStyle.StandardPixmap)
- [x] `checkable` parameter for toggle actions
- [x] Auto-connect `on_triggered()` method to triggered signal
- [x] Auto-connect `on_toggled()` method to toggled signal
- [x] Auto-add QAction/QMenu fields to parent menu
- [x] Nested submenus support
- [x] `separator()` factory for menu separators

### API Design

```python
from qtpie import action, menu, make

@action("&New", shortcut="Ctrl+N", tooltip="Create new file")
class NewAction(QAction):
    def on_triggered(self) -> None:
        print("New file!")

@action("&Bold", shortcut="Ctrl+B", checkable=True)
class BoldAction(QAction):
    def on_toggled(self, checked: bool) -> None:
        print(f"Bold: {checked}")

@menu("&Recent")
class RecentMenu(QMenu):
    pass

@menu("&File")
class FileMenu(QMenu):
    new: NewAction = make(NewAction)
    recent: RecentMenu = make(RecentMenu)  # submenu

@window(title="Editor")
class MainWindow(QMainWindow):
    file_menu: FileMenu = make(FileMenu)  # auto-added to menu bar
```

---

## Phase 5: Data Binding ✅ COMPLETE

**Goal**: Two-way binding between widgets and model objects.

### Accomplished

- [x] Binding registry: map widget types to their "default" bindable property
  - QLineEdit → text, QLabel → text, QTextEdit → text, QPlainTextEdit → text
  - QSpinBox → value, QDoubleSpinBox → value, QSlider → value, QDial → value
  - QCheckBox → checked, QRadioButton → checked
  - QComboBox → currentText, QProgressBar → value
- [x] `bind` parameter in `make()`: `bind="property_name"`
- [x] `bind_prop` parameter to override default property
- [x] `make_later()` for fields initialized in setup()
- [x] Observable model integration (observant library)
- [x] Two-way sync with infinite loop prevention
- [x] Nested path binding: `bind="proxy.owner.name"`
- [x] Optional chaining: `bind="proxy.owner?.name"`
- [x] `bind()` function for manual binding
- [x] `register_binding()` for custom widget types
- [x] 31 new tests (127 total)
- [x] 0 pyright errors (strict mode)
- [x] 0 ruff errors

### API Design

```python
from dataclasses import dataclass, field
from observant import ObservableProxy

@dataclass
class Dog:
    name: str = ""
    age: int = 0

@widget()
class DogEditor(QWidget, Widget[Dog]):
    name_edit: QLineEdit = make(QLineEdit, bind="name")
    age_spin: QSpinBox = make(QSpinBox, bind="age")
```

### Files Created/Modified

```
lib/qtpie/
├── __init__.py              # Added: bind, make_later, register_binding
├── bindings/                # NEW MODULE
│   ├── __init__.py
│   ├── registry.py          # BindingRegistry + 12 default bindings
│   └── bind.py              # Two-way bind() function
├── factories/
│   └── make.py              # Added: bind, bind_prop, make_later()
└── decorators/
    └── widget.py            # Added: _process_bindings()

tests/unit/
└── test_bindings.py         # Binding tests
```

---

## Phase 6: Widget Base Class ✅ COMPLETE

**Goal**: Base class for widgets with automatic model binding.

### Accomplished

- [x] Unified `Widget[T]` generic base class with Python 3.13 type parameter syntax
- [x] Works **both** with and without type parameter:
  - `Widget[None]` - simple mixin, no model binding
  - `Widget[Dog]` - enables automatic model binding
- [x] Auto-detect model type from generic parameter
- [x] Auto-create model as `T()` when no model field defined
- [x] Support custom model factory via `model: Person = make(Person, name="Bob")`
- [x] Support manual model setup via `model: Person = make_later()` + set in `setup()`
- [x] Error if `make_later()` used but model not set in `setup()`
- [x] Auto-create `ObservableProxy` wrapping the model
- [x] Auto-bind widget fields to model properties by matching names
- [x] `set_model()` method for changing model after creation
- [x] `ModelWidget` kept as backwards-compatibility alias for `Widget`
- [x] 16 tests for Widget base class (149 total)
- [x] 0 pyright errors (strict mode)
- [x] 0 ruff errors
- [x] 96% code coverage

### API Design

```python
from dataclasses import dataclass
from qtpie import Widget, widget, make, make_later

@dataclass
class Person:
    name: str = ""
    age: int = 0

# Simple widget without model binding
@widget()
class SimpleWidget(QWidget, Widget[None]):
    label: QLabel = make(QLabel, "Hello")

# Auto-creates Person() as model, auto-binds by field name
@widget()
class PersonEditor(QWidget, Widget[Person]):
    name: QLineEdit = make(QLineEdit)  # auto-binds to model.name
    age: QSpinBox = make(QSpinBox)      # auto-binds to model.age

# Custom model factory
@widget()
class PersonEditor(QWidget, Widget[Person]):
    model: Person = make(Person, name="Unknown", age=0)
    name: QLineEdit = make(QLineEdit)

# Manual model setup
@widget()
class PersonEditor(QWidget, Widget[Person]):
    model: Person = make_later()
    name: QLineEdit = make(QLineEdit)

    def setup(self) -> None:
        self.model = load_person_from_db()
```

### Files Created/Modified

```
lib/qtpie/
├── __init__.py              # Added: Widget, ModelWidget exports
├── widget_base.py           # NEW: Widget[T] base class + helper functions
├── factories/
│   └── make.py              # Fixed: signal detection only for QObject subclasses
└── decorators/
    └── widget.py            # Added: _process_model_widget(), _process_model_widget_auto_bindings()

tests/unit/
└── test_model_widget.py     # Widget tests
```

---

## Phase 7: Pre-built Widgets & Utilities

**Goal**: Common widgets and helpers that aren't in Qt.

### TODO

- [ ] `FilterableDropdown` - searchable combo box
- [ ] `AutoHeightTextEdit` - grows with content
- [ ] `ColoredSvgIcon` - SVG with dynamic color
- [ ] `center_on_screen()` utility
- [ ] `screen_geometry()` utility
- [ ] Dock system helpers (TabbedDocksMainWindow, DockManager)

---

## Phase 8: Styling System ✅ COMPLETE

**Goal**: SCSS-based styling with hot reload.

### Accomplished

- [x] SCSS → QSS compilation
- [x] CSS class selectors via Qt properties
- [x] Hot reload with file system watcher
- [x] `add_class()`, `remove_class()`, `toggle_class()`, `has_class()` helpers
- [x] `enable_dark_mode()`, `enable_light_mode()`, `set_color_scheme()`
- [x] Stylesheet loading and watching
- [x] Tests for styling

### API Design

```python
from qtpie import widget, make, enable_dark_mode
from qtpie.styles import add_class, remove_class, toggle_class

# Enable dark mode
enable_dark_mode()

# Usage
@widget(classes=["card"])
class MyCard(QWidget):
    title: QLabel = make(QLabel, "Title")
    action: QPushButton = make(QPushButton, "Go")

    def highlight(self) -> None:
        add_class(self, "highlighted")

    def toggle_active(self) -> None:
        toggle_class(self.action, "active")
```

### Files Created/Modified

```
lib/qtpie/
├── styles/
│   ├── __init__.py          # Exports class helpers and color scheme
│   ├── classes.py           # add_class, remove_class, toggle_class, etc.
│   ├── color_scheme.py      # Dark/light mode helpers
│   ├── compiler.py          # SCSS compilation
│   ├── loader.py            # Stylesheet loading
│   └── watcher.py           # File system watcher for hot reload

tests/unit/
├── test_styles_classes.py
├── test_styles_compiler.py
├── test_styles_loader.py
└── test_styles_watcher.py
```

---

## Phase 9: App Class & Entry Point ✅ COMPLETE

**Goal**: Simplified application bootstrapping.

### Accomplished

- [x] `App` class extending QApplication with lifecycle hooks
- [x] `@entry_point` decorator for main functions and classes
- [x] Async support with qasync event loop
- [x] `run_app()` standalone function for non-App usage
- [x] `dark_mode` and `light_mode` parameters
- [x] `load_stylesheet()` method for QSS/SCSS loading
- [x] Auto-run detection (`__main__` module check)
- [x] pytest-qt integration (qapp_cls fixture override)
- [x] E2E subprocess tests for full app lifecycle
- [x] 18 new tests (242 total)
- [x] 0 pyright errors (strict mode)
- [x] 0 ruff errors

### API Design

```python
from qtpie import App, entry_point, run_app

# Simplest - function returning a widget
@entry_point
def main():
    return QLabel("Hello World!")

# With configuration
@entry_point(dark_mode=True, title="My App", size=(800, 600))
def main():
    return MyWidget()

# On a @widget class
@entry_point
@widget
class MyApp(QWidget):
    label: QLabel = make(QLabel, "Hello!")

# App subclass with lifecycle hooks
@entry_point
class MyApp(App):
    def setup(self):
        self.load_stylesheet("styles.qss")

    def create_window(self):
        return MyMainWindow()

# Standalone run_app for plain QApplication
app = QApplication([])
window = MyWidget()
window.show()
run_app(app)
```

### Files Created/Modified

```
lib/qtpie/
├── __init__.py              # Added: App, entry_point, run_app
├── app.py                   # NEW: App class and run_app()
└── decorators/
    └── entry_point.py       # NEW: @entry_point decorator

tests/
├── conftest.py              # qapp_cls fixture override
├── unit/
│   ├── test_app.py          # App class tests
│   └── test_entry_point.py  # @entry_point unit tests
└── e2e/
    └── test_entry_point_e2e.py  # subprocess E2E tests
```

---

## Future Ideas (Backlog)

- [ ] QML-like declarative syntax (if Python ever gets macros...)
- [ ] Visual designer integration
- [ ] State machines for complex UI flows
- [ ] Undo/redo framework integration
- [ ] Drag and drop helpers
- [ ] Internationalization helpers
- [ ] Accessibility helpers
- [ ] Testing utilities for qtpie_test
- [ ] Documentation site
- [ ] Example applications

---

## Current Status

| Phase                      | Status      |
| -------------------------- | ----------- |
| Phase 1: Core Foundation   | ✅ Complete |
| Phase 2: Layout Extensions | ✅ Complete |
| Phase 3: @window           | ✅ Complete |
| Phase 4: @menu/@action     | ✅ Complete |
| Phase 5: Data Binding      | ✅ Complete |
| Phase 6: Widget Base Class | ✅ Complete |
| Phase 7: Pre-built Widgets | Planned     |
| Phase 8: Styling           | ✅ Complete |
| Phase 9: App Class         | ✅ Complete |

**Total tests:** 248
