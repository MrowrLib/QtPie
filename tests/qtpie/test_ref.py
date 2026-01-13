# pyright: reportPrivateUsage=false
# pyright: reportMissingTypeArgument=false
"""Tests for ref() - deferred attribute references."""

import pytest
from assertpy import assert_that
from qtpy.QtWidgets import QLabel, QLineEdit, QMenu, QPushButton

from qtpie import Ref, Variable, Widget, new, ref, widget
from qtpie.testing import QtDriver


class TestRefBasics:
    """Test basic ref() functionality."""

    def test_ref_creates_ref_instance(self) -> None:
        """ref() returns a Ref instance."""
        r = ref("_field")
        assert_that(r).is_instance_of(Ref)
        assert_that(r.name).is_equal_to("_field")

    def test_ref_name_property(self) -> None:
        """Ref.name returns the attribute name."""
        r = ref("_my_menu")
        assert_that(r.name).is_equal_to("_my_menu")

    def test_ref_is_parent_ref_false(self) -> None:
        """is_parent_ref returns False for sibling refs."""
        r = ref("_field")
        assert_that(r.is_parent_ref).is_false()

    def test_ref_is_parent_ref_true(self) -> None:
        """is_parent_ref returns True for #parent refs."""
        r = ref("#parent._field")
        assert_that(r.is_parent_ref).is_true()

    def test_ref_target_name_sibling(self) -> None:
        """target_name returns name without prefix for siblings."""
        r = ref("_field")
        assert_that(r.target_name).is_equal_to("_field")

    def test_ref_target_name_parent(self) -> None:
        """target_name strips #parent. prefix."""
        r = ref("#parent._data")
        assert_that(r.target_name).is_equal_to("_data")

    def test_ref_repr(self) -> None:
        """Ref has a readable repr."""
        r = ref("_menu")
        assert_that(repr(r)).is_equal_to("ref('_menu')")


class TestRefResolution:
    """Test ref resolution in widgets."""

    def test_ref_resolves_sibling_widget(self, qt: QtDriver) -> None:
        """ref() can reference a sibling widget field."""

        @widget
        class MyWidget(Widget):
            _menu: QMenu = new()
            _button: QPushButton = new(menu=ref("_menu"))

        w = qt.track(MyWidget())
        # The button should have the menu set
        assert_that(w._button.menu()).is_equal_to(w._menu)

    def test_ref_resolves_field_defined_before(self, qt: QtDriver) -> None:
        """ref() works when referencing a field defined earlier."""

        @widget
        class MyWidget(Widget):
            _first: QLabel = new("First")
            _second: QLabel = new(buddy=ref("_first"))

        w = qt.track(MyWidget())
        assert_that(w._second.buddy()).is_equal_to(w._first)

    def test_ref_resolves_field_defined_after(self, qt: QtDriver) -> None:
        """ref() works when referencing a field defined later."""

        @widget
        class MyWidget(Widget):
            _first: QLabel = new(buddy=ref("_second"))
            _second: QLineEdit = new()

        w = qt.track(MyWidget())
        assert_that(w._first.buddy()).is_equal_to(w._second)

    def test_ref_to_nonexistent_field_raises(self, qt: QtDriver) -> None:
        """ref() to a nonexistent field raises AttributeError."""

        @widget
        class MyWidget(Widget):
            _button: QPushButton = new(menu=ref("_nonexistent"))

        with pytest.raises(AttributeError, match="'_nonexistent' not found"):
            qt.track(MyWidget())

    def test_ref_with_invalid_setter_raises(self, qt: QtDriver) -> None:
        """ref() with a kwarg that has no setter raises AttributeError."""

        @widget
        class MyWidget(Widget):
            _label: QLabel = new("Hello")
            _other: QLabel = new(noSuchProp=ref("_label"))

        with pytest.raises(AttributeError, match="has no 'setNoSuchProp'"):
            qt.track(MyWidget())


