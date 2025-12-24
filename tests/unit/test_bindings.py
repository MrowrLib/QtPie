"""Tests for data binding functionality."""

from dataclasses import dataclass, field
from typing import override

from assertpy import assert_that
from observant import ObservableProxy
from qtpy.QtCore import QDate, QDateTime, QTime
from qtpy.QtGui import QFont, QKeySequence
from qtpy.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDateEdit,
    QDateTimeEdit,
    QDial,
    QDoubleSpinBox,
    QFontComboBox,
    QKeySequenceEdit,
    QLabel,
    QLineEdit,
    QListWidget,
    QPlainTextEdit,
    QProgressBar,
    QRadioButton,
    QSlider,
    QSpinBox,
    QTextEdit,
    QTimeEdit,
    QWidget,
)

from qtpie import Widget, bind, make, make_later, register_binding, widget
from qtpie.bindings import get_binding_registry
from qtpie.testing import QtDriver


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


class TestDictBindings:
    """Tests for dict-style multi-property bindings."""

    def test_dict_bind_single_property(self, qt: QtDriver) -> None:
        """Should bind to explicit property via dict syntax."""

        @dataclass
        class Model:
            selected: str = "Option A"

        @widget()
        class Editor(QWidget, Widget[Model]):
            model: Model = make(Model)
            proxy: ObservableProxy[Model] = make_later()
            combo: QComboBox = make(QComboBox, bind={"currentText": "proxy.selected"})

            @override
            def setup(self) -> None:
                self.combo.addItems(["Option A", "Option B", "Option C"])
                self.proxy = ObservableProxy(self.model, sync=True)

        w = Editor()
        qt.track(w)

        w.proxy.observable(str, "selected").set("Option B")
        assert_that(w.combo.currentText()).is_equal_to("Option B")

    def test_dict_bind_multiple_properties(self, qt: QtDriver) -> None:
        """Should bind multiple properties to different paths."""

        @dataclass
        class Model:
            name: str = "Alice"
            placeholder: str = "Enter name..."
            editable: bool = True

        @widget()
        class Editor(QWidget, Widget[Model]):
            model: Model = make(Model)
            proxy: ObservableProxy[Model] = make_later()
            name_edit: QLineEdit = make(
                QLineEdit,
                bind={
                    "text": "proxy.name",
                    "placeholderText": "proxy.placeholder",
                },
            )

            @override
            def setup(self) -> None:
                self.proxy = ObservableProxy(self.model, sync=True)

        w = Editor()
        qt.track(w)

        # Check initial values
        assert_that(w.name_edit.text()).is_equal_to("Alice")
        assert_that(w.name_edit.placeholderText()).is_equal_to("Enter name...")

        # Update via proxy - both properties should update
        w.proxy.observable(str, "name").set("Bob")
        assert_that(w.name_edit.text()).is_equal_to("Bob")

        w.proxy.observable(str, "placeholder").set("Type here...")
        assert_that(w.name_edit.placeholderText()).is_equal_to("Type here...")


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


