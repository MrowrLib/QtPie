from qtpy.QtWidgets import QApplication, QLabel


def main():
    app = QApplication([])
    windows = QLabel("Hello, World!")
    windows.show()
    app.exec_()


if __name__ == "__main__":
    main()
