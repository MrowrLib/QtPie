# pyright: reportPrivateUsage=false
"""Tests for Variable bindings - passing state DOWN to child widgets."""

import pytest
from qtpy.QtWidgets import QApplication, QLabel

from qtpie import Variable, Widget, new, widget


# Ensure QApplication exists for widget tests
@pytest.fixture(scope="module", autouse=True)
def app():
    """Create QApplication for tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


# =============================================================================
# A.1: Detect Bare Variable Annotations
# =============================================================================


def test_bare_variable_detected_as_required():
    """Bare Variable[T] (no = new()) is a required binding."""

    @widget
    class Child(Widget):
        count: Variable[int]  # No = new()

    assert "count" in Child._qtpie_config.required_bindings


def test_variable_with_default_is_optional():
    """Variable[T] = new(default) is optional (has a default)."""

    @widget
    class Child(Widget):
        count: Variable[int] = new(0)

    assert "count" not in Child._qtpie_config.required_bindings


def test_multiple_required_bindings():
    """Multiple bare Variables are all detected."""

    @widget
    class Child(Widget):
        count: Variable[int]
        name: Variable[str]
        enabled: Variable[bool]

    assert Child._qtpie_config.required_bindings == {"count", "name", "enabled"}


def test_mixed_required_and_optional():
    """Mix of required (bare) and optional (with default) Variables."""

    @widget
    class Child(Widget):
        required_var: Variable[int]  # Required
        optional_var: Variable[str] = new("default")  # Optional
        another_required: Variable[bool]  # Required

    assert Child._qtpie_config.required_bindings == {"required_var", "another_required"}


def test_non_variable_annotations_ignored():
    """Non-Variable annotations should not be detected as bindings."""

    @widget
    class Child(Widget):
        count: Variable[int]  # Required binding
        label: QLabel = new("Hello")  # Regular widget, not a binding

    assert Child._qtpie_config.required_bindings == {"count"}


# =============================================================================
# A.2: Store Required/Optional Bindings in Config
# =============================================================================


def test_config_tracks_required_bindings():
    """Config stores set of required binding names."""

    @widget
    class Child(Widget):
        required_var: Variable[int]
        optional_var: Variable[str] = new("default")

    assert Child._qtpie_config.required_bindings == {"required_var"}
    # optional_bindings will be tested when we track defaults


# =============================================================================
# A.3: Accept Bindings via new() kwargs - will test after implementation
# =============================================================================


# =============================================================================
# A.4: Validate Required Bindings at Instantiation
# =============================================================================


def test_missing_required_binding_raises_error_on_access():
    """Accessing unresolved bare Variable raises error."""

    @widget
    class Child(Widget):
        count: Variable[int]  # Required - but not in parent hierarchy

    @widget
    class Parent(Widget):
        child: Child = new()  # No matching 'count' Variable on parent

    # Widget creation succeeds, but accessing the unresolved Variable fails
    parent = Parent()
    with pytest.raises(AttributeError, match="'count' requires a binding"):
        _ = parent.child.count  # Access triggers resolution attempt


def test_all_bindings_provided_no_error():
    """When all required bindings are provided, no error."""

    @widget
    class Child(Widget):
        count: Variable[int]

    @widget
    class Parent(Widget):
        _my_count: Variable[int] = new(0)
        child: Child = new(count="_my_count")

    # Should not raise
    parent = Parent()
    assert parent.child is not None


def test_optional_binding_not_required():
    """Optional bindings (with defaults) don't need to be provided."""

    @widget
    class Child(Widget):
        count: Variable[int] = new(42)  # Optional with default

    @widget
    class Parent(Widget):
        child: Child = new()  # No binding provided, uses default

    parent = Parent()
    assert parent.child.count.value == 42


# =============================================================================
# A.5: Create Reactive Binding Between Parent and Child Variables
# =============================================================================


def test_bound_variable_syncs_with_parent():
    """Child variable bound to parent updates when parent changes."""

    @widget
    class Child(Widget):
        count: Variable[int]

    @widget
    class Parent(Widget):
        _my_count: Variable[int] = new(0)
        child: Child = new(count="_my_count")

    parent = Parent()

    # Initially synced
    assert parent.child.count.value == 0

    # Parent changes -> child updates
    parent._my_count.value = 42
    assert parent.child.count.value == 42


