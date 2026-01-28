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
from PySide6.QtWidgets import QLabel, QLineEdit, QTabWidget

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


# =============================================================================
# Record Propagation Tests
# =============================================================================


@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestTabWidgetRecordPropagation:
    """Test that Widget[T] tabs inherit parent's record when types match."""

    def test_tabs_inherit_record_from_parent(self, base_class, decorator, qt: QtDriver) -> None:
        """Child Widget[T] tabs inherit parent's record when T matches."""
        from dataclasses import dataclass

        @dataclass
        class Person:
            name: str = ""
            age: int = 0

        @widget(title="Name Tab")
        class NameTab(Widget[Person]):
            _label: QLabel = new(bind="Name: {name}")

        @widget(title="Age Tab")
        class AgeTab(Widget[Person]):
            _label: QLabel = new(bind="Age: {age}")

        @decorator(record=Person("Alice", 30))
        class TestClass(base_class[Person]):
            _tabs: QTabWidget = new(tabs=[NameTab, AgeTab])

        instance = create_and_track(qt, TestClass, base_class)

        # Tab widgets should have inherited the record
        name_tab = instance._tabs.widget(0)
        age_tab = instance._tabs.widget(1)

        assert_that(name_tab._label.text()).is_equal_to("Name: Alice")
        assert_that(age_tab._label.text()).is_equal_to("Age: 30")

    def test_tabs_update_when_parent_record_changes(self, base_class, decorator, qt: QtDriver) -> None:
        """Child tabs update when parent's record is modified."""
        from dataclasses import dataclass

        @dataclass
        class Person:
            name: str = ""

        @widget(title="Details")
        class DetailsTab(Widget[Person]):
            _label: QLabel = new(bind="Hello, {name}!")

        @decorator(record=Person("Bob"))
        class TestClass(base_class[Person]):
            _tabs: QTabWidget = new(tabs=[DetailsTab])

        instance = create_and_track(qt, TestClass, base_class)
        details_tab = instance._tabs.widget(0)

        assert_that(details_tab._label.text()).is_equal_to("Hello, Bob!")

        # Change parent's record field
        instance.record.name = "Charlie"
        assert_that(details_tab._label.text()).is_equal_to("Hello, Charlie!")

    def test_tabs_receive_record_set_later_via_binding(self, base_class, decorator, qt: QtDriver) -> None:
        """Child tabs receive record when parent's record is set via Variable binding."""
        from dataclasses import dataclass

        @dataclass
        class Response:
            status: int = 0
            body: str = ""

        @widget(title="Status")
        class StatusTab(Widget[Response]):
            _label: QLabel = new(bind="Status: {status}")

        @widget(title="Body")
        class BodyTab(Widget[Response]):
            _label: QLabel = new(bind="Body: {body}")

        @widget
        class ResponseViewer(Widget[Response]):
            _tabs: QTabWidget = new(tabs=[StatusTab, BodyTab])

        @decorator
        class TestClass(base_class):
            response: Variable[Response | None] = new(None)
            _viewer: ResponseViewer = new(bind="response")

        instance = create_and_track(qt, TestClass, base_class)

        # Initially no response
        status_tab = instance._viewer._tabs.widget(0)
        body_tab = instance._viewer._tabs.widget(1)

        # Set the response - this should propagate to child tabs
        instance.response = Response(status=200, body="OK")

        assert_that(status_tab._label.text()).is_equal_to("Status: 200")
        assert_that(body_tab._label.text()).is_equal_to("Body: OK")

    def test_tabs_do_not_inherit_mismatched_record_types(self, base_class, decorator, qt: QtDriver) -> None:
        """Child Widget[T] tabs don't inherit parent's Widget[U] record when T != U."""
        from dataclasses import dataclass

        @dataclass
        class Request:
            url: str = ""

        @dataclass
        class Response:
            status: int = 0

        @widget(title="Response Tab")
        class ResponseTab(Widget[Response]):
            _label: QLabel = new("Response placeholder")

        # Parent has Request, child expects Response - should NOT propagate
        @decorator(record=Request("http://example.com"))
        class TestClass(base_class[Request]):
            _tabs: QTabWidget = new(tabs=[ResponseTab])

        instance = create_and_track(qt, TestClass, base_class)
        response_tab = instance._tabs.widget(0)

        # Child's record should NOT be set (types don't match)
        # Access to record.status would fail if record isn't a Response
        # The label should show the static text since binding couldn't resolve
        assert_that(response_tab._label.text()).is_equal_to("Response placeholder")


# =============================================================================
# Field Binding with Different Record Type Tests (bind="field")
# =============================================================================


