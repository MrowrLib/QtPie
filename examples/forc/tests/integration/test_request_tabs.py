# pyright: reportPrivateUsage=false
"""Integration tests for request tab management."""

from assertpy import assert_that
from forc.app.windows import ForcWindow
from forc.domain.models import Collection, Request, Workspace

from qtpie.testing import QtDriver

from .helpers import click_tree_item, find_tree_index


def find_first_request(workspace: Workspace) -> Request:
    """Find the first Request in the workspace collections."""
    for collection in workspace.collections:
        request = _find_request_in_collection(collection)
        if request is not None:
            return request
    raise ValueError("No requests found in workspace")


def _find_request_in_collection(collection: Collection) -> Request | None:
    """Recursively find a Request in a collection."""
    for item in collection.items:
        if isinstance(item, Request):
            return item
        # item must be Collection here (it's Request | Collection)
        request = _find_request_in_collection(item)
        if request is not None:
            return request
    return None


class TestClickRequestOpensTab:
    """Tests for clicking a request in the tree to open a tab."""

    def test_no_tabs_initially(self, main_window: ForcWindow, qt: QtDriver) -> None:
        """No request tabs should be open initially."""
        assert_that(main_window._editors.value).is_empty()

    def test_clicking_request_opens_tab(self, main_window: ForcWindow, workspace: Workspace, qt: QtDriver) -> None:
        """Clicking a request should open it in a new tab."""
        request = find_first_request(workspace)

        # Simulate clicking the request in the tree
        main_window.on_collection_item_clicked(request)
        qt.process_events()

        # Verify tab was opened
        assert_that(main_window._editors.value).is_length(1)
        assert_that(main_window._editors.value[0]).is_same_as(request)

    def test_clicking_same_request_switches_tab(
        self, main_window: ForcWindow, workspace: Workspace, qt: QtDriver
    ) -> None:
        """Clicking an already-open request should switch to its tab, not open a new one."""
        request = find_first_request(workspace)

        # Open the request
        main_window.on_collection_item_clicked(request)
        qt.process_events()

        # Click it again
        main_window.on_collection_item_clicked(request)
        qt.process_events()

        # Should still only have one tab
        assert_that(main_window._editors.value).is_length(1)

    def test_clicking_different_requests_opens_multiple_tabs(
        self, main_window: ForcWindow, workspace: Workspace, qt: QtDriver
    ) -> None:
        """Clicking different requests should open multiple tabs."""
        # Find two different requests
        requests: list[Request] = []
        for collection in workspace.collections:
            for item in collection.items:
                if isinstance(item, Request):
                    requests.append(item)
                    if len(requests) >= 2:
                        break
            if len(requests) >= 2:
                break

        if len(requests) < 2:
            # Skip if workspace doesn't have enough requests
            return

        # Open both requests
        main_window.on_collection_item_clicked(requests[0])
        main_window.on_collection_item_clicked(requests[1])
        qt.process_events()

        # Should have two tabs
        assert_that(main_window._editors.value).is_length(2)
        assert_that(main_window._editors.value[0]).is_same_as(requests[0])
        assert_that(main_window._editors.value[1]).is_same_as(requests[1])

    def test_selected_tab_index_updates(self, main_window: ForcWindow, workspace: Workspace, qt: QtDriver) -> None:
        """Selected tab index should update when opening/switching tabs."""
        # Find two different requests
        requests: list[Request] = []
        for collection in workspace.collections:
            for item in collection.items:
                if isinstance(item, Request):
                    requests.append(item)
                    if len(requests) >= 2:
                        break
            if len(requests) >= 2:
                break

        if len(requests) < 2:
            return

        # Open first request
        main_window.on_collection_item_clicked(requests[0])
        qt.process_events()
        assert_that(main_window._selected_request_index.value).is_equal_to(0)

        # Open second request
        main_window.on_collection_item_clicked(requests[1])
        qt.process_events()
        assert_that(main_window._selected_request_index.value).is_equal_to(1)

        # Click first request again - should switch back
        main_window.on_collection_item_clicked(requests[0])
        qt.process_events()
        assert_that(main_window._selected_request_index.value).is_equal_to(0)

    def test_clicking_collection_does_not_open_tab(
        self, main_window: ForcWindow, workspace: Workspace, qt: QtDriver
    ) -> None:
        """Clicking a Collection (folder) should not open a tab."""
        collection = workspace.collections[0]

        main_window.on_collection_item_clicked(collection)
        qt.process_events()

        # No tabs should be opened
        assert_that(main_window._editors.value).is_empty()


class TestTreeViewClicking:
    """Tests for clicking items directly in the QTreeView."""

    def test_click_request_in_tree_opens_tab(self, main_window: ForcWindow, workspace: Workspace, qt: QtDriver) -> None:
        """Clicking a request in the actual QTreeView should open a tab."""
        # Get the tree view
        sidebar = main_window._sidebar.widget
        tree = sidebar._collections._treeview

        # Find a request to click
        request = find_first_request(workspace)

        # Find its index in the tree model
        idx = find_tree_index(tree, request)
        assert_that(idx.isValid()).is_true()

        # Expand parents so the item is visible
        tree.expandAll()
        qt.process_events()

        # Click on the item (select + emit clicked)
        click_tree_item(tree, idx)
        qt.process_events()

        # Verify tab was opened
        assert_that(main_window._editors.value).is_length(1)
        assert_that(main_window._editors.value[0]).is_same_as(request)

    def test_click_collection_in_tree_does_not_open_tab(
        self, main_window: ForcWindow, workspace: Workspace, qt: QtDriver
    ) -> None:
        """Clicking a collection (folder) in the QTreeView should not open a tab."""
        # Get the tree view
        sidebar = main_window._sidebar.widget
        tree = sidebar._collections._treeview

        # Get the first collection
        collection = workspace.collections[0]

        # Find its index in the tree model
        idx = find_tree_index(tree, collection)
        assert_that(idx.isValid()).is_true()

        # Click on the collection
        click_tree_item(tree, idx)
        qt.process_events()

        # No tabs should be opened
        assert_that(main_window._editors.value).is_empty()

    def test_click_multiple_requests_in_tree(self, main_window: ForcWindow, workspace: Workspace, qt: QtDriver) -> None:
        """Clicking multiple requests in tree should open multiple tabs."""
        sidebar = main_window._sidebar.widget
        tree = sidebar._collections._treeview
        tree.expandAll()
        qt.process_events()

        # Find two requests
        requests: list[Request] = []
        for collection in workspace.collections:
            for item in collection.items:
                if isinstance(item, Request):
                    requests.append(item)
                    if len(requests) >= 2:
                        break
            if len(requests) >= 2:
                break

        if len(requests) < 2:
            return

        # Click both requests in tree
        for request in requests:
            idx = find_tree_index(tree, request)
            click_tree_item(tree, idx)
            qt.process_events()

        # Should have two tabs
        assert_that(main_window._editors.value).is_length(2)
