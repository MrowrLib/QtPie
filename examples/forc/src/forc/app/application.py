from qtpy.QtWidgets import QLabel

from forc.app.widgets.layout import SidebarWidget
from qtpie import App, Dock, app, new


@app(title="Free Open-source Rest Client")
class ForcApp(App):
    header: QLabel = new("Free Open-source Rest Client")

    sidebar: Dock[SidebarWidget] = new(dock="left")
