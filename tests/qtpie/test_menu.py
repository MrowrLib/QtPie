# pyright: reportPrivateUsage=false
# pyright: reportMissingTypeArgument=false
# pyright: reportUnknownMemberType=false
# pyright: reportUnknownArgumentType=false
# pyright: reportUnknownLambdaType=false
"""Tests for the Menu system (@menu decorator)."""

from typing import override

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
            doc_dirty: Variable[bool]  # Required binding
            save: QAction = new("&Save", enabled="{doc_dirty}")

        @window(title="Test App")
        class App(Window):
            _doc_dirty: Variable[bool] = new(False)
            file_menu: FileMenu = new(doc_dirty="_doc_dirty")

        app = qt.track(App())

        # Initially disabled
        assert_that(app.file_menu.doc_dirty.value).is_false()

        # Window changes -> menu updates
        app._doc_dirty.value = True
        assert_that(app.file_menu.doc_dirty.value).is_true()


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


# =============================================================================
# Menu Dirty Tracking
# =============================================================================


class TestMenuDirtyTracking:
    """Test Menu dirty tracking (is_dirty, reset_dirty, dirty_fields)."""

    def test_initially_not_dirty(self, qt: QtDriver) -> None:
        """New menu is not dirty."""

        @menu(text="&File")
        class FileMenu(Menu):
            _count: Variable[int] = new(0)
            action: QAction = new("Action")

        m = qt.track(FileMenu())
        assert_that(m.is_dirty.get()).is_false()

    def test_dirty_after_variable_change(self, qt: QtDriver) -> None:
        """Menu becomes dirty after Variable change."""

        @menu(text="&File")
        class FileMenu(Menu):
            _count: Variable[int] = new(0)
            action: QAction = new("Action")

        m = qt.track(FileMenu())
        m._count.value = 42
        assert_that(m.is_dirty.get()).is_true()

    def test_dirty_fields_tracks_which_changed(self, qt: QtDriver) -> None:
        """dirty_fields returns only the changed fields."""

        @menu(text="&File")
        class FileMenu(Menu):
            _name: Variable[str] = new("")
            _count: Variable[int] = new(0)
            action: QAction = new("Action")

        m = qt.track(FileMenu())
        m._name.value = "changed"

        assert_that(m.dirty_fields).is_equal_to({"_name"})

    def test_dirty_fields_multiple(self, qt: QtDriver) -> None:
        """dirty_fields returns all changed fields."""

        @menu(text="&File")
        class FileMenu(Menu):
            _name: Variable[str] = new("")
            _count: Variable[int] = new(0)
            action: QAction = new("Action")

        m = qt.track(FileMenu())
        m._name.value = "changed"
        m._count.value = 42

        assert_that(m.dirty_fields).is_equal_to({"_name", "_count"})

    def test_reset_dirty_clears_all(self, qt: QtDriver) -> None:
        """reset_dirty() marks all Variables as clean."""

        @menu(text="&File")
        class FileMenu(Menu):
            _name: Variable[str] = new("")
            _count: Variable[int] = new(0)
            action: QAction = new("Action")

        m = qt.track(FileMenu())
        m._name.value = "changed"
        m._count.value = 42
        assert_that(m.is_dirty.get()).is_true()

        m.reset_dirty()
        assert_that(m.is_dirty.get()).is_false()
        assert_that(m.dirty_fields).is_equal_to(set())

    def test_dirty_after_reset_and_change(self, qt: QtDriver) -> None:
        """After reset, changing a value makes it dirty again."""

        @menu(text="&File")
        class FileMenu(Menu):
            _name: Variable[str] = new("")
            action: QAction = new("Action")

        m = qt.track(FileMenu())
        m._name.value = "first"
        m.reset_dirty()

        m._name.value = "second"
        assert_that(m.is_dirty.get()).is_true()

    def test_is_dirty_is_observable(self, qt: QtDriver) -> None:
        """is_dirty is Observable[bool] for reactive bindings."""
        from observant import Observable

        @menu(text="&File")
        class FileMenu(Menu):
            _count: Variable[int] = new(0)
            action: QAction = new("Action")

        m = qt.track(FileMenu())
        assert_that(m.is_dirty).is_instance_of(Observable)


