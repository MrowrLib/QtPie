# Variable[T, W] Features

## Widget Type Extraction

Variable can take a second type parameter to automatically create and bind a widget. `Variable[T, W]` extracts `W` as the widget type, creates an instance, and binds it to the variable's value.

```python
@widget
class Test(Widget):
    _name: Variable[str, QLineEdit] = new("hello")  # type: ignore[type-arg]

w = qt.track(Test())

# Widget is created and bound
assert isinstance(w._name.widget, QLineEdit)
assert w._name.widget.text() == "hello"

# Changing Variable updates widget
w._name.value = "world"
assert w._name.widget.text() == "world"

# Two-way: changing widget updates Variable
w._name.widget.setText("updated")
assert w._name.value == "updated"
```

## Layout Order

Variable[T, W] widgets appear in the layout in the same order as field declaration, interleaved with regular widgets.

```python
@widget
class MixedForm(Widget):
    _label1: QLabel = new("First")
    _name: Variable[str, QLabel] = new("Second")  # type: ignore[type-arg]
    _label2: QLabel = new("Third")
    _age: Variable[str, QLabel] = new("Fourth")  # type: ignore[type-arg]

w = qt.track(MixedForm())
layout = w.layout()

# Should be 4 widgets in order: label1, name.widget, label2, age.widget
assert layout.count() == 4
assert layout.itemAt(0).widget().text() == "First"
assert layout.itemAt(1).widget().text() == "Second"
assert layout.itemAt(2).widget().text() == "Third"
assert layout.itemAt(3).widget().text() == "Fourth"
```

## Type Conversion in Bindings

Binding automatically converts types when needed - primitives to strings for QLabel, dataclasses using `__str__()`.

```python
@widget
class IntDisplay(Widget):
    _count: Variable[int] = new(42)
    _label: QLabel = new("")

    def __setup__(self) -> None:
        bind(self._count).to(self._label)

w = qt.track(IntDisplay())

# Initial binding should convert int to str
assert w._label.text() == "42"

# Changing the value should update the label
w._count.value = 100
assert w._label.text() == "100"
```

## Callable Chain Syntax

`new(value_args)(widget_args)` allows passing constructor kwargs to the widget separately from the variable's default value.

```python
@widget
class Test(Widget):
    _name: Variable[str, QLineEdit] = new("default")(placeholderText="Enter name...")  # type: ignore[type-arg]

w = qt.track(Test())

# Value should be set
assert w._name.value == "default"
assert w._name.widget.text() == "default"

# Widget kwarg should be applied
assert w._name.widget.placeholderText() == "Enter name..."
```

```python
@widget
class Test(Widget):
    _count: Variable[int, QSpinBox] = new(50)(minimum=0, maximum=100)  # type: ignore[type-arg]

w = qt.track(Test())

assert w._count.value == 50
assert w._count.widget.value() == 50
assert w._count.widget.minimum() == 0
assert w._count.widget.maximum() == 100
```

## Proxy Field Access

For `Variable[MyClass]`, direct field access on the variable forwards to the wrapped object and is reactive via ObservableProxy.

```python
@dataclass
class Dog:
    name: str
    age: int

@widget
class Test(Widget):
    _dog: Variable[Dog] = new(Dog("Fido", 3))
    _label: QLabel = new("")

    def __setup__(self) -> None:
        # Set initial value
        self._label.setText(f"Name: {self._dog.name}")
        # Bind to the observable manually to verify reactivity
        self._dog.observable.name.on_change(lambda v: self._label.setText(f"Name: {v}"))

w = qt.track(Test())

# Initial state
assert w._label.text() == "Name: Fido"

# Change via direct field access
w._dog.name = "Max"

# Should have triggered the callback
assert w._label.text() == "Name: Max"
```

Field assignment updates bound widgets:

```python
@widget(layout="form")
class DogEditor(Widget[Dog]):
    _name: QLineEdit = new(label="Name")
    _age: QSpinBox = new(label="Age")

@widget
class Test(Widget):
    _dog: Variable[Dog, DogEditor] = new(Dog("Fido", 3))  # type: ignore[type-arg]

w = qt.track(Test())
editor = w._dog.widget

# Initial state - widget should show values
assert editor._name.text() == "Fido"
assert editor._age.value() == 3

# Change via direct field access on Variable
w._dog.name = "Buddy"
w._dog.age = 5

# Widget should update
assert editor._name.text() == "Buddy"
assert editor._age.value() == 5
```

## Signal Connections

Signal connections in the callable chain (e.g., `returnPressed="handler"`) are extracted and properly connected to the parent widget's methods, not passed to the widget constructor.

```python
@widget
class Test(Widget):
    _input: Variable[str, QLineEdit] = new("")(returnPressed="on_submit")  # type: ignore[type-arg]

    def on_submit(self) -> None:
        nonlocal call_count
        call_count += 1

w = qt.track(Test())

# Simulate pressing Enter in the line edit
w._input.widget.returnPressed.emit()

assert call_count == 1
```

Multiple signals can be connected:

```python
@widget
class Test(Widget):
    _input: Variable[str, QLineEdit] = new("")(  # type: ignore[type-arg]
        returnPressed="on_return",
        editingFinished="on_editing_finished",
    )

    def on_return(self) -> None:
        nonlocal return_pressed_count
        return_pressed_count += 1

    def on_editing_finished(self) -> None:
        nonlocal editing_finished_count
        editing_finished_count += 1

w = qt.track(Test())

w._input.widget.returnPressed.emit()
assert return_pressed_count == 1
assert editing_finished_count == 0

w._input.widget.editingFinished.emit()
assert return_pressed_count == 1
assert editing_finished_count == 1
```
