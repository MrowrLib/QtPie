# pyright: reportUnknownArgumentType=false, reportPrivateUsage=false
"""Tests for Workspace state and path-based saving."""

from pathlib import Path

from assertpy import assert_that
from forc2.domain import Collection, HttpMethod, Request, Workspace
from forc2.format import load_collection, save_collection


class TestWorkspace:
    """Tests for Workspace state."""

    def test_initial_state(self) -> None:
        """Workspace starts with None path and collection."""
        ws = Workspace()

        assert_that(ws.path.value).is_none()
        assert_that(ws.collection.value).is_none()

    def test_set_path_loads_collection(self, tmp_path: Path) -> None:
        """Setting path reactively loads the collection."""
        # Create a collection on disk
        coll_dir = tmp_path / "my-api"
        coll_dir.mkdir()
        (coll_dir / "_collection.yaml").write_text("name: My API\n")
        (coll_dir / "test.yaml").write_text("name: Test Request\nmethod: GET\nurl: /test\n")

        ws = Workspace()
        ws.path.value = coll_dir

        assert_that(ws.collection.value).is_not_none()
        assert ws.collection.value is not None
        assert_that(ws.collection.value.name.value).is_equal_to("My API")
        assert_that(list(ws.collection.value.items.value)).is_length(1)

    def test_set_path_none_unloads(self, tmp_path: Path) -> None:
        """Setting path to None clears the collection."""
        # Create a collection
        coll_dir = tmp_path / "api"
        coll_dir.mkdir()
        (coll_dir / "_collection.yaml").write_text("name: API\n")

        ws = Workspace()
        ws.path.value = coll_dir
        assert_that(ws.collection.value).is_not_none()

        # Unload
        ws.path.value = None
        assert_that(ws.collection.value).is_none()

    def test_change_path_switches_collection(self, tmp_path: Path) -> None:
        """Changing path loads a different collection."""
        # Create two collections
        api1 = tmp_path / "api1"
        api1.mkdir()
        (api1 / "_collection.yaml").write_text("name: API 1\n")

        api2 = tmp_path / "api2"
        api2.mkdir()
        (api2 / "_collection.yaml").write_text("name: API 2\n")

        ws = Workspace()

        ws.path.value = api1
        assert ws.collection.value is not None
        assert_that(ws.collection.value.name.value).is_equal_to("API 1")

        ws.path.value = api2
        assert ws.collection.value is not None
        assert_that(ws.collection.value.name.value).is_equal_to("API 2")

    def test_collection_state_parent_is_workspace(self, tmp_path: Path) -> None:
        """Loaded collection has workspace as state_parent."""
        coll_dir = tmp_path / "api"
        coll_dir.mkdir()
        (coll_dir / "_collection.yaml").write_text("name: API\n")

        ws = Workspace()
        ws.path.value = coll_dir

        assert ws.collection.value is not None
        assert_that(ws.collection.value.state_parent).is_same_as(ws)

    def test_save_writes_to_disk(self, tmp_path: Path) -> None:
        """on_save.emit() saves the collection to disk."""
        # Create initial collection
        coll_dir = tmp_path / "api"
        coll_dir.mkdir()
        (coll_dir / "_collection.yaml").write_text("name: Original\n")

        ws = Workspace()
        ws.path.value = coll_dir

        # Modify
        assert ws.collection.value is not None
        ws.collection.value.name.value = "Modified"

        # Save
        ws.on_save.emit()

        # Reload and check
        reloaded = load_collection(coll_dir)
        assert_that(reloaded.name.value).is_equal_to("Modified")


