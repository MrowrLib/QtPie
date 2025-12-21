from dataclasses import dataclass

from qtpy.QtCore import Qt
from qtpy.QtWidgets import QLabel, QLineEdit, QSlider, QWidget

from qtpie import Widget, entry_point, make, widget


@dataclass
class Dog:
    name: str = ""
    age: int = 0


@entry_point
@widget(layout="form")
class MyWidget(QWidget, Widget[Dog]):
    name: QLineEdit = make(QLineEdit, form_label="Name")
    age: QSlider = make(QSlider, Qt.Orientation.Horizontal, form_label="Age", minimum=0, maximum=20)
    info: QLabel = make(QLabel, bind="Name: {name}, Age: {age}")
