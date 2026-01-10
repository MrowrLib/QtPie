# Window Test Summary

## Central Widget Layout

Window automatically creates a central widget with a layout to hold child widgets. Default layout is vertical (QVBoxLayout), but can be configured via `layout=` parameter.

```python
@window(layout="horizontal")
class MainWindow(Window):
    label: QLabel = new("Hello")
    button: QPushButton = new("Click")

w = qt.track(MainWindow())
central = w.centralWidget()
assert_that(central.layout()).is_instance_of(QHBoxLayout)
```

## Layout Margins

Central widget layout margins can be set as a single integer (all sides) or 4-tuple (left, top, right, bottom).

```python
@window(margins=(1, 2, 3, 4))
class MainWindow(Window):
    label: QLabel = new("Hello")

w = qt.track(MainWindow())
margins = w.centralWidget().layout().contentsMargins()
assert_that(margins.left()).is_equal_to(1)
assert_that(margins.top()).is_equal_to(2)
```

## Menu Bar Integration

Menu fields are automatically added to the window's menu bar in declaration order. Other widgets go to the central widget.

```python
@menu(text="&File")
class FileMenu(Menu):
    pass

@window
class MainWindow(Window):
    file_menu: FileMenu = new()
    label: QLabel = new("Hello")
    button: QPushButton = new("Click")

w = qt.track(MainWindow())
menubar = w.menuBar()
assert_that(menubar.actions()[0].text()).is_equal_to("&File")
layout = w.centralWidget().layout()
assert_that(layout.itemAt(0).widget()).is_equal_to(w.label)
```

## Explicit Central Widget

A field named `central_widget` becomes the central widget directly, bypassing layout creation. Other widget fields are ignored for layout purposes.

```python
@window
class MainWindow(Window):
    central_widget: QLabel = new("I AM THE CENTRAL WIDGET")
    other_label: QLabel = new("Other")  # Not added to layout

w = qt.track(MainWindow())
central = w.centralWidget()
assert_that(central).is_same_as(w.central_widget)
assert_that(w.other_label).is_not_none()  # Exists but not in layout
```

## Layout Exclusion

Widgets with `layout=False` are created but not added to the central widget layout.

```python
@window
class MainWindow(Window):
    visible: QLabel = new("Visible")
    hidden: QLabel = new("Hidden", layout=False)
    also_visible: QLabel = new("Also Visible")

w = qt.track(MainWindow())
layout = w.centralWidget().layout()
assert_that(layout.count()).is_equal_to(2)  # Only 2 widgets
assert_that(w.hidden).is_not_none()  # But exists as attribute
```

## Setup Hook

`__setup__()` is called after initialization and after menus are added to menubar.

```python
@menu(text="&File")
class FileMenu(Menu):
    pass

setup_menu_count = 0

@window
class MainWindow(Window):
    file_menu: FileMenu = new()

    def __setup__(self) -> None:
        nonlocal setup_menu_count
        setup_menu_count = len(self.menuBar().actions())

qt.track(MainWindow())
assert_that(setup_menu_count).is_equal_to(1)
```

## Decorator Required

Window classes must be decorated with `@window`, otherwise instantiation raises TypeError.

```python
class MainWindow(Window):
    label: QLabel = new("Hello")

with pytest.raises(TypeError) as exc_info:
    MainWindow()

assert "must be decorated with @window" in str(exc_info.value)
```

## Signal Connections

Signals can be connected to methods by name or to callables.

```python
@window
class MainWindow(Window):
    btn: QPushButton = new("Click", clicked="on_clicked")
    was_clicked: bool = False

    def on_clicked(self) -> None:
        self.was_clicked = True

w = qt.track(MainWindow())
w.btn.click()
assert_that(w.was_clicked).is_true()
```

## Window Properties

Decorator kwargs map to window properties. Common aliases: `title=` for `windowTitle=`, `stylesheet=` for `styleSheet=`.

```python
@window(title="My Window", minimumWidth=800, minimumHeight=600)
class MainWindow(Window):
    label: QLabel = new("Hello")

w = qt.track(MainWindow())
assert_that(w.windowTitle()).is_equal_to("My Window")
assert_that(w.minimumWidth()).is_equal_to(800)
```

## Object Name and CSS Classes

