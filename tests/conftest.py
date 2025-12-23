"""pytest configuration for all tests."""

import pytest

from qtpie import App


@pytest.fixture(scope="session")
def qapp_cls() -> type[App]:
    """Override pytest-qt's qapp_cls to use our App class."""

    # pytest-qt calls qapp_cls(qapp_args) where qapp_args is a list
    # Our App expects (name, *, argv=...) so we need a wrapper
    class TestApp(App):
        def __init__(self, args: list[str] | None = None) -> None:
            super().__init__("pytest-qtpie", argv=args or [])

    return TestApp
