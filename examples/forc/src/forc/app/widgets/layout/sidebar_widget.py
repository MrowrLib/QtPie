from forc.app.widgets.collections import CollectionsTreeWidget
from forc.app.widgets.environments import EnvironmentSelectorWidget
from qtpie import Widget, widget


@widget
class SidebarWidget(Widget):
    _collections: CollectionsTreeWidget
    _environments: EnvironmentSelectorWidget
