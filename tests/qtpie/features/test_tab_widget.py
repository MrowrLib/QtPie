# pyright: reportPrivateUsage=false
# pyright: reportMissingParameterType=false
# pyright: reportUnknownParameterType=false
# pyright: reportUntypedBaseClass=false
# pyright: reportUntypedClassDecorator=false
# pyright: reportUnknownArgumentType=false
# pyright: reportUnknownMemberType=false
# pyright: reportOptionalMemberAccess=false
# pyright: reportAttributeAccessIssue=false
# pyright: reportCallIssue=false
# pyright: reportIndexIssue=false
# pyright: reportArgumentType=false
"""Tests for QTabWidget declarative support.

Tests tabs= with dict and list, and selectedIndex=/selectedWidget= bindings.

Syntax:
    tabs={"Tab1": WidgetClass1, "Tab2": WidgetClass2}  # Dict - explicit tab names
    tabs=[WidgetClass1, WidgetClass2]  # List - names from windowTitle() or class name
    tabs="_tab_defs"  # Variable reference for reactive tabs
    selectedIndex="_selected"  # Two-way binding for current tab index
    selectedWidget="_widget"  # Binding for current tab widget reference
"""

import pytest
from assertpy import assert_that
from PySide6.QtWidgets import QLabel, QTabWidget

from qtpie import Variable, Widget, new, widget
from qtpie.testing import QtDriver

from .conftest import WIDGET_CLASS_TYPES, create_and_track


@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestTabWidgetStaticDict:
    """Static tabs= with literal dict."""

    def test_tabs_from_dict_hello_world(self, base_class, decorator, qt: QtDriver) -> None:
        """QTabWidget with tabs=dict creates tabs (hello world with QLabel)."""

        @decorator
        class TestClass(base_class):
            _tabs: QTabWidget = new(tabs={"Tab A": QLabel, "Tab B": QLabel})

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance._tabs.count()).is_equal_to(2)
        assert_that(instance._tabs.tabText(0)).is_equal_to("Tab A")
        assert_that(instance._tabs.tabText(1)).is_equal_to("Tab B")

    def test_tabs_from_dict_with_widget_classes(self, base_class, decorator, qt: QtDriver) -> None:
        """QTabWidget with tabs=dict using custom Widget classes."""

        @widget
        class SettingsTab(Widget):
            _label: QLabel = new("Settings content")

        @widget
        class ProfileTab(Widget):
            _label: QLabel = new("Profile content")

        @decorator
        class TestClass(base_class):
            _tabs: QTabWidget = new(
                tabs={
                    "Settings": SettingsTab,
                    "Profile": ProfileTab,
                }
            )

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance._tabs.count()).is_equal_to(2)
        assert_that(instance._tabs.tabText(0)).is_equal_to("Settings")
        assert_that(instance._tabs.tabText(1)).is_equal_to("Profile")
        # Verify tab content is actual widget instance
        assert_that(instance._tabs.widget(0)).is_instance_of(SettingsTab)
        assert_that(instance._tabs.widget(1)).is_instance_of(ProfileTab)

    def test_tabs_dict_widget_content_accessible(self, base_class, decorator, qt: QtDriver) -> None:
        """Tab widgets are properly instantiated with their content."""

        @widget
        class ContentTab(Widget):
            _content: QLabel = new("Hello from tab!")

        @decorator
        class TestClass(base_class):
            _tabs: QTabWidget = new(tabs={"Content": ContentTab})

        instance = create_and_track(qt, TestClass, base_class)
        tab = instance._tabs.widget(0)
        assert_that(tab._content.text()).is_equal_to("Hello from tab!")


