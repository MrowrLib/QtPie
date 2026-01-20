# pyright: reportPrivateUsage=false
"""Tests for workspace service."""

import tempfile
from pathlib import Path

from assertpy import assert_that
from forc.domain.models import Collection, HttpMethod, KeyValue, Request
from forc.services.workspace import WorkspaceService


class TestWorkspaceServiceBasic:
    def setup_method(self) -> None:
        self.tmp_dir = Path(tempfile.mkdtemp())
        self.svc = WorkspaceService()

    def test_initially_not_loaded(self) -> None:
        assert_that(self.svc.is_loaded).is_false()
        assert_that(self.svc.workspace).is_none()
        assert_that(self.svc.path).is_none()

    def test_create_workspace(self) -> None:
        ws = self.svc.create("My Project", self.tmp_dir / "project")

        assert_that(self.svc.is_loaded).is_true()
        assert_that(ws.name).is_equal_to("My Project")
        assert_that(self.svc.path).is_equal_to(self.tmp_dir / "project")

    def test_load_workspace(self) -> None:
        # Create first
        self.svc.create("Test", self.tmp_dir / "test")
        self.svc.close()

        # Load it back
        ws = self.svc.load(self.tmp_dir / "test")

        assert_that(ws.name).is_equal_to("Test")
        assert_that(self.svc.is_loaded).is_true()

    def test_close_workspace(self) -> None:
        self.svc.create("Test", self.tmp_dir / "test")
        self.svc.close()

        assert_that(self.svc.is_loaded).is_false()
        assert_that(self.svc.workspace).is_none()

    def test_save_updates_disk(self) -> None:
        ws = self.svc.create("Original", self.tmp_dir / "project")
        ws.name = "Updated"
        self.svc.save()

        # Reload and verify
        self.svc.close()
        reloaded = self.svc.load(self.tmp_dir / "project")
        assert_that(reloaded.name).is_equal_to("Updated")


class TestWorkspaceServiceEnvironments:
    """Tests for environment operations via EnvironmentsService."""

    def setup_method(self) -> None:
        self.tmp_dir = Path(tempfile.mkdtemp())
        self.svc = WorkspaceService()
        self.svc.create("Test", self.tmp_dir / "test")

    def test_create_environment(self) -> None:
        self.svc.environments.create("dev")

        assert self.svc.workspace is not None
        assert_that(list(self.svc.workspace.environments)).is_length(1)
        assert_that(self.svc.workspace.environments[0].name).is_equal_to("dev")

    def test_delete_environment(self) -> None:
        self.svc.environments.create("dev")
        self.svc.environments.create("prod")
        self.svc.environments.delete("dev")

        assert self.svc.workspace is not None
        assert_that(list(self.svc.workspace.environments)).is_length(1)
        assert_that(self.svc.workspace.environments[0].name).is_equal_to("prod")

    def test_set_active_environment(self) -> None:
        self.svc.environments.create("dev")
        assert self.svc.workspace is not None
        self.svc.workspace.active_environment.set("dev")

        assert_that(self.svc.workspace.active_environment.get()).is_equal_to("dev")

    def test_get_active_environment(self) -> None:
        self.svc.environments.create("dev")
        self.svc.environments.add_variable("dev", "X", "Y")
        assert self.svc.workspace is not None
        self.svc.workspace.active_environment.set("dev")

        active_name = self.svc.workspace.active_environment.get()
        assert active_name is not None
        active = self.svc.environments.get(active_name)

        assert active is not None
        assert_that(active.name).is_equal_to("dev")
        assert_that(list(active.variables)).is_length(1)

    def test_get_active_environment_none(self) -> None:
        assert self.svc.workspace is not None
        assert_that(self.svc.workspace.active_environment.get()).is_none()

    def test_delete_active_environment_clears_active(self) -> None:
        self.svc.environments.create("dev")
        assert self.svc.workspace is not None
        self.svc.workspace.active_environment.set("dev")
        self.svc.environments.delete("dev")

        assert_that(self.svc.workspace.active_environment.get()).is_none()

    def test_active_environment_change_persists(self) -> None:
        """When active_environment Observable changes, it persists to disk."""
        self.svc.environments.create("dev")
        self.svc.environments.create("prod")
        assert self.svc.workspace is not None

        # Set active and save
        self.svc.workspace.active_environment.set("dev")
        self.svc.save()

        # Reload and verify
        svc2 = WorkspaceService()
        ws2 = svc2.load(self.tmp_dir / "test")
        assert_that(ws2.active_environment.get()).is_equal_to("dev")

        # Change to different environment and save
        self.svc.workspace.active_environment.set("prod")
        self.svc.save()

        # Reload again and verify the change persisted
        svc3 = WorkspaceService()
        ws3 = svc3.load(self.tmp_dir / "test")
        assert_that(ws3.active_environment.get()).is_equal_to("prod")

    def test_active_environment_clear_persists(self) -> None:
        """Clearing active_environment persists to disk."""
        self.svc.environments.create("dev")
        assert self.svc.workspace is not None

        # Set active, save, then clear
        self.svc.workspace.active_environment.set("dev")
        self.svc.save()
        self.svc.workspace.active_environment.set(None)
        self.svc.save()

        # Reload and verify it's cleared
        svc2 = WorkspaceService()
        ws2 = svc2.load(self.tmp_dir / "test")
        assert_that(ws2.active_environment.get()).is_none()


