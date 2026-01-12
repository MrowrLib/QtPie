from qtpy.QtWidgets import QLabel

from qtpie import App, app, new


@app(title="Free Open-source Rest Client")
class ForcApp(App):
    header: QLabel = new("Free Open-source RTOS Configuration Tool")
