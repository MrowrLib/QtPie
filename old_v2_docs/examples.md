# Examples

Complete example applications demonstrating QtPie patterns. Each example shows practical usage of multiple features working together.

## Todo List Application

A classic todo app with add, remove, and completion tracking:

```python
from dataclasses import dataclass
from PySide6.QtWidgets import QCheckBox, QHBoxLayout, QLineEdit, QPushButton, QWidget
from qtpie import Variable, Widget, entrypoint, new, widget

@dataclass
class TodoItem:
    text: str
    done: bool = False

@widget(layout="horizontal")
class TodoRow(Widget[TodoItem]):
    checkbox: QCheckBox = new()
    label_text: QLabel = new(bind="{text}")
    delete_btn: QPushButton = new("X", clicked="on_delete")

    def __setup__(self) -> None:
        from qtpie import bind
        bind(self.record_state.done).to(self.checkbox, "checked")

    def on_delete(self) -> None:
        # Signal parent to remove this item
        pass

@entrypoint(title="Todo List", size=(400, 500))
@widget
class TodoApp(Widget):
    _items: Variable[list[TodoItem]] = new([])
    _new_text: Variable[str, QLineEdit] = new("")(
        placeholderText="What needs to be done?",
        returnPressed="add_item"
    )

    add_btn: QPushButton = new("Add", clicked="add_item")

    _todo_list: list[TodoRow] = new(bind="_items")

    def add_item(self) -> None:
        if self._new_text.value.strip():
            self._items.append(TodoItem(text=self._new_text.value))
            self._new_text.value = ""

    def remove_item(self, index: int) -> None:
        if 0 <= index < len(self._items.value):
            del self._items.value[index]
```

## Counter with History

A counter that tracks all changes:

```python
from PySide6.QtWidgets import QLabel, QPushButton
from qtpie import Variable, Widget, entrypoint, new, widget

@entrypoint(title="Counter", size=(300, 400))
@widget
class CounterApp(Widget):
    _count: Variable[int] = new(0)
    _history: Variable[list[str]] = new([])

    display: QLabel = new(bind="Count: {_count}")

    decrement: QPushButton = new("-", clicked="on_decrement")
    increment: QPushButton = new("+", clicked="on_increment")
    reset_btn: QPushButton = new("Reset", clicked="on_reset")

    history_label: QLabel = new("History:")
    _history_items: list[QLabel] = new(bind="_history")

    def on_increment(self) -> None:
        self._count += 1
        self._history.append(f"+1 -> {self._count.value}")

    def on_decrement(self) -> None:
        self._count -= 1
        self._history.append(f"-1 -> {self._count.value}")

    def on_reset(self) -> None:
        old = self._count.value
        self._count.value = 0
        self._history.append(f"Reset from {old} -> 0")
```

## Settings Dialog with Validation

A settings form with validation and dirty tracking:

```python
from dataclasses import dataclass
from PySide6.QtWidgets import QCheckBox, QLabel, QLineEdit, QPushButton, QSpinBox
from qtpie import Variable, Widget, entrypoint, new, widget

@dataclass
class Settings:
    username: str = ""
    email: str = ""
    max_items: int = 100
    dark_mode: bool = False

@entrypoint(title="Settings", size=(400, 300))
@widget(layout="form", record=Settings())
class SettingsApp(Widget[Settings]):
    username: QLineEdit = new(label="Username:")
    email: QLineEdit = new(label="Email:")
    max_items: QSpinBox = new(label="Max Items:")
    dark_mode: QCheckBox = new(label="Dark Mode:")

    # Status bar
    error_label: QLabel = new(
        bind="{', '.join(validation_error_messages)}",
        stylesheet="color: red;"
    )

    # Buttons
    save_btn: QPushButton = new(
        "Save",
        enabled="{is_valid and view_model.is_dirty}",
        clicked="on_save"
    )
    cancel_btn: QPushButton = new("Cancel", clicked="on_cancel")

    def __setup__(self) -> None:
        self.add_validator("username", "required",
            lambda v: None if v else "Username required")
        self.add_validator("username", "length",
            lambda v: None if len(v) >= 3 else "Min 3 characters")
        self.add_validator("email", "format",
            lambda v: None if "@" in v else "Invalid email")

    def on_save(self) -> None:
        print(f"Saving: {self.record}")
        self.view_model.reset_dirty()

    def on_cancel(self) -> None:
        self.close()

    def on_dirty_changed(self, is_dirty: bool) -> None:
        title = "Settings" + (" *" if is_dirty else "")
        self.setWindowTitle(title)
```

## File Browser with Menus

A window with menu bar and file operations:

