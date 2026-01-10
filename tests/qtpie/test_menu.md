# Menu Tests Summary

## @menu Decorator

Decorates a Menu subclass to create declarative menus. Title derived from class name (FileMenu → "File") or explicit `text=` parameter. ObjectName from `name=` or class name.

```python
@menu(text="&File")
class FileMenu(Menu):
    new_action: QAction = new("&New")
    open_action: QAction = new("&Open")

m = qt.track(FileMenu())
assert_that(m.title()).is_equal_to("&File")
```

```python
@menu
class FileMenu(Menu):
    pass

m = qt.track(FileMenu())
assert_that(m.title()).is_equal_to("File")  # Derived from class name
```

## QAction Fields

QAction fields are automatically added to the menu. Signals connect via `triggered="method_name"` or lambda.

```python
@menu(text="&File")
class FileMenu(Menu):
    new_action: QAction = new("&New", triggered="on_new")

    def on_new(self) -> None:
        nonlocal triggered
        triggered = True

m = qt.track(FileMenu())
m.new_action.trigger()
```

## Separator

Bare `Separator` annotation creates menu separator. Field name is ignored.

```python
@menu(text="&File")
class FileMenu(Menu):
    new_action: QAction = new("&New")
    ____: Separator
    exit_action: QAction = new("E&xit")

m = qt.track(FileMenu())
actions = m.actions()
assert_that(actions[1].isSeparator()).is_true()
```

## Section

Section marker creates a non-interactive section header. Text derived from field name with underscores stripped (___recent___ → "Recent", ___recent_files___ → "Recent Files") or explicit via `new("text")`.

```python
@menu(text="&File")
class FileMenu(Menu):
    ___recent___: Section
    file1: QAction = new("file1.txt")

m = qt.track(FileMenu())
actions = m.actions()
assert_that(actions[0].text()).is_equal_to("Recent")
```

```python
@menu(text="&File")
class FileMenu(Menu):
    ___recent_files___: Section
    file1: QAction = new("file1.txt")

m = qt.track(FileMenu())
assert_that(m.actions()[0].text()).is_equal_to("Recent Files")
```

## Variable Support

Menus support Variables like Widgets. Bare `Variable[T]` is a required binding, `Variable[T] = new(default)` is optional.

```python
@menu
class FileMenu(Menu):
    _dark_mode: Variable[bool] = new(False)

m = qt.track(FileMenu())
m._dark_mode.value = True
assert_that(m._dark_mode.value).is_true()
```

```python
@menu
class FileMenu(Menu):
    recent_files: Variable[list[str]]  # Required binding

assert "recent_files" in FileMenu._qtpie_config.required_bindings
```

## Checkable Actions

Actions can be checkable with two-way binding to Variables via `checked="_variable"`.

```python
@menu(text="&View")
class ViewMenu(Menu):
    word_wrap: QAction = new("Word Wrap", checkable=True, checked=True)

m = qt.track(ViewMenu())
assert_that(m.word_wrap.isChecked()).is_true()
```

```python
@menu(text="&View")
class ViewMenu(Menu):
    _word_wrap: Variable[bool] = new(False)
    word_wrap: QAction = new("Word Wrap", checkable=True, checked="_word_wrap")

m = qt.track(ViewMenu())
# Variable changes -> action updates
m._word_wrap.value = True
assert_that(m.word_wrap.isChecked()).is_true()

# Action changes -> variable updates
m.word_wrap.setChecked(False)
assert_that(m._word_wrap.value).is_false()
```

## ActionRepeater (Dynamic Action Lists)

`list[QAction] = new(bind=...)` creates dynamic actions from a Variable. Supports `format=` with placeholders like `{#self}`, `{#index}`. Reactive to list changes (append, remove). Handler receives the item.

```python
@menu(text="&Window")
class WindowMenu(Menu):
    _windows: Variable[list[str]] = new(["Win1", "Win2"])
    window_actions: list[QAction] = new(bind="_windows")

m = qt.track(WindowMenu())
assert_that(len(m.actions())).is_equal_to(2)

m._windows.append("Win3")
assert_that(len(m.actions())).is_equal_to(3)
```

```python
@menu(text="&Window")
class WindowMenu(Menu):
    _windows: Variable[list[str]] = new(["Main", "Settings"])
    window_actions: list[QAction] = new(bind="_windows", format="Open {#self}")

m = qt.track(WindowMenu())
assert_that(m.actions()[0].text()).is_equal_to("Open Main")
```

