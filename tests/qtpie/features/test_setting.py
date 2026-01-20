# pyright: reportPrivateUsage=false
# pyright: reportUnknownMemberType=false
"""Tests for Setting - persistent Variables backed by QSettings."""

from dataclasses import dataclass
from enum import Enum

import pytest
from qtpy.QtCore import QCoreApplication
from qtpy.QtWidgets import QLabel, QLineEdit

from qtpie import Setting, Widget, new, widget
from qtpie.settings_backend import SettingsBackend, get_settings_backend, reset_settings_backend


@pytest.fixture(autouse=True)
def setup_app(qapp: QCoreApplication) -> None:
    """Set up org/app name for QSettings."""
    qapp.setOrganizationName("QtPieTest")
    qapp.setApplicationName("SettingTests")


@pytest.fixture(autouse=True)
def clear_settings() -> None:
    """Clear settings before each test."""
    reset_settings_backend()


class TestSettingBasics:
    """Test basic Setting functionality."""

    def test_setting_default_value(self) -> None:
        """Setting uses default value when no stored value exists."""

        @widget
        class DefaultValueWidget(Widget):
            count: Setting[int] = new(42)

        w = DefaultValueWidget()
        assert w.count.value == 42

    def test_setting_persists_on_change(self) -> None:
        """Setting persists to QSettings on value change."""

        @widget
        class PersistWidget(Widget):
            count: Setting[int] = new(0)

        w = PersistWidget()
        w.count.value = 100

        # Check that it's in QSettings
        backend = get_settings_backend()
        stored = backend.get("PersistWidget:count", -1, int)
        assert stored == 100

    def test_setting_loads_stored_value(self) -> None:
        """Setting loads stored value on creation."""
        backend = get_settings_backend()
        backend.set("MyWidget2:count", 999, int)
        backend.sync()

        @widget
        class MyWidget2(Widget):
            count: Setting[int] = new(0)

        w = MyWidget2()
        assert w.count.value == 999

    def test_setting_with_explicit_group(self) -> None:
        """Setting uses explicit group in key."""

        @widget
        class MyWidget(Widget):
            window_width: Setting[int] = new(800, group="window")

        w = MyWidget()
        w.window_width.value = 1024

        backend = get_settings_backend()
        # Key should be "window:window_width", not "MyWidget:window_width"
        stored = backend.get("window:window_width", -1, int)
        assert stored == 1024


class TestSettingTypes:
    """Test Setting with different types."""

    def test_setting_string(self) -> None:
        """Setting works with strings."""

        @widget
        class MyWidget(Widget):
            name: Setting[str] = new("default")

        w = MyWidget()
        w.name.value = "hello"

        backend = get_settings_backend()
        stored = backend.get("MyWidget:name", "", str)
        assert stored == "hello"

    def test_setting_bool(self) -> None:
        """Setting works with booleans."""

        @widget
        class MyWidget(Widget):
            enabled: Setting[bool] = new(False)

        w = MyWidget()
        w.enabled.value = True

        backend = get_settings_backend()
        stored = backend.get("MyWidget:enabled", False, bool)
        assert stored is True

    def test_setting_float(self) -> None:
        """Setting works with floats."""

        @widget
        class MyWidget(Widget):
            ratio: Setting[float] = new(1.0)

        w = MyWidget()
        w.ratio.value = 3.14

        backend = get_settings_backend()
        stored = backend.get("MyWidget:ratio", 0.0, float)
        assert stored == pytest.approx(3.14)

    def test_setting_list(self) -> None:
        """Setting works with lists."""

        @widget
        class ListWidget(Widget):
            items: Setting[list[str]] = new([])

        w = ListWidget()
        w.items.value = ["a", "b", "c"]

        backend = get_settings_backend()
        stored = backend.get("ListWidget:items", [], list[str])
        assert stored == ["a", "b", "c"]

    def test_setting_list_mutations(self) -> None:
        """Setting persists list mutations (append, extend, etc.)."""

        @widget
        class ListMutationWidget(Widget):
            items: Setting[list[str]] = new([])

        w = ListMutationWidget()

        # Test append
        w.items.append("a")
        backend = get_settings_backend()
        assert backend.get("ListMutationWidget:items", [], list[str]) == ["a"]

        # Test extend
        w.items.extend(["b", "c"])
        assert backend.get("ListMutationWidget:items", [], list[str]) == ["a", "b", "c"]

        # Test remove
        w.items.remove("b")
        assert backend.get("ListMutationWidget:items", [], list[str]) == ["a", "c"]

    def test_setting_none(self) -> None:
        """Setting handles None values."""

        @widget
        class MyWidget(Widget):
            maybe: Setting[str | None] = new(None)

        w = MyWidget()
        assert w.maybe.value is None

        w.maybe.value = "something"
        assert w.maybe.value == "something"

        w.maybe.value = None
        backend = get_settings_backend()
        stored = backend.get("MyWidget:maybe", "default", str | None)
        assert stored is None