class TestShortFormBinding:
    """Tests for short form bind syntax (bind='name' instead of bind='proxy.name')."""

    def test_short_form_simple_property(self, qt: QtDriver) -> None:
        """bind='name' should work as shorthand for bind='model_observable_proxy.name'."""

        @dataclass
        class Dog:
            name: str = ""

        @widget()
        class DogEditor(QWidget, Widget[Dog]):
            name_edit: QLineEdit = make(QLineEdit, bind="name")  # Short form!

        w = DogEditor()
        qt.track(w)

        # Model → Widget
        w.model_observable_proxy.observable(str, "name").set("Buddy")
        assert_that(w.name_edit.text()).is_equal_to("Buddy")

        # Widget → Model
        w.name_edit.setText("Max")
        assert_that(w.model.name).is_equal_to("Max")

    def test_short_form_nested_path(self, qt: QtDriver) -> None:
        """bind='address.city' should work as shorthand for bind='model_observable_proxy.address.city'."""

        @dataclass
        class Address:
            city: str = ""

        @dataclass
        class Person:
            address: Address = field(default_factory=Address)

        @widget()
        class PersonEditor(QWidget, Widget[Person]):
            city_edit: QLineEdit = make(QLineEdit, bind="address.city")  # Short form nested!

        w = PersonEditor()
        qt.track(w)

        w.model_observable_proxy.observable_for_path("address.city").set("New York")
        assert_that(w.city_edit.text()).is_equal_to("New York")

    def test_explicit_proxy_still_works(self, qt: QtDriver) -> None:
        """bind='proxy.name' should still work (backwards compatible)."""

        @dataclass
        class Dog:
            name: str = ""

        @widget()
        class DogEditor(QWidget, Widget[Dog]):
            model: Dog = make(Dog)
            proxy: ObservableProxy[Dog] = make_later()
            name_edit: QLineEdit = make(QLineEdit, bind="proxy.name")  # Explicit form

            @override
            def setup(self) -> None:
                self.proxy = ObservableProxy(self.model, sync=True)

        w = DogEditor()
        qt.track(w)

        w.proxy.observable(str, "name").set("Buddy")
        assert_that(w.name_edit.text()).is_equal_to("Buddy")

    def test_explicit_other_proxy(self, qt: QtDriver) -> None:
        """bind='other_proxy.name' should use self.other_proxy."""

        @dataclass
        class Dog:
            name: str = ""

        @dataclass
        class Cat:
            name: str = ""

        @widget()
        class PetEditor(QWidget, Widget[Dog]):
            cat_model: Cat = make(Cat)
            cat_proxy: ObservableProxy[Cat] = make_later()

            dog_name: QLineEdit = make(QLineEdit, bind="name")  # Short → model_observable_proxy.name
            cat_name: QLineEdit = make(QLineEdit, bind="cat_proxy.name")  # Explicit

            @override
            def setup(self) -> None:
                self.cat_proxy = ObservableProxy(self.cat_model, sync=True)

        w = PetEditor()
        qt.track(w)

        # Dog uses short form (via auto-created model_observable_proxy)
        w.model_observable_proxy.observable(str, "name").set("Buddy")
        assert_that(w.dog_name.text()).is_equal_to("Buddy")

        # Cat uses explicit proxy
        w.cat_proxy.observable(str, "name").set("Whiskers")
        assert_that(w.cat_name.text()).is_equal_to("Whiskers")

    def test_short_form_with_optional_chaining(self, qt: QtDriver) -> None:
        """bind='owner?.name' should work with optional chaining."""

        @dataclass
        class Owner:
            name: str = ""

        @dataclass
        class Dog:
            owner: Owner | None = None

        @widget()
        class DogEditor(QWidget, Widget[Dog]):
            owner_edit: QLineEdit = make(QLineEdit, bind="owner?.name")  # Short + optional

        w = DogEditor()
        qt.track(w)

        # With None owner, should show empty
        assert_that(w.owner_edit.text()).is_equal_to("")

    def test_short_form_with_widget_base_class(self, qt: QtDriver) -> None:
        """Short form should work with Widget[T] auto-created model_observable_proxy."""

        @dataclass
        class Dog:
            name: str = ""
            age: int = 0

        @widget()
        class DogEditor(QWidget, Widget[Dog]):
            # No explicit model/proxy - Widget[Dog] creates them
            name_edit: QLineEdit = make(QLineEdit, bind="name")
            age_spin: QSpinBox = make(QSpinBox, bind="age")

        w = DogEditor()
        qt.track(w)

        # model_observable_proxy is auto-created by Widget[Dog]
        assert_that(w.model_observable_proxy).is_not_none()

        w.model_observable_proxy.observable(str, "name").set("Rex")
        assert_that(w.name_edit.text()).is_equal_to("Rex")

        w.age_spin.setValue(5)
        assert_that(w.model.age).is_equal_to(5)


