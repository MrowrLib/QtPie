# pyright: reportPrivateUsage=false
# pyright: reportMissingParameterType=false
# pyright: reportUnknownParameterType=false
# pyright: reportUntypedBaseClass=false
# pyright: reportUntypedClassDecorator=false
# pyright: reportUnknownArgumentType=false
# pyright: reportUnknownMemberType=false
"""Tests for #parent placeholder in menu expressions.

The #parent placeholder allows menus to reference variables from
their parent Window.
"""

from assertpy import assert_that
from PySide6.QtGui import QAction

from qtpie import Menu, Variable, Window, menu, new, window
from qtpie.testing import QtDriver


class TestParentPlaceholderEnabled:
    """#parent placeholder in enabled= bindings."""

    def test_enabled_bound_to_parent_variable(self, qt: QtDriver) -> None:
        """enabled= can reference parent window's Variable."""

        @menu(text="&File")
        class FileMenu(Menu):
            save: QAction = new("Save", enabled="{#parent._is_dirty}")

        @window(title="App")
        class App(Window):
            _is_dirty: Variable[bool] = new(False)
            file_menu: FileMenu = new()

        app = App()
        qt.track(app)

        # Initially disabled (parent._is_dirty is False)
        assert_that(app.file_menu.save.isEnabled()).is_false()

    def test_enabled_updates_with_parent_variable(self, qt: QtDriver) -> None:
        """enabled= updates when parent Variable changes."""

        @menu(text="&File")
        class FileMenu(Menu):
            save: QAction = new("Save", enabled="{#parent._is_dirty}")

        @window(title="App")
        class App(Window):
            _is_dirty: Variable[bool] = new(False)
            file_menu: FileMenu = new()

        app = App()
        qt.track(app)

        app._is_dirty.value = True
        assert_that(app.file_menu.save.isEnabled()).is_true()

        app._is_dirty.value = False
        assert_that(app.file_menu.save.isEnabled()).is_false()

    def test_enabled_complex_parent_expression(self, qt: QtDriver) -> None:
        """enabled= with complex parent expression."""

        @menu(text="&File")
        class FileMenu(Menu):
            save: QAction = new("Save", enabled="{#parent._is_dirty and #parent._can_save}")

        @window(title="App")
        class App(Window):
            _is_dirty: Variable[bool] = new(True)
            _can_save: Variable[bool] = new(False)
            file_menu: FileMenu = new()

        app = App()
        qt.track(app)

        # One condition true, one false
        assert_that(app.file_menu.save.isEnabled()).is_false()

        # Both conditions true
        app._can_save.value = True
        assert_that(app.file_menu.save.isEnabled()).is_true()

        # First condition becomes false
        app._is_dirty.value = False
        assert_that(app.file_menu.save.isEnabled()).is_false()


class TestParentPlaceholderVisible:
    """#parent placeholder in visible= bindings."""

    def test_visible_bound_to_parent_variable(self, qt: QtDriver) -> None:
        """visible= can reference parent window's Variable."""

        @menu(text="&Advanced")
        class AdvancedMenu(Menu):
            debug: QAction = new("Debug", visible="{#parent._show_debug}")

        @window(title="App")
        class App(Window):
            _show_debug: Variable[bool] = new(False)
            advanced_menu: AdvancedMenu = new()

        app = App()
        qt.track(app)

        assert_that(app.advanced_menu.debug.isVisible()).is_false()

        app._show_debug.value = True
        assert_that(app.advanced_menu.debug.isVisible()).is_true()


# NOTE: Mixed #parent and local menu variables in same expression
# (e.g., enabled="{#parent._is_dirty and _has_file}") is not yet supported.
# When implemented, add tests here.


class TestParentPlaceholderWithoutUnderscore:
    """#parent with variable names that may or may not have underscores."""

    def test_parent_variable_lookup_with_underscore(self, qt: QtDriver) -> None:
        """#parent._var looks up _var on parent."""

        @menu(text="&File")
        class FileMenu(Menu):
            action: QAction = new("Action", enabled="{#parent._enabled}")

        @window(title="App")
        class App(Window):
            _enabled: Variable[bool] = new(True)
            file_menu: FileMenu = new()

        app = App()
        qt.track(app)

        assert_that(app.file_menu.action.isEnabled()).is_true()

    def test_parent_variable_lookup_without_underscore(self, qt: QtDriver) -> None:
        """#parent.var looks up var (without underscore) on parent."""

        @menu(text="&File")
        class FileMenu(Menu):
            action: QAction = new("Action", enabled="{#parent.is_ready}")

        @window(title="App")
        class App(Window):
            is_ready: Variable[bool] = new(True)
            file_menu: FileMenu = new()

        app = App()
        qt.track(app)

        assert_that(app.file_menu.action.isEnabled()).is_true()


class TestParentPlaceholderMultipleMenus:
    """Multiple menus referencing same parent variables."""

    def test_multiple_menus_same_parent_variable(self, qt: QtDriver) -> None:
        """Multiple menus can bind to same parent Variable."""

        @menu(text="&File")
        class FileMenu(Menu):
            save: QAction = new("Save", enabled="{#parent._is_dirty}")

        @menu(text="&Edit")
        class EditMenu(Menu):
            undo: QAction = new("Undo", enabled="{#parent._is_dirty}")

        @window(title="App")
        class App(Window):
            _is_dirty: Variable[bool] = new(False)
            file_menu: FileMenu = new()
            edit_menu: EditMenu = new()

        app = App()
        qt.track(app)

        # Both disabled initially
        assert_that(app.file_menu.save.isEnabled()).is_false()
        assert_that(app.edit_menu.undo.isEnabled()).is_false()

        # Both update when parent changes
        app._is_dirty.value = True
        assert_that(app.file_menu.save.isEnabled()).is_true()
        assert_that(app.edit_menu.undo.isEnabled()).is_true()
