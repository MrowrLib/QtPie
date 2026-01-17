from qtpy.QtWidgets import QLabel, QPushButton

from forc.app.widgets.collections import CollectionsTreeWidget
from forc.app.widgets.cookie_manager import CookieManagerWidget
from forc.app.widgets.environments import EnvironmentSelectorWidget
from qtpie import Dialog, DialogButton, Stretch, Widget, dialog, new, widget


@dialog(size=(900, 600), title="Cookie Manager", icon=":/icon.png")
class CookieManagerDialog(Dialog):
    header: QLabel = new("Cookie Manager")
    cookie_manager: CookieManagerWidget
    stretch: Stretch
    ok: DialogButton


@widget(title="Test", icon=":/icon.png")
class SomeWidget(Widget):
    label: QLabel = new("Some Widget Placeholder")


@widget
class SidebarWidget(Widget):
    btn: QPushButton = new("Cookie Manager", clicked="show_cookie_manager")

    _collections: CollectionsTreeWidget
    _environments: EnvironmentSelectorWidget

    def show_cookie_manager(self):
        CookieManagerDialog.show_dialog()
