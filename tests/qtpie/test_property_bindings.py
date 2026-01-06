# pyright: reportPrivateUsage=false
"""Tests for property bindings (visible=, enabled=, etc.)."""

from __future__ import annotations

import pytest
from qtpy.QtWidgets import QApplication, QLabel, QPushButton

from qtpie import Widget, new, widget
from qtpie.variable import Variable


@pytest.fixture(scope="module")
def qapp():
    """Create QApplication for tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


# Helper: Qt's isVisible() returns False for hidden parent widgets
# Use isHidden() which checks the widget's own visibility state
# isHidden() returns True if setVisible(False) was called on THIS widget
def is_widget_visible(widget: QLabel | QPushButton) -> bool:
    """Check if widget's OWN visibility is set to True (ignoring parent visibility)."""
    return not widget.isHidden()


# =============================================================================
# Basic visible= binding
# =============================================================================


class TestVisibleBinding:
    """Tests for visible= property binding."""

    def test_visible_binding_simple_variable(self, qapp: QApplication) -> None:
        """Test visible= bound to a simple Variable[bool]."""

        @widget
        class TestWidget(Widget):
            _is_visible: Variable[bool] = new(True)
            _label: QLabel = new("Hello", visible="_is_visible")

        w = TestWidget()

        # Initial state - label should be visible
        assert is_widget_visible(w._label) is True

        # Change variable - label should hide
        w._is_visible.value = False
        assert is_widget_visible(w._label) is False

        # Change back - label should show
        w._is_visible.value = True
        assert is_widget_visible(w._label) is True

    def test_visible_binding_starts_hidden(self, qapp: QApplication) -> None:
        """Test visible= with initial False value."""

        @widget
        class TestWidget(Widget):
            _show_label: Variable[bool] = new(False)
            _label: QLabel = new("Hidden", visible="_show_label")

        w = TestWidget()

        # Initial state - label should be hidden
        assert is_widget_visible(w._label) is False

        # Show it
        w._show_label.value = True
        assert is_widget_visible(w._label) is True


class TestEnabledBinding:
    """Tests for enabled= property binding."""

    def test_enabled_binding_simple_variable(self, qapp: QApplication) -> None:
        """Test enabled= bound to a simple Variable[bool]."""

        @widget
        class TestWidget(Widget):
            _can_click: Variable[bool] = new(True)
            _button: QPushButton = new("Click me", enabled="_can_click")

        w = TestWidget()

        # Initial state - button should be enabled
        assert w._button.isEnabled() is True

        # Disable via variable
        w._can_click.value = False
        assert w._button.isEnabled() is False

        # Enable again
        w._can_click.value = True
        assert w._button.isEnabled() is True

    def test_enabled_binding_starts_disabled(self, qapp: QApplication) -> None:
        """Test enabled= with initial False value."""

        @widget
        class TestWidget(Widget):
            _is_enabled: Variable[bool] = new(False)
            _button: QPushButton = new("Disabled", enabled="_is_enabled")

        w = TestWidget()

        # Initial state - button should be disabled
        assert w._button.isEnabled() is False


# =============================================================================
# Expression bindings with {}
# =============================================================================


class TestExpressionBindings:
    """Tests for expression-based property bindings."""

    def test_visible_expression_comparison(self, qapp: QApplication) -> None:
        """Test visible= with comparison expression."""

        @widget
        class TestWidget(Widget):
            _count: Variable[int] = new(0)
            _label: QLabel = new("Has items", visible="{_count > 0}")

        w = TestWidget()

        # Initial: count=0, so not visible
        assert is_widget_visible(w._label) is False

        # count=1, now visible
        w._count.value = 1
        assert is_widget_visible(w._label) is True

        # count=5, still visible
        w._count.value = 5
        assert is_widget_visible(w._label) is True

        # back to 0, hidden again
        w._count.value = 0
        assert is_widget_visible(w._label) is False

    def test_enabled_expression_len(self, qapp: QApplication) -> None:
        """Test enabled= with len() expression."""

        @widget
        class TestWidget(Widget):
            _name: Variable[str] = new("")
            _submit: QPushButton = new("Submit", enabled="{len(_name) > 0}")

        w = TestWidget()

        # Empty name - button disabled
        assert w._submit.isEnabled() is False

        # Non-empty name - button enabled
        w._name.value = "Alice"
        assert w._submit.isEnabled() is True

        # Empty again - disabled
        w._name.value = ""
        assert w._submit.isEnabled() is False

    def test_visible_expression_boolean_and(self, qapp: QApplication) -> None:
        """Test visible= with boolean and expression."""

        @widget
        class TestWidget(Widget):
            _logged_in: Variable[bool] = new(False)
            _is_admin: Variable[bool] = new(False)
            _admin_panel: QLabel = new("Admin Panel", visible="{_logged_in and _is_admin}")

        w = TestWidget()

        # Neither condition - hidden
        assert is_widget_visible(w._admin_panel) is False

        # Only logged in - still hidden
        w._logged_in.value = True
        assert is_widget_visible(w._admin_panel) is False

        # Logged in AND admin - visible
        w._is_admin.value = True
        assert is_widget_visible(w._admin_panel) is True

        # Only admin, not logged in - hidden
        w._logged_in.value = False
        assert is_widget_visible(w._admin_panel) is False

    def test_enabled_expression_or(self, qapp: QApplication) -> None:
        """Test enabled= with boolean or expression."""

        @widget
        class TestWidget(Widget):
            _has_permission: Variable[bool] = new(False)
            _is_owner: Variable[bool] = new(False)
            _edit_btn: QPushButton = new("Edit", enabled="{_has_permission or _is_owner}")

        w = TestWidget()

        # Neither - disabled
        assert w._edit_btn.isEnabled() is False

        # Has permission - enabled
        w._has_permission.value = True
        assert w._edit_btn.isEnabled() is True

        # Is owner (but no permission) - enabled
        w._has_permission.value = False
        w._is_owner.value = True
        assert w._edit_btn.isEnabled() is True

        # Both - still enabled
        w._has_permission.value = True
        assert w._edit_btn.isEnabled() is True


