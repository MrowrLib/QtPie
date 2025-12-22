from typing import override

from qtpy.QtWidgets import QLabel

from qtpie import App, entrypoint


@entrypoint
class MyApp(App):
    @override
    def create_window(self):
        return QLabel("Hello from App!")