class TestAllWidgetBindings:
    """Tests for all registered widget bindings."""

    def test_text_edit_binding(self, qt: QtDriver) -> None:
        """QTextEdit should bind to text property."""

        @dataclass
        class Model:
            content: str = ""

        @widget()
        class Editor(QWidget, Widget[Model]):
            model: Model = make(Model)
            proxy: ObservableProxy[Model] = make_later()
            text_edit: QTextEdit = make(QTextEdit, bind="proxy.content")

            @override
            def setup(self) -> None:
                self.proxy = ObservableProxy(self.model, sync=True)

        w = Editor()
        qt.track(w)

        w.proxy.observable(str, "content").set("Hello World")
        assert_that(w.text_edit.toPlainText()).is_equal_to("Hello World")

        w.text_edit.setPlainText("Updated")
        assert_that(w.model.content).is_equal_to("Updated")

    def test_plain_text_edit_binding(self, qt: QtDriver) -> None:
        """QPlainTextEdit should bind to text property."""

        @dataclass
        class Model:
            content: str = ""

        @widget()
        class Editor(QWidget, Widget[Model]):
            model: Model = make(Model)
            proxy: ObservableProxy[Model] = make_later()
            text_edit: QPlainTextEdit = make(QPlainTextEdit, bind="proxy.content")

            @override
            def setup(self) -> None:
                self.proxy = ObservableProxy(self.model, sync=True)

        w = Editor()
        qt.track(w)

        w.proxy.observable(str, "content").set("Plain text")
        assert_that(w.text_edit.toPlainText()).is_equal_to("Plain text")

        w.text_edit.setPlainText("Changed")
        assert_that(w.model.content).is_equal_to("Changed")

    def test_double_spinbox_binding(self, qt: QtDriver) -> None:
        """QDoubleSpinBox should bind to float values."""

        @dataclass
        class Model:
            price: float = 0.0

        @widget()
        class Editor(QWidget, Widget[Model]):
            model: Model = make(Model)
            proxy: ObservableProxy[Model] = make_later()
            price_spin: QDoubleSpinBox = make(QDoubleSpinBox, bind="proxy.price")

            @override
            def setup(self) -> None:
                self.proxy = ObservableProxy(self.model, sync=True)

        w = Editor()
        qt.track(w)

        w.proxy.observable(float, "price").set(19.99)
        assert_that(w.price_spin.value()).is_equal_to(19.99)

        w.price_spin.setValue(29.99)
        assert_that(w.model.price).is_equal_to(29.99)

    def test_radio_button_binding(self, qt: QtDriver) -> None:
        """QRadioButton should bind to bool (checked) property."""

        @dataclass
        class Model:
            selected: bool = False

        @widget()
        class Editor(QWidget, Widget[Model]):
            model: Model = make(Model)
            proxy: ObservableProxy[Model] = make_later()
            radio: QRadioButton = make(QRadioButton, "Option", bind="proxy.selected")

            @override
            def setup(self) -> None:
                self.proxy = ObservableProxy(self.model, sync=True)

        w = Editor()
        qt.track(w)

        w.proxy.observable(bool, "selected").set(True)
        assert_that(w.radio.isChecked()).is_true()

        w.radio.setChecked(False)
        assert_that(w.model.selected).is_false()

    def test_dial_binding(self, qt: QtDriver) -> None:
        """QDial should bind to int value."""

        @dataclass
        class Model:
            rotation: int = 0

        @widget()
        class Editor(QWidget, Widget[Model]):
            model: Model = make(Model)
            proxy: ObservableProxy[Model] = make_later()
            dial: QDial = make(QDial, bind="proxy.rotation")

            @override
            def setup(self) -> None:
                self.proxy = ObservableProxy(self.model, sync=True)

        w = Editor()
        qt.track(w)

        w.proxy.observable(int, "rotation").set(50)
        assert_that(w.dial.value()).is_equal_to(50)

        w.dial.setValue(75)
        assert_that(w.model.rotation).is_equal_to(75)

    def test_progress_bar_binding(self, qt: QtDriver) -> None:
        """QProgressBar should bind one-way (model → widget only)."""

        @dataclass
        class Model:
            progress: int = 0

        @widget()
        class Editor(QWidget, Widget[Model]):
            model: Model = make(Model)
            proxy: ObservableProxy[Model] = make_later()
            bar: QProgressBar = make(QProgressBar, bind="proxy.progress")

            @override
            def setup(self) -> None:
                self.proxy = ObservableProxy(self.model, sync=True)

        w = Editor()
        qt.track(w)

        w.proxy.observable(int, "progress").set(50)
        assert_that(w.bar.value()).is_equal_to(50)

        w.proxy.observable(int, "progress").set(100)
        assert_that(w.bar.value()).is_equal_to(100)

    def test_date_edit_binding(self, qt: QtDriver) -> None:
        """QDateEdit should bind to QDate values."""

        @dataclass
        class Model:
            birth_date: QDate = field(default_factory=lambda: QDate.currentDate())

        @widget()
        class Editor(QWidget, Widget[Model]):
            model: Model = make(Model)
            proxy: ObservableProxy[Model] = make_later()
            date_edit: QDateEdit = make(QDateEdit, bind="proxy.birth_date")

            @override
            def setup(self) -> None:
                self.proxy = ObservableProxy(self.model, sync=True)

        w = Editor()
        qt.track(w)

        test_date = QDate(2000, 6, 15)
        w.proxy.observable(QDate, "birth_date").set(test_date)
        assert_that(w.date_edit.date()).is_equal_to(test_date)

        new_date = QDate(1990, 1, 1)
        w.date_edit.setDate(new_date)
        assert_that(w.model.birth_date).is_equal_to(new_date)

    def test_time_edit_binding(self, qt: QtDriver) -> None:
        """QTimeEdit should bind to QTime values."""

        @dataclass
        class Model:
            alarm_time: QTime = field(default_factory=lambda: QTime.currentTime())

        @widget()
        class Editor(QWidget, Widget[Model]):
            model: Model = make(Model)
            proxy: ObservableProxy[Model] = make_later()
            time_edit: QTimeEdit = make(QTimeEdit, bind="proxy.alarm_time")

            @override
            def setup(self) -> None:
                self.proxy = ObservableProxy(self.model, sync=True)

        w = Editor()
        qt.track(w)

        test_time = QTime(14, 30, 0)
        w.proxy.observable(QTime, "alarm_time").set(test_time)
        assert_that(w.time_edit.time()).is_equal_to(test_time)

        new_time = QTime(8, 0, 0)
        w.time_edit.setTime(new_time)
        assert_that(w.model.alarm_time).is_equal_to(new_time)

    def test_datetime_edit_binding(self, qt: QtDriver) -> None:
        """QDateTimeEdit should bind to QDateTime values."""

        @dataclass
        class Model:
            event_time: QDateTime = field(default_factory=lambda: QDateTime.currentDateTime())

        @widget()
        class Editor(QWidget, Widget[Model]):
            model: Model = make(Model)
            proxy: ObservableProxy[Model] = make_later()
            datetime_edit: QDateTimeEdit = make(QDateTimeEdit, bind="proxy.event_time")

            @override
            def setup(self) -> None:
                self.proxy = ObservableProxy(self.model, sync=True)

        w = Editor()
        qt.track(w)

        test_dt = QDateTime(QDate(2024, 12, 25), QTime(12, 0, 0))
        w.proxy.observable(QDateTime, "event_time").set(test_dt)
        assert_that(w.datetime_edit.dateTime()).is_equal_to(test_dt)

        new_dt = QDateTime(QDate(2025, 1, 1), QTime(0, 0, 0))
        w.datetime_edit.setDateTime(new_dt)
        assert_that(w.model.event_time).is_equal_to(new_dt)

    def test_font_combo_box_binding(self, qt: QtDriver) -> None:
        """QFontComboBox should bind to QFont values."""

        @dataclass
        class Model:
            selected_font: QFont = field(default_factory=QFont)

        @widget()
        class Editor(QWidget, Widget[Model]):
            model: Model = make(Model)
            proxy: ObservableProxy[Model] = make_later()
            font_combo: QFontComboBox = make(QFontComboBox, bind="proxy.selected_font")

            @override
            def setup(self) -> None:
                self.proxy = ObservableProxy(self.model, sync=True)

        w = Editor()
        qt.track(w)

        # Test setting font from model
        test_font = QFont("Arial")
        w.proxy.observable(QFont, "selected_font").set(test_font)
        assert_that(w.font_combo.currentFont().family()).is_equal_to(test_font.family())

    def test_key_sequence_edit_binding(self, qt: QtDriver) -> None:
        """QKeySequenceEdit should bind to QKeySequence values."""

        @dataclass
        class Model:
            shortcut: QKeySequence = field(default_factory=QKeySequence)

        @widget()
        class Editor(QWidget, Widget[Model]):
            model: Model = make(Model)
            proxy: ObservableProxy[Model] = make_later()
            key_edit: QKeySequenceEdit = make(QKeySequenceEdit, bind="proxy.shortcut")

            @override
            def setup(self) -> None:
                self.proxy = ObservableProxy(self.model, sync=True)

        w = Editor()
        qt.track(w)

        test_seq = QKeySequence("Ctrl+S")
        w.proxy.observable(QKeySequence, "shortcut").set(test_seq)
        assert_that(w.key_edit.keySequence().toString()).is_equal_to(test_seq.toString())

        new_seq = QKeySequence("Ctrl+N")
        w.key_edit.setKeySequence(new_seq)
        assert_that(w.model.shortcut.toString()).is_equal_to(new_seq.toString())

    def test_list_widget_binding(self, qt: QtDriver) -> None:
        """QListWidget should bind currentRow to int values."""

        @dataclass
        class Model:
            selected_index: int = -1

        @widget()
        class Editor(QWidget, Widget[Model]):
            model: Model = make(Model)
            proxy: ObservableProxy[Model] = make_later()
            list_widget: QListWidget = make(QListWidget, bind="proxy.selected_index")

            @override
            def setup(self) -> None:
                self.list_widget.addItems(["Item 1", "Item 2", "Item 3"])
                self.proxy = ObservableProxy(self.model, sync=True)

        w = Editor()
        qt.track(w)

        w.proxy.observable(int, "selected_index").set(1)
        assert_that(w.list_widget.currentRow()).is_equal_to(1)

        w.list_widget.setCurrentRow(2)
        assert_that(w.model.selected_index).is_equal_to(2)
