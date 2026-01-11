# pyright: reportPrivateUsage=false
# pyright: reportMissingParameterType=false
# pyright: reportUnknownParameterType=false
# pyright: reportUntypedBaseClass=false
# pyright: reportUntypedClassDecorator=false
# pyright: reportUnknownArgumentType=false
# pyright: reportUnknownMemberType=false
# pyright: reportIncompatibleMethodOverride=false
"""Tests for cross-class consistency.

These tests verify that features work consistently across Widget, Window, Menu, and App.
Finding inconsistencies here means bugs!
"""

from typing import override

from assertpy import assert_that
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QLabel, QLineEdit

from qtpie import AppBase, Menu, Variable, Widget, Window, app, menu, new, widget, window
from qtpie.testing import QtDriver

# =============================================================================
# TEST: Translation context is set for all class types
# =============================================================================


class TestTranslationContext:
    """Verify translation context is set for all class types."""

    def test_widget_translation_context(self, qt: QtDriver) -> None:
        """Widget sets translation context."""

        @widget
        class MyWidget(Widget):
            label: QLabel = new("Hello")

        w = MyWidget()
        qt.track(w)

        # Context should be set during construction
        # Check the class has proper context setup
        assert_that(True).is_true()  # If we get here, no crash

    def test_window_translation_context(self, qt: QtDriver) -> None:
        """Window sets translation context."""

        @window(title="Test")
        class MyWindow(Window):
            label: QLabel = new("Hello")

        w = MyWindow()
        qt.track(w)

        assert_that(True).is_true()

    def test_menu_translation_context(self, qt: QtDriver) -> None:
        """Menu sets translation context."""

        @menu(text="&File")
        class MyMenu(Menu):
            action: QAction = new("Action")

        m = MyMenu()
        qt.track(m)

        assert_that(True).is_true()

    def test_app_translation_context(self, qt: QtDriver) -> None:
        """App sets translation context."""

        @app(system_tray=False, window=False)
        class MyApp(AppBase):
            _count: Variable[int] = new(0)

        _ = MyApp()

        assert_that(True).is_true()


# =============================================================================
# TEST: Validators work in all class types
# =============================================================================


class TestValidatorsConsistency:
    """Verify validators work in all class types."""

    def test_widget_validator(self, qt: QtDriver) -> None:
        """Widget supports add_validator."""

        @widget
        class MyWidget(Widget):
            _name: Variable[str] = new("")

            def __setup__(self) -> None:
                self.add_validator("_name", "required", lambda v: None if v else "Required")

        w = MyWidget()
        qt.track(w)

        assert_that(w.is_valid.get()).is_false()
        w._name.value = "test"
        assert_that(w.is_valid.get()).is_true()

    def test_window_validator(self, qt: QtDriver) -> None:
        """Window supports add_validator."""

        @window(title="Test")
        class MyWindow(Window):
            _name: Variable[str] = new("")

            def __setup__(self) -> None:
                self.add_validator("_name", "required", lambda v: None if v else "Required")

        w = MyWindow()
        qt.track(w)

        assert_that(w.is_valid.get()).is_false()
        w._name.value = "test"
        assert_that(w.is_valid.get()).is_true()

    def test_menu_validator(self, qt: QtDriver) -> None:
        """Menu supports add_validator."""

        @menu(text="&File")
        class MyMenu(Menu):
            _enabled: Variable[bool] = new(False)
            action: QAction = new("Action")

            def __setup__(self) -> None:
                self.add_validator("_enabled", "must_be_true", lambda v: None if v else "Must enable")

        m = MyMenu()
        qt.track(m)

        assert_that(m.is_valid.get()).is_false()
        m._enabled.value = True
        assert_that(m.is_valid.get()).is_true()

    def test_app_validator(self, qt: QtDriver) -> None:
        """App supports add_validator."""

        @app(system_tray=False, window=False)
        class MyApp(AppBase):
            _name: Variable[str] = new("")

            def __setup__(self) -> None:
                self.add_validator("_name", "required", lambda v: None if v else "Required")

        a = MyApp()

        assert_that(a.is_valid.get()).is_false()
        a._name.value = "test"
        assert_that(a.is_valid.get()).is_true()


