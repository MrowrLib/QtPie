# pyright: reportPrivateUsage=false
# pyright: reportMissingTypeArgument=false
# pyright: reportUnknownMemberType=false
"""Tests for the Menu system (@menu decorator)."""

from assertpy import assert_that
from qtpy.QtGui import QAction

from qtpie import Menu, Section, Separator, Variable, Window, menu, new, window
from qtpie.testing import QtDriver

# =============================================================================
# C.1: Menu Base Class with Variable Support
# =============================================================================


class TestMenuBaseClass:
    """Test Menu base class."""

    def test_menu_has_config(self, qt: QtDriver) -> None:
        """Menu subclass has _qtpie_config."""

        @menu
        class FileMenu(Menu):
            pass

        assert hasattr(FileMenu, "_qtpie_config")

    def test_bare_variable_detected_as_required(self, qt: QtDriver) -> None:
        """Bare Variable[T] is a required binding."""

        @menu
        class FileMenu(Menu):
            recent_files: Variable[list[str]]  # Required

        assert "recent_files" in FileMenu._qtpie_config.required_bindings

    def test_variable_with_default_is_optional(self, qt: QtDriver) -> None:
        """Variable[T] = new(default) is optional."""

        @menu
        class FileMenu(Menu):
            recent_files: Variable[list[str]] = new([])

        assert "recent_files" not in FileMenu._qtpie_config.required_bindings


# =============================================================================
# C.2: @menu Decorator
# =============================================================================


class TestMenuDecorator:
    """Test @menu decorator."""

    def test_menu_without_args(self, qt: QtDriver) -> None:
        """@menu without args works."""

        @menu
        class FileMenu(Menu):
            pass

        m = qt.track(FileMenu())
        assert_that(m.title()).is_equal_to("File")

    def test_menu_with_text(self, qt: QtDriver) -> None:
        """@menu(text="&File") sets menu title."""

        @menu(text="&File")
        class MyMenu(Menu):
            pass

        m = qt.track(MyMenu())
        assert_that(m.title()).is_equal_to("&File")

    def test_menu_derives_title_from_classname(self, qt: QtDriver) -> None:
        """Menu title derived from class name: FileMenu -> "File"."""

        @menu
        class FileMenu(Menu):
            pass

        @menu
        class EditMenu(Menu):
            pass

        @menu
        class HelpMenu(Menu):
            pass

        file_menu = qt.track(FileMenu())
        edit_menu = qt.track(EditMenu())
        help_menu = qt.track(HelpMenu())

        assert_that(file_menu.title()).is_equal_to("File")
        assert_that(edit_menu.title()).is_equal_to("Edit")
        assert_that(help_menu.title()).is_equal_to("Help")

    def test_menu_with_name(self, qt: QtDriver) -> None:
        """@menu(name="...") sets objectName."""

        @menu(name="file-menu")
        class FileMenu(Menu):
            pass

        m = qt.track(FileMenu())
        assert_that(m.objectName()).is_equal_to("file-menu")

    def test_menu_default_objectname(self, qt: QtDriver) -> None:
        """Default objectName is class name."""

        @menu
        class FileMenu(Menu):
            pass

        m = qt.track(FileMenu())
        assert_that(m.objectName()).is_equal_to("FileMenu")


# =============================================================================
# C.3: Process QAction Fields
# =============================================================================


