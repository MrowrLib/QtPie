from forc.app.widgets.environments import EnvironmentSelectorWidget
from qtpie import Widget, new, widget


@widget
class SidebarWidget(Widget):
    environment_selector: EnvironmentSelectorWidget = new()
