"""Tests for the @window decorator."""

from assertpy import assert_that
from qtpy.QtWidgets import QLabel, QMainWindow, QMenu, QPushButton, QTextEdit

from qtpie import make, window
from qtpie_test import QtDriver


class TestWindowDecorator:
    """Phase 3: Basic @window functionality."""

    def test_window_creates_valid_main_window(self, qt: QtDriver) -> None:
        """A decorated class should be a valid QMainWindow."""

        @window()
        class MyWindow(QMainWindow):
            pass

        w = MyWindow()
        qt.track(w)

        assert_that(w).is_instance_of(QMainWindow)

    def test_window_without_parens(self, qt: QtDriver) -> None:
        """@window without parentheses should work with defaults."""

        @window
        class MyWindow(QMainWindow):
            pass

        w = MyWindow()
        qt.track(w)

        assert_that(w).is_instance_of(QMainWindow)


class TestWindowTitle:
    """Tests for the title parameter."""

    def test_title_sets_window_title(self, qt: QtDriver) -> None:
        """title parameter should set the window title."""

        @window(title="My Application")
        class MyWindow(QMainWindow):
            pass

        w = MyWindow()
        qt.track(w)

        assert_that(w.windowTitle()).is_equal_to("My Application")

    def test_no_title_by_default(self, qt: QtDriver) -> None:
        """Without title param, window title should be empty."""

        @window()
        class MyWindow(QMainWindow):
            pass

        w = MyWindow()
        qt.track(w)

        assert_that(w.windowTitle()).is_equal_to("")


class TestWindowSize:
    """Tests for the size parameter."""

    def test_size_sets_window_dimensions(self, qt: QtDriver) -> None:
        """size parameter should set window width and height."""

        @window(size=(800, 600))
        class MyWindow(QMainWindow):
            pass

        w = MyWindow()
        qt.track(w)

        assert_that(w.width()).is_equal_to(800)
        assert_that(w.height()).is_equal_to(600)

    def test_size_tuple_order(self, qt: QtDriver) -> None:
        """size should be (width, height) not (height, width)."""

        @window(size=(1024, 768))
        class MyWindow(QMainWindow):
            pass

        w = MyWindow()
        qt.track(w)

        assert_that(w.width()).is_equal_to(1024)
        assert_that(w.height()).is_equal_to(768)


class TestWindowName:
    """Tests for the name parameter."""

    def test_explicit_name_sets_object_name(self, qt: QtDriver) -> None:
        """name parameter should set the widget's objectName."""

        @window(name="MainAppWindow")
        class MyWindow(QMainWindow):
            pass

        w = MyWindow()
        qt.track(w)

        assert_that(w.objectName()).is_equal_to("MainAppWindow")

    def test_auto_name_from_class_name(self, qt: QtDriver) -> None:
        """Without name param, objectName should be derived from class name."""

        @window()
        class SomeWindow(QMainWindow):
            pass

        w = SomeWindow()
        qt.track(w)

        # "Window" suffix should be stripped
        assert_that(w.objectName()).is_equal_to("Some")

    def test_auto_name_without_window_suffix(self, qt: QtDriver) -> None:
        """Class name without Window suffix should be used as-is."""

        @window()
        class Editor(QMainWindow):
            pass

        w = Editor()
        qt.track(w)

        assert_that(w.objectName()).is_equal_to("Editor")


class TestWindowClasses:
    """Tests for the classes parameter."""

    def test_classes_set_as_property(self, qt: QtDriver) -> None:
        """classes parameter should set a 'class' property on the window."""

        @window(classes=["dark-theme", "main-window"])
        class MyWindow(QMainWindow):
            pass

        w = MyWindow()
        qt.track(w)

        class_prop = w.property("class")
        assert_that(class_prop).is_equal_to(["dark-theme", "main-window"])


