# Documentation Proposal: Window Feature

## Priority: HIGH

The `Window` class is a core component of QtPie, providing the main application window abstraction. Given its central role and distinct features (menu bar integration, central widget management), comprehensive documentation is critical for users building desktop applications.

---

## Files to Add/Update

### New Files to Create

1. **`docs/guides/windows-menus.md`** (ALREADY EXISTS - needs complete rewrite)
   - Currently nav has this as placeholder entry
   - Should be comprehensive guide combining Window + Menu features

2. **`docs/reference/decorators/window.md`** (ALREADY EXISTS - needs expansion)
   - Currently nav has this entry
   - Detailed @window decorator parameter reference

3. **`docs/reference/classes/window.md`** (ALREADY EXISTS - needs expansion)
   - Currently nav has this entry
   - Window class API reference

### Files to Update

1. **`docs/index.md`**
   - Add Window example to "Key Features" section (currently only shows Widget)
   - Show Window[T] for record types alongside Widget[T]

2. **`docs/why-qtpie.md`**
   - Add QMainWindow vs Window comparison (currently only shows QWidget vs Widget)

3. **`docs/start/concepts.md`**
   - Add Window as a core concept (Widget, Window, Variable, binding)

---

## Suggested Nav Location

Current nav structure is already good:

```yaml
- Guides:
    - Windows & Menus: guides/windows-menus.md  # ← Main guide (expand)
- Reference:
    - Decorators:
        - "@window": reference/decorators/window.md  # ← Expand
    - Classes:
        - Window: reference/classes/window.md  # ← Expand
```

**No nav changes needed** - these pages already exist in structure, just need content.

---

## Content Outline

### 1. `docs/guides/windows-menus.md` (Primary Guide)

**Purpose:** Complete practical guide to building windows and menus

**Sections:**

1. **Introduction**
   - Window vs Widget (QMainWindow vs QWidget)
   - When to use Window vs Widget
   - Central widget concept

2. **Basic Window**
   - Minimal window example
   - Setting window properties (title, size)
   - Running window with @entrypoint

3. **Central Widget & Layouts**
   - How central widget is auto-created
   - Layout options (vertical, horizontal, form, grid)
   - Explicit central_widget field
   - Layout exclusion with `layout=False`

4. **Window Properties**
   - Title, size, minimum/maximum dimensions
   - Window flags and modality
   - Icons and window state
   - Reactive properties with expressions

5. **Menus & Menu Bar**
   - Creating menu classes with @menu
   - Menu fields auto-added to menu bar
   - Nested menus (submenus)
   - Actions and separators
   - Keyboard shortcuts and accelerators
   - Menu signals and handlers

6. **Toolbars & Status Bar**
   - Adding toolbars (declarative)
   - Status bar messages
   - Toolbar actions

7. **Window with Record Types**
   - Window[T] for application state
   - Record auto-binding to widgets
   - Example: Settings window

8. **Child Windows & Dialogs**
   - Creating child windows
   - Modal vs modeless dialogs
   - Passing data between windows
   - Window lifecycle management

9. **Layout Margins & Spacing**
   - margins= parameter (single int or 4-tuple)
   - Customizing layout appearance

10. **Complete Examples**
    - Document editor window (File/Edit/Help menus)
    - Settings/preferences window
    - Multi-window application

### 2. `docs/reference/decorators/window.md` (Reference)

**Purpose:** Complete @window decorator parameter reference

**Sections:**

1. **Overview**
   - Basic syntax and purpose
   - Relationship to Window class

2. **Parameters**

   **Layout & Structure:**
   - `layout=` - Layout type (vertical, horizontal, form, grid)
   - `margins=` - Layout margins (int or 4-tuple)

   **Window Properties:**
   - `title=` - Window title (alias for windowTitle=)
   - `name=` - Object name for QSS/testing
   - `classes=` - CSS classes (list[str])
   - `stylesheet=` - QSS stylesheet (alias for styleSheet=)

   **Window Sizing:**
   - `minimumWidth=`, `minimumHeight=`
   - `maximumWidth=`, `maximumHeight=`
   - `width=`, `height=` (initial size)

   **Record Type:**
   - `record=` - Initial record value for Window[T]

   **Any QMainWindow Property:**
   - Pass-through for any QMainWindow setter
   - Examples: windowIcon=, windowFlags=, windowModality=

3. **Reactive Properties**
   - Using {expression} syntax in parameters
   - Examples with Variable references

4. **Property Aliases**
   - Table of aliases (title → windowTitle, stylesheet → styleSheet)

5. **Type Safety**
   - record= parameter for pyright support
   - Window[T] generic typing

### 3. `docs/reference/classes/window.md` (API Reference)

**Purpose:** Complete Window class API reference

**Sections:**

1. **Class Signature**
   ```python
   class Window(QMainWindow):
       ...
   class Window[T](QMainWindow):  # With record type
       ...
   ```

2. **Properties**
   - `record` - ObservableProxy[T] (for Window[T])
   - `record_state` - RecordState (is_dirty, value, observable)
   - `is_dirty` - Observable[bool] (dirty tracking)
   - `dirty_fields` - set[str] (which fields changed)
   - `is_valid` - bool (validation state)
   - `validation_errors` - Structured error dict
   - `validation_error_messages` - Flat error list

