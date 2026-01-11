# pyright: reportPrivateUsage=false
# pyright: reportMissingParameterType=false
# pyright: reportUnknownParameterType=false
# pyright: reportUntypedBaseClass=false
# pyright: reportUntypedClassDecorator=false
# pyright: reportUnknownArgumentType=false
# pyright: reportUnknownMemberType=false
"""Tests for menu sections.

Sections are labeled groupings in menus with text headers.
"""

from assertpy import assert_that
from PySide6.QtGui import QAction

from qtpie import Menu, menu, new
from qtpie.menu import Section
from qtpie.testing import QtDriver


class TestSectionBasic:
    """Basic section functionality."""

    def test_section_from_field_name(self, qt: QtDriver) -> None:
        """Section text derived from field name (stripping underscores)."""

        @menu(text="&File")
        class FileMenu(Menu):
            ___recent___: Section
            file1: QAction = new("file1.txt")

        m = FileMenu()
        qt.track(m)

        actions = m.actions()
        assert_that(actions).is_length(2)
        # First action is the section (uses addSection which creates a disabled action)
        assert_that(actions[0].text()).is_equal_to("Recent")

    def test_section_snake_case_name(self, qt: QtDriver) -> None:
        """Section converts snake_case to Title Case."""

        @menu(text="&File")
        class FileMenu(Menu):
            ___recent_files___: Section
            file1: QAction = new("file1.txt")

        m = FileMenu()
        qt.track(m)

        actions = m.actions()
        assert_that(actions[0].text()).is_equal_to("Recent Files")

    def test_section_explicit_text(self, qt: QtDriver) -> None:
        """Section with explicit text via new()."""

        @menu(text="&File")
        class FileMenu(Menu):
            ___recent___: Section = new("Recently Opened Files")
            file1: QAction = new("file1.txt")

        m = FileMenu()
        qt.track(m)

        actions = m.actions()
        assert_that(actions[0].text()).is_equal_to("Recently Opened Files")

    def test_section_text_kwarg(self, qt: QtDriver) -> None:
        """Section with text= keyword argument."""

        @menu(text="&File")
        class FileMenu(Menu):
            ___recent___: Section = new(text="Recent Items")
            file1: QAction = new("file1.txt")

        m = FileMenu()
        qt.track(m)

        actions = m.actions()
        assert_that(actions[0].text()).is_equal_to("Recent Items")


class TestSectionOrdering:
    """Section ordering and grouping."""

    def test_multiple_sections(self, qt: QtDriver) -> None:
        """Multiple sections in one menu."""

        @menu(text="&File")
        class FileMenu(Menu):
            ___recent___: Section
            file1: QAction = new("file1.txt")
            file2: QAction = new("file2.txt")
            ___favorites___: Section
            fav1: QAction = new("favorite.txt")

        m = FileMenu()
        qt.track(m)

        actions = m.actions()
        assert_that(actions).is_length(5)
        assert_that(actions[0].text()).is_equal_to("Recent")
        assert_that(actions[3].text()).is_equal_to("Favorites")

    def test_section_preserves_order(self, qt: QtDriver) -> None:
        """Sections appear in declaration order."""

        @menu(text="&View")
        class ViewMenu(Menu):
            ___layout___: Section
            horizontal: QAction = new("Horizontal")
            ___zoom___: Section
            zoom_in: QAction = new("Zoom In")
            ___window___: Section
            fullscreen: QAction = new("Fullscreen")

        m = ViewMenu()
        qt.track(m)

        actions = m.actions()
        texts = [a.text() for a in actions]
        assert_that(texts).is_equal_to(
            [
                "Layout",
                "Horizontal",
                "Zoom",
                "Zoom In",
                "Window",
                "Fullscreen",
            ]
        )


# NOTE: Section bind= is documented but not yet implemented.
# See docstring in menu.py Section class:
#   ___dynamic___: Section = new(bind="_section_title")  # Reactive
# When implemented, add tests here.
