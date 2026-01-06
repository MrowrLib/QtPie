import asyncio
from dataclasses import dataclass
from typing import override

from PySide6.QtGui import QAction
from qtpy.QtWidgets import QApplication, QLabel, QLineEdit, QMainWindow, QMenu, QPushButton, QTabWidget

from qtpie import Variable, Widget, entrypoint, menu, new, slot, widget
from qtpie.widget_base import WidgetBase


@dataclass
class Animal:
    name: str
    species: str


@widget
class RecordValidationWidget(Widget[Animal]):
    _name: QLineEdit = new()

    def __setup__(self) -> None:
        self.record = Animal(name="Fido", species="Dog")
        self.record_state.add_validator("name-length", self.validate_length)
        self.record_state.is_valid.on_change(self.on_validity_change)

    def validate_length(self, value: Animal) -> str | None:
        if len(value.name) < 3:
            return "Name must be at least 3 characters long."
        return None

    def on_validity_change(self, is_valid: bool) -> None:
        print(f"Record validity changed: {is_valid}")


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


@widget
class SomeTabs(Widget):
    tabs: QTabWidget = new()
    user: Variable[User, UserEditor] = new(User("", ""))(layout=False)
    dogs: Variable[list[Dog], DogEditor] = new([])(layout=False)

    btn_add_dog: QPushButton = new("Add Dog", clicked="add_dog")

    btn_print_user: QPushButton = new("Print User", clicked="print_user")
    btn_print_dogs: QPushButton = new("Print Dogs", clicked="print_dogs")

    def __setup__(self) -> None:
        self.tabs.addTab(self.user.widget, "User")
        self.tabs.addTab(self.dogs.widget, "Dogs")

    def add_dog(self) -> None:
        self.dogs.append(Dog(name="New Dog", age=1))

    def print_user(self) -> None:
        print(f"User: {self.user.value.username}, Email: {self.user.value.email}")

    def print_dogs(self) -> None:
        for dog in self.dogs:
            print(f"Dog: {dog.name}, Age: {dog.age}")


@dataclass
class HasListOfStrings:
    strings: list[str]


@widget
class SimpleLists(Widget):
    whatever: Variable[str, QLineEdit] = new("", validate=["validate_not_empty", "validate_length"])
    variable_labels: list[QLabel] = new(bind="validation_error_messages")  # <--- this is a string array

    def validate_not_empty(self, value: str) -> str | None:
        if not value.strip():
            return "Value cannot be empty."
        return None

    def validate_length(self, value: str) -> str | None:
        if len(value) < 5:
            return "Value must be at least 5 characters long."
        return None


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


@menu("&File")
class FileMenu(QMenu):
    action_exit: QAction = new("E&xit", triggered="on_exit")

    def on_exit(self) -> None:
        print("Exit action triggered.")
        app = QApplication.instance()
        if app:
            app.quit()


@entrypoint
class MainWindow(QMainWindow, WidgetBase):
    file_menu: FileMenu = new()

    def __setup__(self) -> None:
        self.menuBar().addMenu(self.file_menu)
