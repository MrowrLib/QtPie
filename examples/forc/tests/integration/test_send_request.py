"""Integration tests for sending HTTP requests."""

from assertpy import assert_that
from forc.app.widgets.requests import RequestWidget
from forc.app.widgets.response.response_viewer_widget import ResponseBodyTabContent
from forc.app.windows import ForcWindow
from forc.domain.models import Collection, Request, Workspace
from qtpy.QtWidgets import QDockWidget

from qtpie.testing import QtDriver


def find_request_by_name(workspace: Workspace, name: str) -> Request | None:
    """Find a request by name in the workspace."""
    for collection in workspace.collections:
        result = _find_in_collection(collection, name)
        if result is not None:
            return result
    return None


def _find_in_collection(collection: Collection, name: str) -> Request | None:
    """Recursively find a request by name in a collection."""
    for item in collection.items:
        if isinstance(item, Request) and item.name == name:
            return item
        if isinstance(item, Collection):
            result = _find_in_collection(item, name)
            if result is not None:
                return result
    return None


def get_request_widget(main_window: ForcWindow, index: int = 0) -> RequestWidget | None:
    """Get the RequestWidget for an open request tab by index."""
    # Find dock widgets in the right area
    for dock in main_window.findChildren(QDockWidget):
        widget = dock.widget()
        if isinstance(widget, RequestWidget):
            # For now just return the first one found
            # TODO: proper index handling
            return widget
    return None


class TestSendRequest:
    """Tests for sending HTTP requests."""

    def test_send_echo_request(self, main_window: ForcWindow, workspace: Workspace, qt: QtDriver) -> None:
        """Send echo request and verify response."""
        # Find the Echo (GET) request in demo collection
        request = find_request_by_name(workspace, "Echo (GET)")
        assert request is not None, "Echo (GET) request not found in workspace"

        # Open the request in a tab
        main_window.on_collection_item_clicked(request)
        qt.process_events()

        # Get the RequestWidget
        request_widget = get_request_widget(main_window)
        assert request_widget is not None, "RequestWidget not found"

        # Send the request by emitting the signal
        request_widget.on_send_request.emit(request)
        qt.process_events()

        # Check the response
        response = request_widget.response.value
        assert response is not None
        assert_that(response.status_code).is_equal_to(200)

        # Body is bytes, decode to check content
        body_text = response.body.decode("utf-8")
        assert_that(body_text).contains("method")
        assert_that(body_text).contains("GET")

    def test_response_contains_query_params(self, main_window: ForcWindow, workspace: Workspace, qt: QtDriver) -> None:
        """Echo request should reflect query params in response."""
        request = find_request_by_name(workspace, "Echo (GET)")
        assert request is not None

        main_window.on_collection_item_clicked(request)
        qt.process_events()

        request_widget = get_request_widget(main_window)
        assert request_widget is not None

        request_widget.on_send_request.emit(request)
        qt.process_events()

        response = request_widget.response.value
        assert response is not None

        # Echo endpoint returns query_params in response
        body_text = response.body.decode("utf-8")
        assert_that(body_text).contains("query_params")
        assert_that(body_text).contains("foo")
        assert_that(body_text).contains("bar")

    def test_response_body_shown_in_ui(self, main_window: ForcWindow, workspace: Workspace, qt: QtDriver) -> None:
        """Response body should be displayed in the ResponseViewerWidget."""
        request = find_request_by_name(workspace, "Echo (GET)")
        assert request is not None

        main_window.on_collection_item_clicked(request)
        qt.process_events()

        request_widget = get_request_widget(main_window)
        assert request_widget is not None

        request_widget.on_send_request.emit(request)
        qt.process_events()

        # Get the response viewer and check the body text widget
        body_tab = request_widget.response_viewer.get_tab(ResponseBodyTabContent)
        assert body_tab is not None
        body_text_edit = body_tab.body_text

        # The QPlainTextEdit should contain the response body
        displayed_text = body_text_edit.toPlainText()
        assert_that(displayed_text).contains("method")
        assert_that(displayed_text).contains("GET")
        assert_that(displayed_text).contains("query_params")
