# pyright: reportMissingTypeArgument=false
# pyright: reportPrivateUsage=false
# pyright: reportUnknownParameterType=false
# pyright: reportMissingParameterType=false
# pyright: reportUnknownVariableType=false
# pyright: reportUnknownMemberType=false
# pyright: reportUnknownArgumentType=false
# pyright: reportUnknownLambdaType=false
"""Tests for sort= string method name resolution in repeaters."""

from dataclasses import dataclass

import pytest
from assertpy import assert_that
from observant import ObservableDict, ObservableList, ObservableSet
from qtpy.QtWidgets import QLabel

from qtpie import Widget, new, widget
from qtpie.dict_widget_repeater import DictWidgetRepeater
from qtpie.set_widget_repeater import SetWidgetRepeater
from qtpie.testing import QtDriver
from qtpie.widget_repeater import WidgetRepeater


@dataclass
class Dog:
    """Simple dataclass for testing."""

    name: str
    age: int


def _get_layout_texts(repeater) -> list[str]:
    """Get widget texts in layout order (visual order)."""
    layout = repeater._layout
    texts = []
    for i in range(layout.count()):
        widget = layout.itemAt(i).widget()
        if widget is not None:
            texts.append(widget.text())
    return texts


class TestWidgetRepeaterSortString:
    """Test sort= string method name resolution for WidgetRepeater (list[QLabel] = new() style)."""

    def test_sort_string_resolves_to_method(self, qt: QtDriver) -> None:
        """sort='method_name' resolves to parent widget method."""

        @widget
        class DogList(Widget):
            # Use plain list attribute (not Variable) for list[QLabel] = new() syntax
            _dogs: list[Dog] = [Dog("Zara", 3), Dog("Buddy", 5), Dog("Ace", 1)]
            _labels: list[QLabel] = new(bind="_dogs", format="{name}", sort="sort_by_name")

            def sort_by_name(self, dog: Dog) -> str:
                return dog.name

        app = qt.track(DogList())

        # Should be sorted by name in layout: Ace, Buddy, Zara
        texts = _get_layout_texts(app._labels)
        assert_that(texts).is_equal_to(["Ace", "Buddy", "Zara"])

    def test_sort_string_with_age(self, qt: QtDriver) -> None:
        """sort='method_name' can sort by different property."""

        @widget
        class DogList(Widget):
            _dogs: list[Dog] = [Dog("Zara", 3), Dog("Buddy", 5), Dog("Ace", 1)]
            _labels: list[QLabel] = new(bind="_dogs", format="{name}", sort="sort_by_age")

            def sort_by_age(self, dog: Dog) -> int:
                return dog.age

        app = qt.track(DogList())

        # Should be sorted by age in layout: Ace(1), Zara(3), Buddy(5)
        texts = _get_layout_texts(app._labels)
        assert_that(texts).is_equal_to(["Ace", "Zara", "Buddy"])

    def test_sort_string_method_not_found_raises(self, qt: QtDriver) -> None:
        """sort='nonexistent' raises AttributeError."""

        @widget
        class DogList(Widget):
            _dogs: list[Dog] = [Dog("Zara", 3)]
            _labels: list[QLabel] = new(bind="_dogs", format="{name}", sort="nonexistent_method")

        with pytest.raises(AttributeError, match="nonexistent_method"):
            qt.track(DogList())

    def test_sort_callable_still_works(self, qt: QtDriver) -> None:
        """sort=callable still works alongside string support."""

        @widget
        class DogList(Widget):
            _dogs: list[Dog] = [Dog("Zara", 3), Dog("Ace", 1)]
            _labels: list[QLabel] = new(bind="_dogs", format="{name}", sort=lambda d: d.name)

        app = qt.track(DogList())

        texts = _get_layout_texts(app._labels)
        assert_that(texts).is_equal_to(["Ace", "Zara"])

    def test_sort_true_still_works(self, qt: QtDriver) -> None:
        """sort=True still uses default sorted()."""

        @widget
        class NumberList(Widget):
            _nums: list[int] = [3, 1, 4, 1, 5]
            _labels: list[QLabel] = new(bind="_nums", sort=True)

        app = qt.track(NumberList())

        texts = _get_layout_texts(app._labels)
        assert_that(texts).is_equal_to(["1", "1", "3", "4", "5"])

    def test_sort_false_preserves_order(self, qt: QtDriver) -> None:
        """sort=False preserves list order."""

        @widget
        class NumberList(Widget):
            _nums: list[int] = [3, 1, 4]
            _labels: list[QLabel] = new(bind="_nums", sort=False)

        app = qt.track(NumberList())

        texts = _get_layout_texts(app._labels)
        assert_that(texts).is_equal_to(["3", "1", "4"])


