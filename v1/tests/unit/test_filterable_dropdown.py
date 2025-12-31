"""Tests for FilterableDropdown widget."""

from assertpy import assert_that
from qtpy.QtCore import Qt
from qtpy.QtTest import QTest

from qtpie.testing import QtDriver
from qtpie.widgets import FilterableDropdown


class TestFilterableDropdownBasics:
    """Basic functionality tests."""

    def test_creates_with_no_items(self, qt: QtDriver) -> None:
        """Should create an empty dropdown."""
        dropdown = FilterableDropdown()
        qt.track(dropdown)

        assert_that(dropdown.current_text()).is_equal_to("")

    def test_set_items(self, qt: QtDriver) -> None:
        """Should accept a list of items."""
        dropdown = FilterableDropdown()
        qt.track(dropdown)

        dropdown.set_items(["Apple", "Banana", "Cherry"])

        # Items are set - verify by checking filtered count
        assert_that(dropdown.filtered_count).is_equal_to(3)

    def test_set_placeholder_text(self, qt: QtDriver) -> None:
        """Should set placeholder text on line edit."""
        dropdown = FilterableDropdown()
        qt.track(dropdown)

        dropdown.set_placeholder_text("Search...")

        assert_that(dropdown.placeholder_text()).is_equal_to("Search...")

    def test_current_text(self, qt: QtDriver) -> None:
        """Should return current text from line edit."""
        dropdown = FilterableDropdown()
        qt.track(dropdown)

        dropdown.set_text("Hello")

        assert_that(dropdown.current_text()).is_equal_to("Hello")

    def test_set_text(self, qt: QtDriver) -> None:
        """Should set text in line edit."""
        dropdown = FilterableDropdown()
        qt.track(dropdown)

        dropdown.set_text("World")

        assert_that(dropdown.current_text()).is_equal_to("World")

    def test_clear(self, qt: QtDriver) -> None:
        """Should clear the line edit."""
        dropdown = FilterableDropdown()
        qt.track(dropdown)

        dropdown.set_text("Something")
        dropdown.clear()

        assert_that(dropdown.current_text()).is_equal_to("")


class TestFilterableDropdownFiltering:
    """Filtering behavior tests."""

    def test_filters_case_insensitive(self, qt: QtDriver) -> None:
        """Should filter items case-insensitively."""
        dropdown = FilterableDropdown()
        qt.track(dropdown)
        dropdown.set_items(["Apple", "Apricot", "Banana"])

        # Type lowercase "ap", should match "Apple" and "Apricot" (case-insensitive)
        QTest.keyClicks(dropdown._line_edit, "ap")  # pyright: ignore[reportPrivateUsage]

        assert_that(dropdown.filtered_count).is_equal_to(2)

    def test_filters_on_text_edit(self, qt: QtDriver) -> None:
        """Should filter as user types."""
        dropdown = FilterableDropdown()
        qt.track(dropdown)
        dropdown.set_items(["Apple", "Apricot", "Banana", "Cherry"])

        QTest.keyClicks(dropdown._line_edit, "a")  # pyright: ignore[reportPrivateUsage]
        assert_that(dropdown.filtered_count).is_equal_to(3)  # Apple, Apricot, Banana

        QTest.keyClicks(dropdown._line_edit, "p")  # pyright: ignore[reportPrivateUsage]
        assert_that(dropdown.filtered_count).is_equal_to(2)  # Apple, Apricot

    def test_empty_filter_shows_all(self, qt: QtDriver) -> None:
        """Empty filter should show all items."""
        dropdown = FilterableDropdown()
        qt.track(dropdown)
        dropdown.set_items(["Apple", "Banana", "Cherry"])

        assert_that(dropdown.filtered_count).is_equal_to(3)


class TestFilterableDropdownPopup:
    """Popup behavior tests."""

    def test_popup_hidden_initially(self, qt: QtDriver) -> None:
        """Popup should be hidden on creation."""
        dropdown = FilterableDropdown()
        qt.track(dropdown)

        assert_that(dropdown.is_popup_visible()).is_false()

    def test_popup_shows_on_typing(self, qt: QtDriver) -> None:
        """Popup should show when user types and there are matches."""
        dropdown = FilterableDropdown()
        qt.track(dropdown)
        dropdown.set_items(["Apple", "Banana"])
        dropdown.show()

        QTest.keyClicks(dropdown._line_edit, "a")  # pyright: ignore[reportPrivateUsage]

        assert_that(dropdown.is_popup_visible()).is_true()

    def test_popup_hides_on_escape(self, qt: QtDriver) -> None:
        """Escape key should hide the popup."""
        dropdown = FilterableDropdown()
        qt.track(dropdown)
        dropdown.set_items(["Apple", "Banana"])
        dropdown.show()

        # Show popup by typing
        QTest.keyClicks(dropdown._line_edit, "a")  # pyright: ignore[reportPrivateUsage]
        assert_that(dropdown.is_popup_visible()).is_true()

        # Press escape
        QTest.keyClick(dropdown._line_edit, Qt.Key.Key_Escape)  # pyright: ignore[reportPrivateUsage]

        assert_that(dropdown.is_popup_visible()).is_false()

    def test_popup_hides_when_no_matches(self, qt: QtDriver) -> None:
        """Popup should hide when filter returns no matches."""
        dropdown = FilterableDropdown()
        qt.track(dropdown)
        dropdown.set_items(["Apple", "Banana"])
        dropdown.show()

        QTest.keyClicks(dropdown._line_edit, "xyz")  # pyright: ignore[reportPrivateUsage]

        assert_that(dropdown.is_popup_visible()).is_false()

    def test_show_popup_method(self, qt: QtDriver) -> None:
        """show_popup() should programmatically show the popup."""
        dropdown = FilterableDropdown()
        qt.track(dropdown)
        dropdown.set_items(["Apple", "Banana"])
        dropdown.show()

        dropdown.show_popup()

        assert_that(dropdown.is_popup_visible()).is_true()

    def test_hide_popup_method(self, qt: QtDriver) -> None:
        """hide_popup() should programmatically hide the popup."""
        dropdown = FilterableDropdown()
        qt.track(dropdown)
        dropdown.set_items(["Apple", "Banana"])
        dropdown.show()

        dropdown.show_popup()
        dropdown.hide_popup()

        assert_that(dropdown.is_popup_visible()).is_false()