class TestWindowCentralWidget:
    """Tests for auto-setting central widget."""

    def test_central_widget_field_auto_set(self, qt: QtDriver) -> None:
        """Field named 'central_widget' should be auto-set as central widget."""

        @window()
        class MyWindow(QMainWindow):
            central_widget: QTextEdit = make(QTextEdit)

        w = MyWindow()
        qt.track(w)

        assert_that(w.centralWidget()).is_same_as(w.central_widget)

    def test_central_widget_receives_content(self, qt: QtDriver) -> None:
        """Central widget should be fully functional."""

        @window()
        class MyWindow(QMainWindow):
            central_widget: QLabel = make(QLabel, "Hello from central!")

        w = MyWindow()
        qt.track(w)

        central = w.centralWidget()
        assert isinstance(central, QLabel)
        assert_that(central.text()).is_equal_to("Hello from central!")

    def test_no_central_widget_field_is_ok(self, qt: QtDriver) -> None:
        """Window without central_widget field should work fine."""

        @window()
        class MyWindow(QMainWindow):
            pass

        w = MyWindow()
        qt.track(w)

        # No crash, centralWidget is None
        assert_that(w.centralWidget()).is_none()


class TestWindowLifecycleHooks:
    """Tests for lifecycle hooks."""

    def test_setup_called_on_init(self, qt: QtDriver) -> None:
        """setup() should be called after window initialization."""
        calls: list[str] = []

        @window()
        class MyWindow(QMainWindow):
            def setup(self) -> None:
                calls.append("setup")

        w = MyWindow()
        qt.track(w)

        assert_that(calls).is_equal_to(["setup"])

    def test_all_lifecycle_hooks_called_in_order(self, qt: QtDriver) -> None:
        """All lifecycle hooks should be called in the correct order."""
        calls: list[str] = []

        @window()
        class MyWindow(QMainWindow):
            def setup(self) -> None:
                calls.append("setup")

            def setup_values(self) -> None:
                calls.append("setup_values")

            def setup_bindings(self) -> None:
                calls.append("setup_bindings")

            def setup_styles(self) -> None:
                calls.append("setup_styles")

            def setup_events(self) -> None:
                calls.append("setup_events")

            def setup_signals(self) -> None:
                calls.append("setup_signals")

        w = MyWindow()
        qt.track(w)

        assert_that(calls).is_equal_to(
            [
                "setup",
                "setup_values",
                "setup_bindings",
                "setup_styles",
                "setup_events",
                "setup_signals",
            ]
        )

    def test_setup_has_access_to_child_widgets(self, qt: QtDriver) -> None:
        """setup() should have access to child widgets."""

        @window()
        class MyWindow(QMainWindow):
            central_widget: QLabel = make(QLabel, "Initial")

            def setup(self) -> None:
                self.central_widget.setText("Modified in setup")

        w = MyWindow()
        qt.track(w)

        assert_that(w.central_widget.text()).is_equal_to("Modified in setup")


class TestWindowSignalConnections:
    """Tests for signal connections via make()."""

    def test_signal_connection_by_method_name(self, qt: QtDriver) -> None:
        """Signals should connect via method name string."""
        clicked = False

        @window()
        class MyWindow(QMainWindow):
            central_widget: QPushButton = make(QPushButton, "Click", clicked="on_click")

            def on_click(self) -> None:
                nonlocal clicked
                clicked = True

        w = MyWindow()
        qt.track(w)

        qt.click(w.central_widget)

        assert_that(clicked).is_true()


class TestWindowCenter:
    """Tests for the center parameter."""

    def test_center_does_not_crash(self, qt: QtDriver) -> None:
        """center=True should not crash (hard to test actual centering)."""

        @window(title="Centered", size=(400, 300), center=True)
        class MyWindow(QMainWindow):
            pass

        w = MyWindow()
        qt.track(w)

        # Just verify it doesn't crash and window exists
        assert_that(w).is_instance_of(QMainWindow)
        assert_that(w.width()).is_equal_to(400)


class TestWindowMenuBar:
    """Tests for auto-adding menus to menu bar."""

    def test_qmenu_field_added_to_menubar(self, qt: QtDriver) -> None:
        """QMenu fields should be auto-added to the menu bar."""
        from dataclasses import field

        @window()
        class MyWindow(QMainWindow):
            file_menu: QMenu = field(default_factory=lambda: QMenu("&File"))

        w = MyWindow()
        qt.track(w)

        menubar = w.menuBar()
        actions = menubar.actions()

        # Should have one menu
        assert_that(len(actions)).is_equal_to(1)
        assert_that(actions[0].text()).is_equal_to("&File")
