# Window Features

## Central Widget Auto-Layout

Window automatically creates a central widget with a layout for non-menu fields. Default is vertical, configurable via `layout=` parameter.

```python
@window(layout="horizontal")
class MainWindow(Window):
    label: QLabel = new("Hello")
    button: QPushButton = new("Click")
```

Supports `"vertical"`, `"horizontal"`, `"form"`, `"grid"`, or `None`. With `layout=None`, no central widget is created.

## Layout Margins

Configure central widget layout margins with `margins=` parameter.

```python
@window(margins=(1, 2, 3, 4))  # left, top, right, bottom
class MainWindow(Window):
    label: QLabel = new("Hello")
```

## Menu Bar Integration

Menu fields are automatically added to the menu bar in declaration order.

```python
@menu(text="&File")
class FileMenu(Menu):
    action_exit: QAction = new("E&xit", triggered="on_exit")
    def on_exit(self) -> None:
        pass

@window
class MainWindow(Window):
    file_menu: FileMenu = new()
    label: QLabel = new("Content")
```

## Explicit Central Widget

A field named `central_widget` becomes the central widget directly, bypassing auto-layout.

```python
@window
class MainWindow(Window):
    central_widget: QLabel = new("I AM THE CENTRAL WIDGET")
    other_label: QLabel = new("Not in layout")
```

Works with `Variable[T, W]`:

```python
@window
class MainWindow(Window):
    central_widget: Variable[str, QLineEdit] = new("")
```

## Layout Exclusion

Exclude widgets from layout with `layout=False`.

```python
@window
class MainWindow(Window):
    visible: QLabel = new("Visible")
    hidden: QLabel = new("Hidden", layout=False)
```

## Setup Hook

The `__setup__()` method is called after widget and menu initialization.

```python
@window
class MainWindow(Window):
    file_menu: FileMenu = new()

    def __setup__(self) -> None:
        # Menus and widgets are ready
        assert len(self.menuBar().actions()) == 1
```

## Decorator Required

Window classes must use the `@window` decorator or raise `TypeError` on instantiation.

```python
class MainWindow(Window):  # Missing @window
    label: QLabel = new("Hello")

MainWindow()  # TypeError: must be decorated with @window
```

## Signal Connections

Signals connect to methods by name or callable.

```python
@window
class MainWindow(Window):
    btn: QPushButton = new("Click", clicked="on_clicked")

    def on_clicked(self) -> None:
        self.was_clicked = True
```

## Window Properties

Decorator kwargs become `setXXX()` calls. Aliases: `title=` for `windowTitle=`, `stylesheet=` for `styleSheet=`.

```python
@window(title="My App", minimumWidth=800, minimumHeight=600)
class MainWindow(Window):
    label: QLabel = new("Hello")
```

## Object Name and CSS Classes

Default objectName is class name. Override with `name=`. Add CSS classes with `classes=`.

```python
@window(name="my-main-window", classes=["dark-theme", "main-window"])
class MainWindow(Window):
    label: QLabel = new("Hello")
```

## Record Type via Decorator

Set initial record value with `record=` parameter.

```python
@dataclass
class Dog:
    name: str
    breed: str

@window(record=Dog("Fido", "Lab"))
class DogWindow(Window[Dog]):
    pass
```

Record is accessible in `__setup__()`, modifiable, and participates in dirty tracking.

## Record Type Support

`Window[T]` provides `record` and `record_state` accessors.

```python
@dataclass
class Dog:
    name: str
    age: int

@window
class DogWindow(Window[Dog]):
    label: QLabel = new("Dog Editor")

w = DogWindow()
w.record = Dog("Fido", 3)
```

## View Model Accessor

Access Variable fields via `view_model`.

```python
@window
class MainWindow(Window):
    _count: Variable[int] = new(0)

w = MainWindow()
w._count = 42
assert w._qtpie.view_model._count.value == 42
```

## #window Binding Placeholder

Use `#window` (alias for `#widget`) in bindings to reference the window instance.

```python
@window(title="Test Window")
class MainWindow(Window):
    label: QLabel = new(bind="Title: {#window.windowTitle()}")
```

## Format Binding Expressions

Complex Python expressions work in format bindings.

