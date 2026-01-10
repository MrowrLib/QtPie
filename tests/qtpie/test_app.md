# test_app.py - Feature Summary

## App Class

QtPie's `App` class extends `QApplication` with convenience methods for styling and execution.

```python
def test_app_has_load_stylesheet_method(self, qapp: App) -> None:
    """App should have a load_stylesheet method."""
    assert_that(qapp.load_stylesheet).is_not_none()

def test_app_load_stylesheet_from_file(self, qapp: App, tmp_path: Path) -> None:
    """App should be able to load a stylesheet from a file."""
    qss_file = tmp_path / "test.qss"
    qss_file.write_text("QWidget { background-color: red; }")
    qapp.load_stylesheet(str(qss_file))
    assert_that(qapp.styleSheet()).contains("background-color")
```

## Variable Fields

Reactive state management using `Variable[T]` and `Variable[T, W]`.

```python
@app(show=False, system_tray=False)
class MyApp(AppBase):
    _count: Variable[int] = new(0)
    _name: Variable[str] = new("default")

instance = MyApp()
assert_that(instance._count.value).is_equal_to(0)
instance._count.value = 42
assert_that(instance._count.value).is_equal_to(42)
```

```python
@app(show=False, system_tray=False, window=False)
class MyApp(AppBase):
    _name: Variable[str, QLineEdit] = new("")

instance = MyApp()
assert_that(instance._name.widget).is_instance_of(QLineEdit)
```

## Dirty Tracking

Tracks which fields have changed from initial values.

```python
@app(show=False, system_tray=False)
class MyApp(AppBase):
    _count: Variable[int] = new(0)

instance = MyApp()
assert_that(instance.is_dirty.get()).is_false()

instance._count.value = 1
assert_that(instance.is_dirty.get()).is_true()
assert_that(instance.dirty_fields).contains("_count")

instance.reset_dirty()
assert_that(instance.is_dirty.get()).is_false()
```

```python
@app(show=False, system_tray=False)
class MyApp(AppBase):
    _count: Variable[int] = new(0)

    @override
    def on_dirty_changed(self, is_dirty: bool) -> None:
        changes.append(is_dirty)

instance = MyApp()
instance._count.value = 1
instance.reset_dirty()
assert_that(changes).is_equal_to([True, False])
```

## Validation

Add validators to fields and track overall validity.

```python
@app(show=False, system_tray=False)
class MyApp(AppBase):
    _name: Variable[str] = new("")

instance = MyApp()
instance.add_validator("_name", "required", lambda v: None if v else "Required")
assert_that(instance.is_valid.get()).is_false()
assert_that(instance.validation_error_messages).contains("Required")

instance._name.value = "Alice"
assert_that(instance.is_valid.get()).is_true()
```

```python
@override
def on_valid_changed(self, is_valid: bool) -> None:
    changes.append(is_valid)
```

## Format String Bindings

Reactive text bindings using format strings with expressions.

```python
@app(show=False, system_tray=False, window=False)
class MyApp(AppBase):
    _name: Variable[str] = new("Alice")
    _label: QLabel = new(bind="{_name}")

instance = MyApp()
assert_that(instance._label.text()).is_equal_to("Alice")
```

```python
@app(show=False, system_tray=False, window=False)
class MyApp(AppBase):
    _count: Variable[int] = new(0)
    _label: QLabel = new(bind="Count: {_count}")

instance = MyApp()
assert_that(instance._label.text()).is_equal_to("Count: 0")
instance._count.value = 42
assert_that(instance._label.text()).is_equal_to("Count: 42")
```

```python
@app(show=False, system_tray=False, window=False)
class MyApp(AppBase):
    _x: Variable[int] = new(10)
    _y: Variable[int] = new(5)
    _label: QLabel = new(bind="{_x + _y}")

instance = MyApp()
assert_that(instance._label.text()).is_equal_to("15")
```

```python
@app(show=False, system_tray=False, window=False)
class MyApp(AppBase):
    _name: Variable[str] = new("hello")
    _label: QLabel = new(bind="{_name.upper()}")

instance = MyApp()
assert_that(instance._label.text()).is_equal_to("HELLO")
```

