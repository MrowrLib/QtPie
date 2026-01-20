# pyright: reportUnknownParameterType=false
# pyright: reportMissingTypeArgument=false
# pyright: reportUnknownMemberType=false
# pyright: reportUnknownLambdaType=false
# pyright: reportUnknownArgumentType=false
"""Pytest configuration for Forc tests.

This file controls test collection and ordering to ensure proper isolation
between unit tests (pytest-asyncio) and integration tests (qasync).
"""


def pytest_collection_modifyitems(items: list) -> None:
    """Ensure unit tests run before integration tests.

    Integration tests set up a qasync event loop with already_running=True,
    which affects pytest-asyncio's event loop management. Running unit tests
    first avoids this conflict.
    """
    # Sort so unit tests come before integration tests
    items.sort(key=lambda item: "integration" in str(item.fspath))