class TestWorkspaceServiceCollections:
    def setup_method(self) -> None:
        self.tmp_dir = Path(tempfile.mkdtemp())
        self.svc = WorkspaceService()
        self.svc.create("Test", self.tmp_dir / "test")

    def test_create_collection(self) -> None:
        coll = self.svc.create_collection("Users API")
        self.svc.create_request("Get Users", coll)

        assert self.svc.workspace is not None
        assert_that(list(self.svc.workspace.collections)).is_length(1)
        assert_that(self.svc.workspace.collections[0].name).is_equal_to("Users API")

    def test_delete_collection(self) -> None:
        coll1 = self.svc.create_collection("API 1")
        self.svc.create_collection("API 2")
        self.svc.delete_collection(coll1)

        assert self.svc.workspace is not None
        assert_that(list(self.svc.workspace.collections)).is_length(1)
        assert_that(self.svc.workspace.collections[0].name).is_equal_to("API 2")


class TestWorkspaceServiceVariableResolution:
    def setup_method(self) -> None:
        self.tmp_dir = Path(tempfile.mkdtemp())
        self.svc = WorkspaceService()
        self.svc.create("Test", self.tmp_dir / "test")

    def test_resolve_from_environment(self) -> None:
        self.svc.environments.create("dev")
        self.svc.environments.add_variable("dev", "API_URL", "http://localhost:3000")
        self.svc.environments.add_variable("dev", "VERSION", "v1")
        assert self.svc.workspace is not None
        self.svc.workspace.active_environment.set("dev")

        result = self.svc.resolve_variables("${API_URL}/${VERSION}/users")

        assert_that(result).is_equal_to("http://localhost:3000/v1/users")

    def test_resolve_secret_variable(self) -> None:
        """Secret variables resolve the same as regular ones."""
        self.svc.environments.create("dev")
        self.svc.environments.add_variable("dev", "SECRET_KEY", "abc123", secret=True)
        assert self.svc.workspace is not None
        self.svc.workspace.active_environment.set("dev")

        result = self.svc.resolve_variables("Key: ${SECRET_KEY}")

        assert_that(result).is_equal_to("Key: abc123")

    def test_secret_and_regular_vars_together(self) -> None:
        """Both secret and regular variables resolve correctly."""
        self.svc.environments.create("dev")
        self.svc.environments.add_variable("dev", "BASE_URL", "https://api.example.com")
        self.svc.environments.add_variable("dev", "API_KEY", "secret123", secret=True)
        assert self.svc.workspace is not None
        self.svc.workspace.active_environment.set("dev")

        result = self.svc.resolve_variables("${BASE_URL}?key=${API_KEY}")

        assert_that(result).is_equal_to("https://api.example.com?key=secret123")

    def test_disabled_env_vars_not_resolved(self) -> None:
        self.svc.environments.create("dev")
        self.svc.environments.add_variable("dev", "DISABLED", "should_not_appear")
        self.svc.environments.update_variable("dev", "DISABLED", enabled=False)
        assert self.svc.workspace is not None
        self.svc.workspace.active_environment.set("dev")

        # strict=False to test "left as-is" behavior
        result = self.svc._environments.resolve("${DISABLED}", "dev", strict=False)

        assert_that(result).is_equal_to("${DISABLED}")  # Left as-is

    def test_unresolved_left_as_is(self) -> None:
        # strict=False to test "left as-is" behavior
        result = self.svc._environments.resolve("${UNKNOWN_VAR}", None, strict=False)
        assert_that(result).is_equal_to("${UNKNOWN_VAR}")


