# Record Field Bindings

## Auto-Binding by Name

Fields with the same name as record properties automatically bind to those properties. Leading underscores are stripped for matching (`_name` binds to `record.name`). Binding is two-way: record changes update the widget, widget changes update the record.

```python
@widget
class PersonEditor(Widget[Person]):
    _name: QLineEdit = new()
    _age: QSpinBox = new()

w = qt.track(PersonEditor())

# Record to widget
w.record_state.observable.name.set("Charlie")
assert_that(w._name.text()).is_equal_to("Charlie")

# Widget to record
w._name.setText("Typed")
assert_that(w.record_state.value.name).is_equal_to("Typed")
```

## Explicit Binding

Use `bind=` to bind a field to a record property with a different name.

```python
@widget
class PersonEditor(Widget[Person]):
    email_input: QLineEdit = new(bind="email")

w = qt.track(PersonEditor())
w.record_state.observable.email.set("test@example.com")
assert_that(w.email_input.text()).is_equal_to("test@example.com")
```

## Disabling Auto-Binding

Set `auto_bind=False` to prevent automatic name-based binding. Explicit `bind=` still works.

```python
@widget(auto_bind=False)
class PersonEditor(Widget[Person]):
    _name: QLineEdit = new()  # No auto-bind
    name_field: QLineEdit = new(bind="name")  # Explicit bind works

w = qt.track(PersonEditor())
w.record_state.observable.name.set("NoBinding")
assert_that(w._name.text()).is_equal_to("")  # Still empty
assert_that(w.name_field.text()).is_equal_to("NoBinding")
```

## Format String Bindings

Use `bind=` with format strings to create reactive labels that reference multiple record fields.

```python
@widget
class PersonView(Widget[Person]):
    title: str = "Profile"
    display: QLabel = new(bind="{title}: {name}")
    summary: QLabel = new(bind="{name}, age {age}")

w = qt.track(PersonView())
w.record_state.observable.name.set("Eve")
w.record_state.observable.age.set(25)
assert_that(w.summary.text()).is_equal_to("Eve, age 25")
```

## Optional Chaining

Use `?.` in bind paths to safely access nested optional fields.

```python
@widget
class EmployeeEditor(Widget[Employee]):
    city: QLineEdit = new(bind="address?.city")

w = qt.track(EmployeeEditor())
# address is None, widget shows empty text (doesn't crash)
assert_that(w.city.text()).is_equal_to("")
```

## Binding to Variables

Fields auto-bind to widget-level `Variable` attributes with matching names (after stripping underscores).

```python
@widget
class MyWidget(Widget):
    _count: Variable[int] = new(0)
    count: QSpinBox = new()  # Auto-binds to _count

w = qt.track(MyWidget())
w._count.value = 42
assert_that(w.count.value()).is_equal_to(42)
```

## Binding Resolution Order

When resolving `{name}` in format strings:
1. Exact widget attribute match (`widget.name`)
2. Record field match (`record.name`)
3. Widget attribute with underscore fallback (`widget._name`)

```python
@widget
class PersonEditor(Widget[Person]):
    _name: QLineEdit = new()
    display: QLabel = new(bind="Name: {name}")

w = qt.track(PersonEditor())
w.record_state.observable.name.set("Alice")
# {name} resolves to record.name, not _name widget
assert_that(w.display.text()).is_equal_to("Name: Alice")
```
