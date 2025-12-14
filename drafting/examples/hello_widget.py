from qtpy.QtWidgets import QWidget


class MyWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Hello, World!")


if __name__ == "__main__":
    import sys

    from qtpy.QtWidgets import QApplication

    app = QApplication(sys.argv)
    widget = MyWidget()
    widget.show()
    sys.exit(app.exec_())
