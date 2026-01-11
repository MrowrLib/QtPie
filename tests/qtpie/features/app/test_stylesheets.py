# pyright: reportPrivateUsage=false
# pyright: reportMissingParameterType=false
# pyright: reportUnknownParameterType=false
# pyright: reportUntypedBaseClass=false
# pyright: reportUntypedClassDecorator=false
# pyright: reportUnknownArgumentType=false
# pyright: reportUnknownMemberType=false
# pyright: reportArgumentType=false
# pyright: reportOptionalMemberAccess=false
"""Tests for App stylesheet functionality.

Stylesheets allow customizing the appearance of Qt widgets using CSS-like syntax.
"""

from assertpy import assert_that
from PySide6.QtWidgets import QLabel

from qtpie import AppBase, app, new
from qtpie.testing import QtDriver


class TestStylesheetParameter:
    """stylesheet= parameter on @app decorator."""

    def test_stylesheet_stored_in_config(self, qt: QtDriver) -> None:
        """stylesheet= is stored in widget_props."""

        @app(stylesheet="QLabel { color: red; }")
        class MyApp(AppBase):
            label: QLabel = new("Hello")

        a = MyApp()
        qt.track(a.window)

        config = MyApp._qtpie_config
        assert_that(config.widget_props.get("styleSheet")).is_equal_to("QLabel { color: red; }")

    def test_app_with_stylesheet_creates_widgets(self, qt: QtDriver) -> None:
        """App with stylesheet still creates widgets normally."""

        @app(stylesheet="* { font-size: 14px; }")
        class MyApp(AppBase):
            label: QLabel = new("Styled")

        a = MyApp()
        qt.track(a.window)

        assert_that(a.label.text()).is_equal_to("Styled")


class TestCssClasses:
    """CSS classes on app and widgets."""

    def test_app_classes_parameter(self, qt: QtDriver) -> None:
        """classes= on @app sets CSS classes on window."""

        @app(classes=["dark-theme", "compact"])
        class MyApp(AppBase):
            label: QLabel = new("Hello")

        a = MyApp()
        qt.track(a.window)

        from qtpie.styles import get_classes

        classes = get_classes(a.window)
        assert_that(classes).contains("dark-theme", "compact")

    def test_widget_classes_parameter(self, qt: QtDriver) -> None:
        """classes= on new() sets CSS classes on widget."""

        @app
        class MyApp(AppBase):
            primary: QLabel = new("Primary", classes=["btn", "btn-primary"])
            secondary: QLabel = new("Secondary", classes=["btn", "btn-secondary"])

        a = MyApp()
        qt.track(a.window)

        from qtpie.styles import get_classes

        assert_that(get_classes(a.primary)).is_equal_to(["btn", "btn-primary"])
        assert_that(get_classes(a.secondary)).is_equal_to(["btn", "btn-secondary"])


class TestObjectName:
    """Object names for CSS selectors."""

    def test_app_name_parameter(self, qt: QtDriver) -> None:
        """name= on @app sets window objectName."""

        @app(name="main-app")
        class MyApp(AppBase):
            label: QLabel = new("Hello")

        a = MyApp()
        qt.track(a.window)

        assert_that(a.window.objectName()).is_equal_to("main-app")

    def test_default_window_object_name(self, qt: QtDriver) -> None:
        """Without name=, window objectName is class name."""

        @app
        class MyCustomApp(AppBase):
            label: QLabel = new("Hello")

        a = MyCustomApp()
        qt.track(a.window)

        assert_that(a.window.objectName()).is_equal_to("MyCustomApp")

    def test_widget_name_parameter(self, qt: QtDriver) -> None:
        """name= on new() sets widget objectName."""

        @app
        class MyApp(AppBase):
            title: QLabel = new("Title", name="page-title")

        a = MyApp()
        qt.track(a.window)

        assert_that(a.title.objectName()).is_equal_to("page-title")

    def test_default_widget_object_name(self, qt: QtDriver) -> None:
        """Without name=, widget objectName is field name."""

        @app
        class MyApp(AppBase):
            my_label: QLabel = new("Hello")

        a = MyApp()
        qt.track(a.window)

        assert_that(a.my_label.objectName()).is_equal_to("my_label")


class TestCombinedStyling:
    """Combined stylesheet, classes, and names."""

    def test_full_styling_setup(self, qt: QtDriver) -> None:
        """App with stylesheet, classes, and named widgets."""

        @app(
            name="styled-app",
            classes=["theme-dark"],
            stylesheet="QLabel { padding: 10px; }",
        )
        class MyApp(AppBase):
            header: QLabel = new("Header", name="main-header", classes=["large"])
            content: QLabel = new("Content", classes=["body-text"])

        a = MyApp()
        qt.track(a.window)

        from qtpie.styles import get_classes

        # Window styling
        assert_that(a.window.objectName()).is_equal_to("styled-app")
        assert_that(get_classes(a.window)).is_equal_to(["theme-dark"])

        # Header widget
        assert_that(a.header.objectName()).is_equal_to("main-header")
        assert_that(get_classes(a.header)).is_equal_to(["large"])

        # Content widget
        assert_that(a.content.objectName()).is_equal_to("content")
        assert_that(get_classes(a.content)).is_equal_to(["body-text"])
