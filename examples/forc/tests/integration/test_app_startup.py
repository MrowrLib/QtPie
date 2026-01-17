"""Integration tests for Forc app startup and basic functionality."""

from assertpy import assert_that
from forc.app.windows import ForcWindow
from forc.domain.models import Workspace

from qtpie.testing import QtDriver


class TestAppStartup:
    """Tests for app initialization."""

    def test_workspace_loads(self, workspace: Workspace) -> None:
        """App should load a workspace on startup."""
        assert_that(workspace).is_not_none()
        assert_that(workspace.name).is_equal_to("JSONPlaceholder API")

    def test_workspace_has_collections(self, workspace: Workspace) -> None:
        """Workspace should have collections loaded."""
        assert_that(workspace.collections).is_not_empty()

    def test_workspace_has_environments(self, workspace: Workspace) -> None:
        """Workspace should have environments loaded."""
        assert_that(workspace.environments).is_not_empty()


class TestMainWindow:
    """Tests for the main window."""

    def test_window_title(self, main_window: ForcWindow, qt: QtDriver) -> None:
        """Window should have the correct title."""
        assert_that(main_window.windowTitle()).contains("Forc")

    def test_window_has_sidebar(self, main_window: ForcWindow, qt: QtDriver) -> None:
        """Window should have a sidebar dock."""
        assert_that(main_window.sidebar).is_not_none()

    def test_window_has_menus(self, main_window: ForcWindow, qt: QtDriver) -> None:
        """Window should have file and view menus."""
        assert_that(main_window.file_menu).is_not_none()
        assert_that(main_window.view_menu).is_not_none()


class TestSidebar:
    """Tests for the sidebar."""

    def test_sidebar_shows_workspace_name(self, main_window: ForcWindow, workspace: Workspace, qt: QtDriver) -> None:
        """Sidebar should display the workspace name."""
        sidebar = main_window.sidebar.widget
        collections_widget = sidebar.collections
        header_text = collections_widget.header.text()
        assert_that(header_text).is_equal_to(workspace.name)

    def test_sidebar_has_collections_tree(self, main_window: ForcWindow, qt: QtDriver) -> None:
        """Sidebar should have a collections tree."""
        sidebar = main_window.sidebar.widget
        assert_that(sidebar.collections).is_not_none()
        assert_that(sidebar.collections.treeview).is_not_none()
