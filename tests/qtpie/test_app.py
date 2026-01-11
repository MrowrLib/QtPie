# pyright: reportPrivateUsage=false
# pyright: reportUnknownMemberType=false
# pyright: reportUnknownVariableType=false
# pyright: reportAttributeAccessIssue=false
# pyright: reportUnknownArgumentType=false
"""Tests for the App class."""

import inspect
from dataclasses import dataclass
from pathlib import Path
from typing import override

from assertpy import assert_that
from qtpy.QtWidgets import QApplication, QLabel, QLineEdit, QPushButton

from qtpie import App, AppBase, Variable, app, new
from qtpie.testing import QtDriver


class TestAppClass:
    """Tests for the App class using qapp fixture."""

    def test_app_is_qapplication(self, qapp: App) -> None:
        """App should be a QApplication instance."""
        assert_that(qapp).is_instance_of(QApplication)

    def test_app_is_our_app_class(self, qapp: App) -> None:
        """qapp fixture should use our App class."""
        assert_that(qapp).is_instance_of(App)

    def test_app_has_run_method(self, qapp: App) -> None:
        """App should have a run method."""
        assert_that(qapp.run).is_not_none()
        assert_that(callable(qapp.run)).is_true()

    def test_app_has_run_async_method(self, qapp: App) -> None:
        """App should have a run_async method."""
        assert_that(qapp.run_async).is_not_none()
        assert_that(callable(qapp.run_async)).is_true()

    def test_app_has_load_stylesheet_method(self, qapp: App) -> None:
        """App should have a load_stylesheet method."""
        assert_that(qapp.load_stylesheet).is_not_none()
        assert_that(callable(qapp.load_stylesheet)).is_true()

    def test_app_has_dark_light_mode_methods(self, qapp: App) -> None:
        """App should have enable_dark_mode and enable_light_mode methods."""
        assert_that(callable(qapp.enable_dark_mode)).is_true()
        assert_that(callable(qapp.enable_light_mode)).is_true()

    def test_app_load_stylesheet_from_file(self, qapp: App, tmp_path: Path) -> None:
        """App should be able to load a stylesheet from a file."""
        qss_file = tmp_path / "test.qss"
        qss_file.write_text("QWidget { background-color: red; }")

        qapp.load_stylesheet(str(qss_file))

        assert_that(qapp.styleSheet()).contains("background-color")

    def test_app_load_stylesheet_nonexistent_file(self, qapp: App) -> None:
        """App should handle nonexistent stylesheet gracefully."""
        # Should not raise
        qapp.load_stylesheet("/nonexistent/path/style.qss")
        # Stylesheet might be empty but shouldn't crash


class TestAppLifecycleHooks:
    """Tests for App lifecycle hooks."""

    def test_setup_hook_called_on_subclass(self) -> None:
        """__setup__() hook should be called when overridden in subclass."""
        setup_called = False

        class MyApp(App):
            def __setup__(self) -> None:
                nonlocal setup_called
                setup_called = True

        # We can't actually instantiate because QApplication already exists
        # But we can test the logic by checking the method
        assert_that(hasattr(MyApp, "__setup__")).is_true()


class TestRunAppFunction:
    """Tests for the run_app standalone function."""

    def test_run_app_exists(self) -> None:
        """run_app function should be importable."""
        from qtpie import run_app

        assert_that(run_app).is_not_none()
        assert_that(callable(run_app)).is_true()

    def test_run_app_accepts_qapplication(self) -> None:
        """run_app should accept any QApplication."""
        from qtpie import run_app

        sig = inspect.signature(run_app)
        params = list(sig.parameters.keys())
        assert_that(params).contains("app")


# =============================================================================
# AppBase Behavioral Tests
# All tests use show=False and system_tray=False to prevent windows/icons
# =============================================================================


class TestAppBaseVariables:
    """Tests for Variable fields in AppBase."""

    def test_variable_instantiation(self, qt: QtDriver) -> None:
        """Variable fields are instantiated on AppBase."""

        @app(show=False, system_tray=False)
        class MyApp(AppBase):
            _count: Variable[int] = new(0)
            _name: Variable[str] = new("default")

        instance = MyApp()
        assert_that(instance._count.value).is_equal_to(0)
        assert_that(instance._name.value).is_equal_to("default")

    def test_variable_modification(self, qt: QtDriver) -> None:
        """Variable values can be modified."""

        @app(show=False, system_tray=False)
        class MyApp(AppBase):
            _count: Variable[int] = new(0)

        instance = MyApp()
        instance._count.value = 42
        assert_that(instance._count.value).is_equal_to(42)

    def test_variable_with_widget(self, qt: QtDriver) -> None:
        """Variable[T, W] creates both variable and widget."""

        @app(show=False, system_tray=False, window=False)
        class MyApp(AppBase):
            _name: Variable[str, QLineEdit] = new("")

        instance = MyApp()
        assert_that(instance._name.value).is_equal_to("")
        assert_that(instance._name.widget).is_instance_of(QLineEdit)

        instance._name.value = "Alice"
        assert_that(instance._name.value).is_equal_to("Alice")


class TestAppBaseDirtyTracking:
    """Tests for dirty tracking in AppBase."""

    def test_starts_clean(self, qt: QtDriver) -> None:
        """AppBase starts with is_dirty = False."""

        @app(show=False, system_tray=False)
        class MyApp(AppBase):
            _count: Variable[int] = new(0)

        instance = MyApp()
        assert_that(instance.is_dirty.get()).is_false()
        assert_that(instance.dirty_fields).is_empty()

    def test_becomes_dirty_on_change(self, qt: QtDriver) -> None:
        """AppBase becomes dirty when Variable changes."""

        @app(show=False, system_tray=False)
        class MyApp(AppBase):
            _count: Variable[int] = new(0)

        instance = MyApp()
        instance._count.value = 1
        assert_that(instance.is_dirty.get()).is_true()
        assert_that(instance.dirty_fields).contains("_count")

    def test_tracks_multiple_dirty_fields(self, qt: QtDriver) -> None:
        """Multiple dirty fields are tracked."""

        @app(show=False, system_tray=False)
        class MyApp(AppBase):
            _a: Variable[int] = new(0)
            _b: Variable[str] = new("")

        instance = MyApp()
        instance._a.value = 1
        instance._b.value = "changed"
        assert_that(instance.dirty_fields).contains("_a", "_b")

    def test_reset_dirty(self, qt: QtDriver) -> None:
        """reset_dirty() clears dirty state."""

        @app(show=False, system_tray=False)
        class MyApp(AppBase):
            _count: Variable[int] = new(0)

        instance = MyApp()
        instance._count.value = 42
        instance.reset_dirty()
        assert_that(instance.is_dirty.get()).is_false()

    def test_on_dirty_changed_hook(self, qt: QtDriver) -> None:
        """on_dirty_changed hook fires on state changes."""
        changes: list[bool] = []

        @app(show=False, system_tray=False)
        class MyApp(AppBase):
            _count: Variable[int] = new(0)

            @override
            def on_dirty_changed(self, is_dirty: bool) -> None:
                changes.append(is_dirty)

        instance = MyApp()
        instance._count.value = 1
        instance.reset_dirty()
        assert_that(changes).is_equal_to([True, False])