## Window Integration

Menu subclass fields in Window are auto-added to the menu bar in declaration order. Can receive Variable bindings from parent Window.

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

```python
@menu(text="&File")
class FileMenu(Menu):
    doc_dirty: Variable[bool]  # Required binding
    save: QAction = new("&Save", enabled="{doc_dirty}")

@window(title="Test App")
class App(Window):
    _doc_dirty: Variable[bool] = new(False)
    file_menu: FileMenu = new(doc_dirty="_doc_dirty")

app = qt.track(App())
app._doc_dirty.value = True
assert_that(app.file_menu.doc_dirty.value).is_true()
```

## Menu[T] Record Support

Menus can have a typed record with `Menu[T]`. Set via `record=` decorator parameter or in `__setup__`. Fields are reactive ObservableProxy.

```python
@dataclass
class EditState:
    can_undo: bool = False

@menu(text="&Edit", record=EditState(can_undo=True))
class EditMenu(Menu[EditState]):
    undo: QAction = new("Undo", enabled="{record.can_undo}")

m = qt.track(EditMenu())
assert_that(m.undo.isEnabled()).is_true()

m.record.can_undo = False
assert_that(m.undo.isEnabled()).is_false()
```

## #parent Placeholder

Special `{#parent}` placeholder accesses parent window's variables in bindings. Escape hatch for cases where explicit Variable binding is not suitable.

```python
@menu(text="&File")
class FileMenu(Menu):
    save: QAction = new("Save", enabled="{#parent._is_dirty}")

@window(title="App")
class App(Window):
    _is_dirty: Variable[bool] = new(False)
    file_menu: FileMenu = new()

app = qt.track(App())
app._is_dirty.value = True
assert_that(app.file_menu.save.isEnabled()).is_true()
```

## Dirty Tracking

Menus track which Variables have changed via `is_dirty`, `dirty_fields`, and `reset_dirty()`. `is_dirty` is Observable[bool].

```python
@menu(text="&File")
class FileMenu(Menu):
    _name: Variable[str] = new("")
    _count: Variable[int] = new(0)

m = qt.track(FileMenu())
m._name.value = "changed"
m._count.value = 42

assert_that(m.is_dirty.get()).is_true()
assert_that(m.dirty_fields).is_equal_to({"_name", "_count"})

m.reset_dirty()
assert_that(m.is_dirty.get()).is_false()
```

## Validation

Add validators to fields via `add_validator(field, name, func)`. Aggregate validity via `is_valid`, structured errors via `validation_errors`, flat list via `validation_error_messages`. Both observables.

```python
@menu(text="&File")
class FileMenu(Menu):
    _name: Variable[str] = new("")
    _count: Variable[int] = new(0)

    def __setup__(self) -> None:
        self.add_validator("_name", "required", lambda v: None if v else "Required")
        self.add_validator("_count", "positive", lambda v: None if v > 0 else "Must be positive")

m = qt.track(FileMenu())
assert_that(m.is_valid.get()).is_false()

m._name.value = "Alice"
m._count.value = 5
assert_that(m.is_valid.get()).is_true()
```

## Lifecycle Hooks

Optional `on_dirty_changed(is_dirty: bool)` and `on_valid_changed(is_valid: bool)` hooks fire on state transitions only.

```python
@menu(text="&File")
class FileMenu(Menu):
    _name: Variable[str] = new("")

    @override
    def on_dirty_changed(self, is_dirty: bool) -> None:
        dirty_states.append(is_dirty)

m = qt.track(FileMenu())
m._name.value = "changed"
m.reset_dirty()

assert_that(dirty_states).is_equal_to([True, False])
```

## ref() with Required Bindings

`ref("literal {expression}")` works with required bindings in menus, preserving literal text while resolving expressions.

```python
@menu(text="&Dog")
class DogMenu(Menu):
    dog: Variable[Dog]
    dog_action: QAction = new(text=ref("Dog name: {dog.name}"))

@window(title="Test", record=Dog("Buddy", 4))
class MainWindow(Window[Dog]):
    dog_menu: DogMenu = new(dog="record")

w = qt.track(MainWindow())
assert_that(w.dog_menu.dog_action.text()).is_equal_to("Dog name: Buddy")
```