@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestTabWidgetStaticList:
    """Static tabs= with literal list."""

    def test_tabs_from_list_uses_window_title(self, base_class, decorator, qt: QtDriver) -> None:
        """QTabWidget with tabs=list uses @widget(title=) for tab names."""

        @widget(title="Settings")
        class SettingsTab(Widget):
            _label: QLabel = new("Settings")

        @widget(title="Profile")
        class ProfileTab(Widget):
            _label: QLabel = new("Profile")

        @decorator
        class TestClass(base_class):
            _tabs: QTabWidget = new(tabs=[SettingsTab, ProfileTab])

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance._tabs.count()).is_equal_to(2)
        assert_that(instance._tabs.tabText(0)).is_equal_to("Settings")
        assert_that(instance._tabs.tabText(1)).is_equal_to("Profile")

    def test_tabs_from_list_fallback_to_class_name(self, base_class, decorator, qt: QtDriver) -> None:
        """QTabWidget with tabs=list falls back to class name if no title."""

        @widget
        class MyCustomTab(Widget):
            _label: QLabel = new("Content")

        @widget
        class AnotherTab(Widget):
            _label: QLabel = new("More content")

        @decorator
        class TestClass(base_class):
            _tabs: QTabWidget = new(tabs=[MyCustomTab, AnotherTab])

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance._tabs.tabText(0)).is_equal_to("MyCustomTab")
        assert_that(instance._tabs.tabText(1)).is_equal_to("AnotherTab")

    def test_tabs_list_mixed_titled_and_untitled(self, base_class, decorator, qt: QtDriver) -> None:
        """Mix of tabs with and without explicit titles."""

        @widget(title="Has Title")
        class TitledTab(Widget):
            _label: QLabel = new("Titled")

        @widget
        class UntitledTab(Widget):
            _label: QLabel = new("Untitled")

        @decorator
        class TestClass(base_class):
            _tabs: QTabWidget = new(tabs=[TitledTab, UntitledTab])

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance._tabs.tabText(0)).is_equal_to("Has Title")
        assert_that(instance._tabs.tabText(1)).is_equal_to("UntitledTab")


@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestTabWidgetSelectedIndex:
    """selectedIndex= two-way binding tests."""

    def test_selected_index_initial_value(self, base_class, decorator, qt: QtDriver) -> None:
        """selectedIndex= sets initial tab from Variable value."""

        @widget(title="Tab A")
        class TabA(Widget):
            _label: QLabel = new("A")

        @widget(title="Tab B")
        class TabB(Widget):
            _label: QLabel = new("B")

        @decorator
        class TestClass(base_class):
            _selected: Variable[int] = new(1)  # Start on second tab
            _tabs: QTabWidget = new(
                tabs=[TabA, TabB],
                selectedIndex="_selected",
            )

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance._tabs.currentIndex()).is_equal_to(1)

    def test_selected_index_variable_to_tab(self, base_class, decorator, qt: QtDriver) -> None:
        """Changing Variable updates tab selection."""

        @widget(title="Tab A")
        class TabA(Widget):
            _label: QLabel = new("A")

        @widget(title="Tab B")
        class TabB(Widget):
            _label: QLabel = new("B")

        @decorator
        class TestClass(base_class):
            _selected: Variable[int] = new(0)
            _tabs: QTabWidget = new(
                tabs=[TabA, TabB],
                selectedIndex="_selected",
            )

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance._tabs.currentIndex()).is_equal_to(0)

        # Change Variable -> Tab should update
        instance._selected.value = 1
        assert_that(instance._tabs.currentIndex()).is_equal_to(1)

    def test_selected_index_tab_to_variable(self, base_class, decorator, qt: QtDriver) -> None:
        """Changing tab updates Variable."""

        @widget(title="Tab A")
        class TabA(Widget):
            _label: QLabel = new("A")

        @widget(title="Tab B")
        class TabB(Widget):
            _label: QLabel = new("B")

        @decorator
        class TestClass(base_class):
            _selected: Variable[int] = new(0)
            _tabs: QTabWidget = new(
                tabs=[TabA, TabB],
                selectedIndex="_selected",
            )

        instance = create_and_track(qt, TestClass, base_class)

        # Change Tab -> Variable should update
        instance._tabs.setCurrentIndex(1)
        assert_that(instance._selected.value).is_equal_to(1)

    def test_selected_index_default_syncs_from_widget(self, base_class, decorator, qt: QtDriver) -> None:
        """If Variable has None, it syncs from widget's current index."""

        @widget(title="Tab A")
        class TabA(Widget):
            _label: QLabel = new("A")

        @widget(title="Tab B")
        class TabB(Widget):
            _label: QLabel = new("B")

        @decorator
        class TestClass(base_class):
            _selected: Variable[int] = new(0)  # Default is 0
            _tabs: QTabWidget = new(
                tabs=[TabA, TabB],
                selectedIndex="_selected",
            )

        instance = create_and_track(qt, TestClass, base_class)
        # Variable should sync to widget's initial state (0)
        assert_that(instance._selected.value).is_equal_to(0)


