from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import override

from qtpy.QtCore import Signal
from qtpy.QtGui import QAction
from qtpy.QtWidgets import QAbstractItemView, QCheckBox, QLabel, QLineEdit, QListView, QPushButton, QStyle, QTableView, QTabWidget, QTreeView

from qtpie import App, Menu, Variable, Widget, app, entrypoint, menu, new, ref, set_language, slot, t, widget


@dataclass
class Animal:
    name: str
    species: str


@widget
class VariableValidationWidget(Widget):
    _text: Variable[str] = new("")
    _text_edit: QLineEdit = new(bind="_text")
    _btn: QPushButton = new("Click me", clicked="on_button_clicked")

    def __setup__(self) -> None:
        self._text.add_validator("not-empty", self.validate_not_empty)
        # self._text.is_valid.on_change(self.on_validity_change)
        # self.val

    def validate_not_empty(self, value: str) -> str | None:
        if not value.strip():
            return "Text cannot be empty."
        return None

    def on_validity_change(self, is_valid: bool) -> None:
        print(f"Text validity changed: {is_valid}")
        if not is_valid:
            print("Errors:", self._text.validation_error_messages.get())

    def on_button_clicked(self) -> None:
        print(f"Button clicked! Current text: {self._text.value}")


@widget
class CustomWidgetWhichCanDisplayMultipleErrors(Widget):
    pass


@widget(title="Variables with Widgets")
class VarsWithWidgets(Widget):
    var1: Variable[int, QLineEdit] = new()(placeholderText="Enter a number")
    var2: Variable[str, QLineEdit] = new()(placeholderText="Enter text here")
    btn: QPushButton = new("Print Vars", clicked="print_vars")

    def print_vars(self) -> None:
        print(f"var1: {self.var1.value}, var2: {self.var2.value}")


@dataclass
class Dog:
    name: str
    age: int


@widget(layout="form")
class DogEditor(Widget[Dog]):
    name: QLineEdit = new(label="Dog's Name")
    age: QLineEdit = new(label="Dog's Age")


@widget
class HasOneDogForm(Widget):
    dog: Variable[Dog, DogEditor] = new(Dog("Fido", 3))
    btn_print_dog: QPushButton = new("Print Dog", clicked="print_dog")
    btn_change_dog_name: QPushButton = new("Change Dog Name", clicked="change_dog_name")
    btn_change_dog_object: QPushButton = new("Change Dog Object", clicked="change_dog_object")

    def print_dog(self) -> None:
        print(f"{self.dog.value.name} is {self.dog.value.age} years old.")

    def change_dog_name(self) -> None:
        self.dog.name = "Max"

    def change_dog_object(self) -> None:
        self.dog = Dog("Buddy", 4)  # is there a way to replace the underlying object in an ObservableProxy?


@widget
class HasMultipleDogForms(Widget):
    dogs: Variable[list[Dog], DogEditor] = new([Dog("Fido", 3), Dog("Rex", 5)])
    btn_print_dogs: QPushButton = new("Print Dogs", clicked="print_dogs")

    def print_dogs(self) -> None:
        for dog in self.dogs:
            print(f"{dog.name} is {dog.age} years old.")


@widget
class ListsOfThings(Widget):
    regular_int: Variable[int] = new(0)
    numbers: Variable[list[int], QLabel] = new([1, 2, 3])(bind="Index: {#index} is {#self}")
    dogs: Variable[list[Dog], QLabel] = new([Dog("Fido", 3), Dog("Buddy", 5)])(bind="{name} is {age} years old")

    btn_add: QPushButton = new("Add Number", clicked="add_number")
    btn_remove: QPushButton = new("Remove Number", clicked="remove_number")

    new_dog_name: Variable[str, QLineEdit] = new("")(placeholderText="New Dog Name")
    new_dog_age: Variable[int, QLineEdit] = new(0)(placeholderText="New Dog Age")
    btn_add_dog: QPushButton = new("Add Dog", clicked="add_dog")

    def add_number(self) -> None:
        self.regular_int += 1
        self.numbers.append(self.regular_int.value)

    def remove_number(self) -> None:
        last_number = self.numbers[-1]
        self.numbers.remove(last_number)

    def add_dog(self) -> None:
        name = self.new_dog_name.value.strip()
        age = int(self.new_dog_age)
        if name:
            new_dog = Dog(name=name, age=age)
            self.dogs.append(new_dog)
            self.new_dog_name.value = ""
            self.new_dog_age.value = 0