3. **Methods**
   - `__setup__()` - Post-initialization hook
   - `add_validator(field, name, validator)` - Add field validator
   - `remove_validator(field, name)` - Remove validator
   - `reset_dirty()` - Reset dirty tracking
   - `menuBar()` - QMenuBar (inherited from QMainWindow)
   - `statusBar()` - QStatusBar (inherited from QMainWindow)
   - `centralWidget()` - QWidget (inherited from QMainWindow)

4. **Lifecycle Hooks**
   - `on_dirty_changed(is_dirty: bool)` - Dirty state transition
   - `on_valid_changed(is_valid: bool)` - Validation state change

5. **Accessing QMainWindow APIs**
   - How to use inherited QMainWindow methods
   - Common patterns (dockWidgets, toolBars)

6. **Field Types**
   - Variable[T] - Reactive state
   - Variable[T, W] - Inline widget + state
   - QWidget subclasses - Regular widgets
   - QMenu subclasses - Auto-added to menu bar
   - list[QWidget] - Widget repeaters

7. **Auto-Binding**
   - Variable name matching for two-way binding
   - Record property matching (in Window[T])
   - Explicit bind= override

8. **Usage Notes**
   - Must use @window decorator
   - Central widget auto-creation behavior
   - Menu bar vs central widget distinction
   - When to use Window vs Widget

---

## Code Examples Needed

### Basic Examples (in all docs)

```python
# 1. Minimal window
@window(title="My App")
class MainWindow(Window):
    label: QLabel = new("Hello!")

# 2. Window with menu
@menu(text="&File")
class FileMenu(Menu):
    action_new: QAction = new("&New", triggered="on_new")

    def on_new(self) -> None:
        print("New file")

@window(title="My App")
class MainWindow(Window):
    file_menu: FileMenu = new()
    content: QLabel = new("Content")

# 3. Window with reactive state
@window(title="{_filename} - MyApp")
class MainWindow(Window):
    _filename: Variable[str] = new("untitled.txt")
    content: QTextEdit = new()

# 4. Window with record type
@dataclass
class AppSettings:
    theme: str = "light"
    font_size: int = 12

@window(title="Settings", record=AppSettings())
class SettingsWindow(Window[AppSettings]):
    theme: QComboBox = new(items=["light", "dark"])
    font_size: QSpinBox = new()

# 5. Window with entrypoint
@entrypoint
@window(title="My Application")
class MainWindow(Window):
    label: QLabel = new("Hello, QtPie!")
```

### Advanced Examples

```python
# 1. Multi-window app with state sharing
@dataclass
class AppState:
    documents: list[str] = field(default_factory=list)

@window(title="Document Manager", record=AppState())
class MainWindow(Window[AppState]):
    docs_list: QListWidget = new()

    def open_editor(self) -> None:
        editor = EditorWindow()
        editor.document_changed.connect(self.on_doc_changed)
        editor.show()

# 2. Complex menu structure with submenus
@menu(text="&Recent Files")
class RecentFilesMenu(Menu):
    file1: QAction = new("document1.txt")
    file2: QAction = new("document2.txt")

@menu(text="&File")
class FileMenu(Menu):
    action_new: QAction = new("&New", shortcut="Ctrl+N")
    separator1: QAction = new(separator=True)
    recent_menu: RecentFilesMenu = new()
    separator2: QAction = new(separator=True)
    action_exit: QAction = new("E&xit", shortcut="Ctrl+Q")

# 3. Window with form layout and validation
@window(title="User Registration", layout="form")
class RegistrationWindow(Window):
    _username: Variable[str] = new("", validate="validate_username")
    _email: Variable[str] = new("", validate="validate_email")
    _age: Variable[int] = new(0, validate=lambda v: None if v >= 18 else "Must be 18+")

    username: QLineEdit = new(label="Username:")
    email: QLineEdit = new(label="Email:")
    age: QSpinBox = new(label="Age:")

    submit: QPushButton = new("Register", enabled="{is_valid}", clicked="on_submit")

    def validate_username(self, v: str) -> str | None:
        return None if len(v) >= 3 else "Min 3 characters"

    def validate_email(self, v: str) -> str | None:
        return None if "@" in v else "Invalid email"

    def on_submit(self) -> None:
        print(f"Registered: {self._username.value}")

# 4. Window with explicit central widget
@window(title="Custom Layout")
class MainWindow(Window):
    file_menu: FileMenu = new()
    central_widget: QSplitter = new()  # Explicit central widget
    # Other widgets exist but aren't in layout
    other_widget: QLabel = new("I exist but am not in central widget")

    def __setup__(self) -> None:
        # Manually configure splitter
        left = QTextEdit()
        right = QTextEdit()
        self.central_widget.addWidget(left)
        self.central_widget.addWidget(right)

# 5. Window with layout exclusion
@window(title="Mixed Layout")
class MainWindow(Window):
    visible1: QLabel = new("In layout")
    hidden: QWidget = new(layout=False)  # Created but not in layout
    visible2: QLabel = new("Also in layout")

    def __setup__(self) -> None:
        # Use hidden widget as a floating toolbar or similar
        self.hidden.setWindowFlags(Qt.WindowType.ToolTip)
        self.hidden.show()

# 6. Window with child widget composition
@widget
class StatusPanel(Widget):
    status: Variable[str]  # Required binding
    _label: QLabel = new(bind="Status: {status}")

@window(title="App with Status")
class MainWindow(Window):
    _app_status: Variable[str] = new("Ready")
    content: QTextEdit = new()
    status_panel: StatusPanel = new(status="_app_status")
```

