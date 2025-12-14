"""A simple Qt application - no custom libraries, just plain Qt."""

from qtpy.QtWidgets import QApplication, QLabel, QMainWindow, QPushButton, QVBoxLayout, QWidget


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Regular Qt App")

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout(central_widget)

        self.label = QLabel("Hello, World!")
        self.label.setObjectName("hello_label")
        layout.addWidget(self.label)

        self.button = QPushButton("Click me")
        self.button.setObjectName("click_button")
        self.button.clicked.connect(self._on_button_clicked)
        layout.addWidget(self.button)

        self.click_count = 0

    def _on_button_clicked(self):
        self.click_count += 1
        self.label.setText(f"Clicked {self.click_count} time(s)")


def main():
    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec()


if __name__ == "__main__":
    main()