def test_two_way_binding():
    """Child variable changes propagate back to parent."""

    @widget
    class Child(Widget):
        count: Variable[int]

    @widget
    class Parent(Widget):
        _my_count: Variable[int] = new(0)
        child: Child = new(count="_my_count")

    parent = Parent()

    # Child changes -> parent updates (two-way!)
    parent.child.count.value = 100
    assert parent._my_count.value == 100


# =============================================================================
# A.6: Support Expression Bindings
# =============================================================================


def test_expression_binding():
    """Expression binding like '{len(_items) > 0}' creates one-way computed binding."""

    @widget
    class Child(Widget):
        enabled: Variable[bool]

    @widget
    class Parent(Widget):
        _items: Variable[list[str]] = new([])
        child: Child = new(enabled="{len(_items) > 0}")

    parent = Parent()
    assert parent.child.enabled.value is False

    parent._items.value = ["a", "b"]
    assert parent.child.enabled.value is True


# =============================================================================
# A.7: Support Literal Values
# =============================================================================


def test_literal_value_sets_default():
    """Literal value (not a binding) sets the Variable's default."""

    @widget
    class Child(Widget):
        label_text: Variable[str]

    @widget
    class Parent(Widget):
        # "Hello" doesn't start with _ or contain {}, so it's a literal
        child: Child = new(label_text="Hello")

    parent = Parent()
    assert parent.child.label_text.value == "Hello"


def test_literal_int_value():
    """Literal int value sets the Variable's default."""

    @widget
    class Child(Widget):
        count: Variable[int]

    @widget
    class Parent(Widget):
        child: Child = new(count=42)

    parent = Parent()
    assert parent.child.count.value == 42


# =============================================================================
# A.8: Nested Widget Bindings (Pass-Through)
# =============================================================================


def test_nested_binding_passthrough():
    """Bindings can pass through intermediate widgets."""

    @widget
    class GrandChild(Widget):
        theme: Variable[str]

    @widget
    class Child(Widget):
        theme: Variable[str]  # Required, will pass to grandchild
        grandchild: GrandChild = new(theme="theme")  # Pass our theme down

    @widget
    class Parent(Widget):
        _theme: Variable[str] = new("dark")
        child: Child = new(theme="_theme")

    parent = Parent()
    assert parent.child.grandchild.theme.value == "dark"

    # Changes propagate through the chain
    parent._theme.value = "light"
    assert parent.child.grandchild.theme.value == "light"


# =============================================================================
# COMPREHENSIVE NESTED BINDING TESTS
# These tests stress-test the nested binding solution to catch timing issues
# =============================================================================


def test_nested_passthrough_with_format_binding():
    """
    Exact scenario from sample: GrandChild has format binding using required theme.
    This was the bug: format binding evaluated before theme was set.
    """

    @widget
    class GrandChild(Widget):
        theme: Variable[str]
        _label: QLabel = new(bind="Theme: {theme}")

    @widget
    class Child(Widget):
        theme: Variable[str]  # Required, passed to grandchild
        grandchild: GrandChild = new(theme="theme")

    @widget
    class Parent(Widget):
        _theme: Variable[str] = new("dark")
        child: Child = new(theme="_theme")

    parent = Parent()

    # Format binding should work
    assert parent.child.grandchild._label.text() == "Theme: dark"

    # Updates should propagate
    parent._theme.value = "light"
    assert parent.child.grandchild._label.text() == "Theme: light"


def test_three_level_nesting_with_format_binding():
    """Three levels of nesting with format binding at the deepest level."""

    @widget
    class Level3(Widget):
        value: Variable[str]
        _label: QLabel = new(bind="Value: {value}")

    @widget
    class Level2(Widget):
        value: Variable[str]
        level3: Level3 = new(value="value")

    @widget
    class Level1(Widget):
        value: Variable[str]
        level2: Level2 = new(value="value")

    @widget
    class Root(Widget):
        _value: Variable[str] = new("root")
        level1: Level1 = new(value="_value")

    root = Root()
    assert root.level1.level2.level3._label.text() == "Value: root"

    root._value.value = "changed"
    assert root.level1.level2.level3._label.text() == "Value: changed"