---

## Cross-References

### From Window Docs → Other Docs

- **Widget** - Explain Widget vs Window, when to use each
- **Variable** - Link for reactive state examples
- **Bindings** - Link to binding guide for expressions
- **Record Types** - Link to records guide for Window[T]
- **Layouts** - Link to layout guide for layout types
- **Validation** - Link for validator details
- **Dirty Tracking** - Link for dirty tracking details
- **Menu decorator** - Link to @menu reference
- **@entrypoint** - Link for app entry point
- **Translations** - Window titles can use t()

### From Other Docs → Window Docs

- **Getting Started / Concepts** - Link to Window as core concept
- **Widget docs** - Mention Window for main app windows
- **Record Types** - Show Window[T] examples
- **Validation** - Show Window-level validation
- **Forms guide** - Use Window with form layout
- **@entrypoint** - Show with Window examples
- **Menu docs** - Reference Window menu bar integration

---

## Key Distinctions to Clarify

1. **Window vs Widget**
   - Window = QMainWindow (menu bar, status bar, toolbars, dock widgets)
   - Widget = QWidget (general-purpose container)
   - Use Window for top-level application windows
   - Use Widget for reusable components

2. **Central Widget Concept**
   - Window auto-creates central widget with layout
   - All non-menu widgets go in central widget
   - Explicit `central_widget` field overrides this
   - `layout=False` excludes widgets from layout

3. **Menu Bar Integration**
   - Menu-typed fields auto-added to menu bar
   - Order matches declaration order
   - Menus aren't added to central widget layout
   - Menus work exclusively in Window, not Widget

4. **Window[T] vs Window**
   - Window[T] provides record accessor
   - Window[T] supports record= decorator param
   - Fields auto-bind to record properties
   - record is ObservableProxy for reactivity

5. **Setup Hook Timing**
   - Called after __init__ completes
   - Called after menus added to menu bar
   - Called before window shown
   - Use for custom initialization

---

## Documentation Tone & Style

- **Practical first** - Show working code immediately
- **Progressive disclosure** - Simple → complex examples
- **Cross-reference heavily** - Link to related features
- **Real-world examples** - Document editor, settings window, etc.
- **Type safety emphasis** - Show pyright benefits
- **Visual structure** - Use tables for parameters, admonitions for gotchas

---

## Special Considerations

1. **QMainWindow Compatibility**
   - Document that Window IS a QMainWindow
   - Users can call any QMainWindow method
   - Show how to add toolbars, dock widgets imperatively

2. **Multi-Window Apps**
   - Pattern for creating/managing child windows
   - State sharing between windows
   - Window lifecycle (close events, cleanup)

3. **Common Gotchas**
   - Must use @window decorator (TypeError if missing)
   - Menu fields vs widget fields distinction
   - Central widget auto-creation vs explicit
   - layout=False doesn't destroy widget, just excludes from layout

4. **Migration from Qt**
   - Show QMainWindow equivalent code
   - Highlight boilerplate reduction
   - Mention when to drop to Qt APIs

5. **Testing Windows**
   - How to test window initialization
   - Accessing menu bar in tests
   - Testing window properties
   - Modal dialog testing

---

## Success Metrics

Documentation is complete when users can:

1. Create a basic window with menu in < 5 min
2. Understand Window vs Widget without confusion
3. Build multi-window apps with state sharing
4. Use Window[T] for application state
5. Add menus, toolbars, status bar declaratively
6. Know when to use explicit central_widget
7. Understand layout exclusion pattern
8. Test window-based applications

---

## Implementation Priority

1. **HIGH**: `docs/guides/windows-menus.md` - Primary user-facing guide
2. **HIGH**: Update `docs/index.md` - Add Window to key features
3. **MEDIUM**: `docs/reference/decorators/window.md` - Complete parameter reference
4. **MEDIUM**: `docs/reference/classes/window.md` - Complete API reference
5. **LOW**: Update `docs/why-qtpie.md` - Add QMainWindow comparison
6. **LOW**: Update `docs/start/concepts.md` - Add Window concept

---

## Notes

- test_window.md already provides excellent test-driven examples - leverage these!
- Window shares most features with Widget (Variables, bindings, validation, dirty tracking) - reference Widget docs heavily to avoid duplication
- Focus Window docs on what's UNIQUE: menu bar, central widget, QMainWindow features
- Real-world examples critical - document editor, settings dialog, etc.
- Menu integration is a killer feature - make it shine in examples
