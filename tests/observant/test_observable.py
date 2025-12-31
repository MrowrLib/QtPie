"""Tests for Observable[T]."""

from assertpy import assert_that
from observant import Observable


def test_initial_value() -> None:
    """Observable stores initial value."""
    obs = Observable[int](42)

    assert_that(obs.get()).is_equal_to(42)


def test_set_updates_value() -> None:
    """set() updates the stored value."""
    obs = Observable[str]("hello")

    obs.set("world")

    assert_that(obs.get()).is_equal_to("world")


def test_on_change_callback_fires() -> None:
    """Callback fires when value changes."""
    obs = Observable[int](0)
    received: list[int] = []

    obs.on_change(lambda v: received.append(v))
    obs.set(1)

    assert_that(received).is_equal_to([1])


def test_multiple_callbacks() -> None:
    """Multiple callbacks all fire."""
    obs = Observable[int](0)
    results: list[str] = []

    obs.on_change(lambda v: results.append(f"a:{v}"))
    obs.on_change(lambda v: results.append(f"b:{v}"))
    obs.set(5)

    assert_that(results).is_equal_to(["a:5", "b:5"])


def test_callback_fires_on_every_set() -> None:
    """Callback fires on every set(), not just changes."""
    obs = Observable[int](0)
    count = [0]

    obs.on_change(lambda _: count.__setitem__(0, count[0] + 1))
    obs.set(1)
    obs.set(2)
    obs.set(3)

    assert_that(count[0]).is_equal_to(3)


def test_duplicate_callback_ignored() -> None:
    """Same callback registered twice only fires once."""
    obs = Observable[int](0)
    count = [0]

    def increment(_: int) -> None:
        count[0] += 1

    obs.on_change(increment)
    obs.on_change(increment)  # duplicate
    obs.set(1)

    assert_that(count[0]).is_equal_to(1)


def test_works_with_different_types() -> None:
    """Observable works with various types."""
    str_obs = Observable[str]("test")
    float_obs = Observable[float](3.14)
    list_obs = Observable[list[int]]([1, 2, 3])

    assert_that(str_obs.get()).is_equal_to("test")
    assert_that(float_obs.get()).is_equal_to(3.14)
    assert_that(list_obs.get()).is_equal_to([1, 2, 3])
