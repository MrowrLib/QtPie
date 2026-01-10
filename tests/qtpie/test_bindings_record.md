# Record Field Auto-Binding

## Auto-Binding by Name

Widget fields with matching names automatically bind to record fields. Field names can have leading underscores which are stripped for matching.

```python
@widget
class PersonEditor(Widget[Person]):
    name: QLineEdit = new()
    _age: QSpinBox = new()

w = qt.track(PersonEditor())
w._qtpie.record_state.observable.name.set("Charlie")
w._qtpie.record_state.observable.age.set(30)

assert_that(w.name.text()).is_equal_to("Charlie")
assert_that(w._age.value()).is_equal_to(30)
```

## Two-Way Binding

Widget changes automatically update the record.

```python
@widget
class PersonEditor(Widget[Person]):
    _name: QLineEdit = new()

w = qt.track(PersonEditor())
w._name.setText("Typed")
assert_that(w._qtpie.record_state.value.name).is_equal_to("Typed")
```

## Explicit Binding with `bind=`

Use `bind=` to map a widget to a different field than its name suggests.

```python
@widget
class PersonEditor(Widget[Person]):
    email_input: QLineEdit = new(bind="email")

w = qt.track(PersonEditor())
w._qtpie.record_state.observable.email.set("test@example.com")
assert_that(w.email_input.text()).is_equal_to("test@example.com")
```

## Disabling Auto-Binding

Use `auto_bind=False` to prevent automatic name-based binding. Explicit `bind=` still works.

```python
@widget(auto_bind=False)
class PersonEditor(Widget[Person]):
    _name: QLineEdit = new()  # Won't auto-bind
    name_field: QLineEdit = new(bind="name")  # Explicit still works

w = qt.track(PersonEditor())
w._qtpie.record_state.observable.name.set("NoBinding")
assert_that(w._name.text()).is_equal_to("")  # No binding
```

## Variable Auto-Binding

Fields also auto-bind to widget-level Variables.

```python
@widget
class MyWidget(Widget):
    _count: Variable[int] = new(0)
    count: QSpinBox = new()  # Auto-binds to _count

w = qt.track(MyWidget())
w._count.value = 42
assert_that(w.count.value()).is_equal_to(42)
```

## Format String Binding

Bind widgets to formatted strings combining multiple fields. Updates reactively when any referenced field changes.

```python
@widget
class PersonView(Widget[Person]):
    summary: QLabel = new(bind="{name}, age {age}")

w = qt.track(PersonView())
w._qtpie.record_state.observable.name.set("Eve")
w._qtpie.record_state.observable.age.set(25)
assert_that(w.summary.text()).is_equal_to("Eve, age 25")
```

Format strings can combine reactive record fields with static widget attributes:

```python
@widget
class PersonView(Widget[Person]):
    title: str = "Profile"
    display: QLabel = new(bind="{title}: {name}")

w = qt.track(PersonView())
w._qtpie.record_state.observable.name.set("Eve")
assert_that(w.display.text()).is_equal_to("Profile: Eve")
```

## Optional Chaining

Use `?.` for safe access to nullable nested fields.

```python
@widget
class EmployeeEditor(Widget[Employee]):
    city: QLineEdit = new(bind="address?.city")

w = qt.track(EmployeeEditor())
# address is None, widget shows empty text (no crash)
assert_that(w.city.text()).is_equal_to("")
```

## Binding Resolution Order

Format string field resolution follows priority: exact widget attribute > record field > underscore widget attribute.

```python
@widget
class PersonEditor(Widget[Person]):
    _name: QLineEdit = new()
    display: QLabel = new(bind="Name: {name}")

w = qt.track(PersonEditor())
w._qtpie.record_state.observable.name.set("Alice")

# {name} resolves to record.name, not _name widget
assert_that(w.display.text()).is_equal_to("Name: Alice")
```

```python
@widget
class TitledEditor(Widget[Person]):
    title: str = "Static Title"  # Exact match wins
    display: QLabel = new(bind="{title}: {name}")

w = qt.track(TitledEditor())
w._qtpie.record_state.observable.name.set("Bob")

# title from widget.title, name from record.name
assert_that(w.display.text()).is_equal_to("Static Title: Bob")
```
