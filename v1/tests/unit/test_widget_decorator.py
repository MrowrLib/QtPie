"""Tests for the @widget decorator."""

from dataclasses import field
from typing import override

from assertpy import assert_that
from qtpy.QtWidgets import QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from qtpie import Widget, widget
from qtpie.testing import QtDriver


class TestWidgetDecorator:
    """Phase 1: Basic @widget functionality."""

    def test_widget_with_no_children_creates_valid_widget(self, qt: QtDriver) -> None:
        """A decorated class with no child widgets should still work."""

        @widget()
        class EmptyWidget(QWidget, Widget):
            pass

        w = EmptyWidget()
        qt.track(w)

        assert_that(w).is_instance_of(QWidget)

    def test_widget_without_parens(self, qt: QtDriver) -> None:
        """@widget without parentheses should work with defaults."""

        @widget
        class MyWidget(QWidget, Widget):
            pass

        w = MyWidget()
        qt.track(w)

        assert_that(w).is_instance_of(QWidget)
        assert_that(w.layout()).is_instance_of(QVBoxLayout)

    def test_widget_has_vertical_layout_by_default(self, qt: QtDriver) -> None:
        """Default layout should be vertical."""

        @widget()
        class MyWidget(QWidget, Widget):
            pass

        w = MyWidget()
        qt.track(w)

        assert_that(w.layout()).is_instance_of(QVBoxLayout)

    def test_widget_with_horizontal_layout(self, qt: QtDriver) -> None:
        """layout='horizontal' should create QHBoxLayout."""

        @widget(layout="horizontal")
        class MyWidget(QWidget, Widget):
            pass

        w = MyWidget()
        qt.track(w)

        assert_that(w.layout()).is_instance_of(QHBoxLayout)

    def test_single_child_widget_added_to_layout(self, qt: QtDriver) -> None:
        """A QWidget field should be automatically added to the layout."""

        @widget()
        class MyWidget(QWidget, Widget):
            label: QLabel = field(default_factory=QLabel)

        w = MyWidget()
        qt.track(w)

        # The label should exist as an attribute
        assert_that(w.label).is_instance_of(QLabel)

        # The label should be in the layout
        layout = w.layout()
        assert_that(layout).is_not_none()
        assert layout is not None  # for type narrowing
        assert_that(layout.count()).is_equal_to(1)
        item0 = layout.itemAt(0)
        assert item0 is not None
        assert_that(item0.widget()).is_same_as(w.label)

    def test_multiple_children_added_in_field_order(self, qt: QtDriver) -> None:
        """Multiple widget fields should be added in declaration order."""

        @widget()
        class MyWidget(QWidget, Widget):
            first: QLabel = field(default_factory=QLabel)
            second: QPushButton = field(default_factory=QPushButton)
            third: QLabel = field(default_factory=QLabel)

        w = MyWidget()
        qt.track(w)

        layout = w.layout()
        assert layout is not None

        assert_that(layout.count()).is_equal_to(3)
        item0, item1, item2 = layout.itemAt(0), layout.itemAt(1), layout.itemAt(2)
        assert item0 is not None and item1 is not None and item2 is not None
        assert_that(item0.widget()).is_same_as(w.first)
        assert_that(item1.widget()).is_same_as(w.second)
        assert_that(item2.widget()).is_same_as(w.third)

    def test_non_widget_fields_not_added_to_layout(self, qt: QtDriver) -> None:
        """Non-QWidget fields (like int, str) should not go in the layout."""

        @widget()
        class MyWidget(QWidget, Widget):
            label: QLabel = field(default_factory=QLabel)
            counter: int = 0
            name: str = "test"

        w = MyWidget()
        qt.track(w)

        # Non-widget fields should exist
        assert_that(w.counter).is_equal_to(0)
        assert_that(w.name).is_equal_to("test")

        # But only the label should be in the layout
        layout = w.layout()
        assert layout is not None
        assert_that(layout.count()).is_equal_to(1)

    def test_single_underscore_fields_added_to_layout(self, qt: QtDriver) -> None:
        """Fields starting with _ ARE added to layout (only __ are excluded)."""

        @widget()
        class MyWidget(QWidget, Widget):
            label: QLabel = field(default_factory=QLabel)
            _semi_private: QLabel = field(default_factory=QLabel)

        w = MyWidget()
        qt.track(w)

        # Both fields should exist
        assert_that(w.label).is_instance_of(QLabel)
        assert_that(hasattr(w, "_semi_private")).is_true()

        # Both should be in the layout (single underscore is now included)
        layout = w.layout()
        assert layout is not None
        assert_that(layout.count()).is_equal_to(2)

    def test_excluded_fields_not_added_to_layout(self, qt: QtDriver) -> None:
        """Fields like _foo_ (start AND end with _) are excluded from layout."""

        @widget()
        class MyWidget(QWidget, Widget):
            label: QLabel = field(default_factory=QLabel)
            _excluded_: QLabel = field(default_factory=QLabel)

        w = MyWidget()
        qt.track(w)

        # Both fields should exist
        assert_that(w.label).is_instance_of(QLabel)
        assert_that(hasattr(w, "_excluded_")).is_true()

        # Only the non-excluded one should be in the layout
        layout = w.layout()
        assert layout is not None
        assert_that(layout.count()).is_equal_to(1)
        item0 = layout.itemAt(0)
        assert item0 is not None
        assert_that(item0.widget()).is_same_as(w.label)

    def test_underscore_field_naming_convention(self, qt: QtDriver) -> None:
        """Test the underscore naming convention for fields.

        - `foo`: added to layout, binds to 'foo'
        - `_foo`: added to layout, binds to 'foo' (private but included)
        - `_foo_`: NOT added to layout, no auto-bind (excluded)
        """

        @widget()
        class TestWidget(QWidget, Widget):
            public: QLabel = field(default_factory=QLabel)
            _private: QLabel = field(default_factory=QLabel)
            _excluded_: QLabel = field(default_factory=QLabel)

        w = TestWidget()

        # All fields exist
        assert_that(w.public).is_instance_of(QLabel)
        assert_that(hasattr(w, "_private")).is_true()
        assert_that(hasattr(w, "_excluded_")).is_true()

        # Only public and _private are in layout (not _excluded_)
        layout = w.layout()
        assert layout is not None
        assert_that(layout.count()).is_equal_to(2)

    def test_widget_with_layout_none_has_no_layout(self, qt: QtDriver) -> None:
        """layout='none' should not create any layout."""

        @widget(layout="none")
        class MyWidget(QWidget, Widget):
            pass

        w = MyWidget()
        qt.track(w)

        assert_that(w.layout()).is_none()


