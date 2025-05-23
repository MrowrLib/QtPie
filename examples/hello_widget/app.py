from qtpy.QtWidgets import QLabel, QWidget


class MyWidget(QLabel):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setText("Hello, World!")
        self.setWindowTitle("Hello Widget")
        self.setGeometry(100, 100, 200, 50)


if __name__ == "__main__":
    import sys

    from qtpy.QtWidgets import QApplication

    app = QApplication(sys.argv)
    widget = MyWidget()
    widget.show()
    sys.exit(app.exec_())