@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestTabWidgetFieldBindingDifferentRecordType:
    """Test child Widget[T] inside tabs with bind='field' to parent record's field.

    This is the pattern used in Forc where:
    - RequestAuthWidget (Widget[Request]) is a tab
    - RequestAuthFormWidget (Widget[Auth]) is a child with bind="auth"
    - Auth is a field on Request, so the child gets Request.auth as its record
    """

    def test_child_widget_binds_to_parent_record_field(self, base_class, decorator, qt: QtDriver) -> None:
        """Child Widget[Auth] with bind='auth' gets parent's auth field as its record."""
        from dataclasses import dataclass

        @dataclass
        class Auth:
            username: str = ""
            password: str = ""

        @dataclass
        class Request:
            url: str = ""
            auth: Auth | None = None

        @widget
        class AuthFormWidget(Widget[Auth]):
            """Child widget that expects Auth as its record."""

            _username_label: QLabel = new(bind="Username: {username}")
            _password_label: QLabel = new(bind="Password: {password}")

        @widget(title="Auth")
        class AuthTabWidget(Widget[Request]):
            """Tab widget that has Request as its record, contains AuthFormWidget."""

            auth_form: AuthFormWidget = new(bind="auth")

        @decorator(record=Request(url="http://example.com", auth=Auth("admin", "secret123")))
        class TestClass(base_class[Request]):
            _tabs: QTabWidget = new(tabs=[AuthTabWidget])

        instance = create_and_track(qt, TestClass, base_class)

        # Get the auth tab and its child form
        auth_tab = instance._tabs.widget(0)
        auth_form = auth_tab.auth_form

        # The child's record should be the Auth object from parent's auth field
        assert_that(auth_form._username_label.text()).is_equal_to("Username: admin")
        assert_that(auth_form._password_label.text()).is_equal_to("Password: secret123")

    def test_child_widget_updates_when_parent_record_field_changes(self, base_class, decorator, qt: QtDriver) -> None:
        """Child updates when parent's record.auth field is modified."""
        from dataclasses import dataclass

        @dataclass
        class Auth:
            token: str = ""

        @dataclass
        class Request:
            url: str = ""
            auth: Auth | None = None

        @widget
        class AuthFormWidget(Widget[Auth]):
            _token_label: QLabel = new(bind="Token: {token}")

        @widget(title="Auth")
        class AuthTabWidget(Widget[Request]):
            auth_form: AuthFormWidget = new(bind="auth")

        @decorator(record=Request(url="http://example.com", auth=Auth("initial-token")))
        class TestClass(base_class[Request]):
            _tabs: QTabWidget = new(tabs=[AuthTabWidget])

        instance = create_and_track(qt, TestClass, base_class)

        auth_tab = instance._tabs.widget(0)
        auth_form = auth_tab.auth_form

        assert_that(auth_form._token_label.text()).is_equal_to("Token: initial-token")

        # Modify the token via parent's record proxy
        instance.record.auth.token = "new-token"
        assert_that(auth_form._token_label.text()).is_equal_to("Token: new-token")

    @pytest.mark.xfail(reason="Replacing entire record via Variable doesn't propagate to field-bound children yet")
    def test_child_widget_updates_when_parent_record_replaced(self, base_class, decorator, qt: QtDriver) -> None:
        """Child updates when entire parent record is replaced (e.g., user clicks different request)."""
        from dataclasses import dataclass

        @dataclass
        class Auth:
            auth_type: str = ""

        @dataclass
        class Request:
            name: str = ""
            auth: Auth | None = None

        @widget
        class AuthFormWidget(Widget[Auth]):
            _type_label: QLabel = new(bind="Auth Type: {auth_type}")

        @widget(title="Auth")
        class AuthTabWidget(Widget[Request]):
            auth_form: AuthFormWidget = new(bind="auth")

        @widget
        class RequestEditorWidget(Widget[Request]):
            _tabs: QTabWidget = new(tabs=[AuthTabWidget])

        @decorator
        class TestClass(base_class):
            _request: Variable[Request | None] = new(None)
            _editor: RequestEditorWidget = new(bind="_request")

        instance = create_and_track(qt, TestClass, base_class)

        # Initially no request
        auth_tab = instance._editor._tabs.widget(0)
        auth_form = auth_tab.auth_form

        # Set first request with Basic auth
        instance._request.value = Request(name="Login", auth=Auth("BASIC"))
        assert_that(auth_form._type_label.text()).is_equal_to("Auth Type: BASIC")

        # Switch to different request with Bearer auth
        instance._request.value = Request(name="Profile", auth=Auth("BEARER"))
        assert_that(auth_form._type_label.text()).is_equal_to("Auth Type: BEARER")

    def test_child_widget_with_format_binding_using_record_placeholder(self, base_class, decorator, qt: QtDriver) -> None:
        """Child Widget[Auth] can use {#record} placeholder in format bindings."""
        from dataclasses import dataclass

        @dataclass
        class Auth:
            auth_type: str = "NONE"

            def __str__(self) -> str:  # type: ignore[override]
                return f"Auth({self.auth_type})"

        @dataclass
        class Request:
            url: str = ""
            auth: Auth | None = None

        @widget
        class AuthFormWidget(Widget[Auth]):
            _record_label: QLabel = new(bind="Record: {#record}")

        @widget(title="Auth")
        class AuthTabWidget(Widget[Request]):
            auth_form: AuthFormWidget = new(bind="auth")

        @decorator(record=Request(url="http://example.com", auth=Auth("API_KEY")))
        class TestClass(base_class[Request]):
            _tabs: QTabWidget = new(tabs=[AuthTabWidget])

        instance = create_and_track(qt, TestClass, base_class)

        auth_tab = instance._tabs.widget(0)
        auth_form = auth_tab.auth_form

        assert_that(auth_form._record_label.text()).is_equal_to("Record: Auth(API_KEY)")

    @pytest.mark.xfail(reason="Setting field from None to value doesn't propagate to field-bound children yet")
    def test_child_widget_with_null_field_initially(self, base_class, decorator, qt: QtDriver) -> None:
        """Child Widget[Auth] handles null auth field gracefully."""
        from dataclasses import dataclass

        @dataclass
        class Auth:
            username: str = ""

        @dataclass
        class Request:
            url: str = ""
            auth: Auth | None = None  # Starts as None

        @widget
        class AuthFormWidget(Widget[Auth]):
            _username_label: QLabel = new(bind="User: {username}")

        @widget(title="Auth")
        class AuthTabWidget(Widget[Request]):
            auth_form: AuthFormWidget = new(bind="auth")

        @decorator(record=Request(url="http://example.com", auth=None))
        class TestClass(base_class[Request]):
            _tabs: QTabWidget = new(tabs=[AuthTabWidget])

        instance = create_and_track(qt, TestClass, base_class)

        auth_tab = instance._tabs.widget(0)
        auth_form = auth_tab.auth_form

        # When auth is None, the binding should show empty or placeholder
        # (depends on how format binding handles None)
        _ = auth_form._username_label.text()  # Capture initial text (unused)

        # Now set auth
        instance.record.auth = Auth("admin")
        assert_that(auth_form._username_label.text()).is_equal_to("User: admin")

    def test_deeply_nested_child_bindings(self, base_class, decorator, qt: QtDriver) -> None:
        """Test nested child widgets with bind='field' pattern."""
        from dataclasses import dataclass

        @dataclass
        class Credentials:
            api_key: str = ""

        @dataclass
        class Auth:
            auth_type: str = ""
            credentials: Credentials | None = None

        @dataclass
        class Request:
            url: str = ""
            auth: Auth | None = None

        @widget
        class CredentialsFormWidget(Widget[Credentials]):
            _key_label: QLabel = new(bind="API Key: {api_key}")

        @widget
        class AuthFormWidget(Widget[Auth]):
            _type_label: QLabel = new(bind="Type: {auth_type}")
            _credentials: CredentialsFormWidget = new(bind="credentials")

        @widget(title="Auth")
        class AuthTabWidget(Widget[Request]):
            auth_form: AuthFormWidget = new(bind="auth")

        @decorator(
            record=Request(
                url="http://example.com",
                auth=Auth(auth_type="API_KEY", credentials=Credentials("secret-key-123")),
            )
        )
        class TestClass(base_class[Request]):
            _tabs: QTabWidget = new(tabs=[AuthTabWidget])

        instance = create_and_track(qt, TestClass, base_class)

        auth_tab = instance._tabs.widget(0)
        auth_form = auth_tab.auth_form
        credentials_form = auth_form._credentials

        assert_that(auth_form._type_label.text()).is_equal_to("Type: API_KEY")
        assert_that(credentials_form._key_label.text()).is_equal_to("API Key: secret-key-123")

    @pytest.mark.xfail(reason="Test timing issue - visible= works in real app but not in test setup")
    def test_record_field_named_type_resolves_correctly(self, base_class, decorator, qt: QtDriver) -> None:
        """Test that 'type' field on record resolves correctly, not Python's builtin type()."""
        from dataclasses import dataclass
        from enum import Enum

        class AuthType(Enum):
            NONE = "none"
            BASIC = "basic"
            BEARER = "bearer"

        @dataclass
        class Auth:
            type: AuthType = AuthType.NONE  # Field named 'type' - same as Python builtin!
            username: str = ""

        @dataclass
        class Request:
            url: str = ""
            auth: Auth | None = None

        @widget
        class AuthFormWidget(Widget[Auth]):
            # This should show "BASIC" not error from Python's builtin type()
            _type_label: QLabel = new(bind="Auth Type: {type.name}")
            # With visible= using the type field
            _username: QLineEdit = new(bind="username", visible="{type.name == 'BASIC'}")

        @widget(title="Auth")
        class AuthTabWidget(Widget[Request]):
            auth_form: AuthFormWidget = new(bind="auth")

        @decorator(
            record=Request(
                url="http://example.com",
                auth=Auth(type=AuthType.BASIC, username="admin"),
            )
        )
        class TestClass(base_class[Request]):
            _tabs: QTabWidget = new(tabs=[AuthTabWidget])

        instance = create_and_track(qt, TestClass, base_class)

        # Process events to allow deferred bindings to complete
        from qtpy.QtWidgets import QApplication

        QApplication.processEvents()

        auth_tab = instance._tabs.widget(0)
        auth_form = auth_tab.auth_form

        # The 'type' field should resolve to record.type, not Python's builtin type()
        assert_that(auth_form._type_label.text()).is_equal_to("Auth Type: BASIC")

        # visible= binding should also work with type.name
        assert_that(auth_form._username.isVisible()).is_true()

        # Change auth type - label should update
        instance.record.auth.type = AuthType.BEARER
        assert_that(auth_form._type_label.text()).is_equal_to("Auth Type: BEARER")

        # username should now be hidden
        assert_that(auth_form._username.isVisible()).is_false()


