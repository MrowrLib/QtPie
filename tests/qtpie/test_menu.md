# Menu System Features

## @menu Decorator

Creates declarative menus that can be added to windows. Automatically derives title from class name (FileMenu → "File"), or accepts explicit text.

```python
@menu
class FileMenu(Menu):
    pass

m = qt.track(FileMenu())
assert_that(m.title()).is_equal_to("File")
```

```python
@menu(text="&File")
class MyMenu(Menu):
    pass

m = qt.track(MyMenu())
assert_that(m.title()).is_equal_to("&File")
```

## QAction Fields

QAction fields are automatically added to the menu. Supports signal connections via method name or lambda, shortcuts, and other Qt properties.

```python
@menu(text="&File")
class FileMenu(Menu):
    new_action: QAction = new("&New", triggered="on_new", shortcut="Ctrl+N")

    def on_new(self) -> None:
        nonlocal triggered
        triggered = True
```

## Separator

Bare `Separator` annotation creates a separator in the menu.

```python
@menu(text="&File")
class FileMenu(Menu):
    new_action: QAction = new("&New")
    ____: Separator
    exit_action: QAction = new("E&xit")
```

## Section

Section headers with text derived from field name or explicit text via `new()`.

```python
@menu(text="&File")
class FileMenu(Menu):
    ___recent_files___: Section  # Becomes "Recent Files"
    file1: QAction = new("file1.txt")
```

```python
@menu(text="&File")
class FileMenu(Menu):
    ___recent___: Section = new("Recent Files")
    file1: QAction = new("file1.txt")
```

## Checkable Actions

Actions with checkable state, initial checked value, and toggled signal handlers.

```python
@menu(text="&View")
class ViewMenu(Menu):
    word_wrap: QAction = new("Word Wrap", checkable=True, checked=True, toggled="on_toggle")

    def on_toggle(self, checked: bool) -> None:
        nonlocal toggled_value
        toggled_value = checked
```

## Two-Way Checked Binding

Checkable actions can bind to Variables for bidirectional synchronization.

```python
@menu(text="&View")
class ViewMenu(Menu):
    _word_wrap: Variable[bool] = new(False)
    word_wrap: QAction = new("Word Wrap", checkable=True, checked="_word_wrap")

# Variable changes -> action updates
m._word_wrap.value = True
assert_that(m.word_wrap.isChecked()).is_true()

# Action changes -> variable updates
m.word_wrap.setChecked(False)
assert_that(m._word_wrap.value).is_false()
```

## ActionRepeater (Dynamic Action Lists)

`list[QAction]` bound to a Variable creates dynamic actions that sync with the list. Supports format strings, triggered handlers, and placeholders like `#index` and `#self`.

```python
@menu(text="&Window")
class WindowMenu(Menu):
    _windows: Variable[list[str]] = new(["Win1", "Win2"])
    window_actions: list[QAction] = new(bind="_windows", format="{#index}: {#self}")

m._windows.append("Win3")  # Automatically creates new action
```

```python
@menu(text="&Window")
class WindowMenu(Menu):
    _windows: Variable[list[str]] = new(["Win1", "Win2"])
    window_actions: list[QAction] = new(
        bind="_windows",
        triggered="on_window_select",
    )

    def on_window_select(self, item: str) -> None:
        nonlocal selected_item
        selected_item = item
```

## Window Integration

Menu instances are automatically added to Window's menu bar in declaration order.

```python
@menu(text="&File")
class FileMenu(Menu):
    new_action: QAction = new("&New")

@window(title="Test App")
class App(Window):
    file_menu: FileMenu = new()

app = qt.track(App())
menubar = app.menuBar()
assert_that(menubar.actions()[0].text()).is_equal_to("&File")
```

## Menu Variable Bindings

Menus support Variable fields and can receive bindings from parent Windows.

```python
@menu(text="&File")
class FileMenu(Menu):
    is_dirty: Variable[bool]  # Required binding
    save: QAction = new("&Save", enabled="{is_dirty}")

@window(title="Test App")
class App(Window):
    _is_dirty: Variable[bool] = new(False)
    file_menu: FileMenu = new(is_dirty="_is_dirty")
```

## Menu[T] Record Support

Menus can have record types for reactive state. Records can be set via decorator or in `__setup__`.

```python
@dataclass
class EditState:
    can_undo: bool = False

@menu(text="&Edit", record=EditState())
class EditMenu(Menu[EditState]):
    undo: QAction = new("Undo", enabled="{record.can_undo}")

m.record.can_undo = True
assert_that(m.undo.isEnabled()).is_true()
```

## #parent Placeholder

Escape hatch for accessing parent window variables directly in bindings without explicit binding parameters.

```python
@menu(text="&File")
class FileMenu(Menu):
    save: QAction = new("Save", enabled="{#parent._is_dirty}")

@window(title="App")
class App(Window):
    _is_dirty: Variable[bool] = new(False)
    file_menu: FileMenu = new()

app._is_dirty.value = True
assert_that(app.file_menu.save.isEnabled()).is_true()
```
