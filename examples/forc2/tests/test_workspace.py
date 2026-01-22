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
        # Create a workspace with collections/ subfolder
        workspace_dir = tmp_path / "my-workspace"
        workspace_dir.mkdir()
        coll_dir = workspace_dir / "collections"
        coll_dir.mkdir()
        (coll_dir / "_collection.yaml").write_text("name: My API\n")
        (coll_dir / "test.yaml").write_text("name: Test Request\nmethod: GET\nurl: /test\n")

        ws = Workspace()
        ws.path.value = workspace_dir

        assert_that(ws.collection.value).is_not_none()
        assert ws.collection.value is not None
        assert_that(ws.collection.value.name.value).is_equal_to("My API")
        assert_that(list(ws.collection.value.items.value)).is_length(1)

    def test_set_path_none_unloads(self, tmp_path: Path) -> None:
        """Setting path to None clears the collection."""
        # Create a workspace with collections/ subfolder
        workspace_dir = tmp_path / "workspace"
        workspace_dir.mkdir()
        coll_dir = workspace_dir / "collections"
        coll_dir.mkdir()
        (coll_dir / "_collection.yaml").write_text("name: API\n")

        ws = Workspace()
        ws.path.value = workspace_dir
        assert_that(ws.collection.value).is_not_none()

        # Unload
        ws.path.value = None
        assert_that(ws.collection.value).is_none()

    def test_change_path_switches_collection(self, tmp_path: Path) -> None:
        """Changing path loads a different collection."""
        # Create two workspaces
        ws1_dir = tmp_path / "workspace1"
        ws1_dir.mkdir()
        coll1 = ws1_dir / "collections"
        coll1.mkdir()
        (coll1 / "_collection.yaml").write_text("name: API 1\n")

        ws2_dir = tmp_path / "workspace2"
        ws2_dir.mkdir()
        coll2 = ws2_dir / "collections"
        coll2.mkdir()
        (coll2 / "_collection.yaml").write_text("name: API 2\n")

        ws = Workspace()

        ws.path.value = ws1_dir
        assert ws.collection.value is not None
        assert_that(ws.collection.value.name.value).is_equal_to("API 1")

        ws.path.value = ws2_dir
        assert ws.collection.value is not None
        assert_that(ws.collection.value.name.value).is_equal_to("API 2")

    def test_collection_state_parent_is_workspace(self, tmp_path: Path) -> None:
        """Loaded collection has workspace as state_parent."""
        workspace_dir = tmp_path / "workspace"
        workspace_dir.mkdir()
        coll_dir = workspace_dir / "collections"
        coll_dir.mkdir()
        (coll_dir / "_collection.yaml").write_text("name: API\n")

        ws = Workspace()
        ws.path.value = workspace_dir

        assert ws.collection.value is not None
        assert_that(ws.collection.value.state_parent).is_same_as(ws)

    def test_save_writes_to_disk(self, tmp_path: Path) -> None:
        """on_save.emit() saves the collection to disk."""
        # Create initial workspace
        workspace_dir = tmp_path / "workspace"
        workspace_dir.mkdir()
        coll_dir = workspace_dir / "collections"
        coll_dir.mkdir()
        (coll_dir / "_collection.yaml").write_text("name: Original\n")

        ws = Workspace()
        ws.path.value = workspace_dir

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
        # Create workspace structure
        workspace_dir = tmp_path / "workspace"
        workspace_dir.mkdir()
        coll_dir = workspace_dir / "collections"
        coll_dir.mkdir()
        (coll_dir / "_collection.yaml").write_text("name: API\n")
        (coll_dir / "test-req.yaml").write_text("name: Test\nmethod: GET\nurl: /test\n")

        ws = Workspace()
        ws.path.value = workspace_dir

        assert ws.collection.value is not None
        request = ws.collection.value.items.value[0]
        assert isinstance(request, Request)

        path = request._get_full_path()
        assert path is not None
        # Use Path parts for cross-platform comparison
        assert_that(path.parts[-2:]).is_equal_to(("collections", "test-req.yaml"))

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
        # Create workspace with nested collection structure
        workspace_dir = tmp_path / "workspace"
        workspace_dir.mkdir()
        coll_dir = workspace_dir / "collections"
        coll_dir.mkdir()
        (coll_dir / "_collection.yaml").write_text("name: API\n")

        sub_dir = coll_dir / "users"
        sub_dir.mkdir()
        (sub_dir / "_collection.yaml").write_text("name: Users\n")
        (sub_dir / "get-user.yaml").write_text("name: Get User\nmethod: GET\nurl: /users/1\n")

        ws = Workspace()
        ws.path.value = workspace_dir

        assert ws.collection.value is not None
        sub_coll = ws.collection.value.items.value[0]
        assert isinstance(sub_coll, Collection)
        request = sub_coll.items.value[0]
        assert isinstance(request, Request)

        path = request._get_full_path()
        assert path is not None
        # Use Path parts for cross-platform comparison
        assert_that(path.parts[-3:]).is_equal_to(("collections", "users", "get-user.yaml"))