```python
@window(title="Test")
class MainWindow(Window):
    _x: Variable[int] = new(10)
    _y: Variable[int] = new(20)
    sum_label: QLabel = new(bind="{_x + _y}")
    upper_label: QLabel = new(bind="{_name.upper()}")
    price_label: QLabel = new(bind="${_price:.2f}")
```

Instance methods callable in bindings:

```python
@window(title="Test")
class MainWindow(Window):
    label: QLabel = new(bind="{compute_value()}")

    def compute_value(self) -> str:
        return "Computed!"
```

## Property Bindings

Control visibility and enabled state reactively with `visible=` and `enabled=`.

```python
@window(title="Test")
class MainWindow(Window):
    _show_label: Variable[bool] = new(True)
    label: QLabel = new("Hello", visible="_show_label")

    _count: Variable[int] = new(5)
    label2: QLabel = new("Conditional", visible="{_count > 3}")
```

## Auto-Bindings

QLineEdit fields auto-bind to same-named Variables (without underscore prefix).

```python
@window(title="Test")
class MainWindow(Window):
    _name: Variable[str] = new("Initial")
    name: QLineEdit = new()  # Auto-binds to _name
```

## bind() Function

Programmatically bind Variables to widgets in `__setup__()`.

```python
@window(title="Test")
class MainWindow(Window):
    _name: Variable[str] = new("Hello")
    label: QLabel = new("")

    def __setup__(self) -> None:
        from qtpie import bind
        bind(self._name).to(self.label)
```

## Variable[T, W] Support

Variable with widget type creates and binds the widget automatically.

```python
@window(title="Test")
class MainWindow(Window):
    name: Variable[str, QLineEdit] = new("Initial")

w = MainWindow()
w.name.value = "Updated"
assert w.name.widget.text() == "Updated"
```

Widget kwargs passed via chaining:

```python
name: Variable[str, QLineEdit] = new("")(placeholderText="Enter name")
```

## Reactive Window Properties

Decorator properties can use format strings to be reactive.

```python
@window(windowTitle="{_title}")
class MainWindow(Window):
    _title: Variable[str] = new("Initial Title")

w = MainWindow()
w._title.value = "Updated Title"
assert w.windowTitle() == "Updated Title"
```

## Record Bindings

Fields auto-bind to record properties by name in `Window[T]`.

```python
@dataclass
class Person:
    name: str = ""
    age: int = 0

@window(title="Test")
class MainWindow(Window[Person]):
    name: QLineEdit = new()  # Auto-binds to record.name
    age: QLineEdit = new()   # Auto-binds to record.age
```

Bindings work in format strings:

```python
@window(title="Test")
class MainWindow(Window[User]):
    label: QLabel = new(bind="{username}")
```

## Form and Grid Layouts

Form layout uses `label=` parameter:

```python
@window(title="Test", layout="form")
class MainWindow(Window):
    name: QLineEdit = new(label="Name:")
    email: QLineEdit = new(label="Email:")
```

Grid layout uses `grid=` parameter:

```python
@window(title="Test", layout="grid")
class MainWindow(Window):
    a: QLabel = new("A", grid=(0, 0))
    b: QLabel = new("B", grid=(0, 1))
```

## List Repeater

`Variable[list[T], W]` creates one widget per item.

```python
@window(title="Test")
class MainWindow(Window):
    numbers: Variable[list[int], QLabel] = new([1, 2, 3])(bind="{#self}")

w = MainWindow()
w.numbers.append(4)  # Creates new widget
```

Supports `#index` placeholder and object property access:

```python
items: Variable[list[Item], QLabel] = new([Item("Apple", 5)])(bind="{name}: {count}")
```

## Dict Repeater

`Variable[dict[K, V], W]` creates one widget per entry.

```python
@window(title="Test")
class MainWindow(Window):
    scores: Variable[dict[str, int], QLabel] = new({"Alice": 100})(bind="{#key}: {#value}")

w = MainWindow()
w.scores["Bob"] = 85  # Creates new widget
```

## list[QWidget] Binding

List fields bound to Variables create widgets per item.

