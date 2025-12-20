"""Tests for data binding functionality."""

from dataclasses import dataclass, field
from typing import override

from assertpy import assert_that
from observant import ObservableProxy  # type: ignore[import-untyped]
from qtpy.QtWidgets import (
    QCheckBox,
    QComboBox,
    QLabel,
    QLineEdit,
    QSlider,
    QSpinBox,
    QWidget,
)

from qtpie import Widget, bind, make, make_later, register_binding, widget
from qtpie.bindings import get_binding_registry
from qtpie_test import QtDriver


class TestMakeLater:
    """Tests for make_later() helper."""

    def test_make_later_creates_uninitialized_field(self, qt: QtDriver) -> None:
        """make_later() should create a field that starts uninitialized."""

        @widget()
        class MyWidget(QWidget, Widget):
            value: int = make_later()

            @override
            def setup(self) -> None:
                self.value = 42

        w = MyWidget()
        qt.track(w)

        assert_that(w.value).is_equal_to(42)


class TestBindingRegistry:
    """Tests for binding registry functionality."""

    def test_default_prop_for_line_edit(self) -> None:
        """QLineEdit should default to 'text' property."""
        registry = get_binding_registry()
        edit = QLineEdit()
        assert_that(registry.get_default_prop(edit)).is_equal_to("text")

    def test_default_prop_for_spinbox(self) -> None:
        """QSpinBox should default to 'value' property."""
        registry = get_binding_registry()
        spin = QSpinBox()
        assert_that(registry.get_default_prop(spin)).is_equal_to("value")

    def test_default_prop_for_checkbox(self) -> None:
        """QCheckBox should default to 'checked' property."""
        registry = get_binding_registry()
        check = QCheckBox()
        assert_that(registry.get_default_prop(check)).is_equal_to("checked")

    def test_get_adapter_for_line_edit_text(self) -> None:
        """Should get adapter for QLineEdit.text."""
        registry = get_binding_registry()
        edit = QLineEdit()
        adapter = registry.get(edit, "text")
        assert_that(adapter).is_not_none()
        assert adapter is not None  # for type narrowing
        assert_that(adapter.signal_name).is_equal_to("textChanged")

    def test_custom_binding_registration(self) -> None:
        """Should be able to register custom bindings."""

        class CustomWidget(QWidget, Widget):
            def __init__(self) -> None:
                super().__init__()
                self._custom_value = ""

            def custom_value(self) -> str:
                return self._custom_value

            def set_custom_value(self, v: str) -> None:
                self._custom_value = v

        register_binding(
            CustomWidget,
            "custom",
            getter=lambda w: w.custom_value(),
            setter=lambda w, v: w.set_custom_value(str(v)),
            default=True,
        )

        registry = get_binding_registry()
        custom = CustomWidget()
        assert_that(registry.get_default_prop(custom)).is_equal_to("custom")


class TestBasicBinding:
    """Tests for basic two-way binding."""

    def test_model_to_widget_sync(self, qt: QtDriver) -> None:
        """Model changes should update widget."""

        @dataclass
        class Dog:
            name: str = ""

        @widget()
        class DogEditor(QWidget, Widget[Dog]):
            model: Dog = make(Dog)
            proxy: ObservableProxy[Dog] = make_later()
            name_edit: QLineEdit = make(QLineEdit, bind="proxy.name")

            @override
            def setup(self) -> None:
                self.proxy = ObservableProxy(self.model, sync=True)

        w = DogEditor()
        qt.track(w)

        # Initial value
        assert_that(w.name_edit.text()).is_equal_to("")

        # Model → Widget
        w.proxy.observable(str, "name").set("Buddy")
        assert_that(w.name_edit.text()).is_equal_to("Buddy")

    def test_widget_to_model_sync(self, qt: QtDriver) -> None:
        """Widget changes should update model."""

        @dataclass
        class Dog:
            name: str = ""

        @widget()
        class DogEditor(QWidget, Widget[Dog]):
            model: Dog = make(Dog)
            proxy: ObservableProxy[Dog] = make_later()
            name_edit: QLineEdit = make(QLineEdit, bind="proxy.name")

            @override
            def setup(self) -> None:
                self.proxy = ObservableProxy(self.model, sync=True)

        w = DogEditor()
        qt.track(w)

        # Widget → Model
        w.name_edit.setText("Max")
        assert_that(w.model.name).is_equal_to("Max")

    def test_no_infinite_loop(self, qt: QtDriver) -> None:
        """Changes should not cause infinite loops."""

        @dataclass
        class Counter:
            value: int = 0

        change_count = [0]

        @widget()
        class CounterWidget(QWidget, Widget[Counter]):
            model: Counter = make(Counter)
            proxy: ObservableProxy[Counter] = make_later()
            spin: QSpinBox = make(QSpinBox, bind="proxy.value")

            @override
            def setup(self) -> None:
                self.proxy = ObservableProxy(self.model, sync=True)
                # Track changes to detect infinite loops
                self.proxy.observable(int, "value").on_change(lambda _: change_count.__setitem__(0, change_count[0] + 1))

        w = CounterWidget()
        qt.track(w)

        # Set value - should only trigger one change, not infinite
        w.spin.setValue(10)
        assert_that(change_count[0]).is_less_than(5)  # Allow for initial sync