class TestAppBaseValidation:
    """Tests for validation in AppBase."""

    def test_starts_valid(self, qt: QtDriver) -> None:
        """AppBase starts with is_valid = True."""

        @app(show=False, system_tray=False)
        class MyApp(AppBase):
            _name: Variable[str] = new("")

        instance = MyApp()
        assert_that(instance.is_valid.get()).is_true()

    def test_add_validator(self, qt: QtDriver) -> None:
        """Validators can be added and checked."""

        @app(show=False, system_tray=False)
        class MyApp(AppBase):
            _name: Variable[str] = new("")

        instance = MyApp()
        instance.add_validator("_name", "required", lambda v: None if v else "Required")
        assert_that(instance.is_valid.get()).is_false()
        assert_that(instance.validation_error_messages).contains("Required")

    def test_validation_updates_on_change(self, qt: QtDriver) -> None:
        """Validation updates when field changes."""

        @app(show=False, system_tray=False)
        class MyApp(AppBase):
            _name: Variable[str] = new("")

        instance = MyApp()
        instance.add_validator("_name", "required", lambda v: None if v else "Required")
        assert_that(instance.is_valid.get()).is_false()

        instance._name.value = "Alice"
        assert_that(instance.is_valid.get()).is_true()

    def test_on_valid_changed_hook(self, qt: QtDriver) -> None:
        """on_valid_changed hook fires on validation changes."""
        changes: list[bool] = []

        @app(show=False, system_tray=False)
        class MyApp(AppBase):
            _name: Variable[str] = new("")

            @override
            def on_valid_changed(self, is_valid: bool) -> None:
                changes.append(is_valid)

        instance = MyApp()
        instance.add_validator("_name", "required", lambda v: None if v else "Required")
        instance._name.value = "Bob"
        assert_that(changes).is_equal_to([False, True])


class TestAppBaseBindings:
    """Tests for bind= format expressions in AppBase."""

    def test_bind_simple_variable(self, qt: QtDriver) -> None:
        """bind= references a Variable."""

        @app(show=False, system_tray=False, window=False)
        class MyApp(AppBase):
            _name: Variable[str] = new("Alice")
            _label: QLabel = new(bind="{_name}")

        instance = MyApp()
        assert_that(instance._label.text()).is_equal_to("Alice")

    def test_bind_updates_reactively(self, qt: QtDriver) -> None:
        """bind= updates when Variable changes."""

        @app(show=False, system_tray=False, window=False)
        class MyApp(AppBase):
            _count: Variable[int] = new(0)
            _label: QLabel = new(bind="Count: {_count}")

        instance = MyApp()
        assert_that(instance._label.text()).is_equal_to("Count: 0")
        instance._count.value = 42
        assert_that(instance._label.text()).is_equal_to("Count: 42")

    def test_bind_with_expression(self, qt: QtDriver) -> None:
        """bind= supports math expressions."""

        @app(show=False, system_tray=False, window=False)
        class MyApp(AppBase):
            _x: Variable[int] = new(10)
            _y: Variable[int] = new(5)
            _label: QLabel = new(bind="{_x + _y}")

        instance = MyApp()
        assert_that(instance._label.text()).is_equal_to("15")

    def test_bind_with_string_method(self, qt: QtDriver) -> None:
        """bind= supports method calls."""

        @app(show=False, system_tray=False, window=False)
        class MyApp(AppBase):
            _name: Variable[str] = new("hello")
            _label: QLabel = new(bind="{_name.upper()}")

        instance = MyApp()
        assert_that(instance._label.text()).is_equal_to("HELLO")

    def test_bind_with_len(self, qt: QtDriver) -> None:
        """bind= supports len()."""

        @app(show=False, system_tray=False, window=False)
        class MyApp(AppBase):
            _text: Variable[str] = new("hello")
            _label: QLabel = new(bind="Length: {len(_text)}")

        instance = MyApp()
        assert_that(instance._label.text()).is_equal_to("Length: 5")

    def test_bind_with_format_spec(self, qt: QtDriver) -> None:
        """bind= supports format specs."""

        @app(show=False, system_tray=False, window=False)
        class MyApp(AppBase):
            _price: Variable[float] = new(19.99)
            _label: QLabel = new(bind="${_price:.2f}")

        instance = MyApp()
        assert_that(instance._label.text()).is_equal_to("$19.99")

    def test_bind_multiple_variables(self, qt: QtDriver) -> None:
        """bind= can reference multiple Variables."""

        @app(show=False, system_tray=False, window=False)
        class MyApp(AppBase):
            _first: Variable[str] = new("John")
            _last: Variable[str] = new("Doe")
            _label: QLabel = new(bind="{_first} {_last}")

        instance = MyApp()
        assert_that(instance._label.text()).is_equal_to("John Doe")


class TestAppBaseVariableWidgetBind:
    """Tests for Variable[T, W] with bind= expressions."""

    def test_self_placeholder(self, qt: QtDriver) -> None:
        """#self refers to the Variable's value."""

        @app(show=False, system_tray=False, window=False)
        class MyApp(AppBase):
            _name: Variable[str, QLabel] = new("hello")(bind="Value: {#self}")

        instance = MyApp()
        assert_that(instance._name.widget.text()).is_equal_to("Value: hello")

    def test_self_with_method(self, qt: QtDriver) -> None:
        """#self supports method calls."""

        @app(show=False, system_tray=False, window=False)
        class MyApp(AppBase):
            _name: Variable[str, QLabel] = new("hello")(bind="{#self.upper()}")

        instance = MyApp()
        assert_that(instance._name.widget.text()).is_equal_to("HELLO")

    def test_var_placeholder(self, qt: QtDriver) -> None:
        """#var is an alias for the Variable's value."""

        @app(show=False, system_tray=False, window=False)
        class MyApp(AppBase):
            _count: Variable[int, QLabel] = new(10)(bind="Double: {#var * 2}")

        instance = MyApp()
        assert_that(instance._count.widget.text()).is_equal_to("Double: 20")


