from qtpy.QtWidgets import QLabel, QTabWidget

from qtpie import Widget, new, widget


@widget(title="Params")
class ParamsTabContent(Widget):
    """Params tab content. Placeholder for KeyValueEditor."""

    _placeholder: QLabel = new("Params editor placeholder")


@widget(title="Headers")
class HeadersTabContent(Widget):
    """Headers tab content. Placeholder for KeyValueEditor."""

    _placeholder: QLabel = new("Headers editor placeholder")


@widget(title="Auth")
class AuthTabContent(Widget):
    """Auth tab content. Placeholder for auth type selector + fields."""

    _placeholder: QLabel = new("Auth editor placeholder")


@widget(title="Body")
class BodyTabContent(Widget):
    """Body tab content. Placeholder for body type selector + editor."""

    _placeholder: QLabel = new("Body editor placeholder")


@widget
class RequestTabsWidget(Widget):
    """Tabs for request params, headers, auth, and body."""

    _tabs: QTabWidget = new(
        tabs=[
            ParamsTabContent,
            HeadersTabContent,
            AuthTabContent,
            BodyTabContent,
        ]
    )
