# Variable[T, Widget[T]] Binding

## Single Widget Binding

`Variable[T, Widget[T]]` creates a widget and binds it to an observable proxy. The Variable and the Widget's record share the same ObservableProxy, enabling bidirectional sync.

```python
@widget
class TestWidget(Widget):
    dog: Variable[Dog, DogEditor] = new(Dog("Fido", 3))

w = qt.track(TestWidget())
editor = w.dog.widget

# Shares the same proxy
assert w.dog.observable is editor._qtpie.record_state.observable

# Change via Variable updates widget
w.dog.observable.name.set("Buddy")
assert editor._name.text() == "Buddy"

# Change via widget updates Variable
editor._name.setText("Max")
assert w.dog.observable.name.get() == "Max"
```

## List Widget Binding

`Variable[list[T], Widget[T]]` creates a WidgetRepeater with one Widget[T] instance per list item. Adding/removing items dynamically adds/removes widgets.

```python
@widget
class TestWidget(Widget):
    dogs: Variable[list[Dog], DogEditor] = new([Dog("Fido", 3), Dog("Rex", 5)])

w = qt.track(TestWidget())
repeater = w.dogs.widget

# One editor per item
assert repeater.widget_count() == 2
assert repeater.widget_at(0)._name.text() == "Fido"

# Append adds editor
w.dogs.append(Dog("Buddy", 2))
assert repeater.widget_count() == 3

# Edit in widget updates list
repeater.widget_at(0)._name.setText("Buddy")
assert w.dogs[0].name == "Buddy"
```

## Error Handling

Using a Widget without a record type (plain `Widget`, not `Widget[T]`) raises an error.

```python
@widget
class PlainWidget(Widget):
    _label: QLabel = new("Hello")

@widget
class TestWidget(Widget):
    plain: Variable[str, PlainWidget] = new("test")

# Raises ValueError because PlainWidget has no record type
with pytest.raises(ValueError, match="No binding registered"):
    qt.track(TestWidget())
```

## Nested Widget Records

`Widget[T]` can contain `Variable[U, Widget[U]]` fields for nested records.

```python
@widget(layout="vertical")
class PetWithOwner(Widget[Pet]):
    _pet_name: QLineEdit = new()
    owner_editor: Variable[Owner, OwnerEditor] = new(Owner("John"))

w = qt.track(PetWithOwner())
w.record = Pet("Fido", Owner("Jane"))

# Nested editor uses initial value from new()
assert w.owner_editor.widget._name.text() == "John"

# Bidirectional binding works
w.owner_editor.observable.name.set("Bob")
assert w.owner_editor.widget._name.text() == "Bob"
```