# @widget
# class VariableValidationErrorExample(Widget):
#     text_var: Variable[str] = new("", validate=lambda v: "Text cannot be empty." if not v.strip() else None)

#     # Show error messages from one specific field
#     error_messages: list[QLabel] = new(bind="text_var.validation_error_messages", stylesheet="color: red;")

#     # Or aggregated from the view_model (ALL variables in this widget
#     all_error_messages: list[QLabel] = new(bind="validation_error_messages", stylesheet="color: blue;")


@dataclass
class User:
    username: str
    email: str


@widget(layout="form")
class UserEditor(Widget[User]):
    username: QLineEdit = new(label="Username")
    email: QLineEdit = new(label="Email")

    # Show error messages for just this form (it's from .record)
    # error_messages: list[QLabel] = new(bind="validation_error_messages", stylesheet="color: red;")


@entrypoint
@widget
class SomeTabs(Widget):
    # user: Variable[User, UserEditor] = new(User("", ""))(layout=False)
    # dogs: Variable[list[Dog], DogEditor] = new([])(layout=False)

    # ... oh ^ I wanna be able to bind these! without it making new ones, hmm!
    # tabs: QTabWidget = new(tabs=[user, dogs])

    # Instead of this:
    # How do I even pass the class constructor args here in this syntax?
    tabs: QTabWidget = new(tabs={"User": UserEditor, "Dogs": DogEditor})

    # btn_add_dog: QPushButton = new("Add Dog", clicked="add_dog")

    # btn_print_user: QPushButton = new("Print User", clicked="print_user")
    # btn_print_dogs: QPushButton = new("Print Dogs", clicked="print_dogs")

    # def __setup__(self) -> None:
    #     self.tabs.addTab(self.user.widget, "User")
    #     self.tabs.addTab(self.dogs.widget, "Dogs")

    # def add_dog(self) -> None:
    #     self.dogs.append(Dog(name="New Dog", age=1))

    # def print_user(self) -> None:
    #     print(f"User: {self.user.value.username}, Email: {self.user.value.email}")

    # def print_dogs(self) -> None:
    #     for dog in self.dogs:
    #         print(f"Dog: {dog.name}, Age: {dog.age}")


@dataclass
class HasListOfStrings:
    strings: list[str]


def validate_not_empty(value: str) -> str | None:
    if not value.strip():
        return "Value cannot be empty, yo."
    return None


# @entrypoint
@widget
class SimpleLists(Widget):
    _some_var: Variable[str, QLineEdit] = new("", validate=[validate_not_empty, "validate_length"])
    _errors: list[QLabel] = new(bind="validation_error_messages")
    _reset_dirty: QPushButton = new("Reset Dirty", clicked="reset_dirty")
    _save: QPushButton = new("Save", enabled="{is_valid and is_dirty}")

    def validate_length(self, value: str) -> str | None:
        if len(value) < 5:
            return "Value must be at least 5 characters long."
        return None

    @override
    def on_valid_changed(self, is_valid: bool) -> None:
        print(f"Validity changed: {is_valid}")

    @override
    def on_dirty_changed(self, is_dirty: bool) -> None:
        print(f"Dirty changed: {is_dirty}")


@widget
class LabelListsComplexObject(Widget):
    dogs: Variable[list[Dog]] = new([Dog("Fido", 3), Dog("Rex", 5)])
    dog_labels: list[QLabel] = new(bind="dogs", format="{name} is {age} years old")

    # and let's try a dictionary...
    dogs_dict: Variable[dict[str, Dog]] = new({"Fido": Dog("Fido", 3), "Rex": Dog("Rex", 5)})
    dog_dict_labels: list[QLabel] = new(bind="dogs_dict", format="{#key} is {age} years old")


@widget(title="Dictionaries of Things")
class DictionariesOfThings(Widget):
    # Key = value (simple primitives)
    str_int_dict: Variable[dict[str, int], QLabel] = new({"one": 1, "two": 2})(bind="{#key} = {#value}")

    # Value is a complex object - access properties
    str_dog_dict: Variable[dict[str, Dog], QLabel] = new({"Fido": Dog("Fido", 3), "Rex": Dog("Rex", 5)})(bind="{#key} is {age} years old")

    # Explicit #value.property and #self.property also work
    str_dog_dict2: Variable[dict[str, Dog], QLabel] = new({"Buddy": Dog("Buddy", 2), "Max": Dog("Max", 7)})(bind="{#key}: {#value.name} is {#self.age} years old")

    btn_add: QPushButton = new("Add Entry", clicked="add_entry")
    btn_remove: QPushButton = new("Remove 'one'", clicked="remove_entry")

    def add_entry(self) -> None:
        count = len(self.str_int_dict) + 1
        self.str_int_dict[f"new_{count}"] = count * 10

    def remove_entry(self) -> None:
        if "one" in self.str_int_dict:
            del self.str_int_dict["one"]