class TestMenuActions:
    """Test QAction field processing."""

    def test_action_added_to_menu(self, qt: QtDriver) -> None:
        """QAction fields are added to menu."""

        @menu(text="&File")
        class FileMenu(Menu):
            new_action: QAction = new("&New")
            open_action: QAction = new("&Open")

        m = qt.track(FileMenu())
        actions = m.actions()

        assert_that(len(actions)).is_equal_to(2)
        assert_that(actions[0].text()).is_equal_to("&New")
        assert_that(actions[1].text()).is_equal_to("&Open")

    def test_action_signal_connected_by_name(self, qt: QtDriver) -> None:
        """triggered="method_name" connects signal."""
        triggered = False

        @menu(text="&File")
        class FileMenu(Menu):
            new_action: QAction = new("&New", triggered="on_new")

            def on_new(self) -> None:
                nonlocal triggered
                triggered = True

        m = qt.track(FileMenu())
        m.new_action.trigger()

        assert_that(triggered).is_true()

    def test_action_signal_connected_by_lambda(self, qt: QtDriver) -> None:
        """triggered=lambda connects signal."""
        triggered = False

        @menu(text="&File")
        class FileMenu(Menu):
            new_action: QAction = new("&New", triggered=lambda: nonlocal_set())

        def nonlocal_set() -> None:
            nonlocal triggered
            triggered = True

        m = qt.track(FileMenu())
        m.new_action.trigger()

        assert_that(triggered).is_true()

    def test_action_with_shortcut(self, qt: QtDriver) -> None:
        """QAction with shortcut= kwarg."""

        @menu(text="&File")
        class FileMenu(Menu):
            new_action: QAction = new("&New", shortcut="Ctrl+N")

        m = qt.track(FileMenu())
        assert_that(m.new_action.shortcut().toString()).is_equal_to("Ctrl+N")


# =============================================================================
# C.4: Separator
# =============================================================================


class TestMenuSeparator:
    """Test Separator marker class."""

    def test_separator_bare_annotation(self, qt: QtDriver) -> None:
        """Bare Separator annotation creates separator."""

        @menu(text="&File")
        class FileMenu(Menu):
            new_action: QAction = new("&New")
            ____: Separator
            exit_action: QAction = new("E&xit")

        m = qt.track(FileMenu())
        actions = m.actions()

        assert_that(len(actions)).is_equal_to(3)
        assert_that(actions[0].text()).is_equal_to("&New")
        assert_that(actions[1].isSeparator()).is_true()
        assert_that(actions[2].text()).is_equal_to("E&xit")

    def test_multiple_separators(self, qt: QtDriver) -> None:
        """Multiple separators work."""

        @menu(text="&File")
        class FileMenu(Menu):
            action1: QAction = new("Action 1")
            _1: Separator
            action2: QAction = new("Action 2")
            _2: Separator
            action3: QAction = new("Action 3")

        m = qt.track(FileMenu())
        actions = m.actions()

        assert_that(len(actions)).is_equal_to(5)
        assert_that(actions[1].isSeparator()).is_true()
        assert_that(actions[3].isSeparator()).is_true()


# =============================================================================
# C.5: Section
# =============================================================================


class TestMenuSection:
    """Test Section marker class."""

    def test_section_from_name(self, qt: QtDriver) -> None:
        """Section text derived from field name: ___recent___ -> "Recent"."""

        @menu(text="&File")
        class FileMenu(Menu):
            ___recent___: Section
            file1: QAction = new("file1.txt")

        m = qt.track(FileMenu())
        actions = m.actions()

        # First action should be section
        assert_that(len(actions)).is_equal_to(2)
        assert_that(actions[0].text()).is_equal_to("Recent")

    def test_section_with_explicit_text(self, qt: QtDriver) -> None:
        """Section with explicit text via new()."""

        @menu(text="&File")
        class FileMenu(Menu):
            ___recent___: Section = new("Recent Files")
            file1: QAction = new("file1.txt")

        m = qt.track(FileMenu())
        actions = m.actions()

        assert_that(actions[0].text()).is_equal_to("Recent Files")

    def test_section_snake_case(self, qt: QtDriver) -> None:
        """Section with snake_case name: ___recent_files___ -> "Recent Files"."""

        @menu(text="&File")
        class FileMenu(Menu):
            ___recent_files___: Section
            file1: QAction = new("file1.txt")

        m = qt.track(FileMenu())
        actions = m.actions()

        assert_that(actions[0].text()).is_equal_to("Recent Files")