# =============================================================================
# Menu Validation
# =============================================================================


class TestMenuValidation:
    """Test Menu validation (is_valid, validation_errors, add_validator)."""

    def test_add_validator_to_field(self, qt: QtDriver) -> None:
        """Menu.add_validator adds validator to field."""

        @menu(text="&File")
        class FileMenu(Menu):
            _name: Variable[str] = new("")
            action: QAction = new("Action")

            def __setup__(self) -> None:
                self.add_validator("_name", "required", lambda v: None if v else "Required")

        m = qt.track(FileMenu())
        assert_that(m._name.is_valid.get()).is_false()

    def test_is_valid_aggregates(self, qt: QtDriver) -> None:
        """Menu.is_valid aggregates from all fields."""

        @menu(text="&File")
        class FileMenu(Menu):
            _name: Variable[str] = new("")
            _count: Variable[int] = new(0)
            action: QAction = new("Action")

            def __setup__(self) -> None:
                self.add_validator("_name", "required", lambda v: None if v else "Required")
                self.add_validator("_count", "positive", lambda v: None if v > 0 else "Must be positive")

        m = qt.track(FileMenu())
        assert_that(m.is_valid.get()).is_false()

        m._name.value = "Alice"
        assert_that(m.is_valid.get()).is_false()  # still invalid (count)

        m._count.value = 5
        assert_that(m.is_valid.get()).is_true()

    def test_validation_errors_nested_dict(self, qt: QtDriver) -> None:
        """Menu.validation_errors returns {field: {validator: [errors]}}."""

        @menu(text="&File")
        class FileMenu(Menu):
            _name: Variable[str] = new("")
            action: QAction = new("Action")

            def __setup__(self) -> None:
                self.add_validator("_name", "required", lambda v: None if v else "Required")

        m = qt.track(FileMenu())
        errors = m.validation_errors
        assert_that(errors).contains_key("_name")
        assert_that(errors["_name"]).contains_key("required")
        assert_that(errors["_name"]["required"]).is_equal_to(["Required"])

    def test_validation_error_messages_flat_list(self, qt: QtDriver) -> None:
        """Menu.validation_error_messages returns flat list of messages."""

        @menu(text="&File")
        class FileMenu(Menu):
            _name: Variable[str] = new("")
            action: QAction = new("Action")

            def __setup__(self) -> None:
                self.add_validator("_name", "required", lambda v: None if v else "Required")
                self.add_validator("_name", "min_len", lambda v: None if len(v) >= 3 else "Too short")

        m = qt.track(FileMenu())
        msgs = m.validation_error_messages.get()
        assert_that(msgs).contains("Required", "Too short")

    def test_is_valid_is_observable(self, qt: QtDriver) -> None:
        """is_valid is Observable[bool] for reactive bindings."""
        from observant import Observable

        @menu(text="&File")
        class FileMenu(Menu):
            _count: Variable[int] = new(0)
            action: QAction = new("Action")

        m = qt.track(FileMenu())
        assert_that(m.is_valid).is_instance_of(Observable)

    def test_validation_error_messages_is_observable(self, qt: QtDriver) -> None:
        """validation_error_messages is Observable[list[str]]."""
        from observant import Observable

        @menu(text="&File")
        class FileMenu(Menu):
            _count: Variable[int] = new(0)
            action: QAction = new("Action")

        m = qt.track(FileMenu())
        assert_that(m.validation_error_messages).is_instance_of(Observable)


# =============================================================================
# Menu Lifecycle Hooks
# =============================================================================


