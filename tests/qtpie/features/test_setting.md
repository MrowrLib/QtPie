# Setting Feature Documentation

`Setting[T]` provides persistent reactive state backed by QSettings. It works like `Variable[T]` but automatically saves/loads values to persistent storage.

## Basic Declaration

Declare a Setting with a default value using `new()`:

```python
@widget
class MyWidget(Widget):
    count: Setting[int] = new(42)
    name: Setting[str] = new("default")
    enabled: Setting[bool] = new(False)
```

## Accessing and Modifying Values

Use `.value` property to read/write:

```python
w.count.value = 100
current = w.count.value
```

## Supported Types

### Primitive Types

```python
count: Setting[int] = new(0)
ratio: Setting[float] = new(1.0)
name: Setting[str] = new("")
enabled: Setting[bool] = new(False)
```

### Optional Types

```python
maybe: Setting[str | None] = new(None)
```

### Collections

```python
items: Setting[list[str]] = new([])
scores: Setting[dict[str, int]] = new({})
```

### Enums

```python
class Theme(Enum):
    LIGHT = "light"
    DARK = "dark"

theme: Setting[Theme] = new(Theme.LIGHT)
```

### Dataclasses

```python
@dataclass
class Config:
    name: str = ""
    count: int = 0

config: Setting[Config] = new(Config())
```

## Grouping with `group=`

By default, the storage key is `ClassName:field_name`. Use `group=` for custom grouping:

```python
window_width: Setting[int] = new(800, group="window")
# Stored as "window:window_width" instead of "MyWidget:window_width"
```

Nested groups are supported:

```python
primary: Setting[str] = new("#000", group="ui:theme:colors")
# Stored as "ui:theme:colors:primary"
```

## Collection Mutations

List and dict mutations are automatically persisted:

```python
# List mutations
w.items.append("a")
w.items.extend(["b", "c"])
w.items.remove("b")

# Dict mutations
w.scores["alice"] = 100
w.scores.update({"bob": 85})
del w.scores["bob"]
```

## Augmented Assignment

Augmented operators persist automatically:

```python
w.count += 5
w.items += ["a", "b"]
```

## Setting with Widget (Setting[T, W])

Like `Variable[T, W]`, creates an auto-bound widget:

```python
name: Setting[str, QLineEdit] = new("")
# Access widget via w.name.widget
```

## Widget Bindings

Settings work with format bindings like Variables:

```python
count: Setting[int] = new(0)
label: QLabel = new(bind="Count: {count}")
```

## Dirty Tracking

Settings support dirty tracking:

```python
w.count.is_dirty.get()  # False initially
w.count.value = 100
w.count.is_dirty.get()  # True after change
w.count.reset_dirty()   # Reset to clean
```

## Hierarchy Resolution

### Bare Setting Resolves from Parent

Child widgets can reference parent Settings without defaults:

```python
@widget
class ChildWidget(Widget):
    theme: Setting[str]  # Bare - resolves from parent

@widget
class ParentWidget(Widget):
    theme: Setting[str] = new("light")
    child: ChildWidget = new()
```

### Lookup by Key with `self.setting()`

Look up a Setting's value anywhere in the hierarchy:

```python
def get_theme(self) -> str:
    return self.setting("theme", str)  # By attribute name
    # Or: self.setting("ParentWidget:theme", str)  # By full key
```

## Validation

Settings support validators like Variables:

```python
age: Setting[int] = new(0)

def __setup__(self) -> None:
    self.add_validator("age", "positive", lambda v: None if v >= 0 else "Must be positive")
```

## Important: Dataclass Field Mutation

Direct field mutation on dataclass values does NOT auto-persist. Reassign the whole value:

```python
# This WON'T persist:
w.config.value.name = "modified"

# Do this instead:
w.config.value = Config(name="modified", count=10)
```

## Type Mismatch Handling

When stored data doesn't match the expected type (corrupted, schema change), the default value is used gracefully.
