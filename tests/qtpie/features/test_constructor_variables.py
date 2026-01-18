# pyright: reportPrivateUsage=false
# pyright: reportMissingParameterType=false
# pyright: reportUnknownParameterType=false
# pyright: reportUntypedBaseClass=false
# pyright: reportUntypedClassDecorator=false
# pyright: reportUnknownArgumentType=false
# pyright: reportUnknownLambdaType=false
# pyright: reportUnknownMemberType=false
# pyright: reportAttributeAccessIssue=false
# pyright: reportUnusedClass=false
"""Tests for passing Variable values through constructors.

Tests that Variable[T] fields can receive initial values via constructor kwargs:
- Static values (int, str, etc.) → set as initial value
- Observable → bind to it (share the Observable)
- Variable → bind to its underlying Observable
"""

from typing import cast

import pytest
from assertpy import assert_that
from observant import Observable
from PySide6.QtWidgets import QFormLayout, QLabel, QLineEdit

from qtpie import Variable, Widget, new, widget
from qtpie.testing import QtDriver

from .conftest import ALL_CLASS_TYPES, create_and_track


@pytest.fixture
def qt(qtbot) -> QtDriver:  # type: ignore[no-untyped-def]
    return QtDriver(qtbot)


# =============================================================================
# Static Value Assignment
# =============================================================================


@pytest.mark.parametrize("base_class,decorator", ALL_CLASS_TYPES)
class TestConstructorStaticValues:
    """Passing static values to Variables via constructor."""

    def test_pass_static_int(self, base_class, decorator, qt: QtDriver) -> None:
        """Can pass static int to Variable via constructor."""

        @decorator
        class TestClass(base_class):
            _count: Variable[int] = new(0)

        instance = create_and_track(qt, TestClass, base_class, _count=42)
        assert_that(instance._count.value).is_equal_to(42)

    def test_pass_static_str(self, base_class, decorator, qt: QtDriver) -> None:
        """Can pass static str to Variable via constructor."""

        @decorator
        class TestClass(base_class):
            _name: Variable[str] = new("")

        instance = create_and_track(qt, TestClass, base_class, _name="hello")
        assert_that(instance._name.value).is_equal_to("hello")

    def test_pass_static_bool(self, base_class, decorator, qt: QtDriver) -> None:
        """Can pass static bool to Variable via constructor."""

        @decorator
        class TestClass(base_class):
            _enabled: Variable[bool] = new(False)

        instance = create_and_track(qt, TestClass, base_class, _enabled=True)
        assert_that(instance._enabled.value).is_true()

    def test_override_default_value(self, base_class, decorator, qt: QtDriver) -> None:
        """Constructor value overrides default from new()."""

        @decorator
        class TestClass(base_class):
            _count: Variable[int] = new(100)  # Default 100

        instance = create_and_track(qt, TestClass, base_class, _count=42)
        assert_that(instance._count.value).is_equal_to(42)  # Overridden

    def test_multiple_variables(self, base_class, decorator, qt: QtDriver) -> None:
        """Can pass multiple Variable values in constructor."""

        @decorator
        class TestClass(base_class):
            _count: Variable[int] = new(0)
            _name: Variable[str] = new("")
            _enabled: Variable[bool] = new(False)

        instance = create_and_track(qt, TestClass, base_class, _count=42, _name="test", _enabled=True)
        assert_that(instance._count.value).is_equal_to(42)
        assert_that(instance._name.value).is_equal_to("test")
        assert_that(instance._enabled.value).is_true()

    def test_partial_override(self, base_class, decorator, qt: QtDriver) -> None:
        """Can override some Variables while leaving others at default."""

        @decorator
        class TestClass(base_class):
            _count: Variable[int] = new(10)
            _name: Variable[str] = new("default")

        instance = create_and_track(qt, TestClass, base_class, _count=99)
        assert_that(instance._count.value).is_equal_to(99)  # Overridden
        assert_that(instance._name.value).is_equal_to("default")  # Default


# =============================================================================
# Bare Variable (Required Binding) with Constructor
# =============================================================================


