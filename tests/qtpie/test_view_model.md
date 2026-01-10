# View Model Tests

## Auto-Generated View Model

Widgets automatically get a `view_model` property that contains all `Variable` fields (excluding non-Variable widgets). The view model provides an alternative access path to the same Variable instances, useful for separation of concerns.

```python
@widget
class MyWidget(Widget):
    _name: Variable[str] = new("hello")
    _count: Variable[int] = new(42)
    _label: QLabel = new("Hello")

w = qt.track(MyWidget())

# Access Variables through view_model
assert_that(w._qtpie.view_model._name.value).is_equal_to("hello")
assert_that(w._qtpie.view_model._count.value).is_equal_to(42)

# QLabel is not accessible through view_model
with pytest.raises(AttributeError):
    _ = w._qtpie.view_model._label
```

## Same Instance Sharing

The view model Variables are the exact same instances as the widget's Variables. Changes through either path are immediately visible through the other.

```python
@widget
class MyWidget(Widget):
    _name: Variable[str] = new("")

w = qt.track(MyWidget())

# They should be the exact same Variable instance
assert_that(w._qtpie.view_model._name).is_same_as(w._name)

# Changes via view_model are visible on widget
w._qtpie.view_model._name.value = "changed"
assert_that(w._name.value).is_equal_to("changed")

# Changes via widget are visible on view_model
w._name.value = "changed"
assert_that(w._qtpie.view_model._name.value).is_equal_to("changed")
```

## Binding Support

View model Variables can be used with `bind()` just like regular Variables.

```python
@widget
class MyWidget(Widget):
    _name: Variable[str] = new("Hello")
    _label: QLabel = new("")

    def __setup__(self) -> None:
        bind(self._qtpie.view_model._name).to(self._label)

w = qt.track(MyWidget())
assert_that(w._label.text()).is_equal_to("Hello")

# Update via view_model
w._qtpie.view_model._name.value = "World"
assert_that(w._label.text()).is_equal_to("World")
```