class TestWidgetName:
    """Tests for the name parameter."""

    def test_explicit_name_sets_object_name(self, qt: QtDriver) -> None:
        """name parameter should set the widget's objectName."""

        @widget(name="MyCustomName")
        class MyWidget(QWidget, Widget):
            pass

        w = MyWidget()
        qt.track(w)

        assert_that(w.objectName()).is_equal_to("MyCustomName")

    def test_auto_name_from_class_name(self, qt: QtDriver) -> None:
        """Without name param, objectName should be derived from class name."""

        @widget()
        class SomeWidget(QWidget, Widget):
            pass

        w = SomeWidget()
        qt.track(w)

        # "Widget" suffix should be stripped
        assert_that(w.objectName()).is_equal_to("Some")

    def test_auto_name_without_widget_suffix(self, qt: QtDriver) -> None:
        """Class name without Widget suffix should be used as-is."""

        @widget()
        class Editor(QWidget, Widget):
            pass

        w = Editor()
        qt.track(w)

        assert_that(w.objectName()).is_equal_to("Editor")


class TestWidgetClasses:
    """Tests for the classes parameter (CSS-like styling)."""

    def test_classes_set_as_property(self, qt: QtDriver) -> None:
        """classes parameter should set a 'class' property on the widget."""

        @widget(classes=["card", "shadow"])
        class MyWidget(QWidget, Widget):
            pass

        w = MyWidget()
        qt.track(w)

        class_prop = w.property("class")
        assert_that(class_prop).is_equal_to(["card", "shadow"])

    def test_no_classes_by_default(self, qt: QtDriver) -> None:
        """Without classes param, no class property should be set."""

        @widget()
        class MyWidget(QWidget, Widget):
            pass

        w = MyWidget()
        qt.track(w)

        # Property should be None or not set
        class_prop = w.property("class")
        assert_that(class_prop).is_none()


class TestWidgetLifecycleHooks:
    """Tests for lifecycle hooks (setup, setup_values, etc.)."""

    def test_setup_called_on_init(self, qt: QtDriver) -> None:
        """setup() should be called after widget initialization."""
        calls: list[str] = []

        @widget()
        class MyWidget(QWidget, Widget):
            @override
            def setup(self) -> None:
                calls.append("setup")

        w = MyWidget()
        qt.track(w)

        assert_that(calls).is_equal_to(["setup"])

    def test_all_lifecycle_hooks_called_in_order(self, qt: QtDriver) -> None:
        """Both lifecycle hooks should be called in the correct order."""
        calls: list[str] = []

        @widget()
        class MyWidget(QWidget, Widget):
            @override
            def configure(self) -> None:
                calls.append("configure")

            @override
            def setup(self) -> None:
                calls.append("setup")

        w = MyWidget()
        qt.track(w)

        assert_that(calls).is_equal_to(["configure", "setup"])

    def test_setup_has_access_to_child_widgets(self, qt: QtDriver) -> None:
        """setup() should have access to child widgets."""
        from qtpie import make

        @widget()
        class MyWidget(QWidget, Widget):
            label: QLabel = make(QLabel, "Initial")

            @override
            def setup(self) -> None:
                # Should be able to access and modify child widgets
                self.label.setText("Modified in setup")

        w = MyWidget()
        qt.track(w)

        assert_that(w.label.text()).is_equal_to("Modified in setup")