class TestMenuLifecycleHooks:
    """Test Menu lifecycle hooks (on_dirty_changed, on_valid_changed)."""

    def test_on_dirty_changed_fires_on_transition(self, qt: QtDriver) -> None:
        """on_dirty_changed fires when dirty state transitions."""
        dirty_states: list[bool] = []

        @menu(text="&File")
        class FileMenu(Menu):
            _name: Variable[str] = new("")
            action: QAction = new("Action")

            @override
            def on_dirty_changed(self, is_dirty: bool) -> None:
                dirty_states.append(is_dirty)

        m = qt.track(FileMenu())
        m._name.value = "changed"

        assert_that(dirty_states).contains(True)

    def test_on_dirty_changed_fires_on_reset(self, qt: QtDriver) -> None:
        """on_dirty_changed fires when reset to clean."""
        dirty_states: list[bool] = []

        @menu(text="&File")
        class FileMenu(Menu):
            _name: Variable[str] = new("")
            action: QAction = new("Action")

            @override
            def on_dirty_changed(self, is_dirty: bool) -> None:
                dirty_states.append(is_dirty)

        m = qt.track(FileMenu())
        m._name.value = "changed"
        m.reset_dirty()

        assert_that(dirty_states).is_equal_to([True, False])

    def test_on_valid_changed_fires_on_transition(self, qt: QtDriver) -> None:
        """on_valid_changed fires when validity state transitions."""
        valid_states: list[bool] = []

        @menu(text="&File")
        class FileMenu(Menu):
            _name: Variable[str] = new("")
            action: QAction = new("Action")

            def __setup__(self) -> None:
                self.add_validator("_name", "required", lambda v: None if v else "Required")

            @override
            def on_valid_changed(self, is_valid: bool) -> None:
                valid_states.append(is_valid)

        m = qt.track(FileMenu())
        # Initially invalid, but hook only fires on transitions after setup
        m._name.value = "valid"  # invalid -> valid

        assert_that(valid_states).contains(True)

    def test_on_valid_changed_fires_both_directions(self, qt: QtDriver) -> None:
        """on_valid_changed fires when going valid->invalid and invalid->valid."""
        valid_states: list[bool] = []

        @menu(text="&File")
        class FileMenu(Menu):
            _name: Variable[str] = new("initial")
            action: QAction = new("Action")

            def __setup__(self) -> None:
                self.add_validator("_name", "required", lambda v: None if v else "Required")

            @override
            def on_valid_changed(self, is_valid: bool) -> None:
                valid_states.append(is_valid)

        m = qt.track(FileMenu())
        # Starts valid
        m._name.value = ""  # valid -> invalid
        m._name.value = "valid again"  # invalid -> valid

        assert_that(valid_states).is_equal_to([False, True])


class TestMenuRefWithRequiredBinding:
    """Test ref() with required bindings in Menu."""

    def test_ref_with_literal_text_and_required_binding(self, qt: QtDriver) -> None:
        """ref() with literal text + expression works with required bindings."""
        from dataclasses import dataclass

        from qtpie import ref

        @dataclass
        class Dog:
            name: str = ""
            age: int = 0

        @menu(text="&Dog")
        class DogMenu(Menu):
            dog: Variable[Dog]
            dog_action: QAction = new(text=ref("Dog name: {dog.name}"))

        @window(title="Test", record=Dog("Buddy", 4))
        class MainWindow(Window[Dog]):
            dog_menu: DogMenu = new(dog="record")

        w = qt.track(MainWindow())
        # The ref should resolve with literal text preserved
        assert_that(w.dog_menu.dog_action.text()).is_equal_to("Dog name: Buddy")


# =============================================================================
# Menu Signal-to-Signal Connections
# =============================================================================