@pytest.mark.parametrize("base_class,decorator", ALL_CLASS_TYPES)
class TestBareVariableConstructor:
    """Bare Variable[T] (no = new()) can receive value via constructor."""

    def test_bare_variable_receives_static_value(self, base_class, decorator, qt: QtDriver) -> None:
        """Bare Variable[str] receives static string value from constructor."""

        @decorator
        class TestClass(base_class):
            kind: Variable[str]  # Bare - no = new()

        instance = create_and_track(qt, TestClass, base_class, kind="Collection")
        assert_that(instance.kind.value).is_equal_to("Collection")

    def test_bare_variable_receives_int(self, base_class, decorator, qt: QtDriver) -> None:
        """Bare Variable[int] receives integer value from constructor."""

        @decorator
        class TestClass(base_class):
            count: Variable[int]  # Bare

        instance = create_and_track(qt, TestClass, base_class, count=42)
        assert_that(instance.count.value).is_equal_to(42)

    def test_bare_variable_receives_observable(self, base_class, decorator, qt: QtDriver) -> None:
        """Bare Variable[str] receives Observable and shares it."""

        @decorator
        class TestClass(base_class):
            kind: Variable[str]  # Bare

        external: Observable[str] = Observable("Initial")
        instance = create_and_track(qt, TestClass, base_class, kind=external)

        assert_that(instance.kind.value).is_equal_to("Initial")

        # Verify bidirectional sync
        external.set("Changed")
        assert_that(instance.kind.value).is_equal_to("Changed")

        instance.kind.value = "FromInstance"
        assert_that(external.get()).is_equal_to("FromInstance")

    def test_bare_variable_receives_variable(self, base_class, decorator, qt: QtDriver) -> None:
        """Bare Variable[str] receives another Variable and shares Observable."""

        @decorator
        class TestClass(base_class):
            kind: Variable[str]  # Bare

        # Create first instance with a value
        instance1 = create_and_track(qt, TestClass, base_class, kind="First")

        # Create second instance sharing the first's Variable
        instance2 = create_and_track(qt, TestClass, base_class, kind=instance1.kind)

        assert_that(instance2.kind.value).is_equal_to("First")

        # Bidirectional sync
        instance1.kind.value = "UpdatedFromFirst"
        assert_that(instance2.kind.value).is_equal_to("UpdatedFromFirst")

        instance2.kind.value = "UpdatedFromSecond"
        assert_that(instance1.kind.value).is_equal_to("UpdatedFromSecond")

    def test_mix_bare_and_default_variables(self, base_class, decorator, qt: QtDriver) -> None:
        """Can mix bare Variables and Variables with defaults."""

        @decorator
        class TestClass(base_class):
            kind: Variable[str]  # Bare - required
            count: Variable[int] = new(0)  # Has default

        instance = create_and_track(qt, TestClass, base_class, kind="Item", count=10)
        assert_that(instance.kind.value).is_equal_to("Item")
        assert_that(instance.count.value).is_equal_to(10)

    def test_bare_variable_only_kind_passed(self, base_class, decorator, qt: QtDriver) -> None:
        """Bare Variable provided, other with default not passed."""

        @decorator
        class TestClass(base_class):
            kind: Variable[str]  # Bare - must pass
            count: Variable[int] = new(100)  # Has default

        instance = create_and_track(qt, TestClass, base_class, kind="Request")
        assert_that(instance.kind.value).is_equal_to("Request")
        assert_that(instance.count.value).is_equal_to(100)  # Default


# =============================================================================
# Observable Binding
# =============================================================================