```python
from PySide6.QtWidgets import QLabel, QMenu, QTextEdit
from PySide6.QtGui import QAction
from qtpie import Variable, Window, entrypoint, menu, new, separator, window

@menu("&File")
class FileMenu(QMenu):
    new_action: QAction = new("&New", shortcut="Ctrl+N", triggered="on_new")
    open_action: QAction = new("&Open", shortcut="Ctrl+O", triggered="on_open")
    sep1: QAction = separator()
    save_action: QAction = new("&Save", shortcut="Ctrl+S", triggered="on_save")
    save_as: QAction = new("Save &As...", shortcut="Ctrl+Shift+S")
    sep2: QAction = separator()
    exit_action: QAction = new("E&xit", triggered="on_exit")

    def on_new(self) -> None:
        window = self.parent()
        if window:
            window.new_document()

    def on_open(self) -> None:
        print("Open file dialog...")

    def on_save(self) -> None:
        window = self.parent()
        if window:
            window.save_document()

    def on_exit(self) -> None:
        self.parent().close()

@menu("&Edit")
class EditMenu(QMenu):
    undo: QAction = new("&Undo", shortcut="Ctrl+Z")
    redo: QAction = new("&Redo", shortcut="Ctrl+Y")
    sep: QAction = separator()
    cut: QAction = new("Cu&t", shortcut="Ctrl+X")
    copy: QAction = new("&Copy", shortcut="Ctrl+C")
    paste: QAction = new("&Paste", shortcut="Ctrl+V")

@entrypoint(title="Notepad", size=(800, 600), dark_mode=True)
@window
class NotepadWindow(Window):
    file_menu: FileMenu = new()
    edit_menu: EditMenu = new()

    _filename: Variable[str] = new("untitled.txt")
    _content: Variable[str] = new("")

    central_widget: QTextEdit = new()

    def __setup__(self) -> None:
        from qtpie import bind
        bind(self._content).to(self.central_widget, "plainText")

    def new_document(self) -> None:
        self._filename.value = "untitled.txt"
        self._content.value = ""

    def save_document(self) -> None:
        print(f"Saving {self._filename.value}")
```

## Dashboard with Live Updates

A dashboard showing reactive data:

```python
from PySide6.QtWidgets import QLabel, QProgressBar, QPushButton
from qtpie import Variable, Widget, entrypoint, new, widget

@entrypoint(title="Dashboard", size=(600, 400))
@widget(layout="grid")
class Dashboard(Widget):
    # Stats row
    users_stat: QLabel = new(bind="Users: {_users}", grid=(0, 0))
    sales_stat: QLabel = new(bind="Sales: ${_sales:,.2f}", grid=(0, 1))
    active_stat: QLabel = new(bind="Active: {_active}", grid=(0, 2))

    # Progress bars
    cpu_label: QLabel = new("CPU:", grid=(1, 0))
    _cpu: Variable[int] = new(45)
    cpu_bar: QProgressBar = new(grid=(1, 1, 1, 2))

    memory_label: QLabel = new("Memory:", grid=(2, 0))
    _memory: Variable[int] = new(60)
    memory_bar: QProgressBar = new(grid=(2, 1, 1, 2))

    # Data variables
    _users: Variable[int] = new(1234)
    _sales: Variable[float] = new(56789.99)
    _active: Variable[int] = new(89)

    # Simulate button
    simulate_btn: QPushButton = new(
        "Simulate Update",
        grid=(3, 0, 1, 3),
        clicked="simulate"
    )

    def __setup__(self) -> None:
        from qtpie import bind
        bind(self._cpu).to(self.cpu_bar, "value")
        bind(self._memory).to(self.memory_bar, "value")

    def simulate(self) -> None:
        import random
        self._users += random.randint(-10, 50)
        self._sales += random.uniform(-100, 500)
        self._active.value = random.randint(50, 150)
        self._cpu.value = random.randint(10, 95)
        self._memory.value = random.randint(20, 90)
```

## Multi-Language App

An application with translation support:

```python
from PySide6.QtWidgets import QComboBox, QLabel, QPushButton
from qtpie import Widget, entrypoint, new, set_language, t, widget

@entrypoint(
    title="Translated App",
    translations="translations.yml",
    language="en"
)
@widget
class TranslatedApp(Widget):
    greeting: QLabel = new(t("Hello, World!"))

    lang_label: QLabel = new(t("Language:"))
    lang_selector: QComboBox = new()

    action_btn: QPushButton = new(t("Click Me"), clicked="on_action")
    status: QLabel = new(t("Ready"))

    def __setup__(self) -> None:
        self.lang_selector.addItems(["English", "Francais", "Deutsch"])
        self.lang_selector.currentTextChanged.connect(self.on_lang_change)

    def on_lang_change(self, text: str) -> None:
        lang_map = {"English": "en", "Francais": "fr", "Deutsch": "de"}
        set_language(lang_map.get(text, "en"))

    def on_action(self) -> None:
        self.status.setText(t("Button clicked!")(None))
```

With `translations.yml`:

```yaml
:global:
    "Hello, World!":
        en: Hello, World!
        fr: Bonjour, le monde!
        de: Hallo, Welt!

    "Language:":
        en: "Language:"
        fr: "Langue:"
        de: "Sprache:"

    "Click Me":
        en: Click Me
        fr: Cliquez-moi
        de: Klick mich

    "Ready":
        en: Ready
        fr: Pret
        de: Bereit

    "Button clicked!":
        en: Button clicked!
        fr: Bouton clique!
        de: Knopf geklickt!
```

## Running the Examples

Each example uses `@entrypoint`, so simply run the file:

```bash
# Run any example
uv run python examples/todo_app.py
uv run python examples/counter.py
uv run python examples/settings.py
```

For development with hot-reload:

```python
@entrypoint(
    stylesheet="styles.scss",
    watch_stylesheet=True,
    translations="i18n.yml",
    watch_translations=True
)
```

## See Also

- [Getting Started](start/hello-world.md) - First steps tutorial
- [Widgets](basics/widgets.md) - Widget fundamentals
- [Windows & Menus](guides/windows-menus.md) - Window and menu patterns
- [Variables](state/variables.md) - Reactive state management