class TestMenuSignalToSignal:
    """Test signal-to-signal connections in Menu (like Widget has)."""

    def test_triggered_emits_signal(self, qt: QtDriver) -> None:
        """Action triggered emits a custom signal when handler is signal name."""
        from qtpy.QtCore import Signal

        signal_emitted = False

        @menu(text="&File")
        class FileMenu(Menu):
            file_requested = Signal()
            new_action: QAction = new("&New", triggered="file_requested")

        m = qt.track(FileMenu())

        def on_signal() -> None:
            nonlocal signal_emitted
            signal_emitted = True

        m.file_requested.connect(on_signal)
        m.new_action.trigger()

        assert_that(signal_emitted).is_true()

    def test_method_handler_still_works_in_menu(self, qt: QtDriver) -> None:
        """Existing method handler behavior is unchanged in Menu."""
        method_called = False

        @menu(text="&File")
        class FileMenu(Menu):
            new_action: QAction = new("&New", triggered="on_new")

            def on_new(self) -> None:
                nonlocal method_called
                method_called = True

        m = qt.track(FileMenu())
        m.new_action.trigger()

        assert_that(method_called).is_true()

    def test_lambda_handler_still_works_in_menu(self, qt: QtDriver) -> None:
        """Existing lambda handler behavior is unchanged in Menu."""
        lambda_called = False

        def set_called() -> None:
            nonlocal lambda_called
            lambda_called = True

        @menu(text="&File")
        class FileMenu(Menu):
            new_action: QAction = new("&New", triggered=set_called)

        m = qt.track(FileMenu())
        m.new_action.trigger()

        assert_that(lambda_called).is_true()

    def test_invalid_handler_uses_lazy_resolution_in_menu(self, qt: QtDriver) -> None:
        """Nonexistent handler is deferred until emit (lazy resolution for hierarchy search).

        With lazy hierarchy resolution, nonexistent handlers don't error at init time.
        The menu is created successfully, and the error only occurs at emit time.
        Note: Qt's event loop catches exceptions from signal handlers, so we can't
        easily test the exception with pytest.raises.
        """

        @menu(text="&File")
        class FileMenu(Menu):
            new_action: QAction = new("&New", triggered="nonexistent")

        # Menu is created successfully - error deferred to emit time
        m = qt.track(FileMenu())
        assert m.new_action is not None

    def test_non_callable_non_signal_raises_in_menu(self, qt: QtDriver) -> None:
        """Handler pointing to non-callable, non-signal attribute raises at init.

        Note: If the handler name exists on the menu (but isn't callable/signal),
        the error is raised at init. Only nonexistent handlers use lazy resolution.
        """
        import pytest

        @menu(text="&File")
        class FileMenu(Menu):
            some_value: int = 42
            new_action: QAction = new("&New", triggered="some_value")

        with pytest.raises(AttributeError, match="not callable or a Signal"):
            qt.track(FileMenu())

    def test_toggled_emits_signal(self, qt: QtDriver) -> None:
        """Checkable action toggled emits custom signal when handler is signal name."""
        from qtpy.QtCore import Signal

        received_value: bool | None = None

        @menu(text="&View")
        class ViewMenu(Menu):
            toggle_changed = Signal(bool)
            word_wrap: QAction = new("Word Wrap", checkable=True, toggled="toggle_changed")

        m = qt.track(ViewMenu())

        def on_toggle(val: bool) -> None:
            nonlocal received_value
            received_value = val

        m.toggle_changed.connect(on_toggle)
        m.word_wrap.setChecked(True)

        assert_that(received_value).is_true()

    def test_menu_in_window_signal_to_parent(self, qt: QtDriver) -> None:
        """Menu action can emit signal that parent window handles."""
        from qtpy.QtCore import Signal

        parent_received = False

        @menu(text="&File")
        class FileMenu(Menu):
            file_requested = Signal()
            new_action: QAction = new("&New", triggered="file_requested")

        @window(title="App")
        class App(Window):
            file_menu: FileMenu = new(file_requested="_on_file")

            def _on_file(self) -> None:
                nonlocal parent_received
                parent_received = True

        app = qt.track(App())
        app.file_menu.new_action.trigger()

        assert_that(parent_received).is_true()


