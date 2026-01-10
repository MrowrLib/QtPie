# Variable[T, Widget[T]] Binding

Binding `Variable` to custom `Widget[T]` subclasses, enabling declarative nested editors with automatic record synchronization.

## Single Widget Binding

`Variable[T, Widget[T]]` creates a widget instance and shares the underlying `ObservableProxy` between the Variable and the Widget's record. Changes in either direction propagate automatically.

```python
@widget(layout="form")
class DogEditor(Widget[Dog]):
    _name: QLineEdit = new(label="Dog's Name")
    _age: QSpinBox = new(label="Dog's Age")

@widget
class TestWidget(Widget):
    dog: Variable[Dog, DogEditor] = new(Dog("Fido", 3))

w = TestWidget()

# Variable and Widget[T].record share the same ObservableProxy
assert w.dog.observable is w.dog.widget._qtpie.record_state.observable

# Change via parent's Variable
w.dog.observable.name.set("Buddy")
assert w.dog.widget.record.name == "Buddy"
assert w.dog.widget._name.text() == "Buddy"

# Change via child widget's QLineEdit
w.dog.widget._name.setText("Max")
assert w.dog.observable.name.get() == "Max"
```

## List Widget Binding

`Variable[list[T], Widget[T]]` creates a `WidgetRepeater` with one `Widget[T]` instance per list item. Add/remove operations automatically add/remove widget instances.

```python
@widget
class TestWidget(Widget):
    dogs: Variable[list[Dog], DogEditor] = new([
        Dog("Fido", 3),
        Dog("Rex", 5),
    ])

w = TestWidget()
repeater = w.dogs.widget

# One editor per item
assert repeater.widget_count() == 2
assert repeater.widget_at(0)._name.text() == "Fido"
assert repeater.widget_at(1)._name.text() == "Rex"

# Append adds a new editor
w.dogs.append(Dog("Buddy", 2))
assert repeater.widget_count() == 3

# Edit in one editor updates the underlying list
repeater.widget_at(0)._name.setText("Max")
assert w.dogs[0].name == "Max"
```

## Nested Widget Records

`Widget[T]` can contain `Variable[U, Widget[U]]` for nested editors.

```python
@widget(layout="form")
class OwnerEditor(Widget[Owner]):
    _name: QLineEdit = new(label="Owner Name")

@widget(layout="vertical")
class PetWithOwner(Widget[Pet]):
    _pet_name: QLineEdit = new()
    owner_editor: Variable[Owner, OwnerEditor] = new(Owner("John"))

w = PetWithOwner()
w.record = Pet("Fido", Owner("Jane"))

# Nested editor works
w.owner_editor.observable.name.set("Bob")
assert w.owner_editor.widget._name.text() == "Bob"
```