@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestTabWidgetSelectedWidget:
    """selectedWidget= binding tests."""

    def test_selected_widget_tracks_current(self, base_class, decorator, qt: QtDriver) -> None:
        """selectedWidget= tracks the current tab widget reference."""

        @widget(title="Tab A")
        class TabA(Widget):
            _label: QLabel = new("A")

        @widget(title="Tab B")
        class TabB(Widget):
            _label: QLabel = new("B")

        @decorator
        class TestClass(base_class):
            _current_widget: Variable[object] = new(object())
            _tabs: QTabWidget = new(
                tabs=[TabA, TabB],
                selectedWidget="_current_widget",
            )

        instance = create_and_track(qt, TestClass, base_class)

        # Initial state - should be first tab widget
        assert_that(instance._current_widget.value).is_instance_of(TabA)

        # Change tab -> widget reference should update
        instance._tabs.setCurrentIndex(1)
        assert_that(instance._current_widget.value).is_instance_of(TabB)

    def test_selected_widget_and_index_together(self, base_class, decorator, qt: QtDriver) -> None:
        """selectedWidget= and selectedIndex= work together."""

        @widget(title="Tab A")
        class TabA(Widget):
            _label: QLabel = new("A")

        @widget(title="Tab B")
        class TabB(Widget):
            _label: QLabel = new("B")

        @decorator
        class TestClass(base_class):
            _selected_idx: Variable[int] = new(0)
            _selected_widget: Variable[object] = new(object())
            _tabs: QTabWidget = new(
                tabs=[TabA, TabB],
                selectedIndex="_selected_idx",
                selectedWidget="_selected_widget",
            )

        instance = create_and_track(qt, TestClass, base_class)

        # Both should be in sync
        assert_that(instance._selected_idx.value).is_equal_to(0)
        assert_that(instance._selected_widget.value).is_instance_of(TabA)

        # Change via Variable
        instance._selected_idx.value = 1
        assert_that(instance._selected_widget.value).is_instance_of(TabB)

        # Change via widget
        instance._tabs.setCurrentIndex(0)
        assert_that(instance._selected_idx.value).is_equal_to(0)
        assert_that(instance._selected_widget.value).is_instance_of(TabA)