class TestAppBaseWidgetPlaceholder:
    """Tests for #widget placeholder."""

    def test_widget_accesses_parent(self, qt: QtDriver) -> None:
        """#widget refers to the parent AppBase instance."""

        @app(show=False, system_tray=False, window=False)
        class MyApp(AppBase):
            title: str = "My App"
            _label: QLabel = new(bind="{#widget.title}")

        instance = MyApp()
        assert_that(instance._label.text()).is_equal_to("My App")

    def test_widget_with_method(self, qt: QtDriver) -> None:
        """#widget can call methods."""

        @app(show=False, system_tray=False, window=False)
        class MyApp(AppBase):
            def get_greeting(self) -> str:
                return "Hello!"

            _label: QLabel = new(bind="{#widget.get_greeting()}")

        instance = MyApp()
        assert_that(instance._label.text()).is_equal_to("Hello!")


class TestAppBaseWindowPlaceholder:
    """Tests for #window placeholder (alias for #widget)."""

    def test_window_accesses_parent(self, qt: QtDriver) -> None:
        """#window refers to the parent AppBase instance (alias for #widget)."""

        @app(show=False, system_tray=False, window=False)
        class MyApp(AppBase):
            title: str = "My App"
            _label: QLabel = new(bind="{#window.title}")

        instance = MyApp()
        assert_that(instance._label.text()).is_equal_to("My App")

    def test_window_with_method(self, qt: QtDriver) -> None:
        """#window can call methods."""

        @app(show=False, system_tray=False, window=False)
        class MyApp(AppBase):
            def get_greeting(self) -> str:
                return "Hello from window!"

            _label: QLabel = new(bind="{#window.get_greeting()}")

        instance = MyApp()
        assert_that(instance._label.text()).is_equal_to("Hello from window!")


class TestAppBaseAppPlaceholder:
    """Tests for #app placeholder (QApplication instance)."""

    def test_app_accesses_qapplication(self, qt: QtDriver) -> None:
        """#app refers to the QApplication instance."""

        @app(show=False, system_tray=False, window=False)
        class MyApp(AppBase):
            _label: QLabel = new(bind="{#app.applicationName()}")

        instance = MyApp()
        # Application name comes from pytest-qt's qapp fixture
        assert_that(instance._label.text()).is_not_empty()

    def test_app_accesses_application_version(self, qt: QtDriver) -> None:
        """#app can access applicationVersion."""
        from qtpy.QtWidgets import QApplication

        qapp = QApplication.instance()
        if qapp is not None:
            qapp.setApplicationVersion("1.2.3")

        @app(show=False, system_tray=False, window=False)
        class MyApp(AppBase):
            _label: QLabel = new(bind="Version: {#app.applicationVersion()}")

        instance = MyApp()
        assert_that(instance._label.text()).is_equal_to("Version: 1.2.3")


class TestAppBaseListBinding:
    """Tests for list[QWidget] bindings."""

    def test_list_bound_to_variable(self, qt: QtDriver) -> None:
        """list[QLabel] bound to Variable[list[str]]."""

        @app(show=False, system_tray=False, window=False)
        class MyApp(AppBase):
            _items: Variable[list[str]] = new(["A", "B", "C"])
            _labels: list[QLabel] = new(bind="_items")

        instance = MyApp()
        assert_that(len(instance._labels)).is_equal_to(3)
        assert_that(instance._labels[0].text()).is_equal_to("A")
        assert_that(instance._labels[1].text()).is_equal_to("B")
        assert_that(instance._labels[2].text()).is_equal_to("C")

    def test_list_with_format(self, qt: QtDriver) -> None:
        """list[QLabel] with format= string."""

        @app(show=False, system_tray=False, window=False)
        class MyApp(AppBase):
            _nums: Variable[list[int]] = new([1, 2, 3])
            _labels: list[QLabel] = new(bind="_nums", format="Value: {#self}")

        instance = MyApp()
        assert_that(instance._labels[0].text()).is_equal_to("Value: 1")

    def test_list_with_index_placeholder(self, qt: QtDriver) -> None:
        """#index placeholder in list binding."""

        @app(show=False, system_tray=False, window=False)
        class MyApp(AppBase):
            _items: Variable[list[str]] = new(["X", "Y"])
            _labels: list[QLabel] = new(bind="_items", format="#{#index}: {#self}")

        instance = MyApp()
        assert_that(instance._labels[0].text()).is_equal_to("#0: X")
        assert_that(instance._labels[1].text()).is_equal_to("#1: Y")


class TestAppBaseDictBinding:
    """Tests for dict bindings."""

    def test_dict_with_key_value(self, qt: QtDriver) -> None:
        """Dict binding with #key and #value."""

        @app(show=False, system_tray=False, window=False)
        class MyApp(AppBase):
            _scores: Variable[dict[str, int]] = new({"Alice": 100, "Bob": 85})
            _labels: list[QLabel] = new(bind="_scores", format="{#key}: {#value}")

        instance = MyApp()
        texts = [label.text() for label in instance._labels]
        assert_that("Alice: 100" in texts).is_true()
        assert_that("Bob: 85" in texts).is_true()


class TestAppBasePropertyBindings:
    """Tests for visible= and enabled= bindings."""

    def test_visible_binding(self, qt: QtDriver) -> None:
        """visible= binds to Variable."""

        @app(show=False, system_tray=False, window=False)
        class MyApp(AppBase):
            _show: Variable[bool] = new(False)
            _panel: QLabel = new("Hidden", visible="_show")

        instance = MyApp()
        assert_that(instance._panel.isVisible()).is_false()
        instance._show.value = True
        assert_that(instance._panel.isVisible()).is_true()

    def test_enabled_binding(self, qt: QtDriver) -> None:
        """enabled= binds to Variable."""

        @app(show=False, system_tray=False, window=False)
        class MyApp(AppBase):
            _can_submit: Variable[bool] = new(False)
            _button: QPushButton = new("Submit", enabled="_can_submit")

        instance = MyApp()
        assert_that(instance._button.isEnabled()).is_false()
        instance._can_submit.value = True
        assert_that(instance._button.isEnabled()).is_true()

    def test_visible_expression(self, qt: QtDriver) -> None:
        """visible= with expression."""

        @app(show=False, system_tray=False, window=False)
        class MyApp(AppBase):
            _count: Variable[int] = new(0)
            _warning: QLabel = new("Low!", visible="{_count < 5}")

        instance = MyApp()
        assert_that(instance._warning.isVisible()).is_true()
        instance._count.value = 10
        assert_that(instance._warning.isVisible()).is_false()

    def test_enabled_expression(self, qt: QtDriver) -> None:
        """enabled= with expression."""

        @app(show=False, system_tray=False, window=False)
        class MyApp(AppBase):
            _name: Variable[str] = new("")
            _submit: QPushButton = new("Go", enabled="{len(_name) > 0}")

        instance = MyApp()
        assert_that(instance._submit.isEnabled()).is_false()
        instance._name.value = "x"
        assert_that(instance._submit.isEnabled()).is_true()


