# Observant Integration

QtPie's reactive features are powered by [**Observant**](https://mrowrlib.github.io/observant.py/) ([PyPI](https://pypi.org/project/observant/)), a reactive state management library for Python.

You don't need to understand Observant to use QtPie - the `state()` function and `Widget[T]` handle everything automatically. This page is for users who want to understand the internals or use Observant directly.

---

## What is Observant?

Observant provides:

- **Observable** - A value that notifies listeners when it changes
- **ObservableProxy** - Wraps any object (dataclass, etc.) making all its fields observable
- **Validation** - Field-level validation with reactive error lists
- **Dirty Tracking** - Know which fields changed since last save
- **Undo/Redo** - Per-field history with configurable limits

---

## How QtPie Uses Observant

### state() Fields

When you use `state()`:

```python
@widget
class Counter(QWidget):
    count: int = state(0)
```

Under the hood, QtPie creates an `ObservableProxy` that wraps your value. When you assign to `self.count`, the proxy notifies all bound widgets to update.

### Widget[T] Models

When you use `Widget[T]`:

```python
@widget
class PersonEditor(QWidget, Widget[Person]):
    name: QLineEdit = make(QLineEdit)
```

QtPie automatically:

1. Creates a `Person()` instance as `self.model`
2. Wraps it in `ObservableProxy` as `self.proxy`
3. Auto-binds widget fields to proxy fields by name

The proxy enables two-way binding, validation, dirty tracking, and undo/redo.

---

## Using Observant Directly

Sometimes you need direct access to Observant features.

### Subscribing to Changes

```python
from qtpie.state import get_state_observable

@widget
class Counter(QWidget):
    count: int = state(0)

    def setup(self) -> None:
        obs = get_state_observable(self, "count")
        obs.on_change(lambda value: print(f"Count changed to {value}"))
```

### Working with Widget[T] Proxy

```python
@widget
class PersonEditor(QWidget, Widget[Person]):
    name: QLineEdit = make(QLineEdit)

    def setup_bindings(self) -> None:
        # Get observable for a field
        name_obs = self.proxy.observable(str, "name")

        # Subscribe to changes
        name_obs.on_change(lambda v: print(f"Name: {v}"))

        # Read/write
        current = name_obs.get()
        name_obs.set("Alice")
```

### Nested Path Access

```python
# Get observable for nested path
city_obs = self.proxy.observable_for_path("address.city")

# With optional chaining
owner_name_obs = self.proxy.observable_for_path("owner?.name")
```

---

## When to Use Observant Directly

**You usually don't need to.** QtPie's `bind=` parameter handles most cases.

Use Observant directly when you need:

- Custom change handlers beyond what `bind=` provides
- Programmatic access to observables for complex logic
- Features not exposed through QtPie's API

---

## Learn More

- [Observant Documentation](https://mrowrlib.github.io/observant.py/)
- [Observant on PyPI](https://pypi.org/project/observant/)
- [ObservableProxy Reference](https://mrowrlib.github.io/observant.py/api_reference/observable_proxy/)
- [Nested Paths](https://mrowrlib.github.io/observant.py/features/nested_paths/)
- [Validation](https://mrowrlib.github.io/observant.py/features/validation/)
- [Undo/Redo](https://mrowrlib.github.io/observant.py/features/undo/)

---

## See Also

- [Reactive State](../data/state.md) - Using `state()` for reactive fields
- [Model Widgets](../data/model-widgets.md) - Using `Widget[T]` for forms
- [Validation](../data/validation.md) - Field validation
- [Dirty Tracking](../data/dirty.md) - Change detection
- [Undo & Redo](../data/undo.md) - History management