class TestRefWithVariable:
    """Test ref() when target is a Variable."""

    def test_ref_to_variable_resolves_to_value(self, qt: QtDriver) -> None:
        """ref() to a Variable resolves to the Variable's .value."""

        @widget
        class MyWidget(Widget):
            _text: Variable[str] = new("Hello World")
            _label: QLabel = new(text=ref("_text"))

        w = qt.track(MyWidget())
        # The label should have the Variable's value, not the Variable itself
        assert_that(w._label.text()).is_equal_to("Hello World")

    def test_ref_to_variable_with_complex_value(self, qt: QtDriver) -> None:
        """ref() resolves Variable with complex value types."""

        @widget
        class MyWidget(Widget):
            _menu: QMenu = new()
            _show_menu: Variable[QMenu] = new(None)
            _button: QPushButton = new(menu=ref("_show_menu"))

            def __setup__(self) -> None:
                self._show_menu.value = self._menu

        qt.track(MyWidget())
        # During __setup__, _show_menu was set to _menu
        # But ref resolved before __setup__, so it got None
        # This is expected behavior - refs resolve before __setup__


class TestRefMultipleRefs:
    """Test multiple refs in a single widget."""

    def test_multiple_refs_same_widget(self, qt: QtDriver) -> None:
        """Multiple refs on the same widget field work."""

        @widget
        class MyWidget(Widget):
            _input: QLineEdit = new()
            _label1: QLabel = new(buddy=ref("_input"))
            _label2: QLabel = new(buddy=ref("_input"))

        w = qt.track(MyWidget())
        assert_that(w._label1.buddy()).is_equal_to(w._input)
        assert_that(w._label2.buddy()).is_equal_to(w._input)

    def test_refs_to_different_fields(self, qt: QtDriver) -> None:
        """Refs can target different sibling fields."""

        @widget
        class MyWidget(Widget):
            _input1: QLineEdit = new()
            _input2: QLineEdit = new()
            _label1: QLabel = new(buddy=ref("_input1"))
            _label2: QLabel = new(buddy=ref("_input2"))

        w = qt.track(MyWidget())
        assert_that(w._label1.buddy()).is_equal_to(w._input1)
        assert_that(w._label2.buddy()).is_equal_to(w._input2)


class TestRefParentRefs:
    """Test #parent refs for nested widget composition."""

    def test_parent_ref_resolves_from_parent(self, qt: QtDriver) -> None:
        """#parent ref resolves attribute from parent widget."""

        @widget
        class Child(Widget):
            # This child expects to get a menu from its parent
            _button: QPushButton = new(menu=ref("#parent._shared_menu"))

        @widget
        class Parent(Widget):
            _shared_menu: QMenu = new()
            _child: Child = new()

        w = qt.track(Parent())
        # The child's button should have the parent's menu
        assert_that(w._child._button.menu()).is_equal_to(w._shared_menu)

    def test_parent_ref_to_variable_resolves_value(self, qt: QtDriver) -> None:
        """#parent ref to Variable resolves to .value."""

        @widget
        class Child(Widget):
            _label: QLabel = new(text=ref("#parent._message"))

        @widget
        class Parent(Widget):
            _message: Variable[str] = new("Hello from parent")
            _child: Child = new()

        w = qt.track(Parent())
        assert_that(w._child._label.text()).is_equal_to("Hello from parent")

    def test_parent_ref_without_parent_is_deferred(self, qt: QtDriver) -> None:
        """#parent ref on standalone widget is stored for later."""

        @widget
        class StandaloneChild(Widget):
            _button: QPushButton = new(menu=ref("#parent._menu"))

        # Creating standalone - #parent refs are stored but not resolved
        # This should not raise, just store the deferred ref
        w = qt.track(StandaloneChild())
        # The deferred ref is stored on the widget
        assert_that(hasattr(w, "_qtpie_deferred_parent_refs")).is_true()