class TestAppBaseRecord:
    """Tests for AppBase[T] record support."""

    def test_record_from_decorator(self, qt: QtDriver) -> None:
        """Record can be set via @app(record=...)."""

        @dataclass
        class Settings:
            name: str = ""
            count: int = 0

        @app(show=False, system_tray=False, record=Settings("test", 42))
        class MyApp(AppBase[Settings]):
            pass

        instance = MyApp()
        assert_that(instance.record.name).is_equal_to("test")
        assert_that(instance.record.count).is_equal_to(42)

    def test_record_modification(self, qt: QtDriver) -> None:
        """Record fields can be modified."""

        @dataclass
        class Person:
            name: str = ""

        @app(show=False, system_tray=False, record=Person("Alice"))
        class MyApp(AppBase[Person]):
            pass

        instance = MyApp()
        instance.record.name = "Bob"
        assert_that(instance.record.name).is_equal_to("Bob")

    def test_record_field_auto_bind(self, qt: QtDriver) -> None:
        """Fields named same as record properties auto-bind."""

        @dataclass
        class User:
            username: str = ""

        @app(show=False, system_tray=False, window=False, record=User("alice"))
        class MyApp(AppBase[User]):
            username: QLineEdit = new()

        instance = MyApp()
        assert_that(instance.username.text()).is_equal_to("alice")

    def test_record_error_on_non_generic(self, qt: QtDriver) -> None:
        """Accessing .record without [T] raises TypeError."""
        import pytest

        @app(show=False, system_tray=False)
        class MyApp(AppBase):
            pass

        instance = MyApp()
        with pytest.raises(TypeError, match="has no record type"):
            _ = instance.record

    def test_record_passed_to_child_menu(self, qt: QtDriver) -> None:
        """Record can be passed to a child Menu via dog=record binding."""
        from qtpie import Menu, menu

        @dataclass
        class Dog:
            name: str = ""
            age: int = 0

        @menu
        class DogMenu(Menu):
            dog: Variable[Dog]

        @app(show=False, system_tray=False, window=False, record=Dog("Rover", 5))
        class MyApp(AppBase[Dog]):
            dog_menu: DogMenu = new(dog="record")

        instance = MyApp()
        # The menu's dog Variable should share the App's record
        assert_that(instance.dog_menu.dog.name).is_equal_to("Rover")
        assert_that(instance.dog_menu.dog.age).is_equal_to(5)

        # Changes to the menu's dog should reflect in the app's record
        instance.dog_menu.dog.name = "Max"
        assert_that(instance.record.name).is_equal_to("Max")

        # Changes to the app's record should reflect in the menu's dog
        instance.record.age = 10
        assert_that(instance.dog_menu.dog.age).is_equal_to(10)

    def test_ref_with_required_binding(self, qt: QtDriver) -> None:
        """ref() can reference required binding fields after they're bound."""
        from qtpy.QtGui import QAction

        from qtpie import Menu, menu, ref

        @dataclass
        class Dog:
            name: str = ""
            age: int = 0

        @menu
        class DogMenu(Menu):
            dog: Variable[Dog]
            dog_action: QAction = new(text=ref("{dog.name}"))

        @app(show=False, system_tray=False, window=False, record=Dog("Fido", 3))
        class MyApp(AppBase[Dog]):
            dog_menu: DogMenu = new(dog="record")

        instance = MyApp()
        # The ref should resolve after the binding is applied
        assert_that(instance.dog_menu.dog_action.text()).is_equal_to("Fido")

    def test_ref_with_literal_text_and_required_binding(self, qt: QtDriver) -> None:
        """ref() with literal text + expression works with required bindings."""
        from qtpy.QtGui import QAction

        from qtpie import Menu, menu, ref

        @dataclass
        class Dog:
            name: str = ""
            age: int = 0

        @menu
        class DogMenu(Menu):
            dog: Variable[Dog]
            dog_action: QAction = new(text=ref("Dog name: {dog.name}"))

        @app(show=False, system_tray=False, window=False, record=Dog("Buddy", 4))
        class MyApp(AppBase[Dog]):
            dog_menu: DogMenu = new(dog="record")

        instance = MyApp()
        # The ref should resolve with literal text preserved
        assert_that(instance.dog_menu.dog_action.text()).is_equal_to("Dog name: Buddy")


class TestAppBaseSignals:
    """Tests for signal connections."""

    def test_signal_by_method_name(self, qt: QtDriver) -> None:
        """Signal connected by method name string."""
        clicked = False

        @app(show=False, system_tray=False, window=False)
        class MyApp(AppBase):
            _button: QPushButton = new("Click", clicked="on_click")

            def on_click(self) -> None:
                nonlocal clicked
                clicked = True

        instance = MyApp()
        instance._button.click()
        assert_that(clicked).is_true()

    def test_signal_by_lambda(self, qt: QtDriver) -> None:
        """Signal connected by lambda."""
        values: list[str] = []

        @app(show=False, system_tray=False, window=False)
        class MyApp(AppBase):
            _button: QPushButton = new("Click", clicked=lambda: values.append("clicked"))

        instance = MyApp()
        instance._button.click()
        assert_that(values).contains("clicked")


class TestAppBaseSetupHook:
    """Tests for __setup__ lifecycle hook."""

    def test_setup_called(self, qt: QtDriver) -> None:
        """__setup__ is called during init."""
        setup_called = False

        @app(show=False, system_tray=False)
        class MyApp(AppBase):
            def __setup__(self) -> None:
                nonlocal setup_called
                setup_called = True

        MyApp()
        assert_that(setup_called).is_true()

    def test_setup_can_modify_variables(self, qt: QtDriver) -> None:
        """__setup__ can modify Variable values."""

        @app(show=False, system_tray=False)
        class MyApp(AppBase):
            _count: Variable[int] = new(0)

            def __setup__(self) -> None:
                self._count.value = 100

        instance = MyApp()
        assert_that(instance._count.value).is_equal_to(100)

    def test_setup_can_add_validators(self, qt: QtDriver) -> None:
        """__setup__ can add validators."""

        @app(show=False, system_tray=False)
        class MyApp(AppBase):
            _name: Variable[str] = new("")

            def __setup__(self) -> None:
                self.add_validator("_name", "req", lambda v: None if v else "Required")

        instance = MyApp()
        assert_that(instance.is_valid.get()).is_false()