def test_four_level_nesting():
    """Four levels deep to stress test timing."""

    @widget
    class Level4(Widget):
        data: Variable[int]
        _label: QLabel = new(bind="Data: {data}")

    @widget
    class Level3(Widget):
        data: Variable[int]
        level4: Level4 = new(data="data")

    @widget
    class Level2(Widget):
        data: Variable[int]
        level3: Level3 = new(data="data")

    @widget
    class Level1(Widget):
        data: Variable[int]
        level2: Level2 = new(data="data")

    @widget
    class Root(Widget):
        _data: Variable[int] = new(42)
        level1: Level1 = new(data="_data")

    root = Root()
    assert root.level1.level2.level3.level4._label.text() == "Data: 42"

    root._data.value = 100
    assert root.level1.level2.level3.level4._label.text() == "Data: 100"


def test_five_level_nesting():
    """Five levels deep - extreme nesting test."""

    @widget
    class Level5(Widget):
        msg: Variable[str]
        _label: QLabel = new(bind="{msg}!")

    @widget
    class Level4(Widget):
        msg: Variable[str]
        level5: Level5 = new(msg="msg")

    @widget
    class Level3(Widget):
        msg: Variable[str]
        level4: Level4 = new(msg="msg")

    @widget
    class Level2(Widget):
        msg: Variable[str]
        level3: Level3 = new(msg="msg")

    @widget
    class Level1(Widget):
        msg: Variable[str]
        level2: Level2 = new(msg="msg")

    @widget
    class Root(Widget):
        _msg: Variable[str] = new("hello")
        level1: Level1 = new(msg="_msg")

    root = Root()
    assert root.level1.level2.level3.level4.level5._label.text() == "hello!"


def test_multiple_required_bindings_at_each_level():
    """Multiple required bindings passed through each level."""

    @widget
    class GrandChild(Widget):
        name: Variable[str]
        count: Variable[int]
        enabled: Variable[bool]
        _label: QLabel = new(bind="{name}: {count} ({'on' if enabled else 'off'})")

    @widget
    class Child(Widget):
        name: Variable[str]
        count: Variable[int]
        enabled: Variable[bool]
        grandchild: GrandChild = new(name="name", count="count", enabled="enabled")

    @widget
    class Parent(Widget):
        _name: Variable[str] = new("test")
        _count: Variable[int] = new(5)
        _enabled: Variable[bool] = new(True)
        child: Child = new(name="_name", count="_count", enabled="_enabled")

    parent = Parent()
    assert parent.child.grandchild._label.text() == "test: 5 (on)"

    parent._name.value = "updated"
    parent._count.value = 10
    parent._enabled.value = False
    assert parent.child.grandchild._label.text() == "updated: 10 (off)"


def test_mixed_required_and_optional_nested():
    """Mix of required and optional bindings at different levels."""

    @widget
    class GrandChild(Widget):
        required_var: Variable[str]
        optional_var: Variable[str] = new("default")
        _label: QLabel = new(bind="{required_var} | {optional_var}")

    @widget
    class Child(Widget):
        required_var: Variable[str]
        # Only pass required, leave optional to use default
        grandchild: GrandChild = new(required_var="required_var")

    @widget
    class Parent(Widget):
        _value: Variable[str] = new("provided")
        child: Child = new(required_var="_value")

    parent = Parent()
    assert parent.child.grandchild._label.text() == "provided | default"


def test_optional_overridden_at_intermediate_level():
    """Optional binding overridden at intermediate level."""

    @widget
    class GrandChild(Widget):
        theme: Variable[str] = new("light")
        _label: QLabel = new(bind="Theme: {theme}")

    @widget
    class Child(Widget):
        theme: Variable[str]  # Required for Child, but GrandChild has default
        grandchild: GrandChild = new(theme="theme")  # Pass our theme

    @widget
    class Parent(Widget):
        _theme: Variable[str] = new("dark")
        child: Child = new(theme="_theme")

    parent = Parent()
    # GrandChild's default overridden by binding chain
    assert parent.child.grandchild._label.text() == "Theme: dark"


