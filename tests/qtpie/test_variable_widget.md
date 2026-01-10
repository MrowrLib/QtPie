# Variable[T, W] Features

## Widget Type Extraction

`Variable[T, W]` automatically extracts the widget type from the second type parameter and creates an instance bound to the Variable's value.

```python
@widget
class Test(Widget):
    _name: Variable[str, QLineEdit] = new("hello")

w = Test()
assert isinstance(w._name.widget, QLineEdit)
assert w._name.widget.text() == "hello"
```

Two-way binding is automatic - changing the Variable updates the widget, and changing the widget updates the Variable:

```python
w._name.value = "world"
assert w._name.widget.text() == "world"

w._name.widget.setText("updated")
assert w._name.value == "updated"
```

## Layout Order

`Variable[T, W]` widgets appear in the layout in their declaration order, interleaved with regular widgets:

```python
@widget
class MixedForm(Widget):
    _label1: QLabel = new("First")
    _name: Variable[str, QLabel] = new("Second")
    _label2: QLabel = new("Third")
    _age: Variable[str, QLabel] = new("Fourth")

w = MixedForm()
layout = w.layout()

assert layout.itemAt(0).widget().text() == "First"
assert layout.itemAt(1).widget().text() == "Second"
assert layout.itemAt(2).widget().text() == "Third"
assert layout.itemAt(3).widget().text() == "Fourth"
```

## Type Conversion in Bindings

Bindings automatically convert non-string types to strings for text widgets using `str()`:

```python
@widget
class IntDisplay(Widget):
    _count: Variable[int] = new(42)
    _label: QLabel = new("")

    def __setup__(self) -> None:
        bind(self._count).to(self._label)

w = IntDisplay()
assert w._label.text() == "42"

w._count.value = 100
assert w._label.text() == "100"
```

For dataclasses, the `__str__` method is used:

```python
@dataclass
class Person:
    name: str
    age: int

    def __str__(self) -> str:
        return f"{self.name} ({self.age})"

@widget
class PersonDisplay(Widget):
    _person: Variable[Person] = new(default=Person("Alice", 30))
    _label: QLabel = new("")

    def __setup__(self) -> None:
        bind(self._person).to(self._label)

w = PersonDisplay()
assert w._label.text() == "Alice (30)"
```

## Callable Chain Syntax

Use `new(value_args)(widget_args)` to configure both the Variable value and the widget properties:

```python
@widget
class Test(Widget):
    _name: Variable[str, QLineEdit] = new("default")(placeholderText="Enter name...")

w = Test()
assert w._name.value == "default"
assert w._name.widget.placeholderText() == "Enter name..."
```

Multiple widget kwargs can be passed:

```python
@widget
class Test(Widget):
    _name: Variable[str, QLineEdit] = new("hello")(
        placeholderText="Placeholder",
        maxLength=10,
    )

w = Test()
assert w._name.widget.placeholderText() == "Placeholder"
assert w._name.widget.maxLength() == 10
```

## Proxy Field Access

For `Variable[MyClass]`, you can access and modify fields directly through the Variable - it acts as a transparent proxy to the underlying object:

```python
@dataclass
class Dog:
    name: str
    age: int

@widget
class Test(Widget):
    _dog: Variable[Dog] = new(Dog("Fido", 3))

w = Test()

# Read fields
assert w._dog.name == "Fido"
assert w._dog.age == 3

# Write fields - this is reactive
w._dog.name = "Max"
assert w._dog.name == "Max"
```

Field modifications update bound widgets:

```python
@widget(layout="form")
class DogEditor(Widget[Dog]):
    _name: QLineEdit = new(label="Name")
    _age: QSpinBox = new(label="Age")

@widget
class Test(Widget):
    _dog: Variable[Dog, DogEditor] = new(Dog("Fido", 3))

w = Test()
editor = w._dog.widget

assert editor._name.text() == "Fido"

w._dog.name = "Buddy"
assert editor._name.text() == "Buddy"
```

You can also replace the entire object:

```python
w._dog.value = Dog("Rex", 7)
assert editor._name.text() == "Rex"
```

## Signal Connections

Signal connections can be specified in the widget kwargs using either string method names or callables:

```python
@widget
class Test(Widget):
    _input: Variable[str, QLineEdit] = new("")(returnPressed="on_submit")

    def on_submit(self) -> None:
        print("Submitted!")

w = Test()
w._input.widget.returnPressed.emit()  # Calls on_submit()
```

Signal kwargs are extracted and connected properly - they are NOT passed to the widget constructor (which would cause Qt to mangle the names):

```python
@widget
class Test(Widget):
    _input: Variable[str, QLineEdit] = new("")(
        placeholderText="Type here",
        returnPressed="on_submit",
    )

    def on_submit(self) -> None:
        pass

w = Test()
assert w._input.widget.placeholderText() == "Type here"
```

Multiple signals can be connected:

```python
@widget
class Test(Widget):
    _input: Variable[str, QLineEdit] = new("")(
        returnPressed="on_return",
        editingFinished="on_editing_finished",
    )

    def on_return(self) -> None:
        pass

    def on_editing_finished(self) -> None:
        pass
```
