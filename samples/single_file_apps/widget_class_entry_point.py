from qtpie import entry_point, make, widget
from qtpy.QtWidgets import QLabel, QPushButton, QWidget


@entry_point
@widget
class MyWidget(QWidget):
    text: QLabel = make(QLabel, "Hello, World!")
    button: QPushButton = make(QPushButton, "Click Me", clicked="on_click")

    def on_click(self):
        self.text.setText("Button Clicked!")
