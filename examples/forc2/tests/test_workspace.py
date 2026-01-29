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

    def test_load_workspace(self, tmp_path: Path) -> None:
        """Workspace.load() loads collection from disk."""
        # Create a workspace with collections/ subfolder
        workspace_dir = tmp_path / "my-workspace"
        workspace_dir.mkdir()
        coll_dir = workspace_dir / "collections"
        coll_dir.mkdir()
        (coll_dir / "_collection.yaml").write_text("name: My API\n")
        (coll_dir / "test.yaml").write_text("name: Test Request\nmethod: GET\nurl: /test\n")

        ws = Workspace.load(workspace_dir)

        assert ws is not None
        assert_that(ws.collection.value).is_not_none()
        assert ws.collection.value is not None
        assert_that(ws.collection.value.name.value).is_equal_to("My API")
        assert_that(list(ws.collection.value.items.value)).is_length(1)

    def test_load_nonexistent_returns_none(self, tmp_path: Path) -> None:
        """Workspace.load() returns None for nonexistent folder."""
        ws = Workspace.load(tmp_path / "does-not-exist")
        assert_that(ws).is_none()

    def test_collection_state_parent_is_workspace(self, tmp_path: Path) -> None:
        """Loaded collection has workspace as state_parent."""
        workspace_dir = tmp_path / "workspace"
        workspace_dir.mkdir()
        coll_dir = workspace_dir / "collections"
        coll_dir.mkdir()
        (coll_dir / "_collection.yaml").write_text("name: API\n")

        ws = Workspace.load(workspace_dir)

        assert ws is not None
        assert ws.collection.value is not None
        assert_that(ws.collection.value.state_parent).is_same_as(ws)

    def test_save_writes_to_disk(self, tmp_path: Path) -> None:
        """workspace.save() saves the collection to disk."""
        # Create initial workspace
        workspace_dir = tmp_path / "workspace"
        workspace_dir.mkdir()
        coll_dir = workspace_dir / "collections"
        coll_dir.mkdir()
        (coll_dir / "_collection.yaml").write_text("name: Original\n")

        ws = Workspace.load(workspace_dir)
        assert ws is not None

        # Modify
        assert ws.collection.value is not None
        ws.collection.value.name.value = "Modified"

        # Save
        ws.save()

        # Reload and check
        reloaded = load_collection(coll_dir)
        assert_that(reloaded.name.value).is_equal_to("Modified")

    def test_add_collection(self, tmp_path: Path) -> None:
        """Workspace.add_collection() creates a new top-level collection."""
        workspace_dir = tmp_path / "workspace"
        workspace_dir.mkdir()
        coll_dir = workspace_dir / "collections"
        coll_dir.mkdir()
        (coll_dir / "_collection.yaml").write_text("name: Root\n")

        ws = Workspace.load(workspace_dir)
        assert ws is not None

        new_coll = ws.add_collection("My New Collection")

        assert_that(new_coll.name.value).is_equal_to("My New Collection")
        assert_that(new_coll.state_parent).is_same_as(ws.collection.value)
        assert ws.collection.value is not None
        assert new_coll in ws.collection.value.items.value

    def test_add_request(self, tmp_path: Path) -> None:
        """Workspace.add_request() creates a new top-level request."""
        workspace_dir = tmp_path / "workspace"
        workspace_dir.mkdir()
        coll_dir = workspace_dir / "collections"
        coll_dir.mkdir()
        (coll_dir / "_collection.yaml").write_text("name: Root\n")

        ws = Workspace.load(workspace_dir)
        assert ws is not None

        new_req = ws.add_request("Get Users")

        assert_that(new_req.name.value).is_equal_to("Get Users")
        assert_that(new_req.state_parent).is_same_as(ws.collection.value)
        assert ws.collection.value is not None
        assert new_req in ws.collection.value.items.value


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

        ws = Workspace.load(workspace_dir)

        assert ws is not None
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

        ws = Workspace.load(workspace_dir)

        assert ws is not None
        assert ws.collection.value is not None
        sub_coll = ws.collection.value.items.value[0]
        assert isinstance(sub_coll, Collection)
        request = sub_coll.items.value[0]
        assert isinstance(request, Request)

        path = request._get_full_path()
        assert path is not None
        # Use Path parts for cross-platform comparison
        assert_that(path.parts[-3:]).is_equal_to(("collections", "users", "get-user.yaml"))