class TestWidgetBindings:
    """Tests for different widget type bindings."""

    def test_spinbox_binding(self, qt: QtDriver) -> None:
        """QSpinBox should bind to int values."""

        @dataclass
        class Model:
            age: int = 0

        @widget()
        class Editor(QWidget, Widget[Model]):
            model: Model = make(Model)
            proxy: ObservableProxy[Model] = make_later()
            age_spin: QSpinBox = make(QSpinBox, bind="proxy.age")

            @override
            def setup(self) -> None:
                self.proxy = ObservableProxy(self.model, sync=True)

        w = Editor()
        qt.track(w)

        w.proxy.observable(int, "age").set(25)
        assert_that(w.age_spin.value()).is_equal_to(25)

        w.age_spin.setValue(30)
        assert_that(w.model.age).is_equal_to(30)

    def test_checkbox_binding(self, qt: QtDriver) -> None:
        """QCheckBox should bind to bool values."""

        @dataclass
        class Model:
            active: bool = False

        @widget()
        class Editor(QWidget, Widget[Model]):
            model: Model = make(Model)
            proxy: ObservableProxy[Model] = make_later()
            active_check: QCheckBox = make(QCheckBox, "Active", bind="proxy.active")

            @override
            def setup(self) -> None:
                self.proxy = ObservableProxy(self.model, sync=True)

        w = Editor()
        qt.track(w)

        w.proxy.observable(bool, "active").set(True)
        assert_that(w.active_check.isChecked()).is_true()

        w.active_check.setChecked(False)
        assert_that(w.model.active).is_false()

    def test_label_one_way_binding(self, qt: QtDriver) -> None:
        """QLabel should support one-way binding (model → widget only)."""

        @dataclass
        class Model:
            status: str = "Ready"

        @widget()
        class StatusWidget(QWidget, Widget[Model]):
            model: Model = make(Model)
            proxy: ObservableProxy[Model] = make_later()
            status_label: QLabel = make(QLabel, bind="proxy.status")

            @override
            def setup(self) -> None:
                self.proxy = ObservableProxy(self.model, sync=True)

        w = StatusWidget()
        qt.track(w)

        assert_that(w.status_label.text()).is_equal_to("Ready")

        w.proxy.observable(str, "status").set("Loading...")
        assert_that(w.status_label.text()).is_equal_to("Loading...")

    def test_slider_binding(self, qt: QtDriver) -> None:
        """QSlider should bind to int values."""

        @dataclass
        class Model:
            volume: int = 50

        @widget()
        class Editor(QWidget, Widget[Model]):
            model: Model = make(Model)
            proxy: ObservableProxy[Model] = make_later()
            slider: QSlider = make(QSlider, bind="proxy.volume")

            @override
            def setup(self) -> None:
                self.proxy = ObservableProxy(self.model, sync=True)

        w = Editor()
        qt.track(w)

        w.proxy.observable(int, "volume").set(75)
        assert_that(w.slider.value()).is_equal_to(75)