def test_siblings_with_same_required_binding():
    """Multiple siblings receiving the same binding."""

    @widget
    class ChildWidget(Widget):
        value: Variable[str]
        _label: QLabel = new(bind="{value}")

    @widget
    class Parent(Widget):
        _shared: Variable[str] = new("shared")
        child1: ChildWidget = new(value="_shared")
        child2: ChildWidget = new(value="_shared")
        child3: ChildWidget = new(value="_shared")

    parent = Parent()
    assert parent.child1._label.text() == "shared"
    assert parent.child2._label.text() == "shared"
    assert parent.child3._label.text() == "shared"

    parent._shared.value = "updated"
    assert parent.child1._label.text() == "updated"
    assert parent.child2._label.text() == "updated"
    assert parent.child3._label.text() == "updated"


def test_siblings_with_different_required_bindings():
    """Siblings with different required bindings."""

    @widget
    class ChildWidget(Widget):
        value: Variable[str]
        _label: QLabel = new(bind="{value}")

    @widget
    class Parent(Widget):
        _value1: Variable[str] = new("one")
        _value2: Variable[str] = new("two")
        _value3: Variable[str] = new("three")
        child1: ChildWidget = new(value="_value1")
        child2: ChildWidget = new(value="_value2")
        child3: ChildWidget = new(value="_value3")

    parent = Parent()
    assert parent.child1._label.text() == "one"
    assert parent.child2._label.text() == "two"
    assert parent.child3._label.text() == "three"


def test_complex_format_expression_with_required_binding():
    """Complex format expression using required binding."""

    @widget
    class GrandChild(Widget):
        items: Variable[list[str]]
        _label: QLabel = new(bind="Items: {len(items)} - {', '.join(items)}")

    @widget
    class Child(Widget):
        items: Variable[list[str]]
        grandchild: GrandChild = new(items="items")

    @widget
    class Parent(Widget):
        _items: Variable[list[str]] = new(["a", "b", "c"])
        child: Child = new(items="_items")

    parent = Parent()
    assert parent.child.grandchild._label.text() == "Items: 3 - a, b, c"


def test_nested_with_format_binding_and_expression():
    """Expression binding at intermediate level, format at leaf."""

    @widget
    class GrandChild(Widget):
        visible: Variable[bool]
        _label: QLabel = new(bind="{'Visible' if visible else 'Hidden'}")

    @widget
    class Child(Widget):
        count: Variable[int]
        grandchild: GrandChild = new(visible="{count > 0}")

    @widget
    class Parent(Widget):
        _count: Variable[int] = new(0)
        child: Child = new(count="_count")

    parent = Parent()
    assert parent.child.grandchild._label.text() == "Hidden"

    parent._count.value = 5
    assert parent.child.grandchild._label.text() == "Visible"


def test_format_binding_multiple_required_vars():
    """Format binding using multiple required variables."""

    @widget
    class GrandChild(Widget):
        first: Variable[str]
        last: Variable[str]
        age: Variable[int]
        _label: QLabel = new(bind="{first} {last}, age {age}")

    @widget
    class Child(Widget):
        first: Variable[str]
        last: Variable[str]
        age: Variable[int]
        grandchild: GrandChild = new(first="first", last="last", age="age")

    @widget
    class Parent(Widget):
        _first: Variable[str] = new("John")
        _last: Variable[str] = new("Doe")
        _age: Variable[int] = new(30)
        child: Child = new(first="_first", last="_last", age="_age")

    parent = Parent()
    assert parent.child.grandchild._label.text() == "John Doe, age 30"


def test_branching_nested_tree():
    """Tree structure with multiple branches, each with required bindings."""

    @widget
    class Leaf(Widget):
        value: Variable[str]
        _label: QLabel = new(bind="{value}")

    @widget
    class Branch(Widget):
        value: Variable[str]
        leaf1: Leaf = new(value="value")
        leaf2: Leaf = new(value="value")

    @widget
    class Root(Widget):
        _left: Variable[str] = new("left")
        _right: Variable[str] = new("right")
        branch_left: Branch = new(value="_left")
        branch_right: Branch = new(value="_right")

    root = Root()
    assert root.branch_left.leaf1._label.text() == "left"
    assert root.branch_left.leaf2._label.text() == "left"
    assert root.branch_right.leaf1._label.text() == "right"
    assert root.branch_right.leaf2._label.text() == "right"


