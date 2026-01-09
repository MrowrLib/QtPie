# pyright: reportPrivateUsage=false
"""Tests for Variable bindings - passing state DOWN to child widgets."""

import pytest
from PySide6.QtWidgets import QApplication, QLabel

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


def test_missing_required_binding_raises_error():
    """Instantiating widget with missing required binding raises error."""

    @widget
    class Child(Widget):
        count: Variable[int]  # Required!

    @widget
    class Parent(Widget):
        child: Child = new()  # Missing count binding!

    with pytest.raises(TypeError, match="requires binding for 'count'"):
        Parent()


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