class TestWorkspaceServiceResolveRequest:
    def setup_method(self) -> None:
        self.tmp_dir = Path(tempfile.mkdtemp())
        self.svc = WorkspaceService()
        self.svc.create("Test", self.tmp_dir / "test")

        self.svc.environments.create("dev")
        self.svc.environments.add_variable("dev", "BASE_URL", "https://api.example.com")
        self.svc.environments.add_variable("dev", "TOKEN", "secret123")
        assert self.svc.workspace is not None
        self.svc.workspace.active_environment.set("dev")

    def test_resolve_url(self) -> None:
        req = Request(name="Test", url="${BASE_URL}/users")
        resolved = self.svc.resolve_request(req)

        assert_that(resolved.url).is_equal_to("https://api.example.com/users")

    def test_resolve_headers(self) -> None:
        req = Request(
            name="Test",
            url="https://example.com",
            headers=[KeyValue(key="Authorization", value="Bearer ${TOKEN}")],
        )
        resolved = self.svc.resolve_request(req)

        assert_that(resolved.headers[0].value).is_equal_to("Bearer secret123")

    def test_resolve_query_params(self) -> None:
        req = Request(
            name="Test",
            url="https://example.com",
            query_params=[KeyValue(key="token", value="${TOKEN}")],
        )
        resolved = self.svc.resolve_request(req)

        assert_that(resolved.query_params[0].value).is_equal_to("secret123")

    def test_resolve_body(self) -> None:
        req = Request(
            name="Test",
            url="https://example.com",
            body='{"url": "${BASE_URL}"}',
        )
        resolved = self.svc.resolve_request(req)

        assert_that(resolved.body).is_equal_to('{"url": "https://api.example.com"}')

    def test_original_unchanged(self) -> None:
        req = Request(name="Test", url="${BASE_URL}/users")
        self.svc.resolve_request(req)

        # Original should be unchanged
        assert_that(req.url).is_equal_to("${BASE_URL}/users")


class TestWorkspaceServicePersistence:
    def setup_method(self) -> None:
        self.tmp_dir = Path(tempfile.mkdtemp())
        self.svc = WorkspaceService()

    def test_full_round_trip(self) -> None:
        # Create with data
        self.svc.create("Full Project", self.tmp_dir / "project")
        self.svc.environments.create("dev")
        self.svc.environments.add_variable("dev", "X", "Y")
        api_coll = self.svc.create_collection("API")
        get_req = self.svc.create_request("Get", api_coll)
        get_req.method = HttpMethod.GET
        get_req.url = "/get"
        post_req = self.svc.create_request("Post", api_coll)
        post_req.method = HttpMethod.POST
        post_req.url = "/post"
        assert self.svc.workspace is not None
        self.svc.workspace.active_environment.set("dev")
        self.svc.save()

        # Load fresh
        svc2 = WorkspaceService()
        ws = svc2.load(self.tmp_dir / "project")

        assert_that(ws.name).is_equal_to("Full Project")
        assert_that(list(ws.environments)).is_length(1)
        assert_that(ws.environments[0].name).is_equal_to("dev")
        assert_that(list(ws.collections)).is_length(1)
        assert_that(list(ws.collections[0].items)).is_length(2)
        assert_that(ws.active_environment.get()).is_equal_to("dev")