# =============================================================================
# Variable Bindings in Menu
# =============================================================================


class TestMenuVariableBindings:
    """Test Variable bindings in Menu (same as Widget/Window)."""

    def test_menu_with_optional_variable(self, qt: QtDriver) -> None:
        """Menu with optional Variable works."""

        @menu(text="&View")
        class ViewMenu(Menu):
            _dark_mode: Variable[bool] = new(False)

        m = qt.track(ViewMenu())
        assert_that(m._dark_mode.value).is_false()

        m._dark_mode.value = True
        assert_that(m._dark_mode.value).is_true()

    def test_menu_setup_called(self, qt: QtDriver) -> None:
        """__setup__ is called after menu initialization."""
        setup_called = False

        @menu(text="&File")
        class FileMenu(Menu):
            new_action: QAction = new("&New")

            def __setup__(self) -> None:  # pyright: ignore[reportImplicitOverride]
                nonlocal setup_called
                setup_called = True
                # Actions should be ready
                assert self.new_action is not None

        qt.track(FileMenu())
        assert_that(setup_called).is_true()


# =============================================================================
# C.7: Checkable Actions
# =============================================================================


class TestCheckableActions:
    """Test checkable action support."""

    def test_checkable_action(self, qt: QtDriver) -> None:
        """checkable=True makes action checkable."""

        @menu(text="&View")
        class ViewMenu(Menu):
            word_wrap: QAction = new("Word Wrap", checkable=True)

        m = qt.track(ViewMenu())
        assert_that(m.word_wrap.isCheckable()).is_true()
        assert_that(m.word_wrap.isChecked()).is_false()

    def test_checkable_action_with_initial_checked(self, qt: QtDriver) -> None:
        """checked=True sets initial checked state."""

        @menu(text="&View")
        class ViewMenu(Menu):
            word_wrap: QAction = new("Word Wrap", checkable=True, checked=True)

        m = qt.track(ViewMenu())
        assert_that(m.word_wrap.isChecked()).is_true()

    def test_toggled_handler_called(self, qt: QtDriver) -> None:
        """toggled="handler" is called when action is toggled."""
        toggled_value = None

        @menu(text="&View")
        class ViewMenu(Menu):
            word_wrap: QAction = new("Word Wrap", checkable=True, toggled="on_toggle")

            def on_toggle(self, checked: bool) -> None:
                nonlocal toggled_value
                toggled_value = checked

        m = qt.track(ViewMenu())
        m.word_wrap.setChecked(True)

        assert_that(toggled_value).is_true()

    def test_checked_two_way_binding(self, qt: QtDriver) -> None:
        """checked="_variable" creates two-way binding."""

        @menu(text="&View")
        class ViewMenu(Menu):
            _word_wrap: Variable[bool] = new(False)
            word_wrap: QAction = new("Word Wrap", checkable=True, checked="_word_wrap")

        m = qt.track(ViewMenu())
        assert_that(m.word_wrap.isChecked()).is_false()

        # Variable changes -> action updates
        m._word_wrap.value = True
        assert_that(m.word_wrap.isChecked()).is_true()

        # Action changes -> variable updates
        m.word_wrap.setChecked(False)
        assert_that(m._word_wrap.value).is_false()


# =============================================================================
# C.9: Window Integration
# =============================================================================


