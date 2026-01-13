from forc.app.widgets.collections import CollectionsTreeWidget
from forc.app.widgets.environments import EnvironmentSelectorWidget
from qtpie import Widget, new, widget


@widget
class SidebarWidget(Widget):
    """Sidebar with collections tree and environment selector."""

    _collections: CollectionsTreeWidget = new()
    _environments: EnvironmentSelectorWidget = new()