@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestTabWidgetReactiveDict:
    """Reactive tabs= with Variable[dict] reference."""

    def test_tabs_update_on_dict_insert(self, base_class, decorator, qt: QtDriver) -> None:
        """Tabs update when items are added to Variable[dict]."""

        @widget(title="Settings")
        class SettingsTab(Widget):
            _label: QLabel = new("Settings")

        @widget(title="Profile")
        class ProfileTab(Widget):
            _label: QLabel = new("Profile")

        @decorator
        class TestClass(base_class):
            _tab_defs: Variable[dict[str, type[Widget]]] = new(
                {
                    "Settings": SettingsTab,
                }
            )
            _tabs: QTabWidget = new(tabs="_tab_defs")

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance._tabs.count()).is_equal_to(1)

        # Add a tab
        instance._tab_defs["Profile"] = ProfileTab
        assert_that(instance._tabs.count()).is_equal_to(2)

    def test_tabs_update_on_dict_remove(self, base_class, decorator, qt: QtDriver) -> None:
        """Tabs update when items are removed from Variable[dict]."""

        @widget(title="Settings")
        class SettingsTab(Widget):
            _label: QLabel = new("Settings")

        @widget(title="Profile")
        class ProfileTab(Widget):
            _label: QLabel = new("Profile")

        @decorator
        class TestClass(base_class):
            _tab_defs: Variable[dict[str, type[Widget]]] = new(
                {
                    "Settings": SettingsTab,
                    "Profile": ProfileTab,
                }
            )
            _tabs: QTabWidget = new(tabs="_tab_defs")

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance._tabs.count()).is_equal_to(2)

        # Remove a tab
        del instance._tab_defs["Settings"]
        assert_that(instance._tabs.count()).is_equal_to(1)
        assert_that(instance._tabs.tabText(0)).is_equal_to("Profile")

    def test_tabs_clear_on_dict_clear(self, base_class, decorator, qt: QtDriver) -> None:
        """All tabs removed when dict is cleared."""

        @widget(title="Tab")
        class SomeTab(Widget):
            _label: QLabel = new("Content")

        @decorator
        class TestClass(base_class):
            _tab_defs: Variable[dict[str, type[Widget]]] = new(
                {
                    "Tab1": SomeTab,
                    "Tab2": SomeTab,
                }
            )
            _tabs: QTabWidget = new(tabs="_tab_defs")

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance._tabs.count()).is_equal_to(2)

        # Clear all
        instance._tab_defs.clear()
        assert_that(instance._tabs.count()).is_equal_to(0)


@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestTabWidgetReactiveList:
    """Reactive tabs= with Variable[list] reference."""

    def test_tabs_update_on_list_append(self, base_class, decorator, qt: QtDriver) -> None:
        """Tabs update when items are appended to Variable[list]."""

        @widget(title="Tab A")
        class TabA(Widget):
            _label: QLabel = new("A")

        @widget(title="Tab B")
        class TabB(Widget):
            _label: QLabel = new("B")

        @decorator
        class TestClass(base_class):
            _tab_defs: Variable[list[type[Widget]]] = new([TabA])
            _tabs: QTabWidget = new(tabs="_tab_defs")

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance._tabs.count()).is_equal_to(1)

        # Append a tab
        instance._tab_defs.append(TabB)
        assert_that(instance._tabs.count()).is_equal_to(2)
        assert_that(instance._tabs.tabText(1)).is_equal_to("Tab B")

    def test_tabs_update_on_list_insert(self, base_class, decorator, qt: QtDriver) -> None:
        """Tabs update when items are inserted into Variable[list]."""

        @widget(title="Tab A")
        class TabA(Widget):
            _label: QLabel = new("A")

        @widget(title="Tab B")
        class TabB(Widget):
            _label: QLabel = new("B")

        @widget(title="Tab C")
        class TabC(Widget):
            _label: QLabel = new("C")

        @decorator
        class TestClass(base_class):
            _tab_defs: Variable[list[type[Widget]]] = new([TabA, TabC])
            _tabs: QTabWidget = new(tabs="_tab_defs")

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance._tabs.count()).is_equal_to(2)

        # Insert in middle
        instance._tab_defs.insert(1, TabB)
        assert_that(instance._tabs.count()).is_equal_to(3)
        assert_that(instance._tabs.tabText(0)).is_equal_to("Tab A")
        assert_that(instance._tabs.tabText(1)).is_equal_to("Tab B")
        assert_that(instance._tabs.tabText(2)).is_equal_to("Tab C")

    def test_tabs_update_on_list_remove(self, base_class, decorator, qt: QtDriver) -> None:
        """Tabs update when items are removed from Variable[list]."""

        @widget(title="Tab A")
        class TabA(Widget):
            _label: QLabel = new("A")

        @widget(title="Tab B")
        class TabB(Widget):
            _label: QLabel = new("B")

        @decorator
        class TestClass(base_class):
            _tab_defs: Variable[list[type[Widget]]] = new([TabA, TabB])
            _tabs: QTabWidget = new(tabs="_tab_defs")

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance._tabs.count()).is_equal_to(2)

        # Remove first tab
        instance._tab_defs.pop(0)
        assert_that(instance._tabs.count()).is_equal_to(1)
        assert_that(instance._tabs.tabText(0)).is_equal_to("Tab B")

    def test_tabs_clear_on_list_clear(self, base_class, decorator, qt: QtDriver) -> None:
        """All tabs removed when list is cleared."""

        @widget(title="Tab")
        class SomeTab(Widget):
            _label: QLabel = new("Content")

        @decorator
        class TestClass(base_class):
            _tab_defs: Variable[list[type[Widget]]] = new([SomeTab, SomeTab])
            _tabs: QTabWidget = new(tabs="_tab_defs")

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance._tabs.count()).is_equal_to(2)

        # Clear all
        instance._tab_defs.clear()
        assert_that(instance._tabs.count()).is_equal_to(0)