Window gets class name as default `objectName`, or explicit `name=` parameter. CSS classes via `classes=`.

```python
@window(name="my-main-window", classes=["dark-theme", "main-window"])
class MainWindow(Window):
    label: QLabel = new("Hello")

w = qt.track(MainWindow())
assert_that(w.objectName()).is_equal_to("my-main-window")
class_prop = w.property("class")
assert_that(class_prop).contains("dark-theme")
```

## Record Type via Decorator

`@window(record=...)` sets the initial record value for `Window[T]`.

```python
@dataclass
class Person:
    name: str
    age: int

@window(record=Person("Alice", 30))
class PersonWindow(Window[Person]):
    pass

w = qt.track(PersonWindow())
assert_that(w.record.name).is_equal_to("Alice")
assert_that(w.record.age).is_equal_to(30)
```

## Record Access

`Window[T]` provides `record` accessor for reactive field access. Accessing `record` on `Window` without type parameter raises TypeError.

```python
@dataclass
class Dog:
    name: str
    age: int

@window
class DogWindow(Window[Dog]):
    label: QLabel = new("Dog Editor")

w = qt.track(DogWindow())
w.record = Dog("Fido", 3)
assert_that(w.record.name).is_equal_to("Fido")
```

## Format Binding Expressions

Complex Python expressions work in bindings: function calls, methods, math, format specs.

```python
@window(title="Test")
class MainWindow(Window):
    _x: Variable[int] = new(10)
    _y: Variable[int] = new(20)
    _z: Variable[int] = new(5)
    result_label: QLabel = new(bind="{(_x + _y) * _z}")

w = qt.track(MainWindow())
assert_that(w.result_label.text()).is_equal_to("150")
```

## Window Placeholder in Bindings

`#window` placeholder (alias for `#widget`) provides access to window instance in bindings.

```python
@window(title="Test Window")
class MainWindow(Window):
    label: QLabel = new(bind="Title: {#window.windowTitle()}")

w = qt.track(MainWindow())
assert_that(w.label.text()).is_equal_to("Title: Test Window")
```

## Property Bindings

`visible=` and `enabled=` accept Variable references or expressions for reactive visibility/enabled state.

```python
@window(title="Test")
class MainWindow(Window):
    _show_label: Variable[bool] = new(True)
    label: QLabel = new("Hello", visible="_show_label")

w = qt.track(MainWindow())
assert not w.label.isHidden()

w._show_label.value = False
assert w.label.isHidden()
```

## Auto-Binding

Widget fields auto-bind to same-named Variables. Explicit `bind=` overrides auto-bind.

```python
@window(title="Test")
class MainWindow(Window):
    _name: Variable[str] = new("Initial")
    name: QLineEdit = new()

w = qt.track(MainWindow())
assert_that(w.name.text()).is_equal_to("Initial")

# Two-way: widget → variable
w.name.setText("Updated")
assert_that(w._name.value).is_equal_to("Updated")
```

## bind() Function

Imperative `bind()` function creates reactive connections in `__setup__`.

```python
@window(title="Test")
class MainWindow(Window):
    _text: Variable[str] = new("")
    input: QLineEdit = new("")

    def __setup__(self) -> None:
        from qtpie import bind
        bind(self._text).to(self.input)

w = qt.track(MainWindow())
w.input.setText("User typed")
assert_that(w._text.value).is_equal_to("User typed")
```

## Variable[T, W] Inline Widgets

`Variable[T, W]` creates both a Variable and a widget, with automatic two-way binding.

```python
@window(title="Test")
class MainWindow(Window):
    name: Variable[str, QLineEdit] = new("Initial")

w = qt.track(MainWindow())
assert_that(w.name.widget.text()).is_equal_to("Initial")

# Variable → widget
w.name.value = "Updated"
assert_that(w.name.widget.text()).is_equal_to("Updated")

# Widget → variable
w.name.widget.setText("Typed")
assert_that(w.name.value).is_equal_to("Typed")
```

## Reactive Window Properties

Decorator kwargs with expressions (e.g., `title="{_var}"`) are reactive.

```python
@window(title="{_name.upper()}")
class MainWindow(Window):
    _name: Variable[str] = new("hello")

w = qt.track(MainWindow())
assert_that(w.windowTitle()).is_equal_to("HELLO")

w._name.value = "world"
assert_that(w.windowTitle()).is_equal_to("WORLD")
```