# =============================================================================
# is_tab Property Tests
# =============================================================================


@pytest.mark.parametrize("base_class,decorator", WIDGET_CLASS_TYPES)
class TestTabWidgetIsTabProperty:
    """Test that widgets added to tabs get is_tab='true' property for QSS styling."""

    def test_static_dict_tabs_have_is_tab_property(self, base_class, decorator, qt: QtDriver) -> None:
        """Widgets added via tabs=dict get is_tab='true' property."""

        @widget(title="Tab A")
        class TabA(Widget):
            _label: QLabel = new("A")

        @widget(title="Tab B")
        class TabB(Widget):
            _label: QLabel = new("B")

        @decorator
        class TestClass(base_class):
            _tabs: QTabWidget = new(tabs={"First": TabA, "Second": TabB})

        instance = create_and_track(qt, TestClass, base_class)

        tab_a = instance._tabs.widget(0)
        tab_b = instance._tabs.widget(1)

        assert_that(tab_a.property("is_tab")).is_equal_to("true")
        assert_that(tab_b.property("is_tab")).is_equal_to("true")

    def test_static_list_tabs_have_is_tab_property(self, base_class, decorator, qt: QtDriver) -> None:
        """Widgets added via tabs=list get is_tab='true' property."""

        @widget(title="Tab A")
        class TabA(Widget):
            _label: QLabel = new("A")

        @widget(title="Tab B")
        class TabB(Widget):
            _label: QLabel = new("B")

        @decorator
        class TestClass(base_class):
            _tabs: QTabWidget = new(tabs=[TabA, TabB])

        instance = create_and_track(qt, TestClass, base_class)

        tab_a = instance._tabs.widget(0)
        tab_b = instance._tabs.widget(1)

        assert_that(tab_a.property("is_tab")).is_equal_to("true")
        assert_that(tab_b.property("is_tab")).is_equal_to("true")

    def test_field_ref_tabs_have_is_tab_property(self, base_class, decorator, qt: QtDriver) -> None:
        """Widgets added via field references get is_tab='true' property."""

        @widget(title="Panel A")
        class PanelA(Widget):
            _label: QLabel = new("A")

        @widget(title="Panel B")
        class PanelB(Widget):
            _label: QLabel = new("B")

        @decorator
        class TestClass(base_class):
            _panel_a: PanelA = new(layout=False)
            _panel_b: PanelB = new(layout=False)
            _tabs: QTabWidget = new(tabs=[_panel_a, _panel_b])

        instance = create_and_track(qt, TestClass, base_class)

        assert_that(instance._panel_a.property("is_tab")).is_equal_to("true")
        assert_that(instance._panel_b.property("is_tab")).is_equal_to("true")

    def test_reactive_dict_insert_sets_is_tab_property(self, base_class, decorator, qt: QtDriver) -> None:
        """Widgets added reactively via dict insert get is_tab='true' property."""

        @widget(title="Tab A")
        class TabA(Widget):
            _label: QLabel = new("A")

        @widget(title="Tab B")
        class TabB(Widget):
            _label: QLabel = new("B")

        @decorator
        class TestClass(base_class):
            _tab_defs: Variable[dict[str, type[Widget]]] = new({"First": TabA})
            _tabs: QTabWidget = new(tabs="_tab_defs")

        instance = create_and_track(qt, TestClass, base_class)

        # Initial tab has property
        tab_a = instance._tabs.widget(0)
        assert_that(tab_a.property("is_tab")).is_equal_to("true")

        # Add new tab reactively
        instance._tab_defs["Second"] = TabB
        tab_b = instance._tabs.widget(1)
        assert_that(tab_b.property("is_tab")).is_equal_to("true")

    def test_reactive_dict_remove_clears_is_tab_property(self, base_class, decorator, qt: QtDriver) -> None:
        """Widgets removed reactively via dict remove lose is_tab property."""

        @widget(title="Tab A")
        class TabA(Widget):
            _label: QLabel = new("A")

        @widget(title="Tab B")
        class TabB(Widget):
            _label: QLabel = new("B")

        @decorator
        class TestClass(base_class):
            _tab_defs: Variable[dict[str, type[Widget]]] = new({"First": TabA, "Second": TabB})
            _tabs: QTabWidget = new(tabs="_tab_defs")

        instance = create_and_track(qt, TestClass, base_class)

        tab_a = instance._tabs.widget(0)
        assert_that(tab_a.property("is_tab")).is_equal_to("true")

        # Remove the tab
        del instance._tab_defs["First"]

        # Property should be cleared (None or not set)
        assert_that(tab_a.property("is_tab")).is_none()

    def test_reactive_dict_clear_clears_is_tab_property(self, base_class, decorator, qt: QtDriver) -> None:
        """Widgets removed via dict clear lose is_tab property."""

        @widget(title="Tab")
        class SomeTab(Widget):
            _label: QLabel = new("Content")

        @decorator
        class TestClass(base_class):
            _tab_defs: Variable[dict[str, type[Widget]]] = new({"Tab1": SomeTab, "Tab2": SomeTab})
            _tabs: QTabWidget = new(tabs="_tab_defs")

        instance = create_and_track(qt, TestClass, base_class)

        tab1 = instance._tabs.widget(0)
        tab2 = instance._tabs.widget(1)
        assert_that(tab1.property("is_tab")).is_equal_to("true")
        assert_that(tab2.property("is_tab")).is_equal_to("true")

        # Clear all
        instance._tab_defs.clear()

        # Properties should be cleared
        assert_that(tab1.property("is_tab")).is_none()
        assert_that(tab2.property("is_tab")).is_none()

    def test_reactive_list_append_sets_is_tab_property(self, base_class, decorator, qt: QtDriver) -> None:
        """Widgets added reactively via list append get is_tab='true' property."""

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

        # Initial tab has property
        tab_a = instance._tabs.widget(0)
        assert_that(tab_a.property("is_tab")).is_equal_to("true")

        # Append new tab
        instance._tab_defs.append(TabB)
        tab_b = instance._tabs.widget(1)
        assert_that(tab_b.property("is_tab")).is_equal_to("true")

    def test_reactive_list_remove_clears_is_tab_property(self, base_class, decorator, qt: QtDriver) -> None:
        """Widgets removed reactively via list pop lose is_tab property."""

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

        tab_a = instance._tabs.widget(0)
        assert_that(tab_a.property("is_tab")).is_equal_to("true")

        # Remove the tab
        instance._tab_defs.pop(0)

        # Property should be cleared
        assert_that(tab_a.property("is_tab")).is_none()

    def test_reactive_list_clear_clears_is_tab_property(self, base_class, decorator, qt: QtDriver) -> None:
        """Widgets removed via list clear lose is_tab property."""

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

        tab1 = instance._tabs.widget(0)
        tab2 = instance._tabs.widget(1)
        assert_that(tab1.property("is_tab")).is_equal_to("true")
        assert_that(tab2.property("is_tab")).is_equal_to("true")

        # Clear all
        instance._tab_defs.clear()

        # Properties should be cleared
        assert_that(tab1.property("is_tab")).is_none()
        assert_that(tab2.property("is_tab")).is_none()