def test_deep_nesting_with_format_at_multiple_levels():
    """Format bindings at multiple nesting levels."""

    @widget
    class Level3(Widget):
        msg: Variable[str]
        _label: QLabel = new(bind="L3: {msg}")

    @widget
    class Level2(Widget):
        msg: Variable[str]
        _label: QLabel = new(bind="L2: {msg}")  # Format at intermediate level too
        level3: Level3 = new(msg="msg")

    @widget
    class Level1(Widget):
        msg: Variable[str]
        _label: QLabel = new(bind="L1: {msg}")
        level2: Level2 = new(msg="msg")

    @widget
    class Root(Widget):
        _msg: Variable[str] = new("hello")
        level1: Level1 = new(msg="_msg")

    root = Root()
    assert root.level1._label.text() == "L1: hello"
    assert root.level1.level2._label.text() == "L2: hello"
    assert root.level1.level2.level3._label.text() == "L3: hello"

    root._msg.value = "world"
    assert root.level1._label.text() == "L1: world"
    assert root.level1.level2._label.text() == "L2: world"
    assert root.level1.level2.level3._label.text() == "L3: world"


def test_required_binding_with_none_initial():
    """Required binding where source starts as None-ish value."""

    @widget
    class GrandChild(Widget):
        text: Variable[str]
        _label: QLabel = new(bind="{text}")

    @widget
    class Child(Widget):
        text: Variable[str]
        grandchild: GrandChild = new(text="text")

    @widget
    class Parent(Widget):
        _text: Variable[str] = new("")
        child: Child = new(text="_text")

    parent = Parent()
    assert parent.child.grandchild._label.text() == ""

    parent._text.value = "now has value"
    assert parent.child.grandchild._label.text() == "now has value"


def test_required_binding_bool_false_initial():
    """Required bool binding starting as False."""

    @widget
    class GrandChild(Widget):
        flag: Variable[bool]
        _label: QLabel = new(bind="{'yes' if flag else 'no'}")

    @widget
    class Child(Widget):
        flag: Variable[bool]
        grandchild: GrandChild = new(flag="flag")

    @widget
    class Parent(Widget):
        _flag: Variable[bool] = new(False)
        child: Child = new(flag="_flag")

    parent = Parent()
    assert parent.child.grandchild._label.text() == "no"


def test_required_binding_int_zero_initial():
    """Required int binding starting as 0."""

    @widget
    class GrandChild(Widget):
        count: Variable[int]
        _label: QLabel = new(bind="Count: {count}")

    @widget
    class Child(Widget):
        count: Variable[int]
        grandchild: GrandChild = new(count="count")

    @widget
    class Parent(Widget):
        _count: Variable[int] = new(0)
        child: Child = new(count="_count")

    parent = Parent()
    assert parent.child.grandchild._label.text() == "Count: 0"


def test_diamond_dependency_pattern():
    """Diamond pattern: two intermediates share same root binding."""

    @widget
    class Leaf(Widget):
        value: Variable[str]
        _label: QLabel = new(bind="{value}")

    @widget
    class IntermediateA(Widget):
        value: Variable[str]
        leaf: Leaf = new(value="value")

    @widget
    class IntermediateB(Widget):
        value: Variable[str]
        leaf: Leaf = new(value="value")

    @widget
    class Root(Widget):
        _shared: Variable[str] = new("shared")
        intermediate_a: IntermediateA = new(value="_shared")
        intermediate_b: IntermediateB = new(value="_shared")

    root = Root()
    assert root.intermediate_a.leaf._label.text() == "shared"
    assert root.intermediate_b.leaf._label.text() == "shared"

    # Both should update
    root._shared.value = "updated"
    assert root.intermediate_a.leaf._label.text() == "updated"
    assert root.intermediate_b.leaf._label.text() == "updated"