class TestRequestGetFullPath:
    """Tests for Request._get_full_path()."""

    def test_request_with_workspace_path(self, tmp_path: Path) -> None:
        """Request can resolve full path through workspace."""
        # Create collection structure
        coll_dir = tmp_path / "api"
        coll_dir.mkdir()
        (coll_dir / "_collection.yaml").write_text("name: API\n")
        (coll_dir / "test-req.yaml").write_text("name: Test\nmethod: GET\nurl: /test\n")

        ws = Workspace()
        ws.path.value = coll_dir

        assert ws.collection.value is not None
        request = ws.collection.value.items.value[0]
        assert isinstance(request, Request)

        path = request._get_full_path()
        assert path is not None
        # Use Path parts for cross-platform comparison
        assert_that(path.parts[-2:]).is_equal_to(("api", "test-req.yaml"))

    def test_request_without_workspace_returns_none(self) -> None:
        """Request without workspace in hierarchy returns None."""
        coll = Collection()
        coll.filename.value = "my-coll"
        req = coll.add_request("Test")
        req.filename.value = "test-req"

        # No workspace in hierarchy
        assert_that(req._get_full_path()).is_none()

    def test_nested_request_path(self, tmp_path: Path) -> None:
        """Nested request resolves correct path."""
        # Create nested structure
        coll_dir = tmp_path / "api"
        coll_dir.mkdir()
        (coll_dir / "_collection.yaml").write_text("name: API\n")

        sub_dir = coll_dir / "users"
        sub_dir.mkdir()
        (sub_dir / "_collection.yaml").write_text("name: Users\n")
        (sub_dir / "get-user.yaml").write_text("name: Get User\nmethod: GET\nurl: /users/1\n")

        ws = Workspace()
        ws.path.value = coll_dir

        assert ws.collection.value is not None
        sub_coll = ws.collection.value.items.value[0]
        assert isinstance(sub_coll, Collection)
        request = sub_coll.items.value[0]
        assert isinstance(request, Request)

        path = request._get_full_path()
        assert path is not None
        # Use Path parts for cross-platform comparison
        assert_that(path.parts[-3:]).is_equal_to(("api", "users", "get-user.yaml"))


class TestRequestOnSave:
    """Tests for Request.on_save event."""

    def test_on_save_writes_to_disk(self, tmp_path: Path) -> None:
        """Emitting on_save saves the request to its path."""
        # Create collection structure
        coll_dir = tmp_path / "api"
        coll_dir.mkdir()
        (coll_dir / "_collection.yaml").write_text("name: API\n")
        (coll_dir / "test.yaml").write_text("name: Test\nmethod: GET\nurl: /original\n")

        ws = Workspace()
        ws.path.value = coll_dir

        assert ws.collection.value is not None
        request = ws.collection.value.items.value[0]
        assert isinstance(request, Request)

        # Modify
        request.url.value = "/modified"

        # Save
        request.on_save.emit()

        # Reload and check
        reloaded = load_collection(coll_dir)
        reloaded_req = reloaded.items.value[0]
        assert isinstance(reloaded_req, Request)
        assert_that(reloaded_req.url.value).is_equal_to("/modified")


class TestFilenamePreservation:
    """Tests that filename is preserved through save cycles."""

    def test_save_preserves_request_filename(self, tmp_path: Path) -> None:
        """Modified request saves to original filename."""
        # Create with specific filename
        coll_dir = tmp_path / "api"
        coll_dir.mkdir()
        (coll_dir / "_collection.yaml").write_text("name: API\n")
        (coll_dir / "my-specific-filename.yaml").write_text("name: Different Name\nmethod: GET\nurl: /test\n")

        coll = load_collection(coll_dir)
        request = coll.items.value[0]
        assert isinstance(request, Request)

        # Name is different from filename
        assert_that(request.name.value).is_equal_to("Different Name")
        assert_that(request.filename.value).is_equal_to("my-specific-filename")

        # Modify and save
        request.name.value = "Even More Different"
        save_collection(coll, coll_dir)

        # Should still use original filename
        assert_that((coll_dir / "my-specific-filename.yaml").exists()).is_true()

    def test_new_request_saves_with_slugified_name(self, tmp_path: Path) -> None:
        """New request (no filename) uses slugified name."""
        coll = Collection()
        coll.name.value = "API"
        coll.filename.value = "api"

        req = coll.add_request("Get All Users")
        req.method.value = HttpMethod.GET
        req.url.value = "/users"
        # No filename set

        save_collection(coll, tmp_path / "api")

        # Should create slugified filename
        assert_that((tmp_path / "api" / "get-all-users.yaml").exists()).is_true()

    def test_save_preserves_collection_filename(self, tmp_path: Path) -> None:
        """Collection saves to original folder name."""
        # Create with specific folder name
        coll_dir = tmp_path / "my-specific-folder"
        coll_dir.mkdir()
        (coll_dir / "_collection.yaml").write_text("name: Different Display Name\n")

        root = Collection()
        root.name.value = "Root"
        root.filename.value = "root"

        # Load and add as sub-collection
        sub = load_collection(coll_dir)
        root.items.append(sub)

        # Save
        save_dir = tmp_path / "output"
        save_collection(root, save_dir / "root")

        # Sub-collection should keep its folder name
        assert_that((save_dir / "root" / "my-specific-folder").exists()).is_true()
