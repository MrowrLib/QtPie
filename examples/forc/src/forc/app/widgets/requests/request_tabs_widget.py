from qtpy.QtWidgets import QLabel, QTableView, QTabWidget

from forc.domain.models import Request
from qtpie import Widget, new, widget


@widget(title="Params")
class ParamsTabContent(Widget[Request]):
    """Params tab content showing query parameters."""

    # temp for previewing the data
    _label: QLabel = new(bind="{record.query_params}")

    table: QTableView = new(bind="record.query_params", columns=["key", "value"])

    _label2: QLabel = new("hello?")


@widget(title="Headers")
class HeadersTabContent(Widget[Request]):
    """Headers tab content showing request headers."""

    _label: QLabel = new(bind="{record.headers}")


@widget(title="Auth")
class AuthTabContent(Widget[Request]):
    """Auth tab content showing authentication settings."""

    _label: QLabel = new(bind="{record.auth}")


@widget(title="Body")
class BodyTabContent(Widget[Request]):
    """Body tab content showing request body."""

    _label: QLabel = new(bind="{record.body}")


@widget
class RequestTabsWidget(Widget[Request]):
    _params: ParamsTabContent = new(bind="record")

    _tabs: QTabWidget = new(
        tabs=[
            _params
            # ParamsTabContent,
            # BodyTabContent,
            # AuthTabContent,
            # HeadersTabContent,
        ],
    )