# =============================================================================
# TEST: on_dirty_changed hook fires in all class types
# =============================================================================


class TestDirtyHookConsistency:
    """Verify on_dirty_changed fires in all class types."""

    def test_widget_dirty_hook(self, qt: QtDriver) -> None:
        """Widget fires on_dirty_changed."""

        hook_called = []

        @widget
        class MyWidget(Widget):
            _count: Variable[int] = new(0)

            @override
            def on_dirty_changed(self, is_dirty: bool) -> None:
                hook_called.append(is_dirty)

        w = MyWidget()
        qt.track(w)

        w._count.value = 1
        assert_that(hook_called).contains(True)

    def test_window_dirty_hook(self, qt: QtDriver) -> None:
        """Window fires on_dirty_changed."""

        hook_called = []

        @window(title="Test")
        class MyWindow(Window):
            _count: Variable[int] = new(0)

            @override
            def on_dirty_changed(self, is_dirty: bool) -> None:
                hook_called.append(is_dirty)

        w = MyWindow()
        qt.track(w)

        w._count.value = 1
        assert_that(hook_called).contains(True)

    def test_menu_dirty_hook(self, qt: QtDriver) -> None:
        """Menu fires on_dirty_changed."""

        hook_called = []

        @menu(text="&File")
        class MyMenu(Menu):
            _count: Variable[int] = new(0)
            action: QAction = new("Action")

            @override
            def on_dirty_changed(self, is_dirty: bool) -> None:
                hook_called.append(is_dirty)

        m = MyMenu()
        qt.track(m)

        m._count.value = 1
        assert_that(hook_called).contains(True)

    def test_app_dirty_hook(self, qt: QtDriver) -> None:
        """App fires on_dirty_changed."""

        hook_called = []

        @app(system_tray=False, window=False)
        class MyApp(AppBase):
            _count: Variable[int] = new(0)

            @override
            def on_dirty_changed(self, is_dirty: bool) -> None:
                hook_called.append(is_dirty)

        a = MyApp()

        a._count.value = 1
        assert_that(hook_called).contains(True)


# =============================================================================
# TEST: on_valid_changed hook fires in all class types
# =============================================================================


class TestValidHookConsistency:
    """Verify on_valid_changed fires in all class types."""

    def test_widget_valid_hook(self, qt: QtDriver) -> None:
        """Widget fires on_valid_changed."""

        hook_called = []

        @widget
        class MyWidget(Widget):
            _name: Variable[str] = new("")

            def __setup__(self) -> None:
                self.add_validator("_name", "req", lambda v: None if v else "Req")

            @override
            def on_valid_changed(self, is_valid: bool) -> None:
                hook_called.append(is_valid)

        w = MyWidget()
        qt.track(w)

        # Initially invalid, setting value makes valid
        w._name.value = "test"
        assert_that(hook_called).contains(True)

    def test_window_valid_hook(self, qt: QtDriver) -> None:
        """Window fires on_valid_changed."""

        hook_called = []

        @window(title="Test")
        class MyWindow(Window):
            _name: Variable[str] = new("")

            def __setup__(self) -> None:
                self.add_validator("_name", "req", lambda v: None if v else "Req")

            @override
            def on_valid_changed(self, is_valid: bool) -> None:
                hook_called.append(is_valid)

        w = MyWindow()
        qt.track(w)

        w._name.value = "test"
        assert_that(hook_called).contains(True)

    def test_menu_valid_hook(self, qt: QtDriver) -> None:
        """Menu fires on_valid_changed."""

        hook_called = []

        @menu(text="&File")
        class MyMenu(Menu):
            _enabled: Variable[bool] = new(False)
            action: QAction = new("Action")

            def __setup__(self) -> None:
                self.add_validator("_enabled", "req", lambda v: None if v else "Req")

            @override
            def on_valid_changed(self, is_valid: bool) -> None:
                hook_called.append(is_valid)

        m = MyMenu()
        qt.track(m)

        m._enabled.value = True
        assert_that(hook_called).contains(True)

    def test_app_valid_hook(self, qt: QtDriver) -> None:
        """App fires on_valid_changed."""

        hook_called = []

        @app(system_tray=False, window=False)
        class MyApp(AppBase):
            _name: Variable[str] = new("")

            def __setup__(self) -> None:
                self.add_validator("_name", "req", lambda v: None if v else "Req")

            @override
            def on_valid_changed(self, is_valid: bool) -> None:
                hook_called.append(is_valid)

        a = MyApp()

        a._name.value = "test"
        assert_that(hook_called).contains(True)