@widget(
    stylesheet="""
#my-label {
    color: red;
}

*[class~="my-class"] {
    font-weight: bold;
}

#TestingQss {
    color: blue;
}

#lbl2 {
    font-style: italic;
}
"""
)
class TestingQss(Widget):
    lbl: QLabel = new("Label")
    lbl2: QLabel = new("Should be italic")
    label: QLabel = new("Label", name="my-label")
    label_with_class: QLabel = new("Label with class", classes=["my-class"])


@widget
class ComplexBindings2(Widget):
    simple_string_variable: Variable[str] = new("Hello, World!")

    # Button to change this string (to test reactivity
    btn_change_string: QPushButton = new("Change String", clicked="change_string")

    def change_string(self) -> None:
        self.simple_string_variable = "Goodbye!"

    # Call a function
    call_fn: Variable[str, QLabel] = new("The string value")(bind="Number of characters is: {len(simple_string_variable)}!")

    # Call a function (using self)
    call_fn_on_self: Variable[str, QLabel] = new("The string value")(bind="Number of characters is: {len(#self)}!")

    # Call a instance method
    call_instance_method: Variable[str, QLabel] = new("Hello")(bind="Uppercase is: {simple_string_variable.upper()}!")

    # Some number variables, x and y and z ...
    var_x: Variable[int] = new(10)
    var_y: Variable[int] = new(20)
    var_z: Variable[int] = new(30)

    # Some buttons which increment those variables (to test reactivity)
    btn_inc_x: QPushButton = new("Increment X", clicked="increment_x")
    btn_inc_y: QPushButton = new("Increment Y", clicked="increment_y")
    btn_inc_z: QPushButton = new("Increment Z", clicked="increment_z")

    def increment_x(self) -> None:
        self.var_x += 1

    def increment_y(self) -> None:
        self.var_y += 1

    def increment_z(self) -> None:
        self.var_z += 1

    # Do some math in a QLabel binding
    math_binding: Variable[str, QLabel] = new("Math result")(bind="Result of (x + y) * z is: {(var_x + var_y) * var_z}")

    # Bind to the output of a function, obviously non-reactive
    def compute_something(self) -> str:
        return "Computed Value"

    label_showing_computed: QLabel = new(bind="Value is: {compute_something()}")

    # Same without parens, calls cuz it's a callable
    label_showing_computed_no_parens: QLabel = new(bind="Value is: {compute_something}")

    # Now what about a function which takes a parameter?
    def repeat_string(self, s: str, times: int) -> str:
        return s * times

    label_showing_repeated: QLabel = new(bind="Repeated string: {repeat_string(simple_string_variable, 3)}")  # If the ast stuff can do this, let's do this too


@widget
class ComplexBindings(Widget):
    testing_self: Variable[str, QLabel] = new("Hello")(bind="Value is: {#self.upper()}!")

    _simple_string: Variable[str] = new("Hello, World!")

    btn_change_string: QPushButton = new("Change String", clicked="change_string")

    def change_string(self) -> None:
        self._simple_string.value = "Goodbye!"  # Use .value, not direct assignment

    # Format string bindings use plain QLabel, not Variable[str, QLabel]
    call_fn: QLabel = new(bind="Number of characters is: {len(_simple_string)}!")

    call_instance_method: QLabel = new(bind="Uppercase is: {_simple_string.upper()}!")

    _var_x: Variable[int] = new(10)
    _var_y: Variable[int] = new(20)
    _var_z: Variable[int] = new(30)

    btn_inc_x: QPushButton = new("Increment X", clicked="increment_x")

    def increment_x(self) -> None:
        self._var_x.value += 1  # Use .value

    # Math binding - plain QLabel
    math_binding: QLabel = new(bind="Result of (x + y) * z is: {(_var_x + _var_y) * _var_z}")

    def compute_something(self) -> str:
        return "Computed Value"

    label_showing_computed: QLabel = new(bind="Value is: {compute_something()}")

    def repeat_string(self, s: str, times: int) -> str:
        return s * times

    label_showing_repeated: QLabel = new(bind="Repeated string: {repeat_string(_simple_string, 3)}")