# =============================================================================
# Multiple property bindings on same widget
# =============================================================================


class TestMultiplePropertyBindings:
    """Tests for multiple property bindings on the same widget."""

    def test_both_visible_and_enabled(self, qapp: QApplication) -> None:
        """Test a widget with both visible= and enabled= bindings."""

        @widget
        class TestWidget(Widget):
            _show: Variable[bool] = new(True)
            _allow: Variable[bool] = new(True)
            _button: QPushButton = new("Action", visible="_show", enabled="_allow")

        w = TestWidget()

        # Both true
        assert is_widget_visible(w._button) is True
        assert w._button.isEnabled() is True

        # Hide but keep enabled
        w._show.value = False
        assert is_widget_visible(w._button) is False
        assert w._button.isEnabled() is True

        # Show but disable
        w._show.value = True
        w._allow.value = False
        assert is_widget_visible(w._button) is True
        assert w._button.isEnabled() is False


# =============================================================================
# Edge cases
# =============================================================================


class TestPropertyBindingEdgeCases:
    """Tests for edge cases in property bindings."""

    def test_binding_without_underscore_prefix(self, qapp: QApplication) -> None:
        """Test binding to variable without underscore prefix."""

        @widget
        class TestWidget(Widget):
            show_it: Variable[bool] = new(True)
            _label: QLabel = new("Test", visible="show_it")

        w = TestWidget()

        assert is_widget_visible(w._label) is True
        w.show_it.value = False
        assert is_widget_visible(w._label) is False

    def test_binding_to_nested_path(self, qapp: QApplication) -> None:
        """Test binding with underscore lookup."""

        @widget
        class TestWidget(Widget):
            _enabled_flag: Variable[bool] = new(True)
            _button: QPushButton = new("Test", enabled="enabled_flag")

        w = TestWidget()

        assert w._button.isEnabled() is True
        w._enabled_flag.value = False
        assert w._button.isEnabled() is False

    def test_expression_with_not_operator(self, qapp: QApplication) -> None:
        """Test expression with not operator."""

        @widget
        class TestWidget(Widget):
            _loading: Variable[bool] = new(True)
            _content: QLabel = new("Content", visible="{not _loading}")

        w = TestWidget()

        # Loading = True, so not visible
        assert is_widget_visible(w._content) is False

        # Loading = False, so visible
        w._loading.value = False
        assert is_widget_visible(w._content) is True

    def test_expression_with_ternary(self, qapp: QApplication) -> None:
        """Test expression with ternary operator (not directly supported but works via bool result)."""

        @widget
        class TestWidget(Widget):
            _status: Variable[str] = new("active")
            _badge: QLabel = new("Active", visible="{_status == 'active'}")

        w = TestWidget()

        # status == 'active' - visible
        assert is_widget_visible(w._badge) is True

        # status != 'active' - hidden
        w._status.value = "inactive"
        assert is_widget_visible(w._badge) is False

        # back to active
        w._status.value = "active"
        assert is_widget_visible(w._badge) is True


# =============================================================================
# Reactive @widget decorator props
# =============================================================================


class TestReactiveWidgetDecoratorProps:
    """Tests for reactive properties on @widget decorator."""

    def test_reactive_window_title(self, qapp: QApplication) -> None:
        """Test windowTitle='{title}' on @widget decorator."""

        @widget(windowTitle="{_title}")
        class TestWidget(Widget):
            _title: Variable[str] = new("Initial Title")

        w = TestWidget()

        # Initial title
        assert w.windowTitle() == "Initial Title"

        # Change variable - title updates
        w._title.value = "Updated Title"
        assert w.windowTitle() == "Updated Title"

    def test_reactive_window_title_with_format(self, qapp: QApplication) -> None:
        """Test windowTitle with format string."""

        @widget(windowTitle="Count: {_count}")
        class TestWidget(Widget):
            _count: Variable[int] = new(0)

        w = TestWidget()

        assert w.windowTitle() == "Count: 0"

        w._count.value = 42
        assert w.windowTitle() == "Count: 42"

    def test_static_window_title_still_works(self, qapp: QApplication) -> None:
        """Test that static windowTitle still works."""

        @widget(windowTitle="My App")
        class TestWidget(Widget):
            pass

        w = TestWidget()
        assert w.windowTitle() == "My App"

    def test_reactive_window_title_multiple_vars(self, qapp: QApplication) -> None:
        """Test windowTitle with multiple variables."""

        @widget(windowTitle="{_app_name} - {_filename}")
        class TestWidget(Widget):
            _app_name: Variable[str] = new("Editor")
            _filename: Variable[str] = new("untitled.txt")

        w = TestWidget()

        assert w.windowTitle() == "Editor - untitled.txt"

        w._filename.value = "document.md"
        assert w.windowTitle() == "Editor - document.md"

        w._app_name.value = "Super Editor"
        assert w.windowTitle() == "Super Editor - document.md"