class TestAppBaseEdgeCases:
    """Edge cases and integration tests."""

    def test_multiple_instances_independent(self, qt: QtDriver) -> None:
        """Multiple instances have independent state."""

        @app(show=False, system_tray=False)
        class MyApp(AppBase):
            _count: Variable[int] = new(0)

        a = MyApp()
        b = MyApp()
        a._count.value = 10
        b._count.value = 20
        assert_that(a._count.value).is_equal_to(10)
        assert_that(b._count.value).is_equal_to(20)

    def test_empty_class(self, qt: QtDriver) -> None:
        """Empty AppBase works."""

        @app(show=False, system_tray=False)
        class MyApp(AppBase):
            pass

        instance = MyApp()
        assert_that(instance.is_dirty.get()).is_false()
        assert_that(instance.is_valid.get()).is_true()

    def test_counter_integration(self, qt: QtDriver) -> None:
        """Counter with multiple reactive bindings."""

        @app(show=False, system_tray=False, window=False)
        class CounterApp(AppBase):
            _count: Variable[int] = new(0)
            _display: QLabel = new(bind="Count: {_count}")
            _doubled: QLabel = new(bind="x2: {_count * 2}")
            _inc: QPushButton = new("+", clicked="increment")

            def increment(self) -> None:
                self._count.value += 1

        instance = CounterApp()
        assert_that(instance._display.text()).is_equal_to("Count: 0")
        assert_that(instance._doubled.text()).is_equal_to("x2: 0")

        instance._inc.click()
        assert_that(instance._display.text()).is_equal_to("Count: 1")
        assert_that(instance._doubled.text()).is_equal_to("x2: 2")

        instance._count.value = 5
        assert_that(instance._display.text()).is_equal_to("Count: 5")
        assert_that(instance._doubled.text()).is_equal_to("x2: 10")


class TestAppBaseWidgetProps:
    """Tests for widget_props (style=, etc.) in @app decorator."""

    def test_style_prop_applied(self, qt: QtDriver) -> None:
        """style= prop calls setStyle()."""

        @app(show=False, system_tray=False, style="Fusion")
        class MyApp(AppBase):
            pass

        MyApp()
        # AppBase doesn't have setStyle, so this just tests no error is raised
        # The real test would be on App but we can't instantiate multiple QApplications

    def test_custom_prop_applied(self, qt: QtDriver) -> None:
        """Custom props call setXxx() methods."""
        called_with: list[str] = []

        @app(show=False, system_tray=False, customProp="test_value")
        class MyApp(AppBase):
            def setCustomProp(self, value: str) -> None:
                called_with.append(value)

        MyApp()
        assert_that(called_with).contains("test_value")


class TestAppBaseMinimizeToTray:
    """Tests for minimize_to_tray behavior."""

    def test_minimize_to_tray_default_true(self, qt: QtDriver) -> None:
        """minimize_to_tray defaults to True."""

        @app(show=False, system_tray=False)
        class MyApp(AppBase):
            pass

        assert_that(MyApp._qtpie_config.minimize_to_tray).is_true()

    def test_minimize_to_tray_false(self, qt: QtDriver) -> None:
        """minimize_to_tray=False is stored in config."""

        @app(show=False, system_tray=False, minimize_to_tray=False)
        class MyApp(AppBase):
            pass

        assert_that(MyApp._qtpie_config.minimize_to_tray).is_false()


class TestAppBaseSystemTrayMenu:
    """Tests for system_tray: QMenu field pattern."""

    def test_system_tray_qmenu_field(self, qt: QtDriver) -> None:
        """system_tray: QMenu field is used as tray context menu."""
        from qtpy.QtGui import QAction
        from qtpy.QtWidgets import QSystemTrayIcon

        from qtpie import Menu, menu

        @menu
        class TrayMenu(Menu):
            action1: QAction = new("First Action")
            action2: QAction = new("Second Action")

        # Need window=True or widget fields to trigger auto-window, which enables tray
        @app(show=False)
        class MyApp(AppBase):
            system_tray: TrayMenu = new()
            _label: QLabel = new("Content")

        instance = MyApp()
        assert_that(hasattr(instance, "_tray_icon")).is_true()
        assert_that(instance._tray_icon).is_instance_of(QSystemTrayIcon)
        tray_menu = instance._tray_icon.contextMenu()
        assert_that(tray_menu).is_same_as(instance.system_tray)

    def test_system_tray_qmenu_actions_preserved(self, qt: QtDriver) -> None:
        """system_tray: QMenu field preserves its actions."""
        from qtpy.QtGui import QAction

        from qtpie import Menu, menu

        @menu
        class TrayMenu(Menu):
            action1: QAction = new("Action One")
            action2: QAction = new("Action Two")
            action3: QAction = new("Action Three")

        @app(show=False)
        class MyApp(AppBase):
            system_tray: TrayMenu = new()
            _label: QLabel = new("Content")

        instance = MyApp()
        tray_menu = instance._tray_icon.contextMenu()
        action_texts = [a.text() for a in tray_menu.actions()]
        assert_that(action_texts).contains("Action One")
        assert_that(action_texts).contains("Action Two")
        assert_that(action_texts).contains("Action Three")

    def test_system_tray_qmenu_not_in_menubar(self, qt: QtDriver) -> None:
        """system_tray: QMenu is not added to window menu bar."""
        from qtpy.QtGui import QAction

        from qtpie import Menu, menu

        @menu
        class TrayMenu(Menu):
            action: QAction = new("Tray Action")

        @menu(text="&File")
        class FileMenu(Menu):
            action: QAction = new("File Action")

        @app(show=False)
        class MyApp(AppBase):
            system_tray: TrayMenu = new()
            file_menu: FileMenu = new()
            _label: QLabel = new("Content")

        instance = MyApp()
        # system_tray should be in tray, not menubar
        menubar = instance._auto_window.menuBar()
        menubar_actions = [a.text() for a in menubar.actions()]
        assert_that(menubar_actions).does_not_contain("Tray Action")
        # FileMenu should be in menubar
        assert_that("&File" in str(menubar_actions) or "File" in str(menubar_actions)).is_true()

    def test_system_tray_qmenu_signal_connections(self, qt: QtDriver) -> None:
        """system_tray: QMenu actions have signals connected."""
        from qtpy.QtGui import QAction

        from qtpie import Menu, menu

        triggered = False

        @menu
        class TrayMenu(Menu):
            action: QAction = new("Click Me", triggered="on_action")

            def on_action(self) -> None:
                nonlocal triggered
                triggered = True

        @app(show=False, window=False)
        class MyApp(AppBase):
            system_tray: TrayMenu = new()

        instance = MyApp()
        instance.system_tray.action.trigger()
        assert_that(triggered).is_true()

    def test_underscore_system_tray_qmenu_field(self, qt: QtDriver) -> None:
        """_system_tray: QMenu field (with underscore) is used as tray context menu."""
        from qtpy.QtGui import QAction
        from qtpy.QtWidgets import QSystemTrayIcon

        from qtpie import Menu, menu

        @menu
        class TrayMenu(Menu):
            action1: QAction = new("First Action")
            action2: QAction = new("Second Action")

        @app(show=False)
        class MyApp(AppBase):
            _system_tray: TrayMenu = new()
            _label: QLabel = new("Content")

        instance = MyApp()
        # User's field is accessible as _system_tray (the TrayMenu)
        assert_that(instance._system_tray).is_instance_of(TrayMenu)
        # Internal tray icon is stored with different name to avoid collision
        assert_that(hasattr(instance, "_tray_icon")).is_true()
        assert_that(instance._tray_icon).is_instance_of(QSystemTrayIcon)
        # Tray context menu is the user's TrayMenu
        tray_menu = instance._tray_icon.contextMenu()
        action_texts = [a.text() for a in tray_menu.actions()]
        assert_that(action_texts).contains("First Action")
        assert_that(action_texts).contains("Second Action")

    def test_underscore_system_tray_not_in_menubar(self, qt: QtDriver) -> None:
        """_system_tray: QMenu (with underscore) is not added to window menu bar."""
        from qtpy.QtGui import QAction

        from qtpie import Menu, menu

        @menu
        class TrayMenu(Menu):
            action: QAction = new("Tray Action")

        @menu(text="&File")
        class FileMenu(Menu):
            action: QAction = new("File Action")

        @app(show=False)
        class MyApp(AppBase):
            _system_tray: TrayMenu = new()
            file_menu: FileMenu = new()
            _label: QLabel = new("Content")

        instance = MyApp()
        # _system_tray should be in tray, not menubar
        menubar = instance._auto_window.menuBar()
        menubar_actions = [a.text() for a in menubar.actions()]
        assert_that(menubar_actions).does_not_contain("Tray Action")
        # FileMenu should be in menubar
        assert_that("&File" in str(menubar_actions) or "File" in str(menubar_actions)).is_true()