class TestWorkspaceServiceRename:
    def setup_method(self) -> None:
        self.tmp_dir = Path(tempfile.mkdtemp())
        self.svc = WorkspaceService()
        self.svc.create("Test", self.tmp_dir / "test")

    def test_rename_request(self) -> None:
        coll = self.svc.create_collection("API")
        req = self.svc.create_request("Get Users", coll)
        req.url = "https://example.com/users"
        self.svc.save_request(req)

        old_path = self.tmp_dir / "test" / "collections" / "api" / "get-users.yaml"
        assert_that(old_path.exists()).is_true()

        self.svc.rename_request(req, "List Users")

        assert_that(req.name).is_equal_to("List Users")
        new_path = self.tmp_dir / "test" / "collections" / "api" / "list-users.yaml"
        assert_that(new_path.exists()).is_true()
        assert_that(old_path.exists()).is_false()

    def test_rename_request_preserves_content(self) -> None:
        coll = self.svc.create_collection("API")
        req = self.svc.create_request("Get Users", coll)
        req.url = "https://example.com/users"
        req.method = HttpMethod.POST
        self.svc.save_request(req)

        self.svc.rename_request(req, "List Users")

        # Reload and verify content preserved
        self.svc.close()
        ws = self.svc.load(self.tmp_dir / "test")
        reloaded_req = ws.collections[0].items[0]
        assert isinstance(reloaded_req, Request)
        assert_that(reloaded_req.name).is_equal_to("List Users")
        assert_that(reloaded_req.url).is_equal_to("https://example.com/users")
        assert_that(reloaded_req.method).is_equal_to(HttpMethod.POST)

    def test_rename_collection(self) -> None:
        coll = self.svc.create_collection("Users API")
        self.svc.create_request("Get Users", coll)

        old_path = self.tmp_dir / "test" / "collections" / "users-api"
        assert_that(old_path.exists()).is_true()

        self.svc.rename_collection(coll, "People API")

        assert_that(coll.name).is_equal_to("People API")
        assert_that(coll.folder).is_equal_to("people-api")
        new_path = self.tmp_dir / "test" / "collections" / "people-api"
        assert_that(new_path.exists()).is_true()
        assert_that(old_path.exists()).is_false()

    def test_rename_collection_preserves_contents(self) -> None:
        coll = self.svc.create_collection("Users API")
        req = self.svc.create_request("Get Users", coll)
        req.url = "https://example.com/users"
        self.svc.save_request(req)

        self.svc.rename_collection(coll, "People API")

        # Verify request file still exists in new location
        req_path = self.tmp_dir / "test" / "collections" / "people-api" / "get-users.yaml"
        assert_that(req_path.exists()).is_true()

    def test_rename_nested_collection(self) -> None:
        parent = self.svc.create_collection("API")
        child = self.svc.create_collection("Users", parent=parent)
        self.svc.create_request("Get User", child)

        old_path = self.tmp_dir / "test" / "collections" / "api" / "users"
        assert_that(old_path.exists()).is_true()

        self.svc.rename_collection(child, "People")

        assert_that(child.name).is_equal_to("People")
        assert_that(child.folder).is_equal_to("people")
        new_path = self.tmp_dir / "test" / "collections" / "api" / "people"
        assert_that(new_path.exists()).is_true()
        assert_that(old_path.exists()).is_false()

    def test_rename_request_via_method(self) -> None:
        coll = self.svc.create_collection("API")
        req = self.svc.create_request("Get Users", coll)

        self.svc.rename_request(req, "List Users")

        assert_that(req.name).is_equal_to("List Users")

    def test_rename_collection_via_method(self) -> None:
        coll = self.svc.create_collection("Users API")
        self.svc.create_request("Get Users", coll)

        self.svc.rename_collection(coll, "People API")

        assert_that(coll.name).is_equal_to("People API")
        assert_that(coll.folder).is_equal_to("people-api")

    def test_rename_request_no_workspace_raises(self) -> None:
        import pytest

        self.svc.close()
        req = Request(name="Test")

        with pytest.raises(RuntimeError, match="No workspace"):
            self.svc.rename_request(req, "New Name")

    def test_rename_collection_no_workspace_raises(self) -> None:
        import pytest

        self.svc.close()
        coll = Collection(name="Test")

        with pytest.raises(RuntimeError, match="No workspace"):
            self.svc.rename_collection(coll, "New Name")

    def test_new_collection_persists_name_in_metadata(self) -> None:
        """New collections should save their name to _collection.yaml."""
        coll = self.svc.create_collection("My Cool API")
        self.svc.create_request("Get Users", coll)

        # Reload workspace and verify the collection name comes back correctly
        self.svc.close()
        ws = self.svc.load(self.tmp_dir / "test")

        assert_that(list(ws.collections)).is_length(1)
        assert_that(ws.collections[0].name).is_equal_to("My Cool API")

    def test_renamed_collection_persists_name_in_metadata(self) -> None:
        """Renaming a collection should update _collection.yaml with new name."""
        coll = self.svc.create_collection("Old Name")
        self.svc.create_request("Get Users", coll)

        self.svc.rename_collection(coll, "New Name")

        # Reload workspace and verify the NEW name is persisted
        self.svc.close()
        ws = self.svc.load(self.tmp_dir / "test")

        assert_that(list(ws.collections)).is_length(1)
        assert_that(ws.collections[0].name).is_equal_to("New Name")

    def test_renamed_nested_collection_persists_name_in_metadata(self) -> None:
        """Renaming a nested collection should update its _collection.yaml."""
        parent = self.svc.create_collection("Parent")
        child = self.svc.create_collection("Old Child Name", parent=parent)
        self.svc.create_request("Get User", child)

        self.svc.rename_collection(child, "New Child Name")

        # Reload and verify
        self.svc.close()
        ws = self.svc.load(self.tmp_dir / "test")

        reloaded_child = ws.collections[0].items[0]
        assert isinstance(reloaded_child, Collection)
        assert_that(reloaded_child.name).is_equal_to("New Child Name")