class TestMenuSignalExpressions:
    """Test expression-based signal handlers in Menu (e.g., triggered="{custom_signal(123)}")."""

    def test_triggered_expression_calls_method(self, qt: QtDriver) -> None:
        """Expression like {on_action()} calls the method."""
        method_called = False

        @menu(text="&File")
        class FileMenu(Menu):
            action: QAction = new("Action", triggered="{on_action()}")

            def on_action(self) -> None:
                nonlocal method_called
                method_called = True

        m = qt.track(FileMenu())
        m.action.trigger()

        assert_that(method_called).is_true()

    def test_triggered_expression_emits_signal_with_literal(self, qt: QtDriver) -> None:
        """Expression like {custom_signal(123)} emits signal with literal value."""
        from qtpy.QtCore import Signal

        received_value: int | None = None

        @menu(text="&File")
        class FileMenu(Menu):
            custom_signal = Signal(int)
            # Signals can be called directly (auto-emits)
            action: QAction = new("Action", triggered="{custom_signal(123)}")

        m = qt.track(FileMenu())

        def on_signal(val: int) -> None:
            nonlocal received_value
            received_value = val

        m.custom_signal.connect(on_signal)
        m.action.trigger()

        assert_that(received_value).is_equal_to(123)

    def test_triggered_expression_uses_variable_value(self, qt: QtDriver) -> None:
        """Expression can reference Variable values."""
        from qtpy.QtCore import Signal

        received_values: list[int] = []

        @menu(text="&File")
        class FileMenu(Menu):
            custom_signal = Signal(int, int)
            _some_number: Variable[int] = new(42)
            simple_number: int = 99
            # Signals can be called directly with Variable values
            action: QAction = new("Action", triggered="{custom_signal(some_number, simple_number)}")

        m = qt.track(FileMenu())

        def on_signal(a: int, b: int) -> None:
            received_values.extend([a, b])

        m.custom_signal.connect(on_signal)
        m.action.trigger()

        assert_that(received_values).is_equal_to([42, 99])

    def test_triggered_expression_with_args_placeholder(self, qt: QtDriver) -> None:
        """Expression with #args passes signal arguments."""
        received_checked: bool | None = None

        @menu(text="&View")
        class ViewMenu(Menu):
            action: QAction = new("Toggle", checkable=True, toggled="{on_toggled(#args)}")

            def on_toggled(self, checked: bool) -> None:
                nonlocal received_checked
                received_checked = checked

        m = qt.track(ViewMenu())
        m.action.setChecked(True)

        assert_that(received_checked).is_true()

    def test_triggered_expression_full_example(self, qt: QtDriver) -> None:
        """Full example from user: triggered with Variable and literal values."""
        from dataclasses import dataclass

        from qtpy.QtCore import Signal

        from qtpie import ref

        received_values: list[int] = []

        @dataclass
        class Dog:
            name: str = ""
            age: int = 0

        @menu(text="&File")
        class FileMenu(Menu):
            custom_signal = Signal(int, int)

            dog: Variable[Dog]

            _some_number: Variable[int] = new(123)
            simple_number: int = 42

            # Signals can be called directly (auto-emits)
            print_dog_action: QAction = new(
                text=ref("Dog name: {dog.name}"),
                triggered="{custom_signal(some_number, simple_number)}",
            )

            def on_custom(self, a: int, b: int) -> None:
                received_values.extend([a, b])

        # Create a window that provides the dog binding
        @window(title="Test", record=Dog("Buddy", 4))
        class MainWindow(Window[Dog]):
            file_menu: FileMenu = new(dog="record")

        w = qt.track(MainWindow())

        # Connect to the signal
        w.file_menu.custom_signal.connect(lambda a, b: received_values.extend([a, b]))

        # Trigger the action
        w.file_menu.print_dog_action.trigger()

        assert_that(received_values).is_equal_to([123, 42])
        assert_that(w.file_menu.print_dog_action.text()).is_equal_to("Dog name: Buddy")
