from dataclasses import dataclass

from qtpy.QtWidgets import QApplication, QLabel, QPushButton

from qtpie import Variable, Widget, new, widget


@dataclass
class Animal:
    name: str
    species: str


@widget
class MyWidget(Widget[Animal]):
    _count: Variable[int] = new(0)
    _label: QLabel = new(bind="Count: {count} oh and also {name} the {species}")
    _btn: QPushButton = new("Click me", clicked="on_clicked")

    def __setup__(self) -> None:
        self.record = Animal(name="Fido", species="Dog")

    def on_clicked(self) -> None:
        self._count += 1
        self.record.name = "Buddy!"
        self.record.species = "Cat!"


if __name__ == "__main__":
    app = QApplication([])
    widget = MyWidget()
    widget.show()
    app.exec()
