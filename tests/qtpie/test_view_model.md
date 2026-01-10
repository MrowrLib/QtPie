# View Model Tests

## Auto-Generated View Model

Widgets automatically create a `view_model` property that provides access to all `Variable[T]` fields. Non-Variable fields are excluded. The view model is a stable singleton instance.

```python
@widget
class MyWidget(Widget):
    _name: Variable[str] = new("hello")
    _count: Variable[int] = new(42)

w = qt.track(MyWidget())

# Access Variables through view_model
assert_that(w._qtpie.view_model._name.value).is_equal_to("hello")
assert_that(w._qtpie.view_model._count.value).is_equal_to(42)
```

## Shared Variable References

Variables accessed via `view_model` are the same instances as those on the widget. Changes through either path are immediately visible on the other.

```python
@widget
class MyWidget(Widget):
    _name: Variable[str] = new("")

w = qt.track(MyWidget())

# They are the exact same Variable instance
assert_that(w._qtpie.view_model._name).is_same_as(w._name)

# Changes via view_model reflect on widget
w._qtpie.view_model._name.value = "changed"
assert_that(w._name.value).is_equal_to("changed")
```

## Binding via View Model

View model variables can be used with the `bind()` function for reactive bindings.

```python
@widget
class MyWidget(Widget):
    _name: Variable[str] = new("Hello")
    _label: QLabel = new("")

    def __setup__(self) -> None:
        bind(self._qtpie.view_model._name).to(self._label)

w = qt.track(MyWidget())
assert_that(w._label.text()).is_equal_to("Hello")

w._qtpie.view_model._name.value = "World"
assert_that(w._label.text()).is_equal_to("World")
```