class TestWindowIntegration:
    """Test Menu integration with Window."""

    def test_menu_added_to_window_menubar(self, qt: QtDriver) -> None:
        """Menu subclass is auto-added to Window's menu bar."""
        from qtpie import Window, window

        @menu(text="&File")
        class FileMenu(Menu):
            new_action: QAction = new("&New")

        @window(title="Test App")
        class App(Window):
            file_menu: FileMenu = new()

        app = qt.track(App())
        menubar = app.menuBar()
        assert_that(len(menubar.actions())).is_equal_to(1)
        assert_that(menubar.actions()[0].text()).is_equal_to("&File")

    def test_multiple_menus_in_order(self, qt: QtDriver) -> None:
        """Multiple menus are added in declaration order."""
        from qtpie import Window, window

        @menu(text="&File")
        class FileMenu(Menu):
            pass

        @menu(text="&Edit")
        class EditMenu(Menu):
            pass

        @menu(text="&Help")
        class HelpMenu(Menu):
            pass

        @window(title="Test App")
        class App(Window):
            file_menu: FileMenu = new()
            edit_menu: EditMenu = new()
            help_menu: HelpMenu = new()

        app = qt.track(App())
        menubar = app.menuBar()
        actions = menubar.actions()

        assert_that(len(actions)).is_equal_to(3)
        assert_that(actions[0].text()).is_equal_to("&File")
        assert_that(actions[1].text()).is_equal_to("&Edit")
        assert_that(actions[2].text()).is_equal_to("&Help")

    def test_menu_receives_variable_binding_from_window(self, qt: QtDriver) -> None:
        """Menu can receive Variable bindings from parent Window."""
        from qtpie import Window, window

        @menu(text="&File")
        class FileMenu(Menu):
            is_dirty: Variable[bool]  # Required binding
            save: QAction = new("&Save", enabled="{is_dirty}")

        @window(title="Test App")
        class App(Window):
            _is_dirty: Variable[bool] = new(False)
            file_menu: FileMenu = new(is_dirty="_is_dirty")

        app = qt.track(App())

        # Initially disabled
        assert_that(app.file_menu.is_dirty.value).is_false()

        # Window changes -> menu updates
        app._is_dirty.value = True
        assert_that(app.file_menu.is_dirty.value).is_true()


# =============================================================================
# Menu Order
# =============================================================================


class TestMenuItemOrder:
    """Test that menu items are added in declaration order."""

    def test_items_in_order(self, qt: QtDriver) -> None:
        """Items added in declaration order."""

        @menu(text="&File")
        class FileMenu(Menu):
            new_action: QAction = new("&New")
            open_action: QAction = new("&Open")
            ____: Separator
            ___recent___: Section
            recent1: QAction = new("Recent 1")
            recent2: QAction = new("Recent 2")
            _____: Separator
            exit_action: QAction = new("E&xit")

        m = qt.track(FileMenu())
        actions = m.actions()

        assert_that(len(actions)).is_equal_to(8)
        assert_that(actions[0].text()).is_equal_to("&New")
        assert_that(actions[1].text()).is_equal_to("&Open")
        assert_that(actions[2].isSeparator()).is_true()
        assert_that(actions[3].text()).is_equal_to("Recent")
        assert_that(actions[4].text()).is_equal_to("Recent 1")
        assert_that(actions[5].text()).is_equal_to("Recent 2")
        assert_that(actions[6].isSeparator()).is_true()
        assert_that(actions[7].text()).is_equal_to("E&xit")


# =============================================================================
# C.6: ActionRepeater (Dynamic Action Lists)
# =============================================================================


