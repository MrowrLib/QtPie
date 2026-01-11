# pyright: reportPrivateUsage=false
# pyright: reportMissingParameterType=false
# pyright: reportUnknownParameterType=false
# pyright: reportUntypedBaseClass=false
# pyright: reportUntypedClassDecorator=false
# pyright: reportUnknownArgumentType=false
# pyright: reportUnknownMemberType=false
"""Tests for menu separators.

Separators are visual dividers in menus created with bare Separator annotations.
"""

from assertpy import assert_that
from PySide6.QtGui import QAction

from qtpie import Menu, menu, new
from qtpie.menu import Separator
from qtpie.testing import QtDriver


class TestSeparatorBasic:
    """Basic separator functionality."""

    def test_separator_creates_divider(self, qt: QtDriver) -> None:
        """Separator annotation creates a menu separator."""

        @menu(text="&File")
        class FileMenu(Menu):
            new_action: QAction = new("&New")
            ____: Separator
            exit_action: QAction = new("E&xit")

        m = FileMenu()
        qt.track(m)

        # Menu should have 3 items: action, separator, action
        actions = m.actions()
        assert_that(actions).is_length(3)
        assert_that(actions[1].isSeparator()).is_true()

    def test_separator_preserves_order(self, qt: QtDriver) -> None:
        """Separators appear in declaration order."""

        @menu(text="&File")
        class FileMenu(Menu):
            action1: QAction = new("One")
            _1: Separator
            action2: QAction = new("Two")
            _2: Separator
            action3: QAction = new("Three")

        m = FileMenu()
        qt.track(m)

        actions = m.actions()
        assert_that(actions).is_length(5)
        assert_that(actions[0].text()).is_equal_to("One")
        assert_that(actions[1].isSeparator()).is_true()
        assert_that(actions[2].text()).is_equal_to("Two")
        assert_that(actions[3].isSeparator()).is_true()
        assert_that(actions[4].text()).is_equal_to("Three")

    def test_multiple_separators(self, qt: QtDriver) -> None:
        """Multiple separators can be added."""

        @menu(text="&Edit")
        class EditMenu(Menu):
            cut: QAction = new("Cut")
            copy: QAction = new("Copy")
            paste: QAction = new("Paste")
            _1: Separator
            _2: Separator
            select_all: QAction = new("Select All")

        m = EditMenu()
        qt.track(m)

        actions = m.actions()
        separators = [a for a in actions if a.isSeparator()]
        assert_that(separators).is_length(2)

    def test_separator_at_start(self, qt: QtDriver) -> None:
        """Separator at start of menu."""

        @menu(text="&Test")
        class TestMenu(Menu):
            ____: Separator
            action1: QAction = new("Action")

        m = TestMenu()
        qt.track(m)

        actions = m.actions()
        assert_that(actions).is_length(2)
        assert_that(actions[0].isSeparator()).is_true()

    def test_separator_at_end(self, qt: QtDriver) -> None:
        """Separator at end of menu."""

        @menu(text="&Test")
        class TestMenu(Menu):
            action1: QAction = new("Action")
            ____: Separator

        m = TestMenu()
        qt.track(m)

        actions = m.actions()
        assert_that(actions).is_length(2)
        assert_that(actions[1].isSeparator()).is_true()

    def test_separator_only_underscores_naming(self, qt: QtDriver) -> None:
        """Separator field names can use any underscore pattern."""

        @menu(text="&Test")
        class TestMenu(Menu):
            a: QAction = new("A")
            _: Separator
            b: QAction = new("B")
            __: Separator
            c: QAction = new("C")
            ___: Separator
            d: QAction = new("D")

        m = TestMenu()
        qt.track(m)

        actions = m.actions()
        separators = [a for a in actions if a.isSeparator()]
        assert_that(separators).is_length(3)


class TestSeparatorWithOtherElements:
    """Separators combined with other menu elements."""

    def test_separator_between_actions(self, qt: QtDriver) -> None:
        """Separators work between action groups."""

        @menu(text="&Edit")
        class EditMenu(Menu):
            cut: QAction = new("Cut")
            copy: QAction = new("Copy")
            ____: Separator
            paste: QAction = new("Paste")
            delete: QAction = new("Delete")

        m = EditMenu()
        qt.track(m)

        actions = m.actions()
        assert_that(actions).is_length(5)
        assert_that(actions[0].text()).is_equal_to("Cut")
        assert_that(actions[1].text()).is_equal_to("Copy")
        assert_that(actions[2].isSeparator()).is_true()
        assert_that(actions[3].text()).is_equal_to("Paste")
        assert_that(actions[4].text()).is_equal_to("Delete")