class TestSettingDataclass:
    """Test Setting with dataclass types."""

    def test_setting_dataclass(self) -> None:
        """Setting serializes dataclass to JSON."""

        @dataclass
        class Config:
            name: str = ""
            count: int = 0

        @widget
        class MyWidget(Widget):
            config: Setting[Config] = new(Config())

        w = MyWidget()
        w.config.value = Config(name="test", count=42)

        backend = get_settings_backend()
        stored = backend.get("MyWidget:config", Config(), Config)
        assert stored.name == "test"
        assert stored.count == 42

    def test_setting_nested_dataclass(self) -> None:
        """Setting handles nested dataclasses."""

        @dataclass
        class Inner:
            value: int = 0

        @dataclass
        class Outer:
            inner: Inner | None = None

        @widget
        class MyWidget(Widget):
            data: Setting[Outer] = new(Outer())

        w = MyWidget()
        w.data.value = Outer(inner=Inner(value=123))

        backend = get_settings_backend()
        stored = backend.get("MyWidget:data", Outer(), Outer)
        assert stored.inner is not None
        assert stored.inner.value == 123


class TestSettingEnum:
    """Test Setting with enum types."""

    def test_setting_enum(self) -> None:
        """Setting serializes enum by value."""

        class Theme(Enum):
            LIGHT = "light"
            DARK = "dark"

        @widget
        class MyWidget(Widget):
            theme: Setting[Theme] = new(Theme.LIGHT)

        w = MyWidget()
        w.theme.value = Theme.DARK

        backend = get_settings_backend()
        stored = backend.get("MyWidget:theme", Theme.LIGHT, Theme)
        assert stored == Theme.DARK


class TestSettingBindings:
    """Test that Setting works with bindings like Variable."""

    def test_setting_bind_to_label(self) -> None:
        """Setting can be bound to widgets."""

        @widget
        class MyWidget(Widget):
            count: Setting[int] = new(0)
            label: QLabel = new(bind="Count: {count}")

        w = MyWidget()
        assert w.label.text() == "Count: 0"

        w.count.value = 42
        assert w.label.text() == "Count: 42"

    def test_setting_with_widget(self) -> None:
        """Setting[T, W] creates auto-bound widget."""

        @widget
        class MyWidget(Widget):
            name: Setting[str, QLineEdit] = new("")

        w = MyWidget()
        w.name.widget.setText("hello")
        assert w.name.value == "hello"

        # Also persisted
        backend = get_settings_backend()
        stored = backend.get("MyWidget:name", "", str)
        assert stored == "hello"


class TestSettingDirtyTracking:
    """Test that Setting integrates with dirty tracking."""

    def test_setting_dirty_tracking(self) -> None:
        """Setting supports dirty tracking."""

        @widget
        class MyWidget(Widget):
            count: Setting[int] = new(0)

        w = MyWidget()
        assert w.count.is_dirty.get() is False

        w.count.value = 100
        assert w.count.is_dirty.get() is True

        w.count.reset_dirty()
        assert w.count.is_dirty.get() is False