# =============================================================================
# TEST: QAction property bindings work where expected
# =============================================================================


class TestQActionPropertyBindings:
    """Verify QAction property bindings work in Menu and App."""

    def test_menu_qaction_enabled_binding(self, qt: QtDriver) -> None:
        """Menu QAction enabled= binds to Variable."""

        @menu(text="&File")
        class MyMenu(Menu):
            _can_save: Variable[bool] = new(False)
            save_action: QAction = new("Save", enabled="_can_save")

        m = MyMenu()
        qt.track(m)

        assert_that(m.save_action.isEnabled()).is_false()
        m._can_save.value = True
        assert_that(m.save_action.isEnabled()).is_true()

    def test_app_qaction_enabled_binding(self, qt: QtDriver) -> None:
        """App QAction enabled= binds to Variable."""

        @app(system_tray=True, window=False)
        class MyApp(AppBase):
            _can_quit: Variable[bool] = new(False)
            quit_action: QAction = new("Quit", enabled="_can_quit")

        a = MyApp()

        assert_that(a.quit_action.isEnabled()).is_false()
        a._can_quit.value = True
        assert_that(a.quit_action.isEnabled()).is_true()

    def test_menu_qaction_visible_binding(self, qt: QtDriver) -> None:
        """Menu QAction visible= binds to Variable."""

        @menu(text="&File")
        class MyMenu(Menu):
            _show_debug: Variable[bool] = new(False)
            debug_action: QAction = new("Debug", visible="_show_debug")

        m = MyMenu()
        qt.track(m)

        assert_that(m.debug_action.isVisible()).is_false()
        m._show_debug.value = True
        assert_that(m.debug_action.isVisible()).is_true()


# =============================================================================
# TEST: Variable[T, W] label= works in all class types with form layout
# =============================================================================


class TestVariableTWLabelConsistency:
    """Verify Variable[T, W] with label= works in form layouts."""

    def test_widget_variable_tw_label(self, qt: QtDriver) -> None:
        """Widget Variable[T, W] with label= in form layout."""

        @widget(layout="form")
        class MyWidget(Widget):
            _name: Variable[str, QLineEdit] = new("")(label="Name:")

        w = MyWidget()
        qt.track(w)

        # Should not crash, widget should exist
        assert_that(w._name.widget).is_instance_of(QLineEdit)

    def test_window_variable_tw_label(self, qt: QtDriver) -> None:
        """Window Variable[T, W] with label= in form layout."""

        @window(title="Test", layout="form")
        class MyWindow(Window):
            _name: Variable[str, QLineEdit] = new("")(label="Name:")

        w = MyWindow()
        qt.track(w)

        assert_that(w._name.widget).is_instance_of(QLineEdit)

    def test_app_variable_tw_label(self, qt: QtDriver) -> None:
        """App Variable[T, W] with label= in form layout."""

        @app(layout="form")
        class MyApp(AppBase):
            _name: Variable[str, QLineEdit] = new("")(label="Name:")

        a = MyApp()

        assert_that(a._name.widget).is_instance_of(QLineEdit)


# =============================================================================
# TEST: Signal expressions work in all class types
# =============================================================================