class TestNestedPathBinding:
    """Tests for nested path bindings."""

    def test_simple_nested_path(self, qt: QtDriver) -> None:
        """Should support nested paths like 'proxy.owner.name'."""

        @dataclass
        class Owner:
            name: str = ""

        @dataclass
        class Dog:
            owner: Owner = field(default_factory=Owner)

        @widget()
        class DogEditor(QWidget, Widget[Dog]):
            model: Dog = make(Dog)
            proxy: ObservableProxy[Dog] = make_later()
            owner_edit: QLineEdit = make(QLineEdit, bind="proxy.owner.name")

            @override
            def setup(self) -> None:
                self.proxy = ObservableProxy(self.model, sync=True)

        w = DogEditor()
        qt.track(w)

        # Set via nested path
        w.proxy.observable_for_path("owner.name").set("Alice")
        assert_that(w.owner_edit.text()).is_equal_to("Alice")


class TestOptionalChaining:
    """Tests for optional chaining in bind paths."""

    def test_optional_path_with_none(self, qt: QtDriver) -> None:
        """Should handle None in optional paths gracefully."""

        @dataclass
        class Owner:
            name: str = ""

        @dataclass
        class Dog:
            owner: Owner | None = None

        @widget()
        class DogEditor(QWidget, Widget[Dog]):
            model: Dog = make(Dog)
            proxy: ObservableProxy[Dog] = make_later()
            owner_edit: QLineEdit = make(QLineEdit, bind="proxy.owner?.name")

            @override
            def setup(self) -> None:
                self.proxy = ObservableProxy(self.model, sync=True)

        w = DogEditor()
        qt.track(w)

        # With None owner, should show empty
        assert_that(w.owner_edit.text()).is_equal_to("")


class TestExplicitBindProp:
    """Tests for explicit bind_prop parameter."""

    def test_explicit_bind_prop(self, qt: QtDriver) -> None:
        """Should use explicit bind_prop when specified."""

        @dataclass
        class Model:
            selected: str = "Option A"

        @widget()
        class Editor(QWidget, Widget[Model]):
            model: Model = make(Model)
            proxy: ObservableProxy[Model] = make_later()
            combo: QComboBox = make(QComboBox, bind="proxy.selected", bind_prop="currentText")

            @override
            def setup(self) -> None:
                self.combo.addItems(["Option A", "Option B", "Option C"])
                self.proxy = ObservableProxy(self.model, sync=True)

        w = Editor()
        qt.track(w)

        w.proxy.observable(str, "selected").set("Option B")
        assert_that(w.combo.currentText()).is_equal_to("Option B")


class TestManualBinding:
    """Tests for manual bind() usage."""

    def test_manual_bind_call(self, qt: QtDriver) -> None:
        """Should be able to call bind() manually."""

        @dataclass
        class Model:
            name: str = "Test"

        proxy = ObservableProxy(Model(), sync=True)
        edit = QLineEdit()
        qt.track(edit)

        # Manual binding
        bind(proxy.observable(str, "name"), edit)

        assert_that(edit.text()).is_equal_to("Test")

        proxy.observable(str, "name").set("Updated")
        assert_that(edit.text()).is_equal_to("Updated")


class TestMultipleBindings:
    """Tests for multiple bindings on same model."""

    def test_multiple_widgets_same_field(self, qt: QtDriver) -> None:
        """Multiple widgets can bind to the same model field."""

        @dataclass
        class Model:
            name: str = ""

        @widget()
        class Editor(QWidget, Widget[Model]):
            model: Model = make(Model)
            proxy: ObservableProxy[Model] = make_later()
            edit1: QLineEdit = make(QLineEdit, bind="proxy.name")
            edit2: QLineEdit = make(QLineEdit, bind="proxy.name")
            label: QLabel = make(QLabel, bind="proxy.name")

            @override
            def setup(self) -> None:
                self.proxy = ObservableProxy(self.model, sync=True)

        w = Editor()
        qt.track(w)

        w.proxy.observable(str, "name").set("Shared")
        assert_that(w.edit1.text()).is_equal_to("Shared")
        assert_that(w.edit2.text()).is_equal_to("Shared")
        assert_that(w.label.text()).is_equal_to("Shared")
