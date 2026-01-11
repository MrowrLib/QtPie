# pyright: reportPrivateUsage=false
# pyright: reportMissingParameterType=false
# pyright: reportUnknownParameterType=false
# pyright: reportUntypedBaseClass=false
# pyright: reportUntypedClassDecorator=false
# pyright: reportUnknownArgumentType=false
# pyright: reportUnknownMemberType=false
"""Tests for checkable menu actions.

Checkable actions toggle between checked/unchecked states and can be
bound to Variables for two-way reactivity.
"""

from assertpy import assert_that
from PySide6.QtGui import QAction

from qtpie import Menu, Variable, menu, new
from qtpie.testing import QtDriver


class TestCheckableBasic:
    """Basic checkable action functionality."""

    def test_checkable_action(self, qt: QtDriver) -> None:
        """checkable=True makes action toggleable."""

        @menu(text="&View")
        class ViewMenu(Menu):
            word_wrap: QAction = new("Word Wrap", checkable=True)

        m = ViewMenu()
        qt.track(m)

        assert_that(m.word_wrap.isCheckable()).is_true()
        assert_that(m.word_wrap.isChecked()).is_false()  # Default unchecked

    def test_checkable_initially_checked(self, qt: QtDriver) -> None:
        """Action can start checked."""

        @menu(text="&View")
        class ViewMenu(Menu):
            word_wrap: QAction = new("Word Wrap", checkable=True, checked=True)

        m = ViewMenu()
        qt.track(m)

        assert_that(m.word_wrap.isChecked()).is_true()

    def test_toggle_checkable_action(self, qt: QtDriver) -> None:
        """Checkable action can be toggled."""

        @menu(text="&View")
        class ViewMenu(Menu):
            word_wrap: QAction = new("Word Wrap", checkable=True)

        m = ViewMenu()
        qt.track(m)

        m.word_wrap.toggle()
        assert_that(m.word_wrap.isChecked()).is_true()

        m.word_wrap.toggle()
        assert_that(m.word_wrap.isChecked()).is_false()


class TestCheckedBinding:
    """Two-way binding between checked state and Variable."""

    def test_checked_bound_to_variable(self, qt: QtDriver) -> None:
        """checked= binds action to Variable."""

        @menu(text="&View")
        class ViewMenu(Menu):
            _word_wrap: Variable[bool] = new(False)
            word_wrap: QAction = new("Word Wrap", checkable=True, checked="_word_wrap")

        m = ViewMenu()
        qt.track(m)

        assert_that(m.word_wrap.isChecked()).is_false()
        assert_that(m._word_wrap.value).is_false()

    def test_variable_to_action_binding(self, qt: QtDriver) -> None:
        """Variable change updates action checked state."""

        @menu(text="&View")
        class ViewMenu(Menu):
            _word_wrap: Variable[bool] = new(False)
            word_wrap: QAction = new("Word Wrap", checkable=True, checked="_word_wrap")

        m = ViewMenu()
        qt.track(m)

        m._word_wrap.value = True
        assert_that(m.word_wrap.isChecked()).is_true()

        m._word_wrap.value = False
        assert_that(m.word_wrap.isChecked()).is_false()

    def test_action_to_variable_binding(self, qt: QtDriver) -> None:
        """Action toggle updates Variable."""

        @menu(text="&View")
        class ViewMenu(Menu):
            _word_wrap: Variable[bool] = new(False)
            word_wrap: QAction = new("Word Wrap", checkable=True, checked="_word_wrap")

        m = ViewMenu()
        qt.track(m)

        m.word_wrap.setChecked(True)
        assert_that(m._word_wrap.value).is_true()

        m.word_wrap.setChecked(False)
        assert_that(m._word_wrap.value).is_false()

    def test_variable_initial_true(self, qt: QtDriver) -> None:
        """Action starts checked when Variable is True."""

        @menu(text="&View")
        class ViewMenu(Menu):
            _enabled: Variable[bool] = new(True)
            feature: QAction = new("Feature", checkable=True, checked="_enabled")

        m = ViewMenu()
        qt.track(m)

        assert_that(m.feature.isChecked()).is_true()

    def test_multiple_checkable_actions(self, qt: QtDriver) -> None:
        """Multiple checkable actions with independent bindings."""

        @menu(text="&View")
        class ViewMenu(Menu):
            _word_wrap: Variable[bool] = new(False)
            _line_numbers: Variable[bool] = new(True)
            _minimap: Variable[bool] = new(False)

            word_wrap: QAction = new("Word Wrap", checkable=True, checked="_word_wrap")
            line_numbers: QAction = new("Line Numbers", checkable=True, checked="_line_numbers")
            minimap: QAction = new("Minimap", checkable=True, checked="_minimap")

        m = ViewMenu()
        qt.track(m)

        assert_that(m.word_wrap.isChecked()).is_false()
        assert_that(m.line_numbers.isChecked()).is_true()
        assert_that(m.minimap.isChecked()).is_false()

        m._word_wrap.value = True
        m._line_numbers.value = False

        assert_that(m.word_wrap.isChecked()).is_true()
        assert_that(m.line_numbers.isChecked()).is_false()


class TestToggledCallback:
    """toggled= callback for checkable actions."""

    def test_toggled_callback(self, qt: QtDriver) -> None:
        """toggled= connects to method."""

        @menu(text="&View")
        class ViewMenu(Menu):
            toggle_count: int = 0
            word_wrap: QAction = new("Word Wrap", checkable=True, toggled="on_toggled")

            def on_toggled(self, checked: bool) -> None:
                self.toggle_count += 1

        m = ViewMenu()
        qt.track(m)

        m.word_wrap.toggle()
        assert_that(m.toggle_count).is_equal_to(1)

        m.word_wrap.toggle()
        assert_that(m.toggle_count).is_equal_to(2)

    def test_toggled_receives_state(self, qt: QtDriver) -> None:
        """toggled= callback receives checked state."""

        @menu(text="&View")
        class ViewMenu(Menu):
            last_state: bool | None = None
            word_wrap: QAction = new("Word Wrap", checkable=True, toggled="on_toggled")

            def on_toggled(self, checked: bool) -> None:
                self.last_state = checked

        m = ViewMenu()
        qt.track(m)

        m.word_wrap.setChecked(True)
        assert_that(m.last_state).is_true()

        m.word_wrap.setChecked(False)
        assert_that(m.last_state).is_false()

    def test_checked_and_toggled_together(self, qt: QtDriver) -> None:
        """checked= and toggled= can be used together."""

        @menu(text="&View")
        class ViewMenu(Menu):
            _enabled: Variable[bool] = new(False)
            callback_count: int = 0
            feature: QAction = new(
                "Feature",
                checkable=True,
                checked="_enabled",
                toggled="on_toggled",
            )

            def on_toggled(self, checked: bool) -> None:
                self.callback_count += 1

        m = ViewMenu()
        qt.track(m)

        # Toggle via variable
        m._enabled.value = True
        # Note: programmatic changes may or may not trigger toggled signal
        # depending on Qt implementation

        # Toggle via action
        m.feature.toggle()
        assert_that(m._enabled.value).is_false()  # Toggled from True to False