class TestDictWidgetRepeaterSortString:
    """Test sort= string method name resolution for DictWidgetRepeater."""

    def test_sort_string_resolves_to_method(self, qt: QtDriver) -> None:
        """sort='method_name' resolves to parent widget method for dict keys."""

        @widget
        class ScoreBoard(Widget):
            # Use plain dict attribute for list[QLabel] = new(bind=) syntax
            _scores: dict[str, int] = {"Zara": 100, "Buddy": 85, "Ace": 90}
            _labels: list[QLabel] = new(bind="_scores", format="{#key}: {#value}", sort="sort_by_key")

            def sort_by_key(self, key: str) -> str:
                return key

        app = qt.track(ScoreBoard())

        # Should be sorted by key in layout: Ace, Buddy, Zara
        texts = _get_layout_texts(app._labels)
        assert_that(texts).is_equal_to(["Ace: 90", "Buddy: 85", "Zara: 100"])

    def test_sort_string_method_not_found_raises(self, qt: QtDriver) -> None:
        """sort='nonexistent' raises AttributeError."""

        @widget
        class ScoreBoard(Widget):
            _scores: dict[str, int] = {"A": 1}
            _labels: list[QLabel] = new(bind="_scores", sort="nonexistent_method")

        with pytest.raises(AttributeError, match="nonexistent_method"):
            qt.track(ScoreBoard())


class TestSetWidgetRepeaterSortString:
    """Test sort= string method name resolution for SetWidgetRepeater."""

    def test_sort_string_resolves_to_method(self, qt: QtDriver) -> None:
        """sort='method_name' resolves to parent widget method for set items."""

        @widget
        class TagList(Widget):
            # Use plain set attribute for set[QLabel] = new(bind=) syntax
            _tags: set[str] = {"zebra", "apple", "mango"}
            _labels: set[QLabel] = new(bind="_tags", sort="sort_tags")

            def sort_tags(self, tag: str) -> str:
                return tag

        app = qt.track(TagList())

        # Should be sorted alphabetically in layout: apple, mango, zebra
        texts = _get_layout_texts(app._labels)
        assert_that(texts).is_equal_to(["apple", "mango", "zebra"])

    def test_sort_string_method_not_found_raises(self, qt: QtDriver) -> None:
        """sort='nonexistent' raises AttributeError."""

        @widget
        class TagList(Widget):
            _tags: set[str] = {"a"}
            _labels: set[QLabel] = new(bind="_tags", sort="nonexistent_method")

        with pytest.raises(AttributeError, match="nonexistent_method"):
            qt.track(TagList())


class TestRepeaterSortStringDirectConstruction:
    """Test sort= string method name resolution when constructing repeaters directly."""

    def test_widget_repeater_string_without_parent_raises(self, qt: QtDriver) -> None:
        """WidgetRepeater with sort=string but no parent_widget raises."""
        obs_list = ObservableList([1, 2, 3])

        with pytest.raises(AttributeError, match="cannot resolve method name without parent widget"):
            qt.track(
                WidgetRepeater(
                    observable_list=obs_list,
                    item_type=int,
                    widget_type=QLabel,
                    sort="some_method",
                    parent_widget=None,
                )
            )

    def test_dict_widget_repeater_string_without_parent_raises(self, qt: QtDriver) -> None:
        """DictWidgetRepeater with sort=string but no parent_widget raises."""
        obs_dict = ObservableDict({"a": 1})

        with pytest.raises(AttributeError, match="cannot resolve method name without parent widget"):
            qt.track(
                DictWidgetRepeater(
                    observable_dict=obs_dict,
                    key_type=str,
                    value_type=int,
                    widget_type=QLabel,
                    sort="some_method",
                    parent_widget=None,
                )
            )

    def test_set_widget_repeater_string_without_parent_raises(self, qt: QtDriver) -> None:
        """SetWidgetRepeater with sort=string but no parent_widget raises."""
        obs_set = ObservableSet({1, 2, 3})

        with pytest.raises(AttributeError, match="cannot resolve method name without parent widget"):
            qt.track(
                SetWidgetRepeater(
                    observable_set=obs_set,
                    item_type=int,
                    widget_type=QLabel,
                    sort="some_method",
                    parent_widget=None,
                )
            )