```python
@app(show=False, system_tray=False, window=False)
class MyApp(AppBase):
    _price: Variable[float] = new(19.99)
    _label: QLabel = new(bind="${_price:.2f}")

instance = MyApp()
assert_that(instance._label.text()).is_equal_to("$19.99")
```

## Special Placeholders

Format strings support special placeholders for context access.

```python
@app(show=False, system_tray=False, window=False)
class MyApp(AppBase):
    _name: Variable[str, QLabel] = new("hello")(bind="Value: {#self}")

instance = MyApp()
assert_that(instance._name.widget.text()).is_equal_to("Value: hello")
```

```python
@app(show=False, system_tray=False, window=False)
class MyApp(AppBase):
    _count: Variable[int, QLabel] = new(10)(bind="Double: {#var * 2}")

instance = MyApp()
assert_that(instance._count.widget.text()).is_equal_to("Double: 20")
```

```python
@app(show=False, system_tray=False, window=False)
class MyApp(AppBase):
    title: str = "My App"
    _label: QLabel = new(bind="{#widget.title}")

instance = MyApp()
assert_that(instance._label.text()).is_equal_to("My App")
```

```python
@app(show=False, system_tray=False, window=False)
class MyApp(AppBase):
    def get_greeting(self) -> str:
        return "Hello!"

    _label: QLabel = new(bind="{#widget.get_greeting()}")

instance = MyApp()
assert_that(instance._label.text()).is_equal_to("Hello!")
```

```python
@app(show=False, system_tray=False, window=False)
class MyApp(AppBase):
    _label: QLabel = new(bind="{#app.applicationName()}")

instance = MyApp()
assert_that(instance._label.text()).is_not_empty()
```

## List Binding

Bind widget lists to reactive collections.

```python
@app(show=False, system_tray=False, window=False)
class MyApp(AppBase):
    _items: Variable[list[str]] = new(["A", "B", "C"])
    _labels: list[QLabel] = new(bind="_items")

instance = MyApp()
assert_that(len(instance._labels)).is_equal_to(3)
assert_that(instance._labels[0].text()).is_equal_to("A")
```

```python
@app(show=False, system_tray=False, window=False)
class MyApp(AppBase):
    _nums: Variable[list[int]] = new([1, 2, 3])
    _labels: list[QLabel] = new(bind="_nums", format="Value: {#self}")

instance = MyApp()
assert_that(instance._labels[0].text()).is_equal_to("Value: 1")
```

```python
@app(show=False, system_tray=False, window=False)
class MyApp(AppBase):
    _items: Variable[list[str]] = new(["X", "Y"])
    _labels: list[QLabel] = new(bind="_items", format="#{#index}: {#self}")

instance = MyApp()
assert_that(instance._labels[0].text()).is_equal_to("#0: X")
assert_that(instance._labels[1].text()).is_equal_to("#1: Y")
```

## Dict Binding

Bind widget lists to reactive dictionaries.

```python
@app(show=False, system_tray=False, window=False)
class MyApp(AppBase):
    _scores: Variable[dict[str, int]] = new({"Alice": 100, "Bob": 85})
    _labels: list[QLabel] = new(bind="_scores", format="{#key}: {#value}")

instance = MyApp()
texts = [label.text() for label in instance._labels]
assert_that("Alice: 100" in texts).is_true()
assert_that("Bob: 85" in texts).is_true()
```

## Property Bindings

Control widget visibility and enabled state reactively.

```python
@app(show=False, system_tray=False, window=False)
class MyApp(AppBase):
    _show: Variable[bool] = new(False)
    _panel: QLabel = new("Hidden", visible="_show")

instance = MyApp()
assert_that(instance._panel.isVisible()).is_false()
instance._show.value = True
assert_that(instance._panel.isVisible()).is_true()
```

```python
@app(show=False, system_tray=False, window=False)
class MyApp(AppBase):
    _can_submit: Variable[bool] = new(False)
    _button: QPushButton = new("Submit", enabled="_can_submit")

instance = MyApp()
assert_that(instance._button.isEnabled()).is_false()
instance._can_submit.value = True
assert_that(instance._button.isEnabled()).is_true()
```

```python
@app(show=False, system_tray=False, window=False)
class MyApp(AppBase):
    _count: Variable[int] = new(0)
    _warning: QLabel = new("Low!", visible="{_count < 5}")

instance = MyApp()
assert_that(instance._warning.isVisible()).is_true()
instance._count.value = 10
assert_that(instance._warning.isVisible()).is_false()
```

