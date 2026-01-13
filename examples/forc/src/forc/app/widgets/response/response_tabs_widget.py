from qtpy.QtWidgets import QLabel, QTabWidget

from qtpie import Widget, new, widget


@widget(title="Body")
class ResponseBodyTabContent(Widget):
    """Response body tab. Placeholder for syntax-highlighted viewer."""

    _placeholder: QLabel = new("Response body placeholder")


@widget(title="Headers")
class ResponseHeadersTabContent(Widget):
    """Response headers tab. Placeholder for headers list."""

    _placeholder: QLabel = new("Response headers placeholder")


@widget(title="Cookies")
class ResponseCookiesTabContent(Widget):
    """Response cookies tab. Placeholder for cookies list."""

    _placeholder: QLabel = new("Response cookies placeholder")


@widget
class ResponseTabsWidget(Widget):
    """Tabs for response body, headers, and cookies."""

    _tabs: QTabWidget = new(
        tabs=[
            ResponseBodyTabContent,
            ResponseHeadersTabContent,
            ResponseCookiesTabContent,
        ]
    )