# =============================================================================
# Field Reference Tests
# =============================================================================


@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestTabWidgetFieldReferences:
    """Test tabs= with field references (existing widgets)."""

    def test_tabs_with_newfield_references(self, base_class, decorator, qt: QtDriver) -> None:
        """tabs=[field_ref, ...] references existing widget fields."""

        @widget(title="User Editor")
        class UserEditor(Widget):
            _label: QLabel = new("User content")

        @widget(title="Dog Editor")
        class DogEditor(Widget):
            _label: QLabel = new("Dog content")

        @decorator
        class TestClass(base_class):
            _user: UserEditor = new(layout=False)
            _dogs: DogEditor = new(layout=False)
            _tabs: QTabWidget = new(tabs=[_user, _dogs])

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance._tabs.count()).is_equal_to(2)
        # Tab names from windowTitle()
        assert_that(instance._tabs.tabText(0)).is_equal_to("User Editor")
        assert_that(instance._tabs.tabText(1)).is_equal_to("Dog Editor")
        # Same widget instances (not new copies)
        assert instance._tabs.widget(0) is instance._user
        assert instance._tabs.widget(1) is instance._dogs

    def test_tabs_with_string_references(self, base_class, decorator, qt: QtDriver) -> None:
        """tabs=["field_name", ...] references existing widget fields by name."""

        @widget(title="Settings")
        class SettingsPanel(Widget):
            _label: QLabel = new("Settings")

        @widget(title="Profile")
        class ProfilePanel(Widget):
            _label: QLabel = new("Profile")

        @decorator
        class TestClass(base_class):
            _settings: SettingsPanel = new(layout=False)
            _profile: ProfilePanel = new(layout=False)
            _tabs: QTabWidget = new(tabs=["_settings", "_profile"])

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance._tabs.count()).is_equal_to(2)
        assert_that(instance._tabs.tabText(0)).is_equal_to("Settings")
        assert_that(instance._tabs.tabText(1)).is_equal_to("Profile")
        assert instance._tabs.widget(0) is instance._settings
        assert instance._tabs.widget(1) is instance._profile

    def test_tabs_dict_with_newfield_references(self, base_class, decorator, qt: QtDriver) -> None:
        """tabs={"Tab Name": field_ref} with explicit tab names."""

        @widget(title="Original Title")
        class SomePanel(Widget):
            _label: QLabel = new("Content")

        @decorator
        class TestClass(base_class):
            _panel1: SomePanel = new(layout=False)
            _panel2: SomePanel = new(layout=False)
            _tabs: QTabWidget = new(tabs={"First Tab": _panel1, "Second Tab": _panel2})

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance._tabs.count()).is_equal_to(2)
        # Explicit names override windowTitle
        assert_that(instance._tabs.tabText(0)).is_equal_to("First Tab")
        assert_that(instance._tabs.tabText(1)).is_equal_to("Second Tab")
        assert instance._tabs.widget(0) is instance._panel1
        assert instance._tabs.widget(1) is instance._panel2

    def test_tabs_dict_with_string_references(self, base_class, decorator, qt: QtDriver) -> None:
        """tabs={"Tab Name": "field_name"} with string refs and explicit names."""

        @widget
        class Panel(Widget):
            _label: QLabel = new("Content")

        @decorator
        class TestClass(base_class):
            _panel_a: Panel = new(layout=False)
            _panel_b: Panel = new(layout=False)
            _tabs: QTabWidget = new(tabs={"Alpha": "_panel_a", "Beta": "_panel_b"})

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance._tabs.count()).is_equal_to(2)
        assert_that(instance._tabs.tabText(0)).is_equal_to("Alpha")
        assert_that(instance._tabs.tabText(1)).is_equal_to("Beta")

    def test_tabs_with_variable_widget_references(self, base_class, decorator, qt: QtDriver) -> None:
        """tabs=[var_field, ...] works with Variable[T, W] fields."""
        from dataclasses import dataclass

        @dataclass
        class User:
            name: str = ""

        @dataclass
        class Dog:
            breed: str = ""

        @widget(title="User Form")
        class UserForm(Widget):
            _label: QLabel = new("User form")

        @widget(title="Dog Form")
        class DogForm(Widget):
            _label: QLabel = new("Dog form")

        @decorator
        class TestClass(base_class):
            _user: Variable[User, UserForm] = new(User("Alice"))(layout=False)
            _dog: Variable[Dog, DogForm] = new(Dog("Labrador"))(layout=False)
            _tabs: QTabWidget = new(tabs=[_user, _dog])

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance._tabs.count()).is_equal_to(2)
        # Tab names from widget's windowTitle
        assert_that(instance._tabs.tabText(0)).is_equal_to("User Form")
        assert_that(instance._tabs.tabText(1)).is_equal_to("Dog Form")
        # Widget instances come from Variable.widget
        assert instance._tabs.widget(0) is instance._user.widget
        assert instance._tabs.widget(1) is instance._dog.widget

    def test_tabs_fallback_to_field_name_when_no_title(self, base_class, decorator, qt: QtDriver) -> None:
        """Tab name falls back to field name if no windowTitle."""

        @widget  # No title=
        class UntitledPanel(Widget):
            _label: QLabel = new("Content")

        @decorator
        class TestClass(base_class):
            _my_panel: UntitledPanel = new(layout=False)
            _tabs: QTabWidget = new(tabs=[_my_panel])

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance._tabs.count()).is_equal_to(1)
        # Falls back to field name
        assert_that(instance._tabs.tabText(0)).is_equal_to("_my_panel")

    def test_tabs_mixed_refs_and_classes(self, base_class, decorator, qt: QtDriver) -> None:
        """tabs= can mix field references and widget classes."""

        @widget(title="Existing Panel")
        class ExistingPanel(Widget):
            _label: QLabel = new("Existing")

        @widget(title="New Panel")
        class NewPanel(Widget):
            _label: QLabel = new("New")

        @decorator
        class TestClass(base_class):
            _existing: ExistingPanel = new(layout=False)
            _tabs: QTabWidget = new(tabs=[_existing, NewPanel])

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance._tabs.count()).is_equal_to(2)
        # First is existing, second is new
        assert instance._tabs.widget(0) is instance._existing
        assert isinstance(instance._tabs.widget(1), NewPanel)
        assert instance._tabs.widget(1) is not instance._existing

    def test_tabs_ref_with_selected_index_binding(self, base_class, decorator, qt: QtDriver) -> None:
        """Field references work with selectedIndex= binding."""

        @widget(title="Tab A")
        class TabA(Widget):
            _label: QLabel = new("A")

        @widget(title="Tab B")
        class TabB(Widget):
            _label: QLabel = new("B")

        @decorator
        class TestClass(base_class):
            _selected: Variable[int] = new(1)  # Start on second tab
            _tab_a: TabA = new(layout=False)
            _tab_b: TabB = new(layout=False)
            _tabs: QTabWidget = new(
                tabs=[_tab_a, _tab_b],
                selectedIndex="_selected",
            )

        instance = create_and_track(qt, TestClass, base_class)
        assert_that(instance._tabs.currentIndex()).is_equal_to(1)
        assert instance._tabs.currentWidget() is instance._tab_b

        # Change selection via Variable
        instance._selected.value = 0
        assert instance._tabs.currentWidget() is instance._tab_a
