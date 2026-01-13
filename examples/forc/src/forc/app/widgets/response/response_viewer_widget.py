from qtpie import Widget, new, widget

from .response_status_bar_widget import ResponseStatusBarWidget
from .response_tabs_widget import ResponseTabsWidget


@widget
class ResponseViewerWidget(Widget):
    """Response display widget. Contains status bar and tabs."""

    _status_bar: ResponseStatusBarWidget = new()
    _tabs: ResponseTabsWidget = new()
