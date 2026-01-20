# pyright: reportUnknownParameterType=false
# pyright: reportMissingTypeArgument=false
# pyright: reportUnknownMemberType=false
# pyright: reportUnknownLambdaType=false
# pyright: reportUnknownArgumentType=false
# pyright: reportPrivateUsage=false
# pyright: reportImplicitOverride=false
# pyright: reportAssignmentType=false
"""Pytest configuration for Forc tests.

This file controls test collection and ordering to ensure proper isolation
between unit tests (pytest-asyncio) and integration tests (qasync).
"""

from collections.abc import Generator
from typing import ClassVar

import keyring
import pytest
from keyring.backend import KeyringBackend


class MockKeyring(KeyringBackend):
    """In-memory keyring for testing.

    Avoids OS keychain prompts during tests by using a simple dict backend.
    """

    priority = 1
    _data: ClassVar[dict[str, str]] = {}

    def set_password(self, service: str, username: str, password: str) -> None:
        MockKeyring._data[f"{service}:{username}"] = password

    def get_password(self, service: str, username: str) -> str | None:
        return MockKeyring._data.get(f"{service}:{username}")

    def delete_password(self, service: str, username: str) -> None:
        key = f"{service}:{username}"
        if key in MockKeyring._data:
            del MockKeyring._data[key]
        else:
            import keyring.errors

            raise keyring.errors.PasswordDeleteError()


@pytest.fixture(autouse=True)
def mock_keyring() -> Generator[MockKeyring]:
    """Use in-memory keyring for all tests - no OS prompts."""
    original = keyring.get_keyring()
    mock = MockKeyring()
    MockKeyring._data = {}  # Fresh state for each test
    keyring.set_keyring(mock)
    yield mock
    keyring.set_keyring(original)


def pytest_collection_modifyitems(items: list) -> None:
    """Ensure unit tests run before integration tests.

    Integration tests set up a qasync event loop with already_running=True,
    which affects pytest-asyncio's event loop management. Running unit tests
    first avoids this conflict.
    """
    # Sort so unit tests come before integration tests
    items.sort(key=lambda item: "integration" in str(item.fspath))