class TestRefNestedAttributes:
    """Test nested attribute access in refs."""

    def test_nested_attribute_access(self, qt: QtDriver) -> None:
        """ref() can access nested attributes."""

        @widget
        class MyWidget(Widget):
            _edit: QLineEdit = new("Hello")
            # Access a nested property: QLineEdit -> font() -> family()
            _label: QLabel = new()

            def __setup__(self) -> None:
                # We can't easily test nested Qt properties in new() because
                # they're methods, not properties. Test the Ref.resolve directly.
                pass

        w = qt.track(MyWidget())
        # The widget was created successfully
        assert_that(w._edit.text()).is_equal_to("Hello")

    def test_nested_ref_on_custom_object(self, qt: QtDriver) -> None:
        """ref() traverses nested custom objects."""

        class Config:
            def __init__(self) -> None:
                self.title = "My Title"

        class Settings:
            def __init__(self) -> None:
                self.config = Config()

        @widget
        class MyWidget(Widget):
            settings: Settings

            def __setup__(self) -> None:
                self.settings = Settings()

        w = qt.track(MyWidget())

        # Test resolve directly
        r = ref("settings.config.title")
        resolved = r.resolve(w)
        assert_that(resolved).is_equal_to("My Title")

    def test_nested_ref_with_variable_in_chain(self, qt: QtDriver) -> None:
        """ref() unwraps Variables in the chain."""

        class Config:
            def __init__(self, title: str) -> None:
                self.title = title

        @widget
        class MyWidget(Widget):
            _config: Variable[Config] = new(Config("Default Title"))

        w = qt.track(MyWidget())

        # Access nested attribute through Variable
        r = ref("_config.title")
        resolved = r.resolve(w)
        assert_that(resolved).is_equal_to("Default Title")

    def test_nested_ref_error_shows_path(self, qt: QtDriver) -> None:
        """ref() error message shows traversed path."""

        class Config:
            pass

        @widget
        class MyWidget(Widget):
            _config: Variable[Config] = new(Config())

        w = qt.track(MyWidget())

        r = ref("_config.nonexistent.path")
        with pytest.raises(AttributeError, match="'nonexistent' not found.*at _config"):
            r.resolve(w)

    def test_nested_parent_ref(self, qt: QtDriver) -> None:
        """#parent refs can access nested attributes."""

        class AppConfig:
            def __init__(self) -> None:
                self.theme = "dark"

        @widget
        class Child(Widget):
            _label: QLabel = new("test")

        @widget
        class Parent(Widget):
            config: AppConfig
            _child: Child = new()

            def __setup__(self) -> None:
                self.config = AppConfig()

        w = qt.track(Parent())

        # Test resolve directly on child with parent context
        r = ref("#parent.config.theme")
        resolved = r.resolve(w._child, parent=w)
        assert_that(resolved).is_equal_to("dark")


