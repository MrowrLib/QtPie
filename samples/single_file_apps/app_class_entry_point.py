from typing import override

from qtpie import App, entry_point
from qtpy.QtWidgets import QLabel


@entry_point
class MyApp(App):
    @override
    def create_window(self):
        return QLabel("Hello from App!")