class TestRequestSave:
    """Tests for Request.save() method."""

    def test_save_writes_to_disk(self, tmp_path: Path) -> None:
        """request.save() saves the request to its path."""
        # Create workspace structure
        workspace_dir = tmp_path / "workspace"
        workspace_dir.mkdir()
        coll_dir = workspace_dir / "collections"
        coll_dir.mkdir()
        (coll_dir / "_collection.yaml").write_text("name: API\n")
        (coll_dir / "test.yaml").write_text("name: Test\nmethod: GET\nurl: /original\n")

        ws = Workspace.load(workspace_dir)

        assert ws is not None
        assert ws.collection.value is not None
        request = ws.collection.value.items.value[0]
        assert isinstance(request, Request)

        # Modify
        request.url.value = "/modified"

        # Save
        request.save()

        # Reload and check
        reloaded = load_collection(coll_dir)
        reloaded_req = reloaded.items.value[0]
        assert isinstance(reloaded_req, Request)
        assert_that(reloaded_req.url.value).is_equal_to("/modified")


class TestCollectionSave:
    """Tests for Collection.save() method."""

    def test_save_writes_to_disk(self, tmp_path: Path) -> None:
        """collection.save() saves the collection to its path."""
        workspace_dir = tmp_path / "workspace"
        workspace_dir.mkdir()
        coll_dir = workspace_dir / "collections"
        coll_dir.mkdir()
        (coll_dir / "_collection.yaml").write_text("name: Original\n")

        ws = Workspace.load(workspace_dir)

        assert ws is not None
        assert ws.collection.value is not None

        # Modify
        ws.collection.value.name.value = "Modified"

        # Save just the collection
        ws.collection.value.save()

        # Reload and check
        reloaded = load_collection(coll_dir)
        assert_that(reloaded.name.value).is_equal_to("Modified")


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
  URL:
    value: http://localhost
""")
        (env_dir / "prod.yaml").write_text("""
name: Production
variables:
  URL:
    value: https://api.example.com
