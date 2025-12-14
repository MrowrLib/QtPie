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
- [x] Python 3.12 type parameter syntax (`def widget[T](...)`)
- [x] 30 tests passing
- [x] 0 pyright errors (strict mode)
- [x] 0 ruff errors

### Files Created

```
qtpie/
├── __init__.py
├── decorators/
│   ├── __init__.py
│   └── widget.py
└── factories/
    ├── __init__.py
    └── make.py

tests/test_qtpie/
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
- [x] Stretch support: `_stretch` fields (int type)
- [x] Auto-add "form" class to form layout widgets
- [x] 18 new tests (48 total)
- [x] 0 pyright errors (strict mode)
- [x] 0 ruff errors

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
    _stretch1: int = 1  # pushes content to bottom
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
- [x] 29 new tests (96 total)
- [x] 0 pyright errors (strict mode)
- [x] 0 ruff errors

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
- [x] `bind` parameter in `make()`: `bind="proxy.property"`
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
class DogEditor(QWidget):
    model: Dog = make(Dog)
    proxy: ObservableProxy[Dog] = make_later()

    name_edit: QLineEdit = make(QLineEdit, bind="proxy.name")
    age_spin: QSpinBox = make(QSpinBox, bind="proxy.age")

    def setup(self) -> None:
        self.proxy = ObservableProxy(self.model, sync=True)
```

### Files Created/Modified

```
qtpie/
├── __init__.py              # Added: bind, make_later, register_binding
├── bindings/                # NEW MODULE
│   ├── __init__.py
│   ├── registry.py          # BindingRegistry + 12 default bindings
│   └── bind.py              # Two-way bind() function
├── factories/
│   └── make.py              # Added: bind, bind_prop, make_later()
└── decorators/
    └── widget.py            # Added: _process_bindings()

tests/test_qtpie/
└── test_bindings.py         # 18 binding tests
```

---

## Phase 6: Styling System

**Goal**: SCSS-based styling with hot reload.

### TODO

- [ ] SCSS → QSS compilation
- [ ] CSS class selectors: `.card`, `.primary`, `.danger`
- [ ] Class inheritance/composition
- [ ] Theme variables
- [ ] Hot reload in dev mode
- [ ] `add_class()`, `remove_class()`, `toggle_class()` helpers
- [ ] Tests for styling

### API Design

```python
# styles/main.scss
$primary: #3b82f6;
$danger: #ef4444;

.card {
    background: white;
    border-radius: 8px;
    padding: 16px;
}

.btn-primary {
    background: $primary;
    color: white;
}

# Usage
@widget(classes=["card"])
class MyCard(QWidget):
    title: QLabel = make(QLabel, "Title", classes=["heading"])
    action: QPushButton = make(QPushButton, "Go", classes=["btn-primary"])
```

---

## Phase 7: App Class & Entry Point

**Goal**: Simplified application bootstrapping.

### TODO

- [ ] `App` class extending QApplication
- [ ] `@entry_point` decorator for main functions
- [ ] Async support with qasync
- [ ] Dev mode: hot reload, debug tools
- [ ] Global stylesheet loading
- [ ] Tests for App class

### API Design

```python
from qtpie import App, entry_point, window

@window(title="My App")
class MainWindow(QMainWindow):
    ...

@entry_point
def main():
    app = App(dev_mode=True, stylesheet="styles/main.scss")
    window = MainWindow()
    window.show()
    return app.run()
```

---

## Phase 8: Pre-built Widgets & Utilities

**Goal**: Common widgets and helpers that aren't in Qt.

### TODO

- [ ] `FilterableDropdown` - searchable combo box
- [ ] `AutoHeightTextEdit` - grows with content
- [ ] `ColoredSvgIcon` - SVG with dynamic color
- [ ] `center_on_screen()` utility
- [ ] `screen_geometry()` utility
- [ ] Dock system helpers (TabbedDocksMainWindow, DockManager)

---

## Phase 9: ModelWidget Base Class

**Goal**: Base class for widgets with automatic model binding.

### TODO

- [ ] `ModelWidget[T]` generic base class
- [ ] Auto-detect model type from generic parameter
- [ ] Auto-bind fields with matching names
- [ ] Model property for accessing the bound model
- [ ] Tests for ModelWidget

### API Design

```python
class Person:
    name: str
    email: str

@widget()
class PersonEditor(ModelWidget[Person]):
    # These auto-bind to person.name and person.email
    name: QLineEdit = make(QLineEdit)
    email: QLineEdit = make(QLineEdit)

    def setup(self) -> None:
        # self.model is typed as Person
        print(f"Editing: {self.model.name}")
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

| Phase | Status | Tests |
|-------|--------|-------|
| Phase 1: Core Foundation | ✅ Complete | 30 |
| Phase 2: Layout Extensions | ✅ Complete | 48 |
| Phase 3: @window | ✅ Complete | 67 |
| Phase 4: @menu/@action | ✅ Complete | 96 |
| Phase 5: Data Binding | ✅ Complete | 127 |
| Phase 6: Styling | 🎯 Next | - |
| Phase 7: App Class | Planned | - |
| Phase 8: Pre-built Widgets | Planned | - |
| Phase 9: ModelWidget | Planned | - |
