# Variable Widget Binding

This documents `Variable[T, Widget[T]]` - binding a Variable to a custom Widget subclass that has a record type.

## Core Concept

When you have a `Widget[T]` subclass (a widget with a typed record), you can use it as the widget type in a `Variable[T, WidgetClass]`. This creates a bidirectional binding where the Variable's observable proxy is shared with the child widget's record.

## Defining a Record Widget

Create a `Widget[T]` subclass that edits a dataclass:

```python
@dataclass
class Dog:
    name: str
    age: int

@widget(layout="form")
class DogEditor(Widget[Dog]):
    _name: QLineEdit = new(label="Dog's Name")
    _age: QSpinBox = new(label="Dog's Age")
```

Fields named after record properties (`_name`, `_age`) auto-bind to `record.name`, `record.age`.

## Single Record Binding

Use `Variable[T, Widget[T]]` to embed an editor widget:

```python
@widget
class TestWidget(Widget):
    dog: Variable[Dog, DogEditor] = new(Dog("Fido", 3))
```

Access the created widget via `.widget`:

```python
editor = w.dog.widget  # Returns DogEditor instance
```

## Bidirectional Reactivity

The Variable and Widget share the same observable proxy:

```python
# Change via parent Variable - updates child widget
w.dog.observable.name.set("Buddy")
assert editor._name.text() == "Buddy"

# Change via child widget - updates parent Variable
editor._name.setText("Max")
assert w.dog.observable.name.get() == "Max"
```

## List Binding with WidgetRepeater

Use `Variable[list[T], Widget[T]]` to create a repeater of editor widgets:

```python
@widget
class TestWidget(Widget):
    dogs: Variable[list[Dog], DogEditor] = new([
        Dog("Fido", 3),
        Dog("Rex", 5),
    ])
```

Access repeater and individual editors:

```python
repeater = w.dogs.widget
assert repeater.widget_count() == 2

editor0 = repeater.widget_at(0)
assert editor0._name.text() == "Fido"
```

## List Mutations

Appending/removing from the list automatically adds/removes editor widgets:

```python
w.dogs.append(Dog("Buddy", 2))
assert repeater.widget_count() == 3

w.dogs.remove(Dog("Fido", 3))
assert repeater.widget_count() == 2
```

## Editing List Items

Changes in any editor update the underlying list:

```python
editor = repeater.widget_at(0)
editor._name.setText("Buddy")
assert w.dogs[0].name == "Buddy"
```

## Nested Widget Records

A `Widget[T]` can contain `Variable[U, Widget[U]]` for nested editing:

```python
@widget(layout="vertical")
class PetWithOwner(Widget[Pet]):
    _pet_name: QLineEdit = new()
    owner_editor: Variable[Owner, OwnerEditor] = new(Owner("John"))
```
