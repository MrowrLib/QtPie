# pyright: reportPrivateUsage=false
# pyright: reportUnknownMemberType=false
# pyright: reportUnknownArgumentType=false
# pyright: reportMissingTypeArgument=false
# pyright: reportUntypedClassDecorator=false
# pyright: reportUntypedBaseClass=false
# pyright: reportUnknownParameterType=false
# pyright: reportMissingParameterType=false
# pyright: reportUnknownVariableType=false
"""Tests for auto-record-bind feature.

When a parent Widget[T] contains a child Widget[T] (same T), the child's record
is automatically bound to the parent's record via bind="record".

This eliminates the need for repetitive bind="record" declarations.
"""

from dataclasses import dataclass

from assertpy import assert_that
from PySide6.QtWidgets import QLabel

from qtpie import Widget, new, widget
from qtpie.testing import QtDriver


@dataclass
class Dog:
    name: str = ""
    age: int = 0


@dataclass
class Cat:
    name: str = ""
    color: str = ""


class TestAutoRecordBind:
    """Auto-bind record when parent and child Widget[T] have same T."""

    def test_child_record_auto_binds_to_parent(self, qt: QtDriver) -> None:
        """Child Widget[T] automatically gets parent's record when T matches."""

        @widget(layout="vertical")
        class ChildWidget(Widget[Dog]):
            name_label: QLabel = new(bind="{name}")

        @widget(layout="vertical", record=Dog("Fido", 3))
        class ParentWidget(Widget[Dog]):
            child: ChildWidget = new()

        parent = qt.track(ParentWidget())
        qt.process_events()

        # Child should have same record as parent
        assert_that(parent.child.record.name).is_equal_to("Fido")

        # Modify parent's record - child should see it
        parent.record.name = "Rex"
        assert_that(parent.child.record.name).is_equal_to("Rex")

    def test_bare_child_auto_binds(self, qt: QtDriver) -> None:
        """Bare Widget[T] annotation (no new()) auto-binds record."""

        @widget(layout="vertical")
        class ChildWidget(Widget[Dog]):
            name_label: QLabel = new(bind="{name}")

        @widget(layout="vertical", record=Dog("Spot", 2))
        class ParentWidget(Widget[Dog]):
            child: ChildWidget  # Bare annotation - auto-new AND auto-record-bind

        parent = qt.track(ParentWidget())
        qt.process_events()

        # Child should have same record
        assert_that(parent.child.record.name).is_equal_to("Spot")

    def test_multiple_children_all_auto_bind(self, qt: QtDriver) -> None:
        """Multiple Widget[T] children all auto-bind to parent's record."""

        @widget(layout="vertical")
        class NameDisplay(Widget[Dog]):
            label: QLabel = new(bind="{name}")

        @widget(layout="vertical")
        class AgeDisplay(Widget[Dog]):
            label: QLabel = new(bind="{age}")

        @widget(layout="vertical", record=Dog("Buddy", 4))
        class ParentWidget(Widget[Dog]):
            name_display: NameDisplay
            age_display: AgeDisplay

        parent = qt.track(ParentWidget())
        qt.process_events()

        # Both children should see the record
        assert_that(parent.name_display.record.name).is_equal_to("Buddy")
        assert_that(parent.age_display.record.age).is_equal_to(4)


class TestDifferentTypeNoAutoBind:
    """No auto-bind when parent and child have different record types."""

    def test_different_type_no_auto_bind(self, qt: QtDriver) -> None:
        """Widget[Cat] child in Widget[Dog] parent does NOT auto-bind."""

        @widget(layout="vertical")
        class CatWidget(Widget[Cat]):
            name_label: QLabel = new(bind="{name}")

        @widget(layout="vertical", record=Dog("Fido", 3))
        class DogWidget(Widget[Dog]):
            cat_child: CatWidget = new()

        parent = qt.track(DogWidget())
        qt.process_events()

        # Cat widget should NOT have parent's Dog record
        # It should have its own empty Cat record
        assert_that(parent.cat_child.record.name).is_equal_to("")

    def test_child_without_record_type_no_auto_bind(self, qt: QtDriver) -> None:
        """Child Widget (no T) does NOT auto-bind to parent Widget[T]."""

        @widget(layout="vertical")
        class PlainWidget(Widget):
            label: QLabel = new("Plain")

        @widget(layout="vertical", record=Dog("Fido", 3))
        class DogWidget(Widget[Dog]):
            plain_child: PlainWidget = new()

        parent = qt.track(DogWidget())
        qt.process_events()

        # Plain child should not have record (no type parameter)
        assert_that(hasattr(parent.plain_child, "record")).is_false()


class TestOptOutWithBindFalse:
    """Use bind=False to opt out of auto-record-bind."""

    def test_bind_false_prevents_auto_bind(self, qt: QtDriver) -> None:
        """bind=False on child prevents auto-record-bind."""

        @widget(layout="vertical")
        class ChildWidget(Widget[Dog]):
            name_label: QLabel = new(bind="{name}")

        @widget(layout="vertical", record=Dog("Fido", 3))
        class ParentWidget(Widget[Dog]):
            child: ChildWidget = new(bind=False)

        parent = qt.track(ParentWidget())
        qt.process_events()

        # Child should NOT have parent's record - has its own default
        assert_that(parent.child.record.name).is_equal_to("")


class TestExplicitBindOverride:
    """Explicit bind="something" takes precedence over auto-bind."""

    def test_explicit_bind_overrides_auto(self, qt: QtDriver) -> None:
        """Explicit bind="record" is redundant but works."""

        @widget(layout="vertical")
        class ChildWidget(Widget[Dog]):
            name_label: QLabel = new(bind="{name}")

        @widget(layout="vertical", record=Dog("Fido", 3))
        class ParentWidget(Widget[Dog]):
            # Explicit bind="record" - same as auto but explicit
            child: ChildWidget = new(bind="record")

        parent = qt.track(ParentWidget())
        qt.process_events()

        assert_that(parent.child.record.name).is_equal_to("Fido")


class TestMixedPatterns:
    """Mix of auto-bind, no-bind, and opt-out in same parent."""

    def test_mix_of_auto_and_optout(self, qt: QtDriver) -> None:
        """Some children auto-bind, others opt out."""

        @widget(layout="vertical")
        class AutoChild(Widget[Dog]):
            label: QLabel = new(bind="{name}")

        @widget(layout="vertical")
        class OptOutChild(Widget[Dog]):
            label: QLabel = new(bind="{name}")

        @widget(layout="vertical")
        class PlainChild(Widget):
            label: QLabel = new("Plain")

        @widget(layout="vertical", record=Dog("Fido", 3))
        class ParentWidget(Widget[Dog]):
            auto1: AutoChild  # Auto-binds
            auto2: AutoChild = new()  # Auto-binds
            optout: OptOutChild = new(bind=False)  # Does NOT auto-bind
            plain: PlainChild  # No record type

        parent = qt.track(ParentWidget())
        qt.process_events()

        # Auto children should have parent's record
        assert_that(parent.auto1.record.name).is_equal_to("Fido")
        assert_that(parent.auto2.record.name).is_equal_to("Fido")

        # Opt-out child should have its own record
        assert_that(parent.optout.record.name).is_equal_to("")

        # Plain child has no record
        assert_that(hasattr(parent.plain, "record")).is_false()