@pytest.mark.parametrize("base_class,decorator", ALL_CLASS_TYPES)
class TestConstructorObservableBinding:
    """Passing Observable to Variables creates shared binding."""

    def test_pass_observable(self, base_class, decorator, qt: QtDriver) -> None:
        """Passing Observable shares it with the Variable."""

        @decorator
        class TestClass(base_class):
            _count: Variable[int] = new(0)

        external: Observable[int] = Observable(42)
        instance = create_and_track(qt, TestClass, base_class, _count=external)

        assert_that(instance._count.value).is_equal_to(42)

        # External change syncs to instance (Observable uses .set() not .value)
        external.set(100)
        assert_that(instance._count.value).is_equal_to(100)

    def test_instance_change_syncs_to_observable(self, base_class, decorator, qt: QtDriver) -> None:
        """Changes on instance sync back to external Observable."""

        @decorator
        class TestClass(base_class):
            _count: Variable[int] = new(0)

        external: Observable[int] = Observable(0)
        instance = create_and_track(qt, TestClass, base_class, _count=external)

        instance._count.value = 50
        assert_that(external.get()).is_equal_to(50)  # Observable uses .get()

    def test_bidirectional_sync(self, base_class, decorator, qt: QtDriver) -> None:
        """Observable binding is bidirectional."""

        @decorator
        class TestClass(base_class):
            _count: Variable[int] = new(0)

        external: Observable[int] = Observable(0)
        instance = create_and_track(qt, TestClass, base_class, _count=external)

        # Instance → External
        instance._count.value = 50
        assert_that(external.get()).is_equal_to(50)  # Observable uses .get()

        # External → Instance
        external.set(75)  # Observable uses .set()
        assert_that(instance._count.value).is_equal_to(75)


@pytest.mark.parametrize("base_class,decorator", ALL_CLASS_TYPES)
class TestConstructorVariableBinding:
    """Passing another Variable shares the underlying Observable."""

    def test_pass_variable_from_another_instance(self, base_class, decorator, qt: QtDriver) -> None:
        """Passing Variable shares its Observable."""

        @decorator
        class TestClass(base_class):
            _count: Variable[int] = new(0)

        instance1 = create_and_track(qt, TestClass, base_class)
        instance1._count.value = 42

        instance2 = create_and_track(qt, TestClass, base_class, _count=instance1._count)
        assert_that(instance2._count.value).is_equal_to(42)

    def test_variable_binding_syncs_both_ways(self, base_class, decorator, qt: QtDriver) -> None:
        """Variable binding is bidirectional."""

        @decorator
        class TestClass(base_class):
            _count: Variable[int] = new(0)

        instance1 = create_and_track(qt, TestClass, base_class)
        instance2 = create_and_track(qt, TestClass, base_class, _count=instance1._count)

        # Change on instance1 reflects on instance2
        instance1._count.value = 100
        assert_that(instance2._count.value).is_equal_to(100)

        # Change on instance2 reflects on instance1
        instance2._count.value = 200
        assert_that(instance1._count.value).is_equal_to(200)


# =============================================================================
# Format Binding Resolution
# =============================================================================


