from dataclasses import dataclass

from qtpy.QtWidgets import QApplication, QLabel, QLineEdit, QPushButton, QTabWidget

from qtpie import Variable, Widget, new, widget


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


@dataclass
class User:
    username: str
    email: str


@widget(layout="form")
class UserEditor(Widget[User]):
    username: QLineEdit = new(label="Username")
    email: QLineEdit = new(label="Email")


@widget
class SomeTabs(Widget):
    tabs: QTabWidget = new()
    user: Variable[User, UserEditor] = new(User("john_doe", "john@example.com"))(layout=False)
    dog: Variable[Dog, DogEditor] = new(Dog("Fido", 3))(layout=False)

    def __setup__(self) -> None:
        self.tabs.addTab(self.user.widget, "User Editor")
        self.tabs.addTab(self.dog.widget, "Dog Editor")


if __name__ == "__main__":
    app = QApplication([])
    widget = SomeTabs()
    widget.show()
    app.exec()
