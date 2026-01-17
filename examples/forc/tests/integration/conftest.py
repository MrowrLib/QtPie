"""Pytest configuration for Forc integration tests."""

import os
import sys
from pathlib import Path

import pytest

# Use offscreen platform by default
if "--onscreen" not in sys.argv:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from forc.app.windows import ForcWindow
from forc.domain.models import Workspace
from forc.services import HttpClientService, WorkspaceService

from qtpie import App
from qtpie.testing import QtDriver

# Path to test fixtures
FIXTURES_DIR = Path(__file__).parent.parent.parent / "fixtures"
DEMO_API_WORKSPACE = FIXTURES_DIR / "demo-api"


@pytest.fixture(scope="session")
def qapp() -> App:
    """Override pytest-qt's qapp to use our ForcApp with test workspace."""
    from forc.app.application import ForcApp

    # Create the app
    app = ForcApp()

    # ForcApp.__setup__ uses relative path that only works from examples/forc/
    # Re-load with absolute path for tests
    app.workspace.value = app.workspace_service.value.load(DEMO_API_WORKSPACE)

    return app


@pytest.fixture
def main_window(qapp: App, qt: QtDriver) -> ForcWindow:
    """Get the main ForcWindow, tracked for cleanup.

    Resets editor tabs before each test for isolation.
    """
    from forc.app.application import ForcApp

    assert isinstance(qapp, ForcApp)
    window = qapp.main_window

    # Reset state for test isolation
    window.editors.clear()
    window.selected_request_index.value = 0

    qt.track(window)
    return window


@pytest.fixture
def workspace(qapp: App) -> Workspace:
    """Get the loaded workspace."""
    from forc.app.application import ForcApp

    assert isinstance(qapp, ForcApp)
    ws = qapp.workspace.value
    assert ws is not None, "Workspace should be loaded"
    return ws


@pytest.fixture
def workspace_service(qapp: App) -> WorkspaceService:
    """Get the workspace service."""
    from forc.app.application import ForcApp

    assert isinstance(qapp, ForcApp)
    return qapp.workspace_service.value


@pytest.fixture
def http_client(qapp: App) -> HttpClientService:
    """Get the HTTP client service."""
    from forc.app.application import ForcApp

    assert isinstance(qapp, ForcApp)
    return qapp.http_client_service.value
