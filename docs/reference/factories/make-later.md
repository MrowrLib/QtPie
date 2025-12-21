# make_later()

Declare a widget field that will be initialized later, typically in the `setup()` lifecycle hook.

## Overview

`make_later()` is used when you need to initialize a field **after** the widget is constructed, usually because:

1. The field depends on other fields that need to be initialized first
2. You need to reference `self` during initialization
3. The field requires complex initialization logic

## Signature

```python
def make_later() -> Any
```

Returns a dataclass field that is excluded from `__init__` and must be set manually.

## Basic Usage

### Simple Deferred Field

```python
from qtpie import widget, make_later

@widget()
class MyWidget(QWidget):
    value: int = make_later()

    def setup(self) -> None:
        self.value = 42
```

The field is uninitialized until you set it in `setup()`.

## Common Use Case: ObservableProxy

The most common use case is creating an `ObservableProxy` that depends on a model field:

```python
from dataclasses import dataclass
from observant import ObservableProxy
from qtpie import Widget, make, make_later, widget

@dataclass
class Dog:
    name: str = ""

@widget()
class DogEditor(QWidget, Widget[Dog]):
    model: Dog = make(Dog)
    proxy: ObservableProxy[Dog] = make_later()  # Must be initialized after model
    name_edit: QLineEdit = make(QLineEdit, bind="proxy.name")

    def setup(self) -> None:
        # Now we can safely reference self.model
        self.proxy = ObservableProxy(self.model, sync=True)
```

**Why use `make_later()` here?**
- The `proxy` needs to wrap the `model` object
- But `model` doesn't exist yet during field initialization
- So we defer `proxy` creation until `setup()` when `model` is available

## Widget[T] with make_later()

When using `Widget[T]`, you can defer model initialization:

```python
@widget()
class PersonEditor(QWidget, Widget[Person]):
    model: Person = make_later()  # Will be set in setup()
    name: QLineEdit = make(QLineEdit)

    def setup(self) -> None:
        # Custom model initialization
        self.model = Person(name="Charlie", age=25)
```

### Error Handling

If you use `make_later()` for the model but **forget** to set it in `setup()`, QtPie will raise a helpful error:

```python
@widget()
class PersonEditor(QWidget, Widget[Person]):
    model: Person = make_later()
    name: QLineEdit = make(QLineEdit)
    # Oops! No setup() method

# Raises: ValueError: Field 'model' marked with make_later() was not set in setup()
w = PersonEditor()
```

This prevents silent failures when you accidentally omit initialization.

## Multiple Deferred Fields

You can use `make_later()` for multiple fields:

```python
@dataclass
class Dog:
    name: str = ""

@dataclass
class Cat:
    name: str = ""

@widget()
class PetEditor(QWidget, Widget[Dog]):
    model: Dog = make(Dog)
    proxy: ObservableProxy[Dog] = make_later()

    cat_model: Cat = make(Cat)
    cat_proxy: ObservableProxy[Cat] = make_later()

    dog_name: QLineEdit = make(QLineEdit, bind="name")
    cat_name: QLineEdit = make(QLineEdit, bind="cat_proxy.name")

    def setup(self) -> None:
        self.proxy = ObservableProxy(self.model, sync=True)
        self.cat_proxy = ObservableProxy(self.cat_model, sync=True)
```

## When to Use make_later()

**Use `make_later()` when:**
- Field initialization depends on other fields
- You need to reference `self` during initialization
- You want to defer complex setup logic to `setup()`

**Don't use `make_later()` when:**
- The field can be initialized independently → Use `make()` instead
- You're just creating a simple widget → Use `make()` instead

## Comparison: make() vs make_later()

```python
# ✓ Use make() - field is independent
label: QLabel = make(QLabel, "Hello")

# ✓ Use make() - simple default value
model: Dog = make(Dog)

# ✓ Use make_later() - depends on model field
proxy: ObservableProxy[Dog] = make_later()

# ✗ DON'T use make_later() unnecessarily
label: QLabel = make_later()  # Just use make()!
```

## Implementation Details

Under the hood, `make_later()` creates a dataclass field with:
- `init=False` - excluded from `__init__`
- Special metadata flag for QtPie tracking

```python
# Equivalent to:
field(init=False, metadata={"qtpie_make_later": True})
```

## Lifecycle Flow

```python
@widget()
class Example(QWidget):
    regular: QLabel = make(QLabel, "I'm created first")
    deferred: int = make_later()

    def setup(self) -> None:
        # Called after regular fields are initialized
        self.deferred = 42

# Execution order:
# 1. __init__() creates 'regular' field
# 2. setup() runs → 'deferred' gets set
# 3. Widget is ready
```

## See Also

- [make()](make.md) - Standard widget factory
- [Widget Lifecycle](../decorators/widget.md#lifecycle-hooks) - When `setup()` is called
- [Widget[T]](../bindings/widget-base.md) - Model widget base class
- [Data Binding](../bindings/bind.md) - Binding widgets to data

## Tips

1. **Always set deferred fields in setup()**
   - QtPie will error if you forget (for Widget[T] models)
   - Your code will error at runtime for other fields

2. **Use for ObservableProxy pattern**
   - This is the #1 use case
   - Model → make(), Proxy → make_later()

3. **Keep it simple**
   - If you can use `make()`, use it
   - Only defer when truly necessary
