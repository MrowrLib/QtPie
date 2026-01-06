from dataclasses import dataclass

from qtpy.QtWidgets import QApplication, QLabel, QLineEdit, QPushButton

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


@widget
class ListsOfThings(Widget):
    numbers: Variable[list[int], QLabel] = new([1, 2, 3])

    btn_add: QPushButton = new("Add Number", clicked="add_number")
    btn_remove: QPushButton = new("Remove Number", clicked="remove_number")

    def add_number(self) -> None:
        self.numbers += [len(self.numbers.value) + 1]

    # def remove_number(self) -> None:
    #     if self.numbers.value:
    #         self.numbers.observable.remove(self.numbers.value[-1])


if __name__ == "__main__":
    app = QApplication([])
    widget = ListsOfThings()
    widget.show()
    app.exec()