@widget
class MyWidget(Widget):
    _show_label: Variable[bool] = new(False)

    btn_toggle_label: QPushButton = new("Toggle Label", clicked="toggle_label")
    cool_label: QLabel = new("This is a cool label!", visible="_show_label")

    def toggle_label(self) -> None:
        self._show_label.value = not self._show_label.value


@widget(windowTitle="{title.upper()}")
class ReactiveWindowTitle(Widget):
    title: Variable[str] = new("Initial Title")

    btn_change_title: QPushButton = new("Change Title", clicked="change_title")

    def change_title(self) -> None:
        self.title.value = "Updated Title"


@widget
class AsyncExample(Widget):
    btn: QPushButton = new("Fetch Data", clicked="fetch_data")
    label: QLabel = new("Ready")

    @slot
    async def fetch_data(self) -> None:
        self.label.setText("Loading...")
        await asyncio.sleep(5)
        self.label.setText("Done!")

    # Async closeEvent - cleanup waits for completion
    @override
    async def on_close(self) -> None:
        print("Cleaning up...")
        await asyncio.sleep(2)
        print("Cleanup complete.")


# @menu("&File")
# class FileMenu(QMenu):
#     action_exit: QAction = new("E&xit", triggered="on_exit")

#     def on_exit(self) -> None:
#         print("Exit action triggered.")
#         app = QApplication.instance()
#         if app:
#             app.quit()


@widget(record=Dog("Fido", 3))
class SomeDogWidget(Widget[Dog]):
    name: QLineEdit = new(label="Dog's Name")
    age: QLineEdit = new(label="Dog's Age")

    btn_print_dog: QPushButton = new("Print Dog", clicked="print_dog")

    def print_dog(self) -> None:
        print(f"Dog Name: {self.record.name}, Age: {self.record.age}")


# @window(title="My App")
# class MainWindow(Window[Dog]):
#     file_menu: FileMenu = new()
#     btn_print_dog: QPushButton = new("Print Dog", clicked="print_dog")

#     def print_dog(self) -> None:
#         print(f"Dog Name: {self.record.name}, Age: {self.record.age}")

#     # add some regular widgets:
#     name: QLineEdit = new()
#     age: QLineEdit = new()

#     # def __setup__(self) -> None:
#     #     self.record = Dog(name="Rover", age=5)


# @entrypoint(translations="samples/example_translations.yml", watch_translations=True)
@widget(record=Dog("Fido", 3), layout="form")
class HasSomeTranslations(Widget[Dog]):
    _name: QLineEdit = new(bind="name", label=t("Dog's Name"))
    _lbl_dog_info: QLabel = new(bind=t("Dog's name is: {name}, age is {age}"), label=t("Dog Info"))
    _btn_change_language: QPushButton = new(t("Change Language"), label=t("Options"), clicked="change_language")

    def change_language(self) -> None:
        set_language("fr")


# =============================================================================
# Variable Bindings Demo - React-style props for QtPie!
# =============================================================================


@widget
class CounterDisplay(Widget):
    """A reusable counter display that REQUIRES a count binding from parent."""

    # Required binding - no = new(), so parent MUST provide it
    count: Variable[int]

    # Optional binding - has default, parent can override
    prefix: Variable[str] = new("Count: ")

    # Display combines prefix and count
    _label: QLabel = new(bind="{prefix}{count}")


@widget
class CounterApp(Widget):
    """Parent widget that provides the count binding."""

    # Our count state
    _my_count: Variable[int] = new(0)

    # Pass our _my_count to CounterDisplay's required 'count' binding
    # This creates a TWO-WAY binding - changes sync both directions!
    display: CounterDisplay = new(count="_my_count")

    # Another display with a custom prefix
    display2: CounterDisplay = new(count="_my_count", prefix="Value = ")

    # Buttons to change the count
    btn_increment: QPushButton = new("+1", clicked="increment")
    btn_decrement: QPushButton = new("-1", clicked="decrement")

    # Show that we can also read the child's value
    btn_print: QPushButton = new("Print from child", clicked="print_child_value")

    def increment(self) -> None:
        self._my_count.value += 1

    def decrement(self) -> None:
        self._my_count.value -= 1

    def print_child_value(self) -> None:
        # Two-way binding means child's value IS parent's value
        print(f"Child's count value: {self.display.count.value}")


