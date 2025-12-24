from qtpy.QtWidgets import QLabel, QPushButton, QWidget

from qtpie import enable_light_mode, entrypoint, make, state, widget

enable_light_mode()


@entrypoint
@widget
class Counter(QWidget):
    # Tracked state - changes update the UI
    count: int = state(0)

    # Updates automatically when count changes
    label: QLabel = make(QLabel, bind="Count: {count}")

    # Calls increment() when clicked
    button: QPushButton = make(QPushButton, "+1", clicked="increment")

    def increment(self) -> None:
        self.count += 1
