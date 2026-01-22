# pyright: reportUnknownArgumentType=false
"""Tests for forc2 domain models."""

from assertpy import assert_that
from forc2.domain import Collection, HttpMethod, Request


class TestRequest:
    """Tests for Request state."""

    def test_create_request(self) -> None:
        """Can create a Request with default values."""
        r = Request()
        assert_that(r.name.value).is_equal_to("")
        assert_that(r.method.value).is_equal_to(HttpMethod.GET)
        assert_that(r.url.value).is_equal_to("")

    def test_modify_request(self) -> None:
        """Can modify Request fields."""
        r = Request()
        r.name.value = "Get Users"
        r.method.value = HttpMethod.POST
        r.url.value = "https://api.example.com/users"

        assert_that(r.name.value).is_equal_to("Get Users")
        assert_that(r.method.value).is_equal_to(HttpMethod.POST)
        assert_that(r.url.value).is_equal_to("https://api.example.com/users")


class TestCollection:
    """Tests for Collection state."""

    def test_create_collection(self) -> None:
        """Can create a Collection with default values."""
        c = Collection()
        assert_that(c.name.value).is_equal_to("")
        assert_that(list(c.items.value)).is_empty()

    def test_add_request(self) -> None:
        """Can add a request to a collection."""
        c = Collection()
        r = c.add_request("Get Users")

        assert_that(r.name.value).is_equal_to("Get Users")
        assert_that(list(c.items.value)).is_length(1)
        assert_that(list(c.items.value)[0]).is_same_as(r)

    def test_add_collection(self) -> None:
        """Can add a sub-collection."""
        parent = Collection()
        parent.name.value = "API"

        child = parent.add_collection("Users")

        assert_that(child.name.value).is_equal_to("Users")
        assert_that(list(parent.items.value)).is_length(1)


class TestStateParent:
    """Tests for state_parent hierarchy."""

    def test_request_parent_is_collection(self) -> None:
        """Request's state_parent is its containing Collection."""
        c = Collection()
        r = c.add_request("Test")

        assert_that(r.state_parent).is_same_as(c)

    def test_nested_collection_parent(self) -> None:
        """Nested Collection's state_parent is its parent Collection."""
        parent = Collection()
        child = parent.add_collection("Child")

        assert_that(child.state_parent).is_same_as(parent)

    def test_top_level_has_no_parent(self) -> None:
        """Top-level Collection has no state_parent."""
        c = Collection()
        assert_that(c.state_parent).is_none()