class TestSettingHierarchy:
    """Test Setting hierarchy resolution (like Variable)."""

    def test_bare_setting_resolves_from_parent(self) -> None:
        """Bare Setting[T] in child resolves to parent's Setting."""

        @widget
        class ChildWidget(Widget):
            theme: Setting[str]  # Bare - resolves from parent

        @widget
        class ParentWidget(Widget):
            theme: Setting[str] = new("light")
            child: ChildWidget = new()

        p = ParentWidget()
        # Child's theme should be the same object as parent's
        assert p.child.theme is p.theme

        # Changing via child updates parent (same object)
        p.child.theme.value = "dark"
        assert p.theme.value == "dark"

    def test_setting_lookup_by_key(self) -> None:
        """self.setting() looks up Setting value by persist key in hierarchy."""

        @widget
        class DeepChild(Widget):
            def get_theme(self) -> str:
                # Look up by key - returns value directly (like self.var())
                return self.setting("SettingLookupParent:theme", str)

        @widget
        class MiddleChild(Widget):
            deep: DeepChild = new()

        @widget
        class SettingLookupParent(Widget):
            theme: Setting[str] = new("light")
            middle: MiddleChild = new()

        p = SettingLookupParent()

        # Deep child can look up Setting value by key
        assert p.middle.deep.get_theme() == "light"

        # Modify through the parent's Setting attribute
        p.theme.value = "dark"
        assert p.middle.deep.get_theme() == "dark"

    def test_setting_lookup_with_explicit_group(self) -> None:
        """self.setting() works with explicit group keys."""

        @widget
        class AppChild(Widget):
            def get_setting_value(self) -> int:
                # Returns value directly
                return self.setting("app:window_width", int)

        @widget
        class AppParent(Widget):
            window_width: Setting[int] = new(800, group="app")
            child: AppChild = new()

        p = AppParent()
        assert p.child.get_setting_value() == 800

    def test_setting_lookup_by_attr_name_only(self) -> None:
        """self.setting() can look up by attribute name without class prefix."""

        @widget
        class ChildWidget(Widget):
            def get_theme(self) -> str:
                # Look up by just "theme" - no class prefix needed
                return self.setting("theme", str)

        @widget
        class ParentWithSetting(Widget):
            theme: Setting[str] = new("dark")  # Key is "ParentWithSetting:theme"
            child: ChildWidget = new()

        p = ParentWithSetting()

        # Should find it by just the attribute name
        assert p.child.get_theme() == "dark"

    def test_setting_lookup_not_found_raises(self) -> None:
        """self.setting() raises AttributeError if key not found."""

        @widget
        class LonelyWidget(Widget):
            pass

        w = LonelyWidget()
        with pytest.raises(AttributeError, match="Setting with key 'nonexistent:key' not found"):
            w.setting("nonexistent:key", int)


class TestSettingDictMutations:
    """Test dict mutation persistence."""

    def test_setting_dict_mutations(self) -> None:
        """Setting persists dict mutations (setitem, update, del)."""

        @widget
        class DictMutationWidget(Widget):
            scores: Setting[dict[str, int]] = new({})

        w = DictMutationWidget()
        backend = get_settings_backend()

        # Test setitem
        w.scores["alice"] = 100
        assert backend.get("DictMutationWidget:scores", {}, dict[str, int]) == {"alice": 100}

        # Test update
        w.scores.update({"bob": 85, "charlie": 90})
        stored = backend.get("DictMutationWidget:scores", {}, dict[str, int])
        assert stored == {"alice": 100, "bob": 85, "charlie": 90}

        # Test del
        del w.scores["bob"]
        stored = backend.get("DictMutationWidget:scores", {}, dict[str, int])
        assert stored == {"alice": 100, "charlie": 90}

        # Test clear via value assignment
        w.scores.value = {"only": 1}
        stored = backend.get("DictMutationWidget:scores", {}, dict[str, int])
        assert stored == {"only": 1}


class TestSettingDataclassFieldMutations:
    """Test dataclass field mutation behavior."""

    def test_dataclass_field_mutation_does_not_persist(self) -> None:
        """Mutating a dataclass field directly does NOT auto-persist.

        This is expected behavior - you must reassign the whole value.
        """

        @dataclass
        class Config:
            name: str = ""
            count: int = 0

        @widget
        class DataclassMutationWidget(Widget):
            config: Setting[Config] = new(Config())

        w = DataclassMutationWidget()
        backend = get_settings_backend()

        # Set initial value
        w.config.value = Config(name="test", count=10)
        stored = backend.get("DataclassMutationWidget:config", Config(), Config)
        assert stored.name == "test"
        assert stored.count == 10

        # Mutate field directly - this WON'T persist!
        w.config.value.name = "modified"

        # The in-memory value is changed
        assert w.config.value.name == "modified"

        # But storage still has old value (expected!)
        stored = backend.get("DataclassMutationWidget:config", Config(), Config)
        assert stored.name == "test"  # Still old value!

        # To persist, must reassign the whole value
        w.config.value = Config(name="modified", count=10)
        stored = backend.get("DataclassMutationWidget:config", Config(), Config)
        assert stored.name == "modified"  # Now it's updated