class TestActionRepeater:
    """Test dynamic action lists bound to Variables."""

    def test_dynamic_action_list(self, qt: QtDriver) -> None:
        """list[QAction] = new(bind=...) creates dynamic actions."""

        @menu(text="&Window")
        class WindowMenu(Menu):
            _windows: Variable[list[str]] = new(["Win1", "Win2"])
            window_actions: list[QAction] = new(bind="_windows")

        m = qt.track(WindowMenu())
        actions = m.actions()

        assert_that(len(actions)).is_equal_to(2)
        assert_that(actions[0].text()).is_equal_to("Win1")
        assert_that(actions[1].text()).is_equal_to("Win2")

    def test_dynamic_action_list_with_format(self, qt: QtDriver) -> None:
        """list[QAction] with format= customizes action text."""

        @menu(text="&Window")
        class WindowMenu(Menu):
            _windows: Variable[list[str]] = new(["Main", "Settings"])
            window_actions: list[QAction] = new(bind="_windows", format="Open {#self}")

        m = qt.track(WindowMenu())
        actions = m.actions()

        assert_that(actions[0].text()).is_equal_to("Open Main")
        assert_that(actions[1].text()).is_equal_to("Open Settings")

    def test_dynamic_action_list_appends(self, qt: QtDriver) -> None:
        """Appending to Variable adds new action."""

        @menu(text="&Window")
        class WindowMenu(Menu):
            _windows: Variable[list[str]] = new(["Win1"])
            window_actions: list[QAction] = new(bind="_windows")

        m = qt.track(WindowMenu())
        assert_that(len(m.actions())).is_equal_to(1)

        m._windows.append("Win2")
        assert_that(len(m.actions())).is_equal_to(2)
        assert_that(m.actions()[1].text()).is_equal_to("Win2")

    def test_dynamic_action_list_removes(self, qt: QtDriver) -> None:
        """Removing from Variable removes action."""

        @menu(text="&Window")
        class WindowMenu(Menu):
            _windows: Variable[list[str]] = new(["Win1", "Win2", "Win3"])
            window_actions: list[QAction] = new(bind="_windows")

        m = qt.track(WindowMenu())
        assert_that(len(m.actions())).is_equal_to(3)

        m._windows.remove("Win2")
        assert_that(len(m.actions())).is_equal_to(2)
        assert_that(m.actions()[0].text()).is_equal_to("Win1")
        assert_that(m.actions()[1].text()).is_equal_to("Win3")

    def test_dynamic_action_list_with_triggered_handler(self, qt: QtDriver) -> None:
        """triggered= handler receives the item."""
        selected_item = None

        @menu(text="&Window")
        class WindowMenu(Menu):
            _windows: Variable[list[str]] = new(["Win1", "Win2"])
            window_actions: list[QAction] = new(
                bind="_windows",
                triggered="on_window_select",
            )

            def on_window_select(self, item: str) -> None:
                nonlocal selected_item
                selected_item = item

        m = qt.track(WindowMenu())
        m.actions()[1].trigger()

        assert_that(selected_item).is_equal_to("Win2")

    def test_dynamic_action_list_with_static_actions(self, qt: QtDriver) -> None:
        """Dynamic actions work alongside static actions."""

        @menu(text="&Window")
        class WindowMenu(Menu):
            tile: QAction = new("Tile")
            cascade: QAction = new("Cascade")
            ____: Separator
            _windows: Variable[list[str]] = new(["Win1", "Win2"])
            window_actions: list[QAction] = new(bind="_windows")
            _____: Separator
            close_all: QAction = new("Close All")

        m = qt.track(WindowMenu())
        actions = m.actions()

        assert_that(len(actions)).is_equal_to(7)
        assert_that(actions[0].text()).is_equal_to("Tile")
        assert_that(actions[1].text()).is_equal_to("Cascade")
        assert_that(actions[2].isSeparator()).is_true()
        assert_that(actions[3].text()).is_equal_to("Win1")
        assert_that(actions[4].text()).is_equal_to("Win2")
        assert_that(actions[5].isSeparator()).is_true()
        assert_that(actions[6].text()).is_equal_to("Close All")

    def test_dynamic_action_list_with_index(self, qt: QtDriver) -> None:
        """Format with #index placeholder."""

        @menu(text="&Window")
        class WindowMenu(Menu):
            _windows: Variable[list[str]] = new(["A", "B", "C"])
            window_actions: list[QAction] = new(bind="_windows", format="{#index}: {#self}")

        m = qt.track(WindowMenu())
        actions = m.actions()

        assert_that(actions[0].text()).is_equal_to("0: A")
        assert_that(actions[1].text()).is_equal_to("1: B")
        assert_that(actions[2].text()).is_equal_to("2: C")