```python
@window(title="Test")
class MainWindow(Window):
    _items: Variable[list[str]] = new(["one", "two"])
    labels: list[QLabel] = new(bind="_items", format="Value: {#self}")
```

## Dirty Tracking

Track whether Variables have changed from initial values.

```python
@window(title="Test")
class MainWindow(Window):
    _name: Variable[str] = new("")

w = MainWindow()
assert w.is_dirty is False

w._name.value = "changed"
assert w.is_dirty is True
assert w.dirty_fields == {"_name"}

w.reset_dirty()
assert w.is_dirty is False
```

## on_dirty_changed Hook

Lifecycle hook fires on dirty state transitions only.

```python
@window(title="Test")
class MainWindow(Window):
    _name: Variable[str] = new("")

    def on_dirty_changed(self, is_dirty: bool) -> None:
        self.save_btn.setEnabled(is_dirty)
```

## Validation

Add validators to fields and check validity.

```python
@window(title="Test")
class MainWindow(Window):
    _name: Variable[str] = new("")

    def __setup__(self) -> None:
        self.add_validator("_name", "required", lambda v: None if v else "Required")

w = MainWindow()
assert w.is_valid is False

w._name.value = "Alice"
assert w.is_valid is True
assert w.validation_errors == {}
assert w.validation_error_messages == []
```

Works with record fields in `Window[T]`:

```python
@window(title="Test")
class PersonWindow(Window[Person]):
    def __setup__(self) -> None:
        self.add_validator("name", "required", lambda v: None if v else "Name required")
```

## on_valid_changed Hook

Lifecycle hook fires when validity changes.

```python
@window(title="Test")
class MainWindow(Window):
    _name: Variable[str] = new("")

    def __setup__(self) -> None:
        self.add_validator("_name", "required", lambda v: None if v else "Required")

    def on_valid_changed(self, is_valid: bool) -> None:
        # Called on state transitions
        pass
```

## Window.is_dirty Property

Aggregates dirty state from Variables AND record (if present). Returns `Observable[bool]`.

```python
@window(title="Test", record=Person())
class PersonWindow(Window[Person]):
    _extra: Variable[str] = new("")

w = PersonWindow()
w._extra.value = "extra"
assert w.is_dirty.get() is True

w.reset_dirty()
assert w.is_dirty.get() is False

w.record.name = "Alice"
assert w.is_dirty.get() is True
```

Can be used in bindings:

```python
_save_btn: QPushButton = new("Save", enabled="is_dirty")
```

## Window.reset_dirty() Method

Clears dirty state for both Variables and record.

```python
@window(title="Test", record=Person())
class PersonWindow(Window[Person]):
    _extra: Variable[str] = new("")

w = PersonWindow()
w._extra.value = "extra"
w.record.name = "Alice"

w.reset_dirty()
assert w.is_dirty.get() is False
```

## Required Variable Bindings

Bare `Variable[T]` (no `= new()`) is a required binding. Must be provided when instantiating.

```python
@window(title="Test")
class MainWindow(Window):
    count: Variable[int]  # Required

assert "count" in MainWindow._qtpie_config.required_bindings
```

## Child Widget Variable Bindings

Pass Variable bindings from Window to child widgets.

```python
from qtpie import Widget, widget

@widget
class CounterDisplay(Widget):
    count: Variable[int]  # Required
    label: QLabel = new(bind="Count: {count}")

@window(title="Counter App")
class App(Window):
    _my_count: Variable[int] = new(0)
    display: CounterDisplay = new(count="_my_count")

app = App()
app._my_count.value = 42
assert app.display.count.value == 42
```

Supports expression bindings and literal values:

```python
child: ConditionalWidget = new(is_enabled="{len(_items) > 0}")
child2: TextWidget = new(text="Hello World")
```

Missing required bindings raise `TypeError`:

```python
child: RequiresBinding = new()  # TypeError: requires binding for 'count'
```

## Variable[T, W] Signal Connections

Signal connections work on Variable widgets, resolving string handlers to parent window methods.

```python
@window(title="Test")
class App(Window):
    _input: Variable[str, QLineEdit] = new("")(returnPressed="on_submit")

    def on_submit(self) -> None:
        pass
```

Signal kwargs are extracted and not passed to widget constructor.
