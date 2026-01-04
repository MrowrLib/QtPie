from qtpy.QtWidgets import QApplication, QLabel, QPushButton

from qtpie import Variable, Widget, new, widget


@widget
class MyWidget(Widget):
    _count: Variable[int] = new(0)
    _label: QLabel = new(bind="Count: {count}")
    _btn: QPushButton = new("Click me", clicked="on_clicked")

    # def on_clicked(self) -> None:
    #     self._count += 1


if __name__ == "__main__":
    app = QApplication([])
    widget = MyWidget()
    widget.show()
    app.exec()