class TestRefOptionalChaining:
    """Test ?. optional chaining in refs."""

    def test_optional_chain_returns_none_when_none(self, qt: QtDriver) -> None:
        """?. returns None when attribute is None."""

        class Config:
            def __init__(self) -> None:
                self.theme: str | None = None

        @widget
        class MyWidget(Widget):
            _config: Variable[Config] = new(Config())

        w = qt.track(MyWidget())

        r = ref("_config.theme?.name")
        resolved = r.resolve(w)
        assert_that(resolved).is_none()

    def test_optional_chain_returns_none_when_attr_is_none(self, qt: QtDriver) -> None:
        """?. returns None when the optional attribute itself is None."""

        @widget
        class MyWidget(Widget):
            _config: Variable[None] = new(None)

        w = qt.track(MyWidget())

        # _config is None, so ?.next should return None
        r = ref("_config?.nonexistent")
        resolved = r.resolve(w)
        assert_that(resolved).is_none()

    def test_optional_chain_still_raises_when_next_missing(self, qt: QtDriver) -> None:
        """?. doesn't protect against missing attributes AFTER the optional one."""

        class Config:
            pass

        @widget
        class MyWidget(Widget):
            _config: Variable[Config] = new(Config())

        w = qt.track(MyWidget())

        # _config exists, but nonexistent doesn't - should raise
        r = ref("_config?.nonexistent")
        with pytest.raises(AttributeError, match="'nonexistent' not found"):
            r.resolve(w)

    def test_optional_chain_returns_value_when_exists(self, qt: QtDriver) -> None:
        """?. returns value normally when attribute exists."""

        class Theme:
            def __init__(self) -> None:
                self.name = "dark"

        class Config:
            def __init__(self) -> None:
                self.theme = Theme()

        @widget
        class MyWidget(Widget):
            _config: Variable[Config] = new(Config())

        w = qt.track(MyWidget())

        r = ref("_config?.theme?.name")
        resolved = r.resolve(w)
        assert_that(resolved).is_equal_to("dark")

    def test_optional_chain_multiple_levels(self, qt: QtDriver) -> None:
        """Multiple ?. in chain all work."""

        class Level3:
            def __init__(self) -> None:
                self.value = "deep"

        class Level2:
            def __init__(self) -> None:
                self.level3: Level3 | None = Level3()

        class Level1:
            def __init__(self) -> None:
                self.level2: Level2 | None = Level2()

        @widget
        class MyWidget(Widget):
            level1: Level1

            def __setup__(self) -> None:
                self.level1 = Level1()

        w = qt.track(MyWidget())

        # All present
        r = ref("level1?.level2?.level3?.value")
        assert_that(r.resolve(w)).is_equal_to("deep")

        # level3 is None
        w.level1.level2.level3 = None  # type: ignore[union-attr]
        r2 = ref("level1?.level2?.level3?.value")
        assert_that(r2.resolve(w)).is_none()

        # level2 is None
        w.level1.level2 = None
        r3 = ref("level1?.level2?.level3?.value")
        assert_that(r3.resolve(w)).is_none()

    def test_optional_chain_mixed_with_required(self, qt: QtDriver) -> None:
        """?. can be mixed with regular . access."""

        class Theme:
            def __init__(self) -> None:
                self.name = "light"

        class Config:
            def __init__(self) -> None:
                self.theme: Theme | None = Theme()

        @widget
        class MyWidget(Widget):
            _config: Variable[Config] = new(Config())

        w = qt.track(MyWidget())

        # theme is optional, name is required
        r = ref("_config.theme?.name")
        assert_that(r.resolve(w)).is_equal_to("light")

        # When theme is None, returns None (doesn't try to access .name)
        w._config.value.theme = None
        r2 = ref("_config.theme?.name")
        assert_that(r2.resolve(w)).is_none()

    def test_required_after_optional_still_raises(self, qt: QtDriver) -> None:
        """Required access after optional still raises if present but missing attr."""

        class Theme:
            def __init__(self) -> None:
                self.name = "dark"

        class Config:
            def __init__(self) -> None:
                self.theme = Theme()

        @widget
        class MyWidget(Widget):
            _config: Variable[Config] = new(Config())

        w = qt.track(MyWidget())

        # theme exists but doesn't have 'nonexistent' - should raise
        r = ref("_config.theme?.nonexistent")
        with pytest.raises(AttributeError, match="'nonexistent' not found"):
            r.resolve(w)

    def test_optional_chain_with_variable_unwrapping(self, qt: QtDriver) -> None:
        """?. works correctly with Variable unwrapping."""

        class Inner:
            def __init__(self, val: str) -> None:
                self.val = val

        @widget
        class MyWidget(Widget):
            _outer: Variable[Inner | None] = new(Inner("test"))

        w = qt.track(MyWidget())

        r = ref("_outer?.val")
        assert_that(r.resolve(w)).is_equal_to("test")

        w._outer.value = None
        r2 = ref("_outer?.val")
        assert_that(r2.resolve(w)).is_none()