def test_six_level_nesting():
    """Six levels deep - extreme stress test."""

    @widget
    class L6(Widget):
        v: Variable[str]
        _l: QLabel = new(bind="{v}")

    @widget
    class L5(Widget):
        v: Variable[str]
        l6: L6 = new(v="v")

    @widget
    class L4(Widget):
        v: Variable[str]
        l5: L5 = new(v="v")

    @widget
    class L3(Widget):
        v: Variable[str]
        l4: L4 = new(v="v")

    @widget
    class L2(Widget):
        v: Variable[str]
        l3: L3 = new(v="v")

    @widget
    class L1(Widget):
        v: Variable[str]
        l2: L2 = new(v="v")

    @widget
    class Root(Widget):
        _v: Variable[str] = new("deep")
        l1: L1 = new(v="_v")

    root = Root()
    assert root.l1.l2.l3.l4.l5.l6._l.text() == "deep"


def test_multiple_format_bindings_same_widget():
    """Multiple format bindings in same widget using required vars."""

    @widget
    class GrandChild(Widget):
        val_x: Variable[int]
        val_y: Variable[int]
        _sum: QLabel = new(bind="Sum: {val_x + val_y}")
        _product: QLabel = new(bind="Product: {val_x * val_y}")
        _diff: QLabel = new(bind="Diff: {val_x - val_y}")

    @widget
    class Child(Widget):
        val_x: Variable[int]
        val_y: Variable[int]
        grandchild: GrandChild = new(val_x="val_x", val_y="val_y")

    @widget
    class Parent(Widget):
        _x: Variable[int] = new(10)
        _y: Variable[int] = new(3)
        child: Child = new(val_x="_x", val_y="_y")

    parent = Parent()
    assert parent.child.grandchild._sum.text() == "Sum: 13"
    assert parent.child.grandchild._product.text() == "Product: 30"
    assert parent.child.grandchild._diff.text() == "Diff: 7"

    parent._x.value = 20
    assert parent.child.grandchild._sum.text() == "Sum: 23"
    assert parent.child.grandchild._product.text() == "Product: 60"
    assert parent.child.grandchild._diff.text() == "Diff: 17"


def test_binding_with_method_call_in_format():
    """Format binding calling method on required variable."""

    @widget
    class GrandChild(Widget):
        text: Variable[str]
        _label: QLabel = new(bind="{text.upper()}")

    @widget
    class Child(Widget):
        text: Variable[str]
        grandchild: GrandChild = new(text="text")

    @widget
    class Parent(Widget):
        _text: Variable[str] = new("hello")
        child: Child = new(text="_text")

    parent = Parent()
    assert parent.child.grandchild._label.text() == "HELLO"


def test_mixed_literal_and_binding():
    """Some children get literals, others get bindings."""

    @widget
    class ChildWidget(Widget):
        value: Variable[str]
        _label: QLabel = new(bind="{value}")

    @widget
    class Parent(Widget):
        _dynamic: Variable[str] = new("dynamic")
        # One child gets a binding, one gets a literal
        bound_child: ChildWidget = new(value="_dynamic")
        literal_child: ChildWidget = new(value="static")

    parent = Parent()
    assert parent.bound_child._label.text() == "dynamic"
    assert parent.literal_child._label.text() == "static"

    parent._dynamic.value = "changed"
    assert parent.bound_child._label.text() == "changed"
    assert parent.literal_child._label.text() == "static"  # Unchanged


def test_nested_with_conditionals_in_format():
    """Nested bindings with conditional expressions in format strings."""

    @widget
    class GrandChild(Widget):
        active: Variable[bool]
        count: Variable[int]
        _label: QLabel = new(bind="{'Active' if active else 'Inactive'}: {count if count > 0 else 'none'}")

    @widget
    class Child(Widget):
        active: Variable[bool]
        count: Variable[int]
        grandchild: GrandChild = new(active="active", count="count")

    @widget
    class Parent(Widget):
        _active: Variable[bool] = new(False)
        _count: Variable[int] = new(0)
        child: Child = new(active="_active", count="_count")

    parent = Parent()
    assert parent.child.grandchild._label.text() == "Inactive: none"

    parent._active.value = True
    parent._count.value = 5
    assert parent.child.grandchild._label.text() == "Active: 5"