class TestSettingTypeMismatch:
    """Test behavior when stored type doesn't match expected type."""

    def test_type_mismatch_uses_default(self) -> None:
        """When stored value has wrong type, use default."""
        backend = get_settings_backend()

        # Store a string where we'll expect an int
        backend.set("TypeMismatchWidget:count", "not_an_int", str)
        backend.sync()

        @widget
        class TypeMismatchWidget(Widget):
            count: Setting[int] = new(42)

        w = TypeMismatchWidget()
        # Should use default because "not_an_int" can't be converted to int
        assert w.count.value == 42  # Falls back to default

    def test_incompatible_dataclass_uses_default(self) -> None:
        """When stored JSON doesn't match dataclass, use default."""

        @dataclass
        class NewConfig:
            name: str = ""
            new_field: int = 0  # This field won't exist in stored data

        backend = get_settings_backend()

        # Store JSON that's missing the new_field
        backend._qsettings.setValue("IncompatibleWidget:config", '{"name": "old", "old_field": 123}')
        backend.sync()

        @widget
        class IncompatibleWidget(Widget):
            config: Setting[NewConfig] = new(NewConfig())

        w = IncompatibleWidget()
        # Should reconstruct with available fields, missing ones get defaults
        assert w.config.value.name == "old"
        assert w.config.value.new_field == 0  # Default value

    def test_corrupted_json_uses_default(self) -> None:
        """When stored value is corrupted JSON, use default."""

        @dataclass
        class CorruptConfig:
            name: str = "default"

        backend = get_settings_backend()

        # Store invalid JSON
        backend._qsettings.setValue("CorruptWidget:config", "not valid json {{{")
        backend.sync()

        @widget
        class CorruptWidget(Widget):
            config: Setting[CorruptConfig] = new(CorruptConfig())

        # This should not crash - should use default
        try:
            w = CorruptWidget()
            # If we get here, it handled the error gracefully
            # Check if it used default
            assert w.config.value.name == "default"
        except Exception as e:
            # If it crashes, that's a bug we should fix
            pytest.fail(f"Corrupted JSON caused crash: {e}")


class TestSettingEdgeCases:
    """Test edge cases and potential issues."""

    def test_special_characters_in_key(self) -> None:
        """Keys with special characters work correctly."""

        @widget
        class SpecialCharsWidget(Widget):
            my_setting: Setting[str] = new("default")

        w = SpecialCharsWidget()
        w.my_setting.value = "test"

        backend = get_settings_backend()
        # Key should be "SpecialCharsWidget:my_setting"
        stored = backend.get("SpecialCharsWidget:my_setting", "", str)
        assert stored == "test"

    def test_unicode_values(self) -> None:
        """Unicode values are preserved."""

        @widget
        class UnicodeWidget(Widget):
            text: Setting[str] = new("")

        w = UnicodeWidget()
        w.text.value = "Hello 世界 🌍 émojis"

        backend = get_settings_backend()
        stored = backend.get("UnicodeWidget:text", "", str)
        assert stored == "Hello 世界 🌍 émojis"

    def test_empty_list_persists(self) -> None:
        """Empty list is distinguishable from missing key."""

        @widget
        class EmptyListWidget(Widget):
            items: Setting[list[str]] = new(["initial"])

        w = EmptyListWidget()
        w.items.value = []  # Set to empty

        backend = get_settings_backend()
        stored = backend.get("EmptyListWidget:items", ["default"], list[str])
        assert stored == []  # Should be empty, not default

    def test_empty_dict_persists(self) -> None:
        """Empty dict is distinguishable from missing key."""

        @widget
        class EmptyDictWidget(Widget):
            data: Setting[dict[str, int]] = new({"initial": 1})

        w = EmptyDictWidget()
        w.data.value = {}  # Set to empty

        backend = get_settings_backend()
        stored = backend.get("EmptyDictWidget:data", {"default": 0}, dict[str, int])
        assert stored == {}  # Should be empty, not default

    def test_false_bool_persists(self) -> None:
        """False boolean is distinguishable from missing key."""

        @widget
        class FalseBoolWidget(Widget):
            flag: Setting[bool] = new(True)

        w = FalseBoolWidget()
        w.flag.value = False

        backend = get_settings_backend()
        stored = backend.get("FalseBoolWidget:flag", True, bool)
        assert stored is False  # Should be False, not default True

    def test_zero_int_persists(self) -> None:
        """Zero integer is distinguishable from missing key."""

        @widget
        class ZeroIntWidget(Widget):
            count: Setting[int] = new(999)

        w = ZeroIntWidget()
        w.count.value = 0

        backend = get_settings_backend()
        stored = backend.get("ZeroIntWidget:count", 999, int)
        assert stored == 0  # Should be 0, not default 999