class TestWorkspaceServiceCRUD:
    """Tests for the new consistent CRUD API with filesystem operations."""

    def setup_method(self) -> None:
        self.tmp_dir = Path(tempfile.mkdtemp())
        self.svc = WorkspaceService()
        self.svc.create("Test", self.tmp_dir / "test")

    # --- create_collection tests ---

    def test_create_collection_creates_folder_and_metadata(self) -> None:
        """create_collection should create the folder and _collection.yaml."""
        coll = self.svc.create_collection("Users API")

        assert_that(coll.name).is_equal_to("Users API")
        folder_path = self.tmp_dir / "test" / "collections" / "users-api"
        assert_that(folder_path.exists()).is_true()
        metadata_path = folder_path / "_collection.yaml"
        assert_that(metadata_path.exists()).is_true()

    def test_create_collection_nested_creates_in_parent(self) -> None:
        """create_collection with parent should create nested folder."""
        parent = self.svc.create_collection("API")
        child = self.svc.create_collection("Users", parent=parent)

        assert_that(child.name).is_equal_to("Users")
        assert_that(child.parent).is_equal_to(parent)
        child_path = self.tmp_dir / "test" / "collections" / "api" / "users"
        assert_that(child_path.exists()).is_true()

    def test_create_collection_no_workspace_raises(self) -> None:
        """create_collection without workspace should raise RuntimeError."""
        import pytest

        self.svc.close()

        with pytest.raises(RuntimeError, match="No workspace"):
            self.svc.create_collection("Test")

    # --- create_request tests ---

    def test_create_request_creates_file(self) -> None:
        """create_request should create the .yaml file on disk."""
        coll = self.svc.create_collection("API")
        req = self.svc.create_request("Get Users", coll)

        assert_that(req.name).is_equal_to("Get Users")
        assert_that(req.collection).is_equal_to(coll)
        file_path = self.tmp_dir / "test" / "collections" / "api" / "get-users.yaml"
        assert_that(file_path.exists()).is_true()

    def test_create_request_in_nested_collection(self) -> None:
        """create_request in nested collection should create file in correct path."""
        parent = self.svc.create_collection("API")
        child = self.svc.create_collection("Users", parent=parent)
        self.svc.create_request("Get User", child)

        file_path = self.tmp_dir / "test" / "collections" / "api" / "users" / "get-user.yaml"
        assert_that(file_path.exists()).is_true()

    def test_create_request_no_workspace_raises(self) -> None:
        """create_request without workspace should raise RuntimeError."""
        import pytest

        self.svc.close()
        coll = Collection(name="Test")

        with pytest.raises(RuntimeError, match="No workspace"):
            self.svc.create_request("Test Request", coll)

    # --- delete_request tests ---

    def test_delete_request_removes_file(self) -> None:
        """delete_request should remove the .yaml file from disk."""
        coll = self.svc.create_collection("API")
        req = self.svc.create_request("Get Users", coll)

        file_path = self.tmp_dir / "test" / "collections" / "api" / "get-users.yaml"
        assert_that(file_path.exists()).is_true()

        self.svc.delete_request(req)

        assert_that(file_path.exists()).is_false()

    def test_delete_request_removes_from_collection(self) -> None:
        """delete_request should remove request from its collection."""
        coll = self.svc.create_collection("API")
        req = self.svc.create_request("Get Users", coll)
        assert_that(list(coll.items)).is_length(1)

        self.svc.delete_request(req)

        assert_that(list(coll.items)).is_length(0)
        assert_that(req.collection).is_none()

    def test_delete_request_no_workspace_raises(self) -> None:
        """delete_request without workspace should raise RuntimeError."""
        import pytest

        self.svc.close()
        req = Request(name="Test")

        with pytest.raises(RuntimeError, match="No workspace"):
            self.svc.delete_request(req)

    def test_delete_request_nonexistent_file_still_removes_from_model(self) -> None:
        """delete_request should remove from model even if file doesn't exist."""
        coll = self.svc.create_collection("API")
        req = self.svc.create_request("Get Users", coll)

        # Manually delete the file
        file_path = self.tmp_dir / "test" / "collections" / "api" / "get-users.yaml"
        file_path.unlink()

        # Should not raise, just remove from model
        self.svc.delete_request(req)

        assert_that(list(coll.items)).is_length(0)

    # --- delete_collection tests ---

    def test_delete_collection_removes_folder(self) -> None:
        """delete_collection should remove the folder from disk."""
        coll = self.svc.create_collection("Users API")

        folder_path = self.tmp_dir / "test" / "collections" / "users-api"
        assert_that(folder_path.exists()).is_true()

        self.svc.delete_collection(coll)

        assert_that(folder_path.exists()).is_false()

    def test_delete_collection_recursive_deletes_contents(self) -> None:
        """delete_collection should recursively delete requests and nested collections."""
        parent = self.svc.create_collection("API")
        child = self.svc.create_collection("Users", parent=parent)
        self.svc.create_request("Get User", child)
        self.svc.create_request("List Users", parent)

        parent_path = self.tmp_dir / "test" / "collections" / "api"
        child_path = parent_path / "users"
        req1_path = child_path / "get-user.yaml"
        req2_path = parent_path / "list-users.yaml"

        assert_that(parent_path.exists()).is_true()
        assert_that(child_path.exists()).is_true()
        assert_that(req1_path.exists()).is_true()
        assert_that(req2_path.exists()).is_true()

        self.svc.delete_collection(parent)

        assert_that(parent_path.exists()).is_false()

    def test_delete_collection_removes_from_workspace(self) -> None:
        """delete_collection should remove top-level collection from workspace."""
        coll = self.svc.create_collection("API")
        assert self.svc.workspace is not None
        assert_that(list(self.svc.workspace.collections)).is_length(1)

        self.svc.delete_collection(coll)

        assert_that(list(self.svc.workspace.collections)).is_length(0)

    def test_delete_collection_nested_removes_from_parent(self) -> None:
        """delete_collection on nested collection should remove from parent."""
        parent = self.svc.create_collection("API")
        child = self.svc.create_collection("Users", parent=parent)
        assert_that(list(parent.items)).is_length(1)

        self.svc.delete_collection(child)

        assert_that(list(parent.items)).is_length(0)
        assert_that(child.parent).is_none()

    def test_delete_collection_no_workspace_raises(self) -> None:
        """delete_collection without workspace should raise RuntimeError."""
        import pytest

        self.svc.close()
        coll = Collection(name="Test")

        with pytest.raises(RuntimeError, match="No workspace"):
            self.svc.delete_collection(coll)

    # --- delete_item tests ---

    def test_delete_item_request(self) -> None:
        """delete_item should dispatch to delete_request for Request."""
        coll = self.svc.create_collection("API")
        req = self.svc.create_request("Get Users", coll)

        file_path = self.tmp_dir / "test" / "collections" / "api" / "get-users.yaml"
        assert_that(file_path.exists()).is_true()

        self.svc.delete_item(req)

        assert_that(file_path.exists()).is_false()
        assert_that(list(coll.items)).is_length(0)

    def test_delete_item_collection(self) -> None:
        """delete_item should dispatch to delete_collection for Collection."""
        coll = self.svc.create_collection("API")

        folder_path = self.tmp_dir / "test" / "collections" / "api"
        assert_that(folder_path.exists()).is_true()

        self.svc.delete_item(coll)

        assert_that(folder_path.exists()).is_false()
        assert self.svc.workspace is not None
        assert_that(list(self.svc.workspace.collections)).is_length(0)