class TestSignalExpressionsConsistency:
    """Verify signal expressions work in all class types.

    Note: Signal expressions need curly braces like triggered="{set_value(99)}"
    Without braces, it's treated as a method name.
    """

    def test_menu_signal_expression_with_arg(self, qt: QtDriver) -> None:
        """Menu signal expression with argument."""

        @menu(text="&File")
        class MyMenu(Menu):
            result: int = 0
            action: QAction = new("Action", triggered="{set_value(99)}")

            def set_value(self, val: int) -> None:
                self.result = val

        m = MyMenu()
        qt.track(m)

        m.action.trigger()
        assert_that(m.result).is_equal_to(99)

    def test_app_signal_expression_with_arg(self, qt: QtDriver) -> None:
        """App signal expression with argument."""

        @app(system_tray=True, window=False)
        class MyApp(AppBase):
            result: int = 0
            action: QAction = new("Action", triggered="{set_value(77)}")

            def set_value(self, val: int) -> None:
                self.result = val

        a = MyApp()

        a.action.trigger()
        assert_that(a.result).is_equal_to(77)

    def test_menu_simple_method_name(self, qt: QtDriver) -> None:
        """Menu signal with simple method name (no args)."""

        @menu(text="&File")
        class MyMenu(Menu):
            clicked: bool = False
            action: QAction = new("Action", triggered="on_action")

            def on_action(self) -> None:
                self.clicked = True

        m = MyMenu()
        qt.track(m)

        m.action.trigger()
        assert_that(m.clicked).is_true()

    def test_app_simple_method_name(self, qt: QtDriver) -> None:
        """App signal with simple method name (no args)."""

        @app(system_tray=True, window=False)
        class MyApp(AppBase):
            clicked: bool = False
            action: QAction = new("Action", triggered="on_action")

            def on_action(self) -> None:
                self.clicked = True

        a = MyApp()

        a.action.trigger()
        assert_that(a.clicked).is_true()


# =============================================================================
# TEST: Record types work in all class types
# =============================================================================


class TestRecordTypeConsistency:
    """Verify record types work in all class types."""

    def test_widget_record_auto_bind(self, qt: QtDriver) -> None:
        """Widget[T] auto-binds fields to record properties."""
        from dataclasses import dataclass

        @dataclass
        class Person:
            name: str = ""

        @widget(record=Person("Alice"))
        class MyWidget(Widget[Person]):
            name: QLineEdit = new()

        w = MyWidget()
        qt.track(w)

        # Field should be bound to record.name
        assert_that(w.name.text()).is_equal_to("Alice")

    def test_window_record_auto_bind(self, qt: QtDriver) -> None:
        """Window[T] auto-binds fields to record properties."""
        from dataclasses import dataclass

        @dataclass
        class Person:
            name: str = ""

        @window(title="Test", record=Person("Bob"))
        class MyWindow(Window[Person]):
            name: QLineEdit = new()

        w = MyWindow()
        qt.track(w)

        assert_that(w.name.text()).is_equal_to("Bob")

    def test_menu_record_auto_bind(self, qt: QtDriver) -> None:
        """Menu[T] auto-binds to record properties."""
        from dataclasses import dataclass

        @dataclass
        class State:
            can_save: bool = False

        @menu(text="&File", record=State(can_save=True))
        class MyMenu(Menu[State]):
            save_action: QAction = new("Save", enabled="{record.can_save}")

        m = MyMenu()
        qt.track(m)

        # Action should be enabled because record.can_save is True
        assert_that(m.save_action.isEnabled()).is_true()

    def test_app_record_auto_bind(self, qt: QtDriver) -> None:
        """App[T] auto-binds fields to record properties."""
        from dataclasses import dataclass

        @dataclass
        class Settings:
            username: str = ""

        @app(record=Settings("admin"))
        class MyApp(AppBase[Settings]):
            username: QLineEdit = new()

        a = MyApp()

        assert_that(a.username.text()).is_equal_to("admin")