class TestSettingAugmentedAssignment:
    """Test augmented assignment operators."""

    def test_setting_augmented_add(self) -> None:
        """Setting += persists."""

        @widget
        class AugAddWidget(Widget):
            count: Setting[int] = new(10)

        w = AugAddWidget()
        w.count += 5

        backend = get_settings_backend()
        assert backend.get("AugAddWidget:count", 0, int) == 15

    def test_setting_augmented_list_extend(self) -> None:
        """Setting list += persists."""

        @widget
        class AugListWidget(Widget):
            items: Setting[list[str]] = new([])

        w = AugListWidget()
        w.items += ["a", "b"]

        backend = get_settings_backend()
        assert backend.get("AugListWidget:items", [], list[str]) == ["a", "b"]


class TestSettingNestedGroups:
    """Test nested group syntax."""

    def test_nested_group_key(self) -> None:
        """Nested group like 'ui:theme:colors' works."""

        @widget
        class NestedGroupWidget(Widget):
            primary: Setting[str] = new("#000", group="ui:theme:colors")

        w = NestedGroupWidget()
        w.primary.value = "#fff"

        backend = get_settings_backend()
        assert backend.get("ui:theme:colors:primary", "", str) == "#fff"


class TestSettingValidation:
    """Test Setting works with validators."""

    def test_setting_with_validator(self) -> None:
        """Setting supports validation like Variable."""

        @widget
        class ValidatedWidget(Widget):
            age: Setting[int] = new(0)

            def __setup__(self) -> None:
                self.add_validator("age", "positive", lambda v: None if v >= 0 else "Must be positive")

        w = ValidatedWidget()
        w.age.value = 25
        assert w.is_valid

        w.age.value = -5
        assert not w.is_valid
        assert "Must be positive" in w.validation_error_messages.get()


class TestSettingsBackend:
    """Test SettingsBackend directly."""

    def test_backend_serialization(self) -> None:
        """Backend correctly serializes/deserializes types."""
        backend = SettingsBackend()

        # Primitives
        backend.set("test:int", 42, int)
        assert backend.get("test:int", 0, int) == 42

        backend.set("test:str", "hello", str)
        assert backend.get("test:str", "", str) == "hello"

        backend.set("test:bool", True, bool)
        assert backend.get("test:bool", False, bool) is True

        # None
        backend.set("test:none", None, str | None)
        assert backend.get("test:none", "default", str | None) is None

    def test_backend_dataclass_serialization(self) -> None:
        """Backend correctly serializes/deserializes dataclasses."""

        @dataclass
        class Point:
            x: int = 0
            y: int = 0

        backend = SettingsBackend()
        backend.set("test:point", Point(10, 20), Point)

        loaded = backend.get("test:point", Point(), Point)
        assert loaded.x == 10
        assert loaded.y == 20

    def test_backend_enum_serialization(self) -> None:
        """Backend correctly serializes/deserializes enums."""

        class Color(Enum):
            RED = 1
            GREEN = 2
            BLUE = 3

        backend = SettingsBackend()
        backend.set("test:color", Color.GREEN, Color)

        loaded = backend.get("test:color", Color.RED, Color)
        assert loaded == Color.GREEN