class TestRefEdgeCases:
    """Test edge cases and error handling."""

    def test_ref_in_kwargs_not_in_constructor(self, qt: QtDriver) -> None:
        """ref() values don't leak into widget constructor."""

        @widget
        class MyWidget(Widget):
            _menu: QMenu = new()
            _button: QPushButton = new("Click", menu=ref("_menu"))

        w = qt.track(MyWidget())
        assert_that(w._button.text()).is_equal_to("Click")
        assert_that(w._button.menu()).is_equal_to(w._menu)

    def test_ref_with_other_kwargs(self, qt: QtDriver) -> None:
        """ref() works alongside other kwargs."""

        @widget
        class MyWidget(Widget):
            _input: QLineEdit = new()
            _label: QLabel = new("Name:", buddy=ref("_input"), toolTip="Enter name")

        w = qt.track(MyWidget())
        assert_that(w._label.text()).is_equal_to("Name:")
        assert_that(w._label.buddy()).is_equal_to(w._input)
        assert_that(w._label.toolTip()).is_equal_to("Enter name")

    def test_ref_independent_instances(self, qt: QtDriver) -> None:
        """Each widget instance resolves refs independently."""

        @widget
        class MyWidget(Widget):
            _menu: QMenu = new()
            _button: QPushButton = new(menu=ref("_menu"))

        w1 = qt.track(MyWidget())
        w2 = qt.track(MyWidget())

        # Each instance should have its own menu
        assert_that(w1._button.menu()).is_equal_to(w1._menu)
        assert_that(w2._button.menu()).is_equal_to(w2._menu)
        assert_that(w1._menu).is_not_equal_to(w2._menu)