class TestRequestOnSave:
    """Tests for Request.on_save event."""

    def test_on_save_writes_to_disk(self, tmp_path: Path) -> None:
        """Emitting on_save saves the request to its path."""
        # Create workspace structure
        workspace_dir = tmp_path / "workspace"
        workspace_dir.mkdir()
        coll_dir = workspace_dir / "collections"
        coll_dir.mkdir()
        (coll_dir / "_collection.yaml").write_text("name: API\n")
        (coll_dir / "test.yaml").write_text("name: Test\nmethod: GET\nurl: /original\n")

        ws = Workspace()
        ws.path.value = workspace_dir

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


class TestWorkspaceEnvironments:
    """Tests for Workspace environment loading."""

    def test_workspace_loads_environments(self, tmp_path: Path) -> None:
        """Workspace loads environments from environments/ subfolder."""
        # Create workspace structure
        workspace_dir = tmp_path / "workspace"
        workspace_dir.mkdir()
        coll_dir = workspace_dir / "collections"
        coll_dir.mkdir()
        (coll_dir / "_collection.yaml").write_text("name: API\n")

        env_dir = workspace_dir / "environments"
        env_dir.mkdir()
        (env_dir / "dev.yaml").write_text("""
name: Development
variables:
  - key: URL
    value: http://localhost
""")
        (env_dir / "prod.yaml").write_text("""
name: Production
variables:
  - key: URL
    value: https://api.example.com
""")

        ws = Workspace()
        ws.path.value = workspace_dir

        assert_that(list(ws.environments.value)).is_length(2)
        # Sorted alphabetically
        assert_that(ws.environments.value[0].name.value).is_equal_to("Development")
        assert_that(ws.environments.value[1].name.value).is_equal_to("Production")

    def test_get_environment_by_name(self, tmp_path: Path) -> None:
        """Can get environment by name."""
        workspace_dir = tmp_path / "workspace"
        workspace_dir.mkdir()
        coll_dir = workspace_dir / "collections"
        coll_dir.mkdir()
        (coll_dir / "_collection.yaml").write_text("name: API\n")

        env_dir = workspace_dir / "environments"
        env_dir.mkdir()
        (env_dir / "dev.yaml").write_text("name: Development\n")

        ws = Workspace()
        ws.path.value = workspace_dir

        dev = ws.get_environment("Development")
        assert dev is not None
        assert_that(dev.name.value).is_equal_to("Development")

        missing = ws.get_environment("NonExistent")
        assert_that(missing).is_none()

    def test_active_environment(self, tmp_path: Path) -> None:
        """Can set and get active environment."""
        workspace_dir = tmp_path / "workspace"
        workspace_dir.mkdir()
        coll_dir = workspace_dir / "collections"
        coll_dir.mkdir()
        (coll_dir / "_collection.yaml").write_text("name: API\n")

        env_dir = workspace_dir / "environments"
        env_dir.mkdir()
        (env_dir / "dev.yaml").write_text("name: Development\n")
        (env_dir / "prod.yaml").write_text("name: Production\n")

        ws = Workspace()
        ws.path.value = workspace_dir

        # Initially no active environment
        assert_that(ws.active_environment.value).is_none()
        assert_that(ws.get_active_environment()).is_none()

        # Set active
        ws.active_environment.value = "Development"
        active = ws.get_active_environment()
        assert active is not None
        assert_that(active.name.value).is_equal_to("Development")

    def test_environment_state_parent_is_workspace(self, tmp_path: Path) -> None:
        """Loaded environments have workspace as state_parent."""
        workspace_dir = tmp_path / "workspace"
        workspace_dir.mkdir()
        coll_dir = workspace_dir / "collections"
        coll_dir.mkdir()
        (coll_dir / "_collection.yaml").write_text("name: API\n")

        env_dir = workspace_dir / "environments"
        env_dir.mkdir()
        (env_dir / "dev.yaml").write_text("name: Dev\n")

        ws = Workspace()
        ws.path.value = workspace_dir

        assert_that(ws.environments.value[0].state_parent).is_same_as(ws)

    def test_load_demo_api_environments(self) -> None:
        """Load environments from demo-api fixtures."""
        fixtures = Path("examples/forc2/fixtures/demo-api")
        if not fixtures.exists():
            return

        ws = Workspace()
        ws.path.value = fixtures

        # Should have loaded environments
        assert_that(list(ws.environments.value)).is_length(2)

        # Find Development environment
        dev = ws.get_environment("Development")
        assert dev is not None
        assert_that(list(dev.variables.value)).is_not_empty()

        # Check a variable
        base_url = dev.get_variable("BASE_URL")
        assert_that(base_url).is_equal_to("http://localhost:8000")


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
