# pyright: reportPrivateUsage=false, reportUnknownMemberType=false
# pyright: reportCallIssue=false, reportAttributeAccessIssue=false
"""Tests for ObservableProxy.observable_for_path()."""

from dataclasses import dataclass

from assertpy import assert_that
from observant import Observable, ObservableProxy


@dataclass
class Address:
    """Nested model."""

    city: str = ""
    zip_code: str = ""


@dataclass
class Person:
    """Model with nested fields."""

    name: str = ""
    age: int = 0
    address: Address | None = None


@dataclass
class Company:
    """Model with nested nullable field."""

    name: str = ""
    ceo: Person | None = None


class TestObservableForPathSimple:
    """Test simple path traversal."""

    def test_single_field(self) -> None:
        """Can get observable for a single field."""
        person = Person(name="Alice", age=30)
        proxy = ObservableProxy(person)

        name_obs = proxy.observable_for_path("name")
        assert_that(name_obs).is_instance_of(Observable)
        assert_that(name_obs.get()).is_equal_to("Alice")

    def test_nested_path(self) -> None:
        """Can traverse nested paths."""
        person = Person(name="Bob", address=Address(city="NYC", zip_code="10001"))
        proxy = ObservableProxy(person)

        city_obs = proxy.observable_for_path("address.city")
        assert_that(city_obs).is_instance_of(Observable)
        assert_that(city_obs.get()).is_equal_to("NYC")

    def test_nested_proxy_returns_proxy(self) -> None:
        """Intermediate paths return ObservableProxy."""
        person = Person(address=Address(city="LA"))
        proxy = ObservableProxy(person)

        addr_proxy = proxy.observable_for_path("address")
        assert_that(addr_proxy).is_instance_of(ObservableProxy)


class TestObservableForPathOptional:
    """Test optional chaining with ?.."""

    def test_optional_on_none_returns_observable_none(self) -> None:
        """Optional chaining on None returns Observable(None)."""
        person = Person(name="Charlie", address=None)
        proxy = ObservableProxy(person)

        result = proxy.observable_for_path("address?.city")
        assert_that(result).is_instance_of(Observable)
        assert_that(result.get()).is_none()

    def test_optional_on_value_returns_actual(self) -> None:
        """Optional chaining with value returns the actual observable."""
        person = Person(address=Address(city="Boston"))
        proxy = ObservableProxy(person)

        result = proxy.observable_for_path("address?.city")
        assert_that(result).is_instance_of(Observable)
        assert_that(result.get()).is_equal_to("Boston")

    def test_deep_optional_chain(self) -> None:
        """Deep optional chain works."""
        company = Company(name="Acme", ceo=Person(address=Address(city="SF")))
        proxy = ObservableProxy(company)

        result = proxy.observable_for_path("ceo?.address?.city")
        assert_that(result).is_instance_of(Observable)
        assert_that(result.get()).is_equal_to("SF")

    def test_deep_optional_chain_with_none(self) -> None:
        """Deep optional chain with None intermediate."""
        company = Company(name="Acme", ceo=None)
        proxy = ObservableProxy(company)

        result = proxy.observable_for_path("ceo?.address?.city")
        assert_that(result).is_instance_of(Observable)
        assert_that(result.get()).is_none()


class TestObservableForPathErrors:
    """Test error handling."""

    def test_missing_field_raises(self) -> None:
        """Missing field without optional raises AttributeError."""
        person = Person(name="Dan")
        proxy = ObservableProxy(person)

        try:
            proxy.observable_for_path("nonexistent")
            assert_that(False).is_true()  # Should not reach
        except AttributeError as e:
            assert_that(str(e)).contains("nonexistent")

    def test_optional_none_intermediate(self) -> None:
        """Optional chaining handles None intermediate values gracefully."""
        person = Person(name="Eve", address=None)
        proxy = ObservableProxy(person)

        # address is None, so address?.city returns Observable(None)
        result = proxy.observable_for_path("address?.city")
        assert_that(result).is_instance_of(Observable)
        assert_that(result.get()).is_none()


class TestObservableForPathParseSegments:
    """Test _parse_path_segments helper."""

    def test_simple_path(self) -> None:
        """Simple path without optional."""
        person = Person()
        proxy = ObservableProxy(person)

        segments = proxy._parse_path_segments("a.b.c")
        assert_that(segments).is_equal_to([("a", False), ("b", False), ("c", False)])

    def test_optional_path(self) -> None:
        """Path with optional segments."""
        person = Person()
        proxy = ObservableProxy(person)

        segments = proxy._parse_path_segments("a?.b.c?.d")
        assert_that(segments).is_equal_to([("a", True), ("b", False), ("c", True), ("d", False)])