## Record Auto-Binding

In `Window[T]`, fields auto-bind to same-named record properties.

```python
@dataclass
class Person:
    name: str = ""
    age: int = 0

@window(title="Test")
class MainWindow(Window[Person]):
    name: QLineEdit = new()
    age: QLineEdit = new()

w = qt.track(MainWindow())
w.record.name = "John"
w.record.age = 30
assert_that(w.name.text()).is_equal_to("John")
assert_that(w.age.text()).is_equal_to("30")
```

## Form Layout

Form layout uses `label=` parameter for row labels.

```python
@window(title="Test", layout="form")
class MainWindow(Window):
    name: QLineEdit = new(label="Name:")
    email: QLineEdit = new(label="Email:")

w = qt.track(MainWindow())
layout = w.centralWidget().layout()
assert isinstance(layout, QFormLayout)
assert layout.rowCount() == 2
```

## Grid Layout

Grid layout uses `grid=` parameter for (row, col, [rowspan], [colspan]).

```python
@window(title="Test", layout="grid")
class MainWindow(Window):
    a: QLabel = new("A", grid=(0, 0))
    b: QLabel = new("B", grid=(0, 1))
    c: QLabel = new("C", grid=(1, 0))
    d: QLabel = new("D", grid=(1, 1))

w = qt.track(MainWindow())
layout = w.centralWidget().layout()
assert isinstance(layout, QGridLayout)
assert layout.count() == 4
```

## List Repeater

`Variable[list[T], W]` creates one widget per list item, with reactive updates.

```python
@window(title="Test")
class MainWindow(Window):
    items: Variable[list[str], QLabel] = new(["x", "y"])(bind="Item {#index}: {#self}")

w = qt.track(MainWindow())
repeater = w.items.widget
assert_that(repeater.widget_at(0).text()).is_equal_to("Item 0: x")
assert_that(repeater.widget_at(1).text()).is_equal_to("Item 1: y")

w.items.append("z")
assert repeater.widget_count() == 3
```

## Dict Repeater

`Variable[dict[K, V], W]` creates one widget per dict entry, with `#key` and `#value` placeholders.

```python
@window(title="Test")
class MainWindow(Window):
    scores: Variable[dict[str, int], QLabel] = new({"Alice": 100, "Bob": 85})(bind="{#key}: {#value}")

w = qt.track(MainWindow())
repeater = w.scores.widget
texts = [repeater.widget_for_key(k).text() for k in repeater.keys()]
assert "Alice: 100" in texts
assert "Bob: 85" in texts
```

## list[QWidget] Binding

`list[QWidget]` fields bound to Variables create a widget per item.

```python
@window(title="Test")
class MainWindow(Window):
    _items: Variable[list[str]] = new(["one", "two", "three"])
    labels: list[QLabel] = new(bind="_items")

w = qt.track(MainWindow())
assert len(w.labels) == 3
assert_that(w.labels[0].text()).is_equal_to("one")
```

## Dirty Tracking

Window tracks which Variables have changed via `is_dirty`, `dirty_fields`, and `reset_dirty()`.

```python
@window(title="Test")
class MainWindow(Window):
    _name: Variable[str] = new("")
    _count: Variable[int] = new(0)

w = qt.track(MainWindow())
w._name.value = "changed"
w._count.value = 42

assert_that(w.is_dirty.get()).is_true()
assert_that(w.dirty_fields).is_equal_to({"_name", "_count"})

w.reset_dirty()
assert_that(w.is_dirty.get()).is_false()
```

## on_dirty_changed Hook

Optional `on_dirty_changed(is_dirty: bool)` hook fires only on state transitions (clean ↔ dirty).

```python
dirty_states: list[bool] = []

@window(title="Test")
class MainWindow(Window):
    _name: Variable[str] = new("")
    _count: Variable[int] = new(0)

    @override
    def on_dirty_changed(self, is_dirty: bool) -> None:
        dirty_states.append(is_dirty)

w = qt.track(MainWindow())
w._name.value = "first"  # clean -> dirty
w._name.value = "second"  # dirty -> dirty (no fire)
w._count.value = 42  # dirty -> dirty (no fire)

assert_that(dirty_states).is_equal_to([True])
```