""")

        ws = Workspace.load(workspace_dir)

        assert ws is not None
        assert_that(list(ws.environments.value)).is_length(2)
        # Sorted alphabetically
        assert_that(ws.environments.value[0].name.value).is_equal_to("Development")
        assert_that(ws.environments.value[1].name.value).is_equal_to("Production")

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

        ws = Workspace.load(workspace_dir)

        assert ws is not None
        assert_that(ws.environments.value[0].state_parent).is_same_as(ws)

    def test_load_demo_api_environments(self) -> None:
        """Load environments from demo-api fixtures."""
        fixtures = Path("examples/forc2/fixtures/demo-api")
        if not fixtures.exists():
            return

        ws = Workspace.load(fixtures)

        assert ws is not None
        # Should have loaded environments
        assert_that(list(ws.environments.value)).is_length(2)

        # Find Development environment by iterating
        dev = next((e for e in ws.environments.value if e.name.value == "Development"), None)
        assert dev is not None
        assert_that(dev.variables.value).is_not_empty()

        # Check a variable
        base_url_var = dev.variables.value.get("BASE_URL")
        assert base_url_var is not None
        assert_that(base_url_var.value).is_equal_to("http://localhost:8000")


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


class TestWorkspaceRefresh:
    """Tests for Workspace.refresh() method."""

    def test_refresh_reloads_collection(self, tmp_path: Path) -> None:
        """refresh() reloads collection from disk."""
        workspace_dir = tmp_path / "workspace"
        workspace_dir.mkdir()
        coll_dir = workspace_dir / "collections"
        coll_dir.mkdir()
        (coll_dir / "_collection.yaml").write_text("name: Original\n")

        ws = Workspace.load(workspace_dir)
        assert ws is not None
        assert ws.collection.value is not None
        assert_that(ws.collection.value.name.value).is_equal_to("Original")

        # Modify file on disk externally
        (coll_dir / "_collection.yaml").write_text("name: Modified\n")

        # Refresh
        result = ws.refresh()

        assert_that(result).is_true()
        assert ws.collection.value is not None
        assert_that(ws.collection.value.name.value).is_equal_to("Modified")

    def test_refresh_reloads_requests(self, tmp_path: Path) -> None:
        """refresh() picks up new requests added to disk."""
        workspace_dir = tmp_path / "workspace"
        workspace_dir.mkdir()
        coll_dir = workspace_dir / "collections"
        coll_dir.mkdir()
        (coll_dir / "_collection.yaml").write_text("name: API\n")

        ws = Workspace.load(workspace_dir)
        assert ws is not None
        assert ws.collection.value is not None
        assert_that(list(ws.collection.value.items.value)).is_empty()

        # Add a request file externally
        (coll_dir / "new-request.yaml").write_text("name: New Request\nmethod: GET\nurl: /new\n")

        # Refresh
        ws.refresh()

        assert_that(list(ws.collection.value.items.value)).is_length(1)

    def test_refresh_reloads_environments(self, tmp_path: Path) -> None:
        """refresh() reloads environments from disk."""
        workspace_dir = tmp_path / "workspace"
        workspace_dir.mkdir()
        coll_dir = workspace_dir / "collections"
        coll_dir.mkdir()
        (coll_dir / "_collection.yaml").write_text("name: API\n")

        ws = Workspace.load(workspace_dir)
        assert ws is not None
        assert_that(list(ws.environments.value)).is_empty()

        # Add environments externally
        env_dir = workspace_dir / "environments"
        env_dir.mkdir()
        (env_dir / "dev.yaml").write_text("name: Development\n")

        # Refresh
        ws.refresh()

        assert_that(list(ws.environments.value)).is_length(1)
        assert_that(ws.environments.value[0].name.value).is_equal_to("Development")

    def test_refresh_returns_false_if_path_missing(self, tmp_path: Path) -> None:
        """refresh() returns False if workspace folder was deleted."""
        workspace_dir = tmp_path / "workspace"
        workspace_dir.mkdir()
        coll_dir = workspace_dir / "collections"
        coll_dir.mkdir()
        (coll_dir / "_collection.yaml").write_text("name: API\n")

        ws = Workspace.load(workspace_dir)
        assert ws is not None

        # Delete the workspace folder
        import shutil

        shutil.rmtree(workspace_dir)

        # Refresh should return False
        result = ws.refresh()
        assert_that(result).is_false()

    def test_refresh_preserves_workspace_identity(self, tmp_path: Path) -> None:
        """refresh() updates in-place, keeping same Workspace instance."""
        workspace_dir = tmp_path / "workspace"
        workspace_dir.mkdir()
        coll_dir = workspace_dir / "collections"
        coll_dir.mkdir()
        (coll_dir / "_collection.yaml").write_text("name: API\n")

        ws = Workspace.load(workspace_dir)
        assert ws is not None
        original_id = id(ws)

        ws.refresh()

        # Same instance
        assert_that(id(ws)).is_equal_to(original_id)

    def test_refresh_after_delete_and_restore(self, tmp_path: Path) -> None:
        """refresh() picks up a request that was deleted then restored on disk."""
        # Setup workspace with a request
        workspace_dir = tmp_path / "workspace"
        workspace_dir.mkdir()
        coll_dir = workspace_dir / "collections"
        coll_dir.mkdir()
        (coll_dir / "_collection.yaml").write_text("name: API\n")
        request_file = coll_dir / "test.yaml"
        request_content = "name: Test\nmethod: GET\nurl: /test\n"
        request_file.write_text(request_content)

        ws = Workspace.load(workspace_dir)
        assert ws is not None
        assert ws.collection.value is not None
        assert_that(list(ws.collection.value.items.value)).is_length(1)

        # Delete the request via domain
        request = ws.collection.value.items.value[0]
        assert isinstance(request, Request)
        request.delete()

        # Verify it's gone from memory and disk
        assert_that(list(ws.collection.value.items.value)).is_empty()
        assert_that(request_file.exists()).is_false()

        # Restore the file on disk (simulating external restore)
        request_file.write_text(request_content)

        # Refresh
        ws.refresh()

        # Should see the restored request
        assert ws.collection.value is not None
        assert_that(list(ws.collection.value.items.value)).is_length(1)


class TestRequestDelete:
    """Tests for Request.delete() method."""

    def test_delete_removes_file_from_disk(self, tmp_path: Path) -> None:
        """request.delete() removes the request file from disk."""
        # Create workspace structure
        workspace_dir = tmp_path / "workspace"
        workspace_dir.mkdir()
        coll_dir = workspace_dir / "collections"
        coll_dir.mkdir()
        (coll_dir / "_collection.yaml").write_text("name: API\n")
        request_file = coll_dir / "test.yaml"
        request_file.write_text("name: Test\nmethod: GET\nurl: /test\n")

        ws = Workspace.load(workspace_dir)

        assert ws is not None
        assert ws.collection.value is not None
        request = ws.collection.value.items.value[0]
        assert isinstance(request, Request)

        # Delete the request
        request.delete()

        # File should be gone
        assert_that(request_file.exists()).is_false()

    def test_delete_removes_from_parent_collection(self, tmp_path: Path) -> None:
        """request.delete() removes the request from parent collection."""
        workspace_dir = tmp_path / "workspace"
        workspace_dir.mkdir()
        coll_dir = workspace_dir / "collections"
        coll_dir.mkdir()
        (coll_dir / "_collection.yaml").write_text("name: API\n")
        (coll_dir / "test.yaml").write_text("name: Test\nmethod: GET\nurl: /test\n")

        ws = Workspace.load(workspace_dir)

        assert ws is not None
        assert ws.collection.value is not None
        request = ws.collection.value.items.value[0]
        assert isinstance(request, Request)

        # Delete the request
        request.delete()

        # Should be removed from parent
        assert_that(list(ws.collection.value.items.value)).is_empty()
        assert_that(request.state_parent).is_none()

    def test_delete_unsaved_request(self) -> None:
        """Deleting unsaved request just removes from parent."""
        coll = Collection()
        coll.name.value = "Test"
        req = coll.add_request("New Request")

        assert_that(list(coll.items.value)).is_length(1)

        req.delete()

        assert_that(list(coll.items.value)).is_empty()


class TestCollectionDelete:
    """Tests for Collection.delete() method."""

    def test_delete_removes_folder_from_disk(self, tmp_path: Path) -> None:
        """collection.delete() removes the collection folder from disk."""
        workspace_dir = tmp_path / "workspace"
        workspace_dir.mkdir()
        coll_dir = workspace_dir / "collections"
        coll_dir.mkdir()
        (coll_dir / "_collection.yaml").write_text("name: API\n")

        sub_dir = coll_dir / "users"
        sub_dir.mkdir()
        (sub_dir / "_collection.yaml").write_text("name: Users\n")
        (sub_dir / "get-user.yaml").write_text("name: Get User\nmethod: GET\nurl: /users/1\n")

        ws = Workspace.load(workspace_dir)

        assert ws is not None
        assert ws.collection.value is not None
        sub_coll = ws.collection.value.items.value[0]
        assert isinstance(sub_coll, Collection)

        # Delete the sub-collection
        sub_coll.delete()

        # Folder should be gone (including contents)
        assert_that(sub_dir.exists()).is_false()

    def test_delete_removes_from_parent_collection(self, tmp_path: Path) -> None:
        """collection.delete() removes from parent collection."""
        workspace_dir = tmp_path / "workspace"
        workspace_dir.mkdir()
        coll_dir = workspace_dir / "collections"
        coll_dir.mkdir()
        (coll_dir / "_collection.yaml").write_text("name: API\n")

        sub_dir = coll_dir / "users"
        sub_dir.mkdir()
        (sub_dir / "_collection.yaml").write_text("name: Users\n")

        ws = Workspace.load(workspace_dir)

        assert ws is not None
        assert ws.collection.value is not None
        sub_coll = ws.collection.value.items.value[0]
        assert isinstance(sub_coll, Collection)

        # Delete the sub-collection
        sub_coll.delete()

        # Should be removed from parent
        assert_that(list(ws.collection.value.items.value)).is_empty()
        assert_that(sub_coll.state_parent).is_none()

    def test_delete_unsaved_collection(self) -> None:
        """Deleting unsaved collection just removes from parent."""
        root = Collection()
        root.name.value = "Root"
        sub = root.add_collection("Sub")

        assert_that(list(root.items.value)).is_length(1)

        sub.delete()

        assert_that(list(root.items.value)).is_empty()