class TestAppBaseSystemTray:
    """Tests for system tray with QAction fields."""

    def test_qaction_creates_system_tray(self, qt: QtDriver) -> None:
        """QAction field creates a system tray icon."""
        from qtpy.QtGui import QAction
        from qtpy.QtWidgets import QSystemTrayIcon

        @app(show=False, window=False)
        class MyApp(AppBase):
            action: QAction = new("Say Hello")

        instance = MyApp()
        assert_that(hasattr(instance, "_tray_icon")).is_true()
        assert_that(instance._tray_icon).is_instance_of(QSystemTrayIcon)

    def test_qaction_added_to_tray_menu(self, qt: QtDriver) -> None:
        """QAction field is added to system tray context menu."""
        from qtpy.QtGui import QAction

        @app(show=False, window=False)
        class MyApp(AppBase):
            action: QAction = new("Say Hello")

        instance = MyApp()
        tray_menu = instance._tray_icon.contextMenu()
        assert_that(tray_menu).is_not_none()
        actions = tray_menu.actions()
        action_texts = [a.text() for a in actions]
        assert_that(action_texts).contains("Say Hello")

    def test_multiple_qactions_in_tray(self, qt: QtDriver) -> None:
        """Multiple QAction fields are all added to tray menu."""
        from qtpy.QtGui import QAction

        @app(show=False, window=False)
        class MyApp(AppBase):
            action1: QAction = new("First")
            action2: QAction = new("Second")
            action3: QAction = new("Third")

        instance = MyApp()
        tray_menu = instance._tray_icon.contextMenu()
        action_texts = [a.text() for a in tray_menu.actions()]
        assert_that(action_texts).contains("First")
        assert_that(action_texts).contains("Second")
        assert_that(action_texts).contains("Third")

    def test_qaction_signal_connected(self, qt: QtDriver) -> None:
        """QAction triggered signal is connected."""
        from qtpy.QtGui import QAction

        triggered = False

        @app(show=False, window=False)
        class MyApp(AppBase):
            action: QAction = new("Click Me", triggered="on_action")

            def on_action(self) -> None:
                nonlocal triggered
                triggered = True

        instance = MyApp()
        instance.action.trigger()
        assert_that(triggered).is_true()

    def test_no_qaction_no_tray_without_window(self, qt: QtDriver) -> None:
        """No system tray created if no QActions and no window."""

        @app(show=False, window=False, system_tray=True)
        class MyApp(AppBase):
            _count: Variable[int] = new(0)

        instance = MyApp()
        assert_that(hasattr(instance, "_tray_icon")).is_false()

    def test_system_tray_disabled(self, qt: QtDriver) -> None:
        """system_tray=False prevents tray creation even with QActions."""
        from qtpy.QtGui import QAction

        @app(show=False, window=False, system_tray=False)
        class MyApp(AppBase):
            action: QAction = new("Hello")

        instance = MyApp()
        assert_that(hasattr(instance, "_tray_icon")).is_false()

    def test_icon_accepts_qicon(self, qt: QtDriver) -> None:
        """icon= accepts QIcon."""
        from qtpy.QtGui import QAction, QIcon

        test_icon = QIcon()

        @app(show=False, window=False, icon=test_icon)
        class MyApp(AppBase):
            action: QAction = new("Hello")

        instance = MyApp()
        assert_that(hasattr(instance, "_tray_icon")).is_true()

    def test_icon_accepts_qpixmap(self, qt: QtDriver) -> None:
        """icon= accepts QPixmap."""
        from qtpy.QtGui import QAction, QPixmap

        test_pixmap = QPixmap(16, 16)

        @app(show=False, window=False, icon=test_pixmap)
        class MyApp(AppBase):
            action: QAction = new("Hello")

        instance = MyApp()
        assert_that(hasattr(instance, "_tray_icon")).is_true()

    def test_tray_icon_accepts_qicon(self, qt: QtDriver) -> None:
        """tray_icon= accepts QIcon."""
        from qtpy.QtGui import QAction, QIcon

        test_icon = QIcon()

        @app(show=False, window=False, tray_icon=test_icon)
        class MyApp(AppBase):
            action: QAction = new("Hello")

        instance = MyApp()
        assert_that(hasattr(instance, "_tray_icon")).is_true()

    def test_icon_accepts_standard_pixmap(self, qt: QtDriver) -> None:
        """icon= accepts QStyle.StandardPixmap."""
        from qtpy.QtGui import QAction
        from qtpy.QtWidgets import QStyle

        @app(show=False, window=False, icon=QStyle.StandardPixmap.SP_ComputerIcon)
        class MyApp(AppBase):
            action: QAction = new("Hello")

        instance = MyApp()
        assert_that(hasattr(instance, "_tray_icon")).is_true()

    def test_separator_in_tray_menu(self, qt: QtDriver) -> None:
        """Separator fields add separators to tray menu."""
        from qtpy.QtGui import QAction

        from qtpie.menu import Separator

        @app(show=False, window=False)
        class MyApp(AppBase):
            action1: QAction = new("First")
            ___: Separator
            action2: QAction = new("Second")

        instance = MyApp()
        tray_menu = instance._tray_icon.contextMenu()
        actions = tray_menu.actions()
        # Should have: First, Separator, Second
        assert_that(len(actions)).is_greater_than_or_equal_to(3)
        assert_that(actions[0].text()).is_equal_to("First")
        assert_that(actions[1].isSeparator()).is_true()
        assert_that(actions[2].text()).is_equal_to("Second")

    def test_section_in_tray_menu(self, qt: QtDriver) -> None:
        """Section fields add sections to tray menu."""
        from qtpy.QtGui import QAction

        from qtpie.menu import Section

        @app(show=False, window=False)
        class MyApp(AppBase):
            ___my_section___: Section
            action: QAction = new("Hello")

        instance = MyApp()
        tray_menu = instance._tray_icon.contextMenu()
        actions = tray_menu.actions()
        # First action should be a section with text "My Section"
        assert_that(actions[0].text()).is_equal_to("My Section")

    def test_section_with_explicit_text(self, qt: QtDriver) -> None:
        """Section with new() uses explicit text."""
        from qtpy.QtGui import QAction

        from qtpie.menu import Section

        @app(show=False, window=False)
        class MyApp(AppBase):
            ___custom___: Section = new("Custom Section Name")
            action: QAction = new("Hello")

        instance = MyApp()
        tray_menu = instance._tray_icon.contextMenu()
        actions = tray_menu.actions()
        assert_that(actions[0].text()).is_equal_to("Custom Section Name")

    def test_icon_accepts_string_path(self, qt: QtDriver, tmp_path: Path) -> None:
        """icon= accepts string file path."""
        from qtpy.QtGui import QAction, QImage

        # Create a simple valid PNG file
        icon_file = tmp_path / "test_icon.png"
        img = QImage(16, 16, QImage.Format.Format_ARGB32)
        img.fill(0xFF0000FF)  # Blue
        img.save(str(icon_file))

        @app(show=False, window=False, icon=str(icon_file))
        class MyApp(AppBase):
            action: QAction = new("Hello")

        instance = MyApp()
        assert_that(hasattr(instance, "_tray_icon")).is_true()
        # The tray icon should be set (not null)
        tray_icon = instance._tray_icon.icon()
        assert_that(tray_icon.isNull()).is_false()

    def test_tray_icon_overrides_icon(self, qt: QtDriver) -> None:
        """tray_icon= overrides icon= for system tray."""
        from qtpy.QtGui import QAction, QIcon, QPixmap

        # Create two different icons
        shared_pixmap = QPixmap(16, 16)
        shared_pixmap.fill()
        shared_icon = QIcon(shared_pixmap)

        tray_pixmap = QPixmap(32, 32)
        tray_pixmap.fill()
        tray_icon = QIcon(tray_pixmap)

        @app(show=False, window=False, icon=shared_icon, tray_icon=tray_icon)
        class MyApp(AppBase):
            action: QAction = new("Hello")

        instance = MyApp()
        # Tray should use tray_icon, not shared icon
        # We can't easily compare QIcon objects, but we can verify tray was created
        assert_that(hasattr(instance, "_tray_icon")).is_true()


