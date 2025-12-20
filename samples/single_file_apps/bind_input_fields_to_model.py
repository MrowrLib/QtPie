from dataclasses import dataclass

from qtpie import Widget, entry_point, make, widget
from qtpy.QtCore import Qt
from qtpy.QtWidgets import QLineEdit, QPushButton, QSlider, QWidget


@dataclass
class Dog:
    name: str = ""
    age: int = 0


@entry_point
@widget(layout="form")
class MyWidget(QWidget, Widget[Dog]):
    name: QLineEdit = make(QLineEdit, form_label="Name", bind="proxy.name")
    age: QSlider = make(QSlider, Qt.Orientation.Horizontal, form_label="Age", minimum=0, maximum=20, bind="proxy.age")
    button: QPushButton = make(QPushButton, "Print Info", clicked="on_button_click")

    def on_button_click(self):
        dog = self.model
        print(f"Dog's Name: {dog.name}, Age: {dog.age}")