## Validation

Window supports validators on Variables and record fields via `add_validator()`, with `is_valid`, `validation_errors`, and `validation_error_messages` accessors.

```python
@window(title="Test")
class MainWindow(Window):
    _name: Variable[str] = new("")
    _age: Variable[int] = new(0)

    def __setup__(self) -> None:
        self.add_validator("_name", "required", lambda v: None if v else "Required")
        self.add_validator("_age", "positive", lambda v: None if v > 0 else "Must be positive")

w = qt.track(MainWindow())
assert_that(w.is_valid).is_false()

w._name.value = "Alice"
w._age.value = 25
assert_that(w.is_valid).is_true()
```

## on_valid_changed Hook

Optional `on_valid_changed(is_valid: bool)` hook fires when validation state changes.

```python
valid_states: list[bool] = []

@window(title="Test")
class MainWindow(Window):
    _name: Variable[str] = new("")

    def __setup__(self) -> None:
        self.add_validator("_name", "required", lambda v: None if v else "Required")

    @override
    def on_valid_changed(self, is_valid: bool) -> None:
        valid_states.append(is_valid)

w = qt.track(MainWindow())
w._name.value = "hello"
assert_that(valid_states).contains(True)
```

## Aggregate is_dirty

`is_dirty` is an `Observable[bool]` that aggregates dirty state from both Variables and record.

```python
@dataclass
class Person:
    name: str = ""

@window(title="Test", record=Person())
class PersonWindow(Window[Person]):
    _extra: Variable[str] = new("")

w = qt.track(PersonWindow())
assert_that(w.is_dirty.get()).is_false()

# Modify Variable
w._extra.value = "extra"
assert_that(w.is_dirty.get()).is_true()

# Modify record
w.record.name = "Bob"
assert_that(w.is_dirty.get()).is_true()
```

## Required Variable Bindings

Bare `Variable[T]` fields (no `= new()`) are required bindings that must be provided when instantiating child widgets.

```python
@widget
class CounterDisplay(Widget):
    count: Variable[int]  # Required
    label: QLabel = new(bind="Count: {count}")

@window(title="Counter App")
class App(Window):
    _my_count: Variable[int] = new(0)
    display: CounterDisplay = new(count="_my_count")

app = qt.track(App())
assert app.display.count.value == 0

# Window changes → widget updates
app._my_count.value = 42
assert app.display.count.value == 42
```

## Variable Binding Expressions

Child widgets can receive expression bindings and literal bindings from parent window.

```python
@widget
class ConditionalWidget(Widget):
    is_enabled: Variable[bool]

@window(title="Test")
class App(Window):
    _items: Variable[list[str]] = new([])
    child: ConditionalWidget = new(is_enabled="{len(_items) > 0}")

app = qt.track(App())
assert app.child.is_enabled.value is False

app._items.value = ["a", "b"]
assert app.child.is_enabled.value is True
```

## validate= Parameter

`validate=` parameter on Variables registers validators: accepts method name, list of names, callable, tuple (name, validator), or mixed list.

```python
@window(title="Test")
class MainWindow(Window):
    _name: Variable[str] = new(
        "",
        validate=[
            "not_empty",  # Method name
            lambda v: None if len(v) <= 50 else "Too long",  # Lambda
            ("custom", "custom_check"),  # Tuple with method
        ],
    )

    def not_empty(self, v: str) -> str | None:
        return None if v else "Empty"

    def custom_check(self, v: str) -> str | None:
        return None if v.isalpha() else "Letters only"

w = qt.track(MainWindow())
w._name.value = "abc123"
assert_that(w._name.is_valid.get()).is_false()
```

## ref() with Required Bindings

`ref()` function works with required bindings, preserving literal text in expressions.

```python
from qtpie import ref

@dataclass
class Dog:
    name: str = ""
    age: int = 0

@widget
class DogDisplay(Widget):
    dog: Variable[Dog]
    name_label: QLabel = new(text=ref("Dog name: {dog.name}"))

@window(title="Test", record=Dog("Max", 7))
class MainWindow(Window[Dog]):
    dog_display: DogDisplay = new(dog="record")

w = qt.track(MainWindow())
assert_that(w.dog_display.name_label.text()).is_equal_to("Dog name: Max")
```