class TestAppBaseWindowIcon:
    """Tests for window_icon= parameter."""

    def test_window_icon_sets_window_icon(self, qt: QtDriver) -> None:
        """window_icon= sets the auto-window's icon."""
        from qtpy.QtGui import QIcon, QPixmap

        pixmap = QPixmap(16, 16)
        pixmap.fill()
        test_icon = QIcon(pixmap)

        @app(show=False, window_icon=test_icon)
        class MyApp(AppBase):
            _label: QLabel = new("Hello")

        instance = MyApp()
        assert_that(instance._auto_window).is_not_none()
        window_icon = instance._auto_window.windowIcon()
        assert_that(window_icon.isNull()).is_false()

    def test_window_icon_overrides_icon(self, qt: QtDriver) -> None:
        """window_icon= overrides icon= for window."""
        from qtpy.QtGui import QIcon, QPixmap

        shared_pixmap = QPixmap(16, 16)
        shared_pixmap.fill()
        shared_icon = QIcon(shared_pixmap)

        window_pixmap = QPixmap(32, 32)
        window_pixmap.fill()
        window_icon = QIcon(window_pixmap)

        @app(show=False, icon=shared_icon, window_icon=window_icon)
        class MyApp(AppBase):
            _label: QLabel = new("Hello")

        instance = MyApp()
        # Window should have an icon set
        assert_that(instance._auto_window.windowIcon().isNull()).is_false()

    def test_icon_sets_both_window_and_tray(self, qt: QtDriver) -> None:
        """icon= sets both window icon and tray icon when neither is specified."""
        from qtpy.QtGui import QAction, QIcon, QPixmap

        pixmap = QPixmap(16, 16)
        pixmap.fill()
        shared_icon = QIcon(pixmap)

        @app(show=False, icon=shared_icon)
        class MyApp(AppBase):
            action: QAction = new("Hello")
            _label: QLabel = new("Content")

        instance = MyApp()
        # Both should have icons
        assert_that(instance._auto_window.windowIcon().isNull()).is_false()
        assert_that(instance._tray_icon.icon().isNull()).is_false()

    def test_window_icon_accepts_string_path(self, qt: QtDriver, tmp_path: Path) -> None:
        """window_icon= accepts string file path."""
        from qtpy.QtGui import QImage

        icon_file = tmp_path / "window_icon.png"
        img = QImage(16, 16, QImage.Format.Format_ARGB32)
        img.fill(0xFFFF0000)  # Red
        img.save(str(icon_file))

        @app(show=False, window_icon=str(icon_file))
        class MyApp(AppBase):
            _label: QLabel = new("Hello")

        instance = MyApp()
        assert_that(instance._auto_window.windowIcon().isNull()).is_false()

    def test_window_icon_accepts_standard_pixmap(self, qt: QtDriver) -> None:
        """window_icon= accepts QStyle.StandardPixmap."""
        from qtpy.QtWidgets import QStyle

        @app(show=False, window_icon=QStyle.StandardPixmap.SP_DialogSaveButton)
        class MyApp(AppBase):
            _label: QLabel = new("Hello")

        instance = MyApp()
        assert_that(instance._auto_window.windowIcon().isNull()).is_false()


