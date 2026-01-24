# Input Validator Feature

Input validators restrict what characters can be typed into a QLineEdit. This is different from Widget-level validation (`add_validator`) which validates the final value after input.

## Regex String Validator

Pass a regex pattern string to `validator=` to create a `QRegularExpressionValidator`.

```python
name: QLineEdit = new(validator=r"[a-zA-Z]+")
```

Common patterns:
```python
age: QLineEdit = new(validator=r"[0-9]+")  # Numbers only
name: QLineEdit = new(validator=r"[a-zA-Z0-9 ]+")  # Alphanumeric + spaces
```

## Lambda/Callable Validator

Pass a lambda or function that takes `text: str` and returns `bool` (True = valid).

```python
name: QLineEdit = new(validator=lambda text: len(text) <= 10)
```

Using a named function:
```python
def no_bad_words(text: str) -> bool:
    return "bad" not in text.lower()

comment: QLineEdit = new(validator=no_bad_words)
```

## Full QValidator.State Callable

For full control, pass a function that takes `(text: str, pos: int)` and returns `QValidator.State`.

```python
def my_validator(text: str, pos: int) -> QValidator.State:
    if len(text) >= 3:
        return QValidator.State.Acceptable
    return QValidator.State.Intermediate

name: QLineEdit = new(validator=my_validator)
```

States:
- `Acceptable` - Input is valid
- `Intermediate` - Input is incomplete but could become valid
- `Invalid` - Input should be rejected

## Method Name String Validator

Pass a method name as a string to look up the method on the widget instance.

```python
@widget
class TestWidget(Widget):
    name: QLineEdit = new(validator="validate_name")

    def validate_name(self, text: str) -> bool:
        return len(text) <= 10
```

Method can access widget state via `self`:
```python
max_length: Variable[int] = new(5)
name: QLineEdit = new(validator="validate_name")

def validate_name(self, text: str) -> bool:
    return len(text) <= self.max_length.value
```

Method can also return `QValidator.State` for full control:
```python
def validate_name(self, text: str, pos: int) -> QValidator.State:
    if len(text) >= 3:
        return QValidator.State.Acceptable
    return QValidator.State.Intermediate
```

## Variable[str, QLineEdit] with Validator

When using `Variable[str, QLineEdit]`, pass `validator=` in the second call (widget kwargs).

```python
name: Variable[str, QLineEdit] = new("")(validator=r"[a-zA-Z]+")
```

Lambda version:
```python
name: Variable[str, QLineEdit] = new("")(validator=lambda t: len(t) <= 10)
```

Method name version:
```python
name: Variable[str, QLineEdit] = new("")(validator="validate_name")
```

## Validator with Bind

Validators work with `bind=` for both Variable bindings and record bindings.

```python
_name: Variable[str] = new("")
name_input: QLineEdit = new(bind="_name", validator=r"[a-zA-Z]+")
```

With record binding:
```python
@widget(record=Person())
class TestWidget(Widget[Person]):
    name: QLineEdit = new(bind="name", validator=lambda t: len(t) <= 10)
```
