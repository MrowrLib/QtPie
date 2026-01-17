from qtpy.QtWidgets import QPushButton

from forc.app.widgets.collections import CollectionsTreeWidget
from forc.app.widgets.cookie_manager import CookieManagerDialog
from forc.app.widgets.environments import EnvironmentSelectorWidget
from qtpie import Widget, new, widget


@widget
class SidebarWidget(Widget):
    _cookie_manager_button: QPushButton = new("Cookie Manager", clicked="show_cookie_manager")
    _collections: CollectionsTreeWidget
    _environments: EnvironmentSelectorWidget

    def show_cookie_manager(self):
        CookieManagerDialog.show_dialog()
