from qtpy.QtWidgets import QLabel, QPushButton, QWidget

from qtpie import entrypoint, make, widget


@entrypoint
@widget
class MyWidget(QWidget):
    text: QLabel = make(QLabel, "Hello, World!")
    button: QPushButton = make(QPushButton, "Click Me", clicked="on_click")

    def on_click(self):
        self.text.setText("Button Clicked!")