@widget
class ConditionalChild(Widget):
    """Child that shows/hides based on a binding."""

    # Required - parent must tell us if we're enabled
    is_enabled: Variable[bool]

    _status: QLabel = new(bind="Status: {'Enabled!' if is_enabled else 'Disabled'}")


@widget
class ExpressionBindingDemo(Widget):
    """Demo of expression bindings - one-way computed values."""

    # Our list of items
    _items: Variable[list[str]] = new([])

    # Input for adding items
    _new_item: Variable[str, QLineEdit] = new("")(placeholderText="Enter item name")

    # Buttons
    btn_add: QPushButton = new("Add Item", clicked="add_item")
    btn_clear: QPushButton = new("Clear All", clicked="clear_items")

    # Child with expression binding - enabled only when we have items
    # This is ONE-WAY (computed), not two-way
    child: ConditionalChild = new(is_enabled="{len(_items) > 0}")

    # Show item count
    _count_label: QLabel = new(bind="Items: {len(_items)}")

    def add_item(self) -> None:
        if self._new_item.value.strip():
            self._items.append(self._new_item.value)
            self._new_item.value = ""

    def clear_items(self) -> None:
        self._items.value = []

    btn_print_items: QPushButton = new("Print Items", clicked="print_items")

    def print_items(self) -> None:
        print("Items:", self._items.value)


@widget
class GrandChild(Widget):
    """Grandchild that receives a binding passed through an intermediate widget."""

    theme: Variable[str]  # Required!
    _label: QLabel = new(bind="Theme: {theme}")


@widget
class Child(Widget):
    """Intermediate widget that passes bindings through to grandchild."""

    theme: Variable[str]  # Required from parent, passed to grandchild
    grandchild: GrandChild = new(theme="theme")  # Pass our theme down


@widget
class NestedBindingDemo(Widget):
    """Demo of nested binding pass-through - state flows down the tree."""

    _theme: Variable[str] = new("dark")

    # Pass _theme -> Child.theme -> GrandChild.theme
    child: Child = new(theme="_theme")

    btn_toggle: QPushButton = new("Toggle Theme", clicked="toggle_theme")

    def toggle_theme(self) -> None:
        self._theme.value = "light" if self._theme.value == "dark" else "dark"
        print(f"Theme changed to: {self._theme.value}")
        print(f"Child sees: {self.child.theme.value}")
        print(f"Grandchild sees: {self.child.grandchild.theme.value}")


@widget
class LiteralBindingDemo(Widget):
    """Demo of literal value bindings."""

    # Child with a literal string (not a variable reference)
    display1: CounterDisplay = new(count=42, prefix="Literal count: ")

    # Child with literal from a different source
    display2: CounterDisplay = new(count=100)

    _label: QLabel = new("These counts are literals, not bound to any variable")


# Uncomment and use as @entrypoint to run:
@widget
class VariableBindingsDemo(Widget):
    """Main demo widget showcasing all Variable binding features."""

    _tabs: QTabWidget = new()

    # The demos (layout=False because we add them to tabs manually)
    counter_demo: CounterApp = new(layout=False)
    expression_demo: ExpressionBindingDemo = new(layout=False)
    nested_demo: NestedBindingDemo = new(layout=False)
    literal_demo: LiteralBindingDemo = new(layout=False)

    def __setup__(self) -> None:
        self._tabs.addTab(self.counter_demo, "Two-Way Binding")
        self._tabs.addTab(self.expression_demo, "Expression Binding")
        self._tabs.addTab(self.nested_demo, "Nested Pass-Through")
        self._tabs.addTab(self.literal_demo, "Literal Values")


@dataclass
class TodoItem:
    text: str
    done: bool = False


@widget(layout="horizontal")
class TodoRow(Widget[TodoItem]):
    on_delete = Signal()
    on_toggle = Signal(bool)
    checkbox: QCheckBox = new(bind="done", toggled="on_toggle")
    label_text: QLabel = new(bind="{text}")
    delete_btn: QPushButton = new("X", clicked="on_delete")


@widget
class TodoApp(Widget):
    _items: Variable[list[TodoItem]] = new([])

    _new_text: Variable[str, QLineEdit] = new("", validate=validate_not_empty)(placeholderText="What needs to be done?", returnPressed="add_item")
    _add_btn: QPushButton = new("Add", clicked="add_item", enabled="{is_valid}")

    # todo: support set. We need an ObservableSet for that
    _todo_list: list[TodoRow] = new(bind="_items", on_delete="remove_item(#index)", on_toggle="on_toggle(#index, #args)")

    def add_item(self) -> None:
        self._items.append(TodoItem(text=self._new_text.value))

    def remove_item(self, index: int) -> None:
        if 0 <= index < len(self._items):
            del self._items[index]

    def on_toggle(self, index: int, done: bool) -> None:
        print(f"Item at index {index} marked as {'done' if done else 'not done'}")