# =============================================================================
# C.8: Menu[T] Record Support
# =============================================================================


class TestMenuRecordSupport:
    """Test Menu[T] record type support."""

    def test_menu_with_record_type(self, qt: QtDriver) -> None:
        """Menu[T] has a record property."""
        from dataclasses import dataclass

        @dataclass
        class EditState:
            can_undo: bool = False

        @menu(text="&Edit")
        class EditMenu(Menu[EditState]):
            pass

        m = qt.track(EditMenu())
        assert hasattr(m, "record")
        assert m.record.can_undo is False

    def test_menu_record_from_decorator(self, qt: QtDriver) -> None:
        """record= in decorator sets initial record value."""
        from dataclasses import dataclass

        @dataclass
        class EditState:
            can_undo: bool = False
            can_redo: bool = False

        @menu(text="&Edit", record=EditState(can_undo=True))
        class EditMenu(Menu[EditState]):
            pass

        m = qt.track(EditMenu())
        assert_that(m.record.can_undo).is_true()
        assert_that(m.record.can_redo).is_false()

    def test_menu_record_reactive_binding(self, qt: QtDriver) -> None:
        """Action enabled bound to record field."""
        from dataclasses import dataclass

        @dataclass
        class EditState:
            can_undo: bool = False

        @menu(text="&Edit", record=EditState())
        class EditMenu(Menu[EditState]):
            undo: QAction = new("Undo", enabled="{record.can_undo}")

        m = qt.track(EditMenu())
        assert_that(m.undo.isEnabled()).is_false()

        m.record.can_undo = True
        assert_that(m.undo.isEnabled()).is_true()

    def test_menu_record_set_in_setup(self, qt: QtDriver) -> None:
        """Record can be set in __setup__."""
        from dataclasses import dataclass

        @dataclass
        class EditState:
            can_undo: bool = False

        @menu(text="&Edit")
        class EditMenu(Menu[EditState]):
            def __setup__(self) -> None:  # pyright: ignore[reportImplicitOverride]
                self.record = EditState(can_undo=True)

        m = qt.track(EditMenu())
        assert_that(m.record.can_undo).is_true()


class TestParentPlaceholder:
    """Tests for #parent placeholder - escape hatch for accessing parent variables."""

    def test_parent_placeholder_enabled_binding(self, qt: QtDriver) -> None:
        """Action enabled can bind to parent window variable."""

        @menu(text="&File")
        class FileMenu(Menu):
            save: QAction = new("Save", enabled="{#parent._is_dirty}")

        @window(title="App")
        class App(Window):
            _is_dirty: Variable[bool] = new(False)
            file_menu: FileMenu = new()

        app = qt.track(App())

        # Initially not enabled
        assert_that(app.file_menu.save.isEnabled()).is_false()

        # Parent changes -> menu action updates
        app._is_dirty.value = True
        assert_that(app.file_menu.save.isEnabled()).is_true()

    def test_parent_placeholder_reactive(self, qt: QtDriver) -> None:
        """Parent placeholder updates when parent variable changes."""

        @menu(text="&Edit")
        class EditMenu(Menu):
            undo: QAction = new("Undo", enabled="{#parent._can_undo}")
            redo: QAction = new("Redo", enabled="{#parent._can_redo}")

        @window(title="Editor")
        class EditorWindow(Window):
            _can_undo: Variable[bool] = new(False)
            _can_redo: Variable[bool] = new(False)
            edit_menu: EditMenu = new()

        editor = qt.track(EditorWindow())

        assert_that(editor.edit_menu.undo.isEnabled()).is_false()
        assert_that(editor.edit_menu.redo.isEnabled()).is_false()

        editor._can_undo.value = True
        assert_that(editor.edit_menu.undo.isEnabled()).is_true()
        assert_that(editor.edit_menu.redo.isEnabled()).is_false()

        editor._can_redo.value = True
        assert_that(editor.edit_menu.redo.isEnabled()).is_true()
