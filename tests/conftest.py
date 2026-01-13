"""Pytest configuration for QtPie tests."""

import os
import sys

# Use offscreen platform by default, unless --onscreen flag is passed
# Must be done before any Qt imports
if "--onscreen" not in sys.argv:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest

from qtpie import App


def pytest_addoption(parser: pytest.Parser) -> None:
    """Add custom pytest options."""
    parser.addoption(
        "--onscreen",
        action="store_true",
        default=False,
        help="Run tests with real display instead of offscreen",
    )


def is_offscreen() -> bool:
    """Check if running in offscreen mode."""
    return os.environ.get("QT_QPA_PLATFORM") == "offscreen"


# Skip marker for tests that require a real display (e.g., color scheme tests)
requires_display = pytest.mark.skipif(
    is_offscreen(),
    reason="Test requires real display (not offscreen platform)",
)


@pytest.fixture(scope="session")
def qapp_cls() -> type[App]:
    """Override pytest-qt's qapp_cls to use our App class."""

    # pytest-qt calls qapp_cls(qapp_args) where qapp_args is a list
    # Our App expects (name, *, argv=...) so we need a wrapper
    class TestApp(App):
        def __init__(self, args: list[str] | None = None) -> None:
            super().__init__("pytest-qtpie", argv=args or [])

    return TestApp