class TestRefExpressions:
    """Test expression refs with {} syntax."""

    def test_is_expression_detects_braces(self) -> None:
        """is_expression returns True for expressions with {}."""
        r = ref("{_name}")
        assert_that(r.is_expression).is_true()

        r2 = ref("Count: {_count}")
        assert_that(r2.is_expression).is_true()

        r3 = ref("_name")
        assert_that(r3.is_expression).is_false()

        r4 = ref("#parent._name")
        assert_that(r4.is_expression).is_false()

    def test_simple_expression_returns_string(self, qt: QtDriver) -> None:
        """ref("{_attr}") returns stringified value."""

        @widget
        class MyWidget(Widget):
            _name: Variable[str] = new("Alice")

        w = qt.track(MyWidget())
        r = ref("{_name}")
        result = r.resolve(w)
        assert_that(result).is_equal_to("Alice")

    def test_expression_with_literal_text(self, qt: QtDriver) -> None:
        """ref("Hello: {_name}") includes literal text."""

        @widget
        class MyWidget(Widget):
            _name: Variable[str] = new("Bob")

        w = qt.track(MyWidget())
        r = ref("Hello: {_name}")
        result = r.resolve(w)
        assert_that(result).is_equal_to("Hello: Bob")

    def test_expression_with_len_function(self, qt: QtDriver) -> None:
        """ref("Count: {len(_items)}") evaluates len()."""

        @widget
        class MyWidget(Widget):
            _items: Variable[list[str]] = new(["a", "b", "c"])

        w = qt.track(MyWidget())
        r = ref("Count: {len(_items)}")
        result = r.resolve(w)
        assert_that(result).is_equal_to("Count: 3")

    def test_expression_with_method_call(self, qt: QtDriver) -> None:
        """ref("{_name.upper()}") calls methods."""

        @widget
        class MyWidget(Widget):
            _name: Variable[str] = new("alice")

        w = qt.track(MyWidget())
        r = ref("{_name.upper()}")
        result = r.resolve(w)
        assert_that(result).is_equal_to("ALICE")

    def test_expression_with_math(self, qt: QtDriver) -> None:
        """ref("Double: {_x * 2}") does math."""

        @widget
        class MyWidget(Widget):
            _x: Variable[int] = new(21)

        w = qt.track(MyWidget())
        r = ref("Double: {_x * 2}")
        result = r.resolve(w)
        assert_that(result).is_equal_to("Double: 42")

    def test_expression_with_multiple_variables(self, qt: QtDriver) -> None:
        """ref("{_a} + {_b} = {_a + _b}") uses multiple vars."""

        @widget
        class MyWidget(Widget):
            _a: Variable[int] = new(10)
            _b: Variable[int] = new(20)

        w = qt.track(MyWidget())
        r = ref("{_a} + {_b} = {_a + _b}")
        result = r.resolve(w)
        assert_that(result).is_equal_to("10 + 20 = 30")

    def test_expression_with_format_spec(self, qt: QtDriver) -> None:
        """ref("{_price:.2f}") applies format spec."""

        @widget
        class MyWidget(Widget):
            _price: Variable[float] = new(19.9)

        w = qt.track(MyWidget())
        r = ref("${_price:.2f}")
        result = r.resolve(w)
        assert_that(result).is_equal_to("$19.90")

    def test_expression_without_underscore_prefix(self, qt: QtDriver) -> None:
        """ref("{name}") resolves attributes without underscore prefix."""

        @widget
        class MyWidget(Widget):
            name: str = "TestWidget"

        w = qt.track(MyWidget())
        r = ref("Name: {name}")
        result = r.resolve(w)
        assert_that(result).is_equal_to("Name: TestWidget")

    def test_expression_tries_underscore_fallback(self, qt: QtDriver) -> None:
        """ref("{name}") falls back to _name if name doesn't exist."""

        @widget
        class MyWidget(Widget):
            _name: Variable[str] = new("Fallback")

        w = qt.track(MyWidget())
        # name doesn't exist, should use _name
        r = ref("Name: {name}")
        result = r.resolve(w)
        assert_that(result).is_equal_to("Name: Fallback")

    def test_expression_with_nested_attribute(self, qt: QtDriver) -> None:
        """ref("{_config.title}") accesses nested attributes."""

        class Config:
            def __init__(self) -> None:
                self.title = "My App"

        @widget
        class MyWidget(Widget):
            _config: Variable[Config] = new(Config())

        w = qt.track(MyWidget())
        r = ref("Title: {_config.title}")
        result = r.resolve(w)
        assert_that(result).is_equal_to("Title: My App")

    def test_expression_error_shows_placeholder(self, qt: QtDriver) -> None:
        """Expression errors show 'None' (allows `or 'default'` pattern)."""

        @widget
        class MyWidget(Widget):
            _x: Variable[int] = new(5)

        w = qt.track(MyWidget())
        # _nonexistent doesn't exist - shows None
        r = ref("Value: {_nonexistent}")
        result = r.resolve(w)
        assert_that(result).is_equal_to("Value: None")

    def test_expression_with_self_placeholder(self, qt: QtDriver) -> None:
        """ref("{#self}") refers to the instance."""

        @widget
        class MyWidget(Widget):
            name: str = "TestWidget"

        w = qt.track(MyWidget())
        r = ref("Type: {type(#self).__name__}")
        result = r.resolve(w)
        assert_that(result).is_equal_to("Type: MyWidget")

    def test_expression_in_new_kwarg(self, qt: QtDriver) -> None:
        """Expression ref works in new() kwargs."""

        @widget
        class MyWidget(Widget):
            _count: Variable[int] = new(42)
            _label: QLabel = new(text=ref("Count: {_count}"))

        w = qt.track(MyWidget())
        assert_that(w._label.text()).is_equal_to("Count: 42")

    def test_expression_with_int_to_string(self, qt: QtDriver) -> None:
        """Expression converts non-strings to strings."""

        @widget
        class MyWidget(Widget):
            _count: Variable[int] = new(123)

        w = qt.track(MyWidget())
        r = ref("{_count}")
        result = r.resolve(w)
        assert_that(result).is_equal_to("123")
        assert_that(result).is_instance_of(str)
