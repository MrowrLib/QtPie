from dataclasses import dataclass

from qtpy.QtCore import Qt
from qtpy.QtWidgets import QLineEdit, QPushButton, QSlider, QWidget

from qtpie import Widget, entry_point, make, widget


@dataclass
class Dog:
    name: str = ""
    age: int = 0


@entry_point
@widget(layout="form")
class MyWidget(QWidget, Widget[Dog]):
    # bind 'name' to the model
    name_hello: QLineEdit = make(QLineEdit, form_label="Name", bind="name")

    # 'age' is automatically bound by matching field name
    age: QSlider = make(QSlider, Qt.Orientation.Horizontal, form_label="Age", minimum=0, maximum=20)

    button: QPushButton = make(QPushButton, "Print Info", clicked="on_button_click")

    def on_button_click(self):
        dog = self.model
        print(f"Dog's Name: {dog.name}, Age: {dog.age}")