class TestConstructorBindingResolution:
    """Format bindings resolve correctly with constructor-provided values."""

    def test_format_binding_resolves(self, qt: QtDriver) -> None:
        """Format binding in bind= resolves from constructor value."""

        @widget
        class TestWidget(Widget):
            kind: Variable[str] = new("")
            label: QLabel = new(bind="New {kind}")

        instance = qt.track(TestWidget(kind="Collection"))
        assert_that(instance.label.text()).is_equal_to("New Collection")

    def test_decorator_binding_resolves(self, qt: QtDriver) -> None:
        """Format binding in decorator kwarg resolves from constructor value."""

        @widget(windowTitle="Edit {kind}")
        class TestWidget(Widget):
            kind: Variable[str] = new("")

        instance = qt.track(TestWidget(kind="Request"))
        assert_that(instance.windowTitle()).is_equal_to("Edit Request")

    def test_bare_variable_title_binding(self, qt: QtDriver) -> None:
        """Bare Variable used in title= binding resolves correctly."""
        from qtpie import Dialog, DialogButton, dialog

        @dialog(layout="form", title="New {kind}")
        class TestDialog(Dialog):
            kind: Variable[str]  # Bare - no = new()
            _ok: DialogButton

        instance = qt.track(TestDialog(kind="Collection"))
        assert_that(instance.windowTitle()).is_equal_to("New Collection")

    def test_bare_variable_in_bind(self, qt: QtDriver) -> None:
        """Bare Variable used in bind= resolves correctly."""

        @widget
        class TestWidget(Widget):
            kind: Variable[str]  # Bare
            label: QLabel = new(bind="Type: {kind}")

        instance = qt.track(TestWidget(kind="Folder"))
        assert_that(instance.label.text()).is_equal_to("Type: Folder")

    def test_reactive_update_after_constructor(self, qt: QtDriver) -> None:
        """Bindings update reactively after constructor sets initial value."""

        @widget
        class TestWidget(Widget):
            kind: Variable[str] = new("")
            label: QLabel = new(bind="Type: {kind}")

        instance = qt.track(TestWidget(kind="A"))
        assert_that(instance.label.text()).is_equal_to("Type: A")

        # Change value after construction
        instance.kind.value = "B"
        assert_that(instance.label.text()).is_equal_to("Type: B")

    def test_multiple_bindings_resolve(self, qt: QtDriver) -> None:
        """Multiple format bindings all resolve from constructor values."""

        @widget
        class TestWidget(Widget):
            kind: Variable[str] = new("")
            count: Variable[int] = new(0)
            label: QLabel = new(bind="{count} {kind}(s)")

        instance = qt.track(TestWidget(kind="item", count=5))
        assert_that(instance.label.text()).is_equal_to("5 item(s)")

    def test_variable_widget_label_format_binding(self, qt: QtDriver) -> None:
        """Format binding in Variable[T, W] label= kwarg resolves correctly."""
        from qtpie import Dialog, dialog

        @dialog(layout="form", title="New {kind}")
        class TestDialog(Dialog):
            kind: Variable[str] = new("")
            name: Variable[str, QLineEdit] = new("")(label="{kind}")

        instance = qt.track(TestDialog(kind="Collection"))
        # The label is created by QFormLayout, find it via labelForField
        layout = instance.layout()
        assert layout is not None
        form_layout = cast(QFormLayout, layout)
        # Get the label for the name field's widget
        label_widget = form_layout.labelForField(instance.name.widget)
        assert label_widget is not None
        # The label should show "Collection", not "{kind}"
        assert_that(label_widget.text()).is_equal_to("Collection")

    def test_variable_widget_placeholder_format_binding(self, qt: QtDriver) -> None:
        """Format binding in Variable[T, W] placeholderText= kwarg resolves correctly."""

        @widget
        class TestWidget(Widget):
            kind: Variable[str] = new("")
            name: Variable[str, QLineEdit] = new("")(placeholderText="Enter {kind} name...")

        instance = qt.track(TestWidget(kind="Request"))
        assert_that(instance.name.widget.placeholderText()).is_equal_to("Enter Request name...")

    def test_variable_widget_format_binding_reactive_update(self, qt: QtDriver) -> None:
        """Format binding in Variable[T, W] kwargs updates reactively."""

        @widget
        class TestWidget(Widget):
            kind: Variable[str] = new("")
            name: Variable[str, QLineEdit] = new("")(placeholderText="Enter {kind} name...")

        instance = qt.track(TestWidget(kind="Collection"))
        assert_that(instance.name.widget.placeholderText()).is_equal_to("Enter Collection name...")

        # Change the kind value - placeholder should update
        instance.kind.value = "Request"
        assert_that(instance.name.widget.placeholderText()).is_equal_to("Enter Request name...")

    def test_bare_variable_in_widget_kwargs(self, qt: QtDriver) -> None:
        """Bare Variable used in Variable[T, W] kwargs resolves correctly."""
        from qtpie import Dialog, DialogButton, dialog

        @dialog(layout="form", title="New {kind}")
        class TestDialog(Dialog):
            kind: Variable[str]  # Bare
            name: Variable[str, QLineEdit] = new("")(label="{kind}", placeholderText="Enter {kind} name...")
            _ok: DialogButton

        instance = qt.track(TestDialog(kind="Folder"))
        assert_that(instance.windowTitle()).is_equal_to("New Folder")
        assert_that(instance.name.widget.placeholderText()).is_equal_to("Enter Folder name...")