@menu(text="&File")
class FileMenu(Menu):
    custom_signal: Signal = Signal(int, int)

    dog: Variable[Dog]

    some_number: Variable[int] = new(123)
    simple_number: int = 42

    print_dog_action: QAction = new(text=ref("Dog name: {dog.name}"), triggered="{just_a_function(some_number, simple_number)}")
    # print_dog_action: QAction = new(text=ref("Dog name: {dog.name}"), triggered="{custom_signal(some_number, simple_number)}")

    def just_a_function(self, *args: object, **kwargs: object) -> None:
        print(f"Just a regular function in the menu called with args: {args}, kwargs: {kwargs}")


#
# @entrypoint
@app(title="My QtPie App with Menu Action", icon=QStyle.StandardPixmap.SP_BrowserReload, minimize_to_tray=False, record=Dog("Rover", 5))
class MyApp(App[Dog]):
    _header: QLabel = new("Welcome to My QtPie App!", stylesheet="font-size: 18px; font-weight: bold;")
    _name: QLineEdit = new()
    _age: QLineEdit = new()

    file_menu: FileMenu = new(dog="record", custom_signal="on_custom_signal")

    def on_custom_signal(self, *args: object, **kwargs: object) -> None:
        print(f"Custom signal receive with args: {args}, kwargs: {kwargs}")


# <--- todo: maybe support for set[Dog] ? not a big deal though. and dict.


@dataclass
class DogsCollection:
    dogs: list[Dog]


@widget(record=DogsCollection(dogs=[Dog("Fido", 3), Dog("Rex", 5), Dog("Buddy", 2)]))
class MyComboBox(Widget[DogsCollection]):
    # Let's have a search box which when typed in filters down the list of dogs shown
    _search_text: Variable[str, QLineEdit] = new("")(placeholderText="Search dogs...")

    _dogs: Variable[list[Dog]]
    _table: QTableView = new(bind="dogs", selectedItems="_dogs")
    _list: QListView = new(bind="dogs", format="{name} ({age} yrs)", selectedItems="_dogs", selectionMode=QAbstractItemView.SelectionMode.MultiSelection)

    _dogs_count: QLabel = new(bind="Selected dogs count: {len(_dogs)}")

    _btn_print_selected_dogs: QPushButton = new("Print Selected Dogs", clicked="print_selected_dogs")

    def print_selected_dogs(self) -> None:
        print(f"There are {len(self._dogs.value)} selected dogs:")
        for dog in self._dogs.value:
            print(f"Selected Dog: {dog.name}, Age: {dog.age}")

    btn_add_dog: QPushButton = new("Add Dog", clicked="add_dog")

    def add_dog(self) -> None:
        self.record.dogs.append(Dog(name="New Dog", age=1))


# Hierarchical Example
@dataclass
class Cat:
    name: str
    age: int
    kittens: list[Cat]


cat = Cat(name="Mittens", age=4, kittens=[Cat(name="Fluffy", age=1, kittens=[]), Cat(name="Snowball", age=2, kittens=[Cat(name="Tiny", age=0, kittens=[Cat(name="Micro", age=0, kittens=[])])])])


# @entrypoint
@widget(record=cat)
class HierarchicalCatsWidget(Widget[Cat]):
    _selected_kitten: Variable[Cat]
    _selected_kittens: Variable[list[Cat]]
    _tree: QTreeView = new(
        bind="kittens",
        format="{name} ({age} yrs)",
        children="kittens",
        selectedItem="_selected_kitten",
        selectedItems="_selected_kittens",
        selectionMode=QAbstractItemView.SelectionMode.MultiSelection,
    )

    _selected_kittens_info: QLabel = new(bind="Selected Kitten Count: {len(_selected_kittens)}")
    _selected_kitten_info: QLabel = new(bind="Last Selected Kitten: {_selected_kitten.name}, Age: {_selected_kitten.age} yrs")

    btn_add_kitten: QPushButton = new("Add Kitten", clicked="add_kitten")

    def add_kitten(self) -> None:
        self.record.kittens.append(Cat(name="Mittens", age=3, kittens=[]))