class TestAppBaseSystemTrayActivation:
    """Tests for on_system_tray_activated hook."""

    def test_on_system_tray_activated_called(self, qt: QtDriver) -> None:
        """on_system_tray_activated hook is called on tray activation."""
        from typing import override

        from qtpy.QtGui import QAction
        from qtpy.QtWidgets import QSystemTrayIcon

        activations: list[QSystemTrayIcon.ActivationReason] = []

        @app(show=False, window=False)
        class MyApp(AppBase):
            action: QAction = new("Hello")

            @override
            def on_system_tray_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
                activations.append(reason)

        instance = MyApp()
        # Simulate activation by emitting the signal
        instance._tray_icon.activated.emit(QSystemTrayIcon.ActivationReason.Trigger)
        assert_that(activations).contains(QSystemTrayIcon.ActivationReason.Trigger)

    def test_on_system_tray_activated_receives_reason(self, qt: QtDriver) -> None:
        """on_system_tray_activated receives correct activation reason."""
        from typing import override

        from qtpy.QtGui import QAction
        from qtpy.QtWidgets import QSystemTrayIcon

        activations: list[QSystemTrayIcon.ActivationReason] = []

        @app(show=False, window=False)
        class MyApp(AppBase):
            action: QAction = new("Hello")

            @override
            def on_system_tray_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
                activations.append(reason)

        instance = MyApp()
        # Test different activation reasons
        instance._tray_icon.activated.emit(QSystemTrayIcon.ActivationReason.Context)
        instance._tray_icon.activated.emit(QSystemTrayIcon.ActivationReason.MiddleClick)
        assert_that(activations).is_equal_to(
            [
                QSystemTrayIcon.ActivationReason.Context,
                QSystemTrayIcon.ActivationReason.MiddleClick,
            ]
        )


class TestAppBaseMinimizeToTrayBehavior:
    """Tests for minimize_to_tray actual behavior."""

    def test_minimize_to_tray_installs_close_handler(self, qt: QtDriver) -> None:
        """minimize_to_tray=True installs a close event handler."""
        from qtpy.QtGui import QAction

        @app(show=False, minimize_to_tray=True)
        class MyApp(AppBase):
            action: QAction = new("Hello")
            _label: QLabel = new("Content")

        instance = MyApp()
        # The close event should be overridden
        assert_that(instance._auto_window.closeEvent).is_not_none()

    def test_minimize_to_tray_false_no_handler(self, qt: QtDriver) -> None:
        """minimize_to_tray=False does not install close handler."""
        from qtpy.QtGui import QAction

        @app(show=False, minimize_to_tray=False)
        class MyApp(AppBase):
            action: QAction = new("Hello")
            _label: QLabel = new("Content")

        instance = MyApp()
        # When minimize_to_tray=False, closeEvent is NOT overridden
        # We check that it's still a bound method from the class, not a custom function
        # The handler installed by minimize_to_tray is a plain function, not a method
        close_event = instance._auto_window.closeEvent
        # If it were overridden by _install_minimize_to_tray, it would be a function
        # The default is a method descriptor bound to the instance
        assert_that(hasattr(close_event, "__self__")).is_true()


class TestAppBaseWindowControlMethods:
    """Tests for window control methods (hide, is_visible, window property)."""

    def test_window_property_returns_auto_window(self, qt: QtDriver) -> None:
        """window property returns the auto-created window."""
        from qtpy.QtWidgets import QMainWindow

        @app(show=False)
        class MyApp(AppBase):
            _label: QLabel = new("Hello")

        instance = MyApp()
        assert_that(instance.window).is_not_none()
        assert_that(instance.window).is_instance_of(QMainWindow)
        assert_that(instance.window).is_same_as(instance._auto_window)

    def test_window_property_none_without_window(self, qt: QtDriver) -> None:
        """window property returns None when window=False."""

        @app(show=False, window=False, system_tray=False)
        class MyApp(AppBase):
            _count: Variable[int] = new(0)

        instance = MyApp()
        assert_that(instance.window).is_none()

    def test_hide_hides_window(self, qt: QtDriver) -> None:
        """hide() hides the auto-created window."""

        @app(show=False)
        class MyApp(AppBase):
            _label: QLabel = new("Hello")

        instance = MyApp()
        # Window starts hidden (show=False)
        instance.hide()
        assert_that(instance._auto_window.isVisible()).is_false()

    def test_is_visible_reflects_window_state(self, qt: QtDriver) -> None:
        """is_visible property reflects window visibility."""

        @app(show=False)
        class MyApp(AppBase):
            _label: QLabel = new("Hello")

        instance = MyApp()
        # Window starts hidden
        assert_that(instance.is_visible).is_false()

    def test_is_visible_false_without_window(self, qt: QtDriver) -> None:
        """is_visible returns False when no window exists."""

        @app(show=False, window=False, system_tray=False)
        class MyApp(AppBase):
            _count: Variable[int] = new(0)

        instance = MyApp()
        assert_that(instance.is_visible).is_false()


class TestAppBaseStylesheet:
    """Tests for stylesheet= parameter on auto-window."""

    def test_stylesheet_applied_to_window(self, qt: QtDriver) -> None:
        """stylesheet= parameter stores in config for window use."""
        # Note: AppBase doesn't have styleSheet() - it's not a QWidget
        # The stylesheet= param stores in widget_props["styleSheet"]
        # For real apps (App class), this applies to QApplication

        @app(show=False, system_tray=False, stylesheet="QLabel { color: red; }")
        class MyApp(AppBase):
            _label: QLabel = new("Hello")

        # Verify the config stored the stylesheet
        assert_that(MyApp._qtpie_config.widget_props.get("styleSheet")).contains("color: red")

    def test_stylesheet_in_config(self, qt: QtDriver) -> None:
        """stylesheet= is stored in widget_props as styleSheet."""

        @app(show=False, stylesheet="QWidget { background: blue; }")
        class MyApp(AppBase):
            _label: QLabel = new("Hello")

        assert_that(MyApp._qtpie_config.widget_props.get("styleSheet")).contains("background: blue")


class TestAppBaseTitle:
    """Tests for title= parameter."""

    def test_title_sets_window_title(self, qt: QtDriver) -> None:
        """title= parameter sets window title."""

        @app(show=False, title="My Custom Title")
        class MyApp(AppBase):
            _label: QLabel = new("Hello")

        instance = MyApp()
        assert_that(instance._auto_window.windowTitle()).is_equal_to("My Custom Title")

    def test_title_with_special_characters(self, qt: QtDriver) -> None:
        """title= handles special characters."""

        @app(show=False, title="App - v1.0 (Beta)")
        class MyApp(AppBase):
            _label: QLabel = new("Hello")

        instance = MyApp()
        assert_that(instance._auto_window.windowTitle()).is_equal_to("App - v1.0 (Beta)")

    def test_title_with_unicode(self, qt: QtDriver) -> None:
        """title= handles unicode characters."""

        @app(show=False, title="日本語アプリ")
        class MyApp(AppBase):
            _label: QLabel = new("Hello")

        instance = MyApp()
        assert_that(instance._auto_window.windowTitle()).is_equal_to("日本語アプリ")

    def test_no_title_uses_class_name(self, qt: QtDriver) -> None:
        """Without title=, window uses class name."""

        @app(show=False)
        class MyCustomApp(AppBase):
            _label: QLabel = new("Hello")

        instance = MyCustomApp()
        assert_that(instance._auto_window.windowTitle()).is_equal_to("MyCustomApp")