# =============================================================================
# Edge Cases
# =============================================================================


@pytest.mark.parametrize("base_class,decorator", ALL_CLASS_TYPES)
class TestConstructorVariableEdgeCases:
    """Edge cases for constructor variable assignment."""

    def test_none_value_allowed(self, base_class, decorator, qt: QtDriver) -> None:
        """Can pass None as a Variable value."""

        @decorator
        class TestClass(base_class):
            _name: Variable[str | None] = new("default")

        instance = create_and_track(qt, TestClass, base_class, _name=None)
        assert_that(instance._name.value).is_none()

    def test_empty_string(self, base_class, decorator, qt: QtDriver) -> None:
        """Can pass empty string as a Variable value."""

        @decorator
        class TestClass(base_class):
            _name: Variable[str] = new("default")

        instance = create_and_track(qt, TestClass, base_class, _name="")
        assert_that(instance._name.value).is_equal_to("")

    def test_zero_value(self, base_class, decorator, qt: QtDriver) -> None:
        """Can pass zero as a Variable value (not treated as falsy)."""

        @decorator
        class TestClass(base_class):
            _count: Variable[int] = new(100)

        instance = create_and_track(qt, TestClass, base_class, _count=0)
        assert_that(instance._count.value).is_equal_to(0)

    def test_false_value(self, base_class, decorator, qt: QtDriver) -> None:
        """Can pass False as a Variable value (not treated as falsy)."""

        @decorator
        class TestClass(base_class):
            _enabled: Variable[bool] = new(True)

        instance = create_and_track(qt, TestClass, base_class, _enabled=False)
        assert_that(instance._enabled.value).is_false()


# =============================================================================
# Dialog show_dialog() Forwarding
# =============================================================================


class TestDialogShowDialogForwarding:
    """show_dialog() forwards kwargs to Dialog constructor."""

    def test_show_dialog_forwards_kwargs(self, qt: QtDriver) -> None:
        """show_dialog(kind=...) forwards to constructor."""
        from PySide6.QtWidgets import QDialog

        from qtpie import Dialog, DialogButton, dialog

        @dialog
        class TestDialog(Dialog):
            kind: Variable[str] = new("")
            _ok: DialogButton

        # Capture instance to check value
        captured_instance: list[Dialog] = []  # type: ignore[type-arg]

        @dialog
        class CaptureDialog(Dialog):
            kind: Variable[str] = new("")
            _ok: DialogButton

            def __init__(self) -> None:
                super().__init__()
                captured_instance.append(self)
                # Override _show_dialog to avoid blocking
                self._show_dialog = lambda: self._build_result(QDialog.DialogCode.Accepted)  # type: ignore[method-assign]

        CaptureDialog.show_dialog(kind="Collection")

        assert len(captured_instance) == 1
        qt.track(captured_instance[0])
        assert_that(captured_instance[0].kind.value).is_equal_to("Collection")

    def test_show_dialog_with_record_and_kwargs(self, qt: QtDriver) -> None:
        """show_dialog(record, kind=...) works with both record and kwargs."""
        from dataclasses import dataclass

        from PySide6.QtWidgets import QDialog

        from qtpie import Dialog, DialogButton, dialog

        @dataclass
        class Data:
            value: str = ""

        captured_instance: list[Dialog[Data]] = []

        @dialog
        class TestDialog(Dialog[Data]):
            kind: Variable[str] = new("")
            value: QLineEdit = new()
            _ok: DialogButton

            def __init__(self) -> None:
                super().__init__()
                captured_instance.append(self)
                self._show_dialog = lambda: self._build_result(QDialog.DialogCode.Accepted)  # type: ignore[method-assign]

        result = TestDialog.show_dialog(Data("test-data"), kind="Item")

        assert len(captured_instance) == 1
        qt.track(captured_instance[0])
        assert_that(captured_instance[0].kind.value).is_equal_to("Item")
        assert result.record is not None
        assert_that(result.record.value).is_equal_to("test-data")
