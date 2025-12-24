"""Pytest plugin that provides the qt fixture."""

import pytest
from pytestqt.qtbot import QtBot

from .driver import QtDriver


@pytest.fixture
def qt(qtbot: QtBot) -> QtDriver:
    """
    Pytest fixture providing a QtDriver instance.

    This is the main entry point for qtpie.testing. Use this fixture
    in your tests instead of pytest-qt's qtbot directly.
    """
    return QtDriver(qtbot)