## Record Type Support

Type-safe record binding with `AppBase[T]`.

```python
@dataclass
class Settings:
    name: str = ""
    count: int = 0

@app(show=False, system_tray=False, record=Settings("test", 42))
class MyApp(AppBase[Settings]):
    pass

instance = MyApp()
assert_that(instance.record.name).is_equal_to("test")
instance.record.name = "Bob"
assert_that(instance.record.name).is_equal_to("Bob")
```

```python
@dataclass
class User:
    username: str = ""

@app(show=False, system_tray=False, window=False, record=User("alice"))
class MyApp(AppBase[User]):
    username: QLineEdit = new()

instance = MyApp()
assert_that(instance.username.text()).is_equal_to("alice")
```

```python
@app(show=False, system_tray=False, window=False, record=Dog("Rover", 5))
class MyApp(AppBase[Dog]):
    dog_menu: DogMenu = new(dog="record")

instance = MyApp()
assert_that(instance.dog_menu.dog.name).is_equal_to("Rover")

instance.dog_menu.dog.name = "Max"
assert_that(instance.record.name).is_equal_to("Max")
```

## ref() with Required Bindings

Use `ref()` to reference fields that will be bound later.

```python
@menu
class DogMenu(Menu):
    dog: Variable[Dog]
    dog_action: QAction = new(text=ref("{dog.name}"))

@app(show=False, system_tray=False, window=False, record=Dog("Fido", 3))
class MyApp(AppBase[Dog]):
    dog_menu: DogMenu = new(dog="record")

instance = MyApp()
assert_that(instance.dog_menu.dog_action.text()).is_equal_to("Fido")
```

## Signal Connections

Connect Qt signals to methods or lambdas.

```python
@app(show=False, system_tray=False, window=False)
class MyApp(AppBase):
    _button: QPushButton = new("Click", clicked="on_click")

    def on_click(self) -> None:
        nonlocal clicked
        clicked = True

instance = MyApp()
instance._button.click()
assert_that(clicked).is_true()
```

```python
@app(show=False, system_tray=False, window=False)
class MyApp(AppBase):
    _button: QPushButton = new("Click", clicked=lambda: values.append("clicked"))

instance = MyApp()
instance._button.click()
assert_that(values).contains("clicked")
```

## Lifecycle Hooks

`__setup__()` hook called during initialization.

```python
@app(show=False, system_tray=False)
class MyApp(AppBase):
    _count: Variable[int] = new(0)

    def __setup__(self) -> None:
        self._count.value = 100

instance = MyApp()
assert_that(instance._count.value).is_equal_to(100)
```

```python
@app(show=False, system_tray=False)
class MyApp(AppBase):
    _name: Variable[str] = new("")

    def __setup__(self) -> None:
        self.add_validator("_name", "req", lambda v: None if v else "Required")

instance = MyApp()
assert_that(instance.is_valid.get()).is_false()
```

## System Tray

QAction fields automatically create system tray icons with context menus.

```python
from qtpy.QtGui import QAction

@app(show=False, window=False)
class MyApp(AppBase):
    action: QAction = new("Say Hello")

instance = MyApp()
assert_that(instance._system_tray).is_instance_of(QSystemTrayIcon)

tray_menu = instance._system_tray.contextMenu()
actions = tray_menu.actions()
action_texts = [a.text() for a in actions]
assert_that(action_texts).contains("Say Hello")
```

```python
@app(show=False, window=False)
class MyApp(AppBase):
    action1: QAction = new("First")
    ___: Separator
    action2: QAction = new("Second")

instance = MyApp()
tray_menu = instance._system_tray.contextMenu()
actions = tray_menu.actions()
assert_that(actions[0].text()).is_equal_to("First")
assert_that(actions[1].isSeparator()).is_true()
assert_that(actions[2].text()).is_equal_to("Second")
```

```python
from qtpie.menu import Section

@app(show=False, window=False)
class MyApp(AppBase):
    ___my_section___: Section
    action: QAction = new("Hello")

instance = MyApp()
tray_menu = instance._system_tray.contextMenu()
actions = tray_menu.actions()
assert_that(actions[0].text()).is_equal_to("My Section")
```
