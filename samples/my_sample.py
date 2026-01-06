from dataclasses import dataclass

from qtpy.QtWidgets import QLabel, QLineEdit, QPushButton, QTabWidget

from qtpie import Variable, Widget, entrypoint, new, widget


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


@entrypoint
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
