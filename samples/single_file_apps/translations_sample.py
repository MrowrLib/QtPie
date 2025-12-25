from qtpy.QtWidgets import QLabel, QPushButton, QWidget

from qtpie import entrypoint, make, tr, widget


@entrypoint(translations="samples/single_file_apps/translations.yml", language="fr", watch_translations=True)
@widget
class MyWidget(QWidget):
    text: QLabel = make(QLabel, "Hello, World!")
    button: QPushButton = make(QPushButton, text=tr["CLICK_ME"], clicked="on_click")

    def on_click(self):
        self.text.setText("Button Clicked!")
