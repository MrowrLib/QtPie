"""Request - the atomic unit of an HTTP request definition."""

from enum import Enum

from qtpie import Event, State, Variable, new, state


class HttpMethod(Enum):
    """HTTP methods supported by Forc."""

    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    PATCH = "PATCH"
    DELETE = "DELETE"
    HEAD = "HEAD"
    OPTIONS = "OPTIONS"


@state
class Request(State):
    """A single HTTP request definition.

    Request is a leaf node in the collection tree. It holds all the data
    needed to construct and send an HTTP request.

    The parent Collection is accessed via `state_parent`.
    """

    name: Variable[str] = new("")
    method: Variable[HttpMethod] = new(HttpMethod.GET)
    url: Variable[str] = new("")

    # Events
    on_changed: Event  # Fires when any field changes

    def __setup__(self) -> None:
        # Wire up change tracking - any field change fires on_changed
        # Use lambda to discard the value argument from on_change callbacks
        self.name.on_change(lambda _: self.on_changed.emit())
        self.method.on_change(lambda _: self.on_changed.emit())
        self.url.on_change(lambda _: self.on_changed.emit())
