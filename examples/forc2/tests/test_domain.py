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

    def test_on_item_added_fires(self) -> None:
        """on_item_added event fires when items are added."""
        c = Collection()
        added: list[object] = []
        c.on_item_added.connect(lambda item: added.append(item))

        r = c.add_request("Test")

        assert_that(added).is_length(1)
        assert_that(added[0]).is_same_as(r)

    def test_on_item_removed_fires(self) -> None:
        """on_item_removed event fires when items are removed."""
        c = Collection()
        r = c.add_request("Test")

        removed: list[object] = []
        c.on_item_removed.connect(lambda item: removed.append(item))

        c.remove(r)

        assert_that(removed).is_length(1)
        assert_that(removed[0]).is_same_as(r)

    def test_nested_on_changed_bubbles(self) -> None:
        """Changes in nested items bubble up via on_changed."""
        root = Collection()
        root.name.value = "Root"

        changes: list[str] = []
        root.on_changed.connect(lambda: changes.append("root_changed"))

        # Add a request
        r = root.add_request("Test")
        assert_that(changes).contains("root_changed")  # Adding fires on_changed

        changes.clear()

        # Modify the request - should bubble up
        r.url.value = "http://test.com"
        assert_that(changes).contains("root_changed")

    def test_deeply_nested_changes_bubble(self) -> None:
        """Changes bubble up through multiple levels."""
        root = Collection()
        child = root.add_collection("Child")
        grandchild = child.add_collection("Grandchild")
        request = grandchild.add_request("Deep Request")

        changes: list[str] = []
        root.on_changed.connect(lambda: changes.append("root"))

        changes.clear()

        # Modify the deeply nested request
        request.name.value = "Modified"

        # Should bubble all the way up
        assert_that(changes).contains("root")


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