class TestFilterableDropdownKeyboardNavigation:
    """Keyboard navigation tests."""

    def test_down_arrow_navigates_forward(self, qt: QtDriver) -> None:
        """Down arrow should move selection forward."""
        dropdown = FilterableDropdown()
        qt.track(dropdown)
        dropdown.set_items(["Apple", "Banana", "Cherry"])
        dropdown.show()

        dropdown.show_popup()
        assert_that(dropdown.current_index).is_equal_to(0)

        QTest.keyClick(dropdown._line_edit, Qt.Key.Key_Down)  # pyright: ignore[reportPrivateUsage]
        assert_that(dropdown.current_index).is_equal_to(1)

        QTest.keyClick(dropdown._line_edit, Qt.Key.Key_Down)  # pyright: ignore[reportPrivateUsage]
        assert_that(dropdown.current_index).is_equal_to(2)

    def test_up_arrow_navigates_backward(self, qt: QtDriver) -> None:
        """Up arrow should move selection backward."""
        dropdown = FilterableDropdown()
        qt.track(dropdown)
        dropdown.set_items(["Apple", "Banana", "Cherry"])
        dropdown.show()

        dropdown.show_popup()
        dropdown.current_index = 2

        QTest.keyClick(dropdown._line_edit, Qt.Key.Key_Up)  # pyright: ignore[reportPrivateUsage]
        assert_that(dropdown.current_index).is_equal_to(1)

    def test_navigation_wraps_around(self, qt: QtDriver) -> None:
        """Navigation should wrap from last to first and vice versa."""
        dropdown = FilterableDropdown()
        qt.track(dropdown)
        dropdown.set_items(["Apple", "Banana", "Cherry"])
        dropdown.show()

        dropdown.show_popup()

        # Go past last item
        dropdown.current_index = 2
        QTest.keyClick(dropdown._line_edit, Qt.Key.Key_Down)  # pyright: ignore[reportPrivateUsage]
        assert_that(dropdown.current_index).is_equal_to(0)

        # Go before first item
        QTest.keyClick(dropdown._line_edit, Qt.Key.Key_Up)  # pyright: ignore[reportPrivateUsage]
        assert_that(dropdown.current_index).is_equal_to(2)

    def test_enter_selects_current_item(self, qt: QtDriver) -> None:
        """Enter key should select the current item."""
        dropdown = FilterableDropdown()
        qt.track(dropdown)
        dropdown.set_items(["Apple", "Banana", "Cherry"])
        dropdown.show()

        dropdown.show_popup()
        QTest.keyClick(dropdown._line_edit, Qt.Key.Key_Down)  # pyright: ignore[reportPrivateUsage]
        QTest.keyClick(dropdown._line_edit, Qt.Key.Key_Return)  # pyright: ignore[reportPrivateUsage]

        assert_that(dropdown.current_text()).is_equal_to("Banana")
        assert_that(dropdown.is_popup_visible()).is_false()


class TestFilterableDropdownSignals:
    """Signal emission tests."""

    def test_item_selected_signal_emitted_on_enter(self, qt: QtDriver) -> None:
        """item_selected signal should emit when item selected via Enter."""
        dropdown = FilterableDropdown()
        qt.track(dropdown)
        dropdown.set_items(["Apple", "Banana"])
        dropdown.show()

        selected_items: list[str] = []
        dropdown.item_selected.connect(selected_items.append)

        dropdown.show_popup()
        QTest.keyClick(dropdown._line_edit, Qt.Key.Key_Return)  # pyright: ignore[reportPrivateUsage]

        assert_that(selected_items).is_equal_to(["Apple"])

    def test_item_selected_signal_emitted_on_select_current(self, qt: QtDriver) -> None:
        """item_selected signal should emit when select_current() called."""
        dropdown = FilterableDropdown()
        qt.track(dropdown)
        dropdown.set_items(["Apple", "Banana"])
        dropdown.show()

        selected_items: list[str] = []
        dropdown.item_selected.connect(selected_items.append)

        dropdown.show_popup()
        dropdown.current_index = 1
        dropdown.select_current()

        assert_that(selected_items).is_equal_to(["Banana"])
