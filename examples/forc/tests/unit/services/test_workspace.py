# pyright: reportPrivateUsage=false
"""Tests for workspace service."""

import tempfile
from pathlib import Path

from assertpy import assert_that
from forc.domain.models import Collection, Environment, HttpMethod, KeyValue, Request
from forc.services.workspace import WorkspaceService


class TestWorkspaceServiceBasic:
    def setup_method(self):
        self.tmp_dir = Path(tempfile.mkdtemp())
        self.svc = WorkspaceService()

    def test_initially_not_loaded(self):
        assert_that(self.svc.is_loaded).is_false()
        assert_that(self.svc.workspace).is_none()
        assert_that(self.svc.path).is_none()

    def test_create_workspace(self):
        ws = self.svc.create("My Project", self.tmp_dir / "project")

        assert_that(self.svc.is_loaded).is_true()
        assert_that(ws.name).is_equal_to("My Project")
        assert_that(self.svc.path).is_equal_to(self.tmp_dir / "project")

    def test_load_workspace(self):
        # Create first
        self.svc.create("Test", self.tmp_dir / "test")
        self.svc.close()

        # Load it back
        ws = self.svc.load(self.tmp_dir / "test")

        assert_that(ws.name).is_equal_to("Test")
        assert_that(self.svc.is_loaded).is_true()

    def test_close_workspace(self):
        self.svc.create("Test", self.tmp_dir / "test")
        self.svc.close()

        assert_that(self.svc.is_loaded).is_false()
        assert_that(self.svc.workspace).is_none()

    def test_save_updates_disk(self):
        ws = self.svc.create("Original", self.tmp_dir / "project")
        ws.name = "Updated"
        self.svc.save()

        # Reload and verify
        self.svc.close()
        reloaded = self.svc.load(self.tmp_dir / "project")
        assert_that(reloaded.name).is_equal_to("Updated")


class TestWorkspaceServiceEnvironments:
    def setup_method(self):
        self.tmp_dir = Path(tempfile.mkdtemp())
        self.svc = WorkspaceService()
        self.svc.create("Test", self.tmp_dir / "test")

    def test_add_environment(self):
        env = Environment(name="dev", variables=[KeyValue(key="URL", value="localhost")])
        self.svc.add_environment(env)

        assert self.svc.workspace is not None
        assert_that(self.svc.workspace.environments).is_length(1)
        assert_that(self.svc.workspace.environments[0].name).is_equal_to("dev")

    def test_remove_environment(self):
        self.svc.add_environment(Environment(name="dev"))
        self.svc.add_environment(Environment(name="prod"))
        self.svc.remove_environment("dev")

        assert self.svc.workspace is not None
        assert_that(self.svc.workspace.environments).is_length(1)
        assert_that(self.svc.workspace.environments[0].name).is_equal_to("prod")

    def test_set_active_environment(self):
        self.svc.add_environment(Environment(name="dev"))
        self.svc.set_active_environment("dev")

        assert self.svc.workspace is not None
        assert_that(self.svc.workspace.active_environment).is_equal_to("dev")

    def test_get_active_environment(self):
        env = Environment(name="dev", variables=[KeyValue(key="X", value="Y")])
        self.svc.add_environment(env)
        self.svc.set_active_environment("dev")

        active = self.svc.get_active_environment()

        assert active is not None
        assert_that(active.name).is_equal_to("dev")
        assert_that(active.variables).is_length(1)

    def test_get_active_environment_none(self):
        assert_that(self.svc.get_active_environment()).is_none()

    def test_remove_active_environment_clears_active(self):
        self.svc.add_environment(Environment(name="dev"))
        self.svc.set_active_environment("dev")
        self.svc.remove_environment("dev")

        assert self.svc.workspace is not None
        assert_that(self.svc.workspace.active_environment).is_none()


class TestWorkspaceServiceCollections:
    def setup_method(self):
        self.tmp_dir = Path(tempfile.mkdtemp())
        self.svc = WorkspaceService()
        self.svc.create("Test", self.tmp_dir / "test")

    def test_add_collection(self):
        coll = self.svc.add_collection("Users API")
        self.svc.add_request("Get Users", coll)

        assert self.svc.workspace is not None
        assert_that(self.svc.workspace.collections).is_length(1)
        assert_that(self.svc.workspace.collections[0].name).is_equal_to("Users API")

    def test_remove_collection(self):
        self.svc.add_collection("API 1")
        self.svc.add_collection("API 2")
        self.svc.remove_collection("API 1")

        assert self.svc.workspace is not None
        assert_that(self.svc.workspace.collections).is_length(1)
        assert_that(self.svc.workspace.collections[0].name).is_equal_to("API 2")


class TestWorkspaceServiceVariableResolution:
    def setup_method(self):
        self.tmp_dir = Path(tempfile.mkdtemp())
        self.svc = WorkspaceService()
        self.svc.create("Test", self.tmp_dir / "test")

    def test_resolve_from_environment(self):
        env = Environment(
            name="dev",
            variables=[
                KeyValue(key="API_URL", value="http://localhost:3000"),
                KeyValue(key="VERSION", value="v1"),
            ],
        )
        self.svc.add_environment(env)
        self.svc.set_active_environment("dev")

        result = self.svc.resolve_variables("${API_URL}/${VERSION}/users")

        assert_that(result).is_equal_to("http://localhost:3000/v1/users")

    def test_resolve_secret_variable(self):
        """Secret variables resolve the same as regular ones."""
        env = Environment(
            name="dev",
            variables=[
                KeyValue(key="SECRET_KEY", value="abc123", secret=True),
            ],
        )
        self.svc.add_environment(env)
        self.svc.set_active_environment("dev")

        result = self.svc.resolve_variables("Key: ${SECRET_KEY}")

        assert_that(result).is_equal_to("Key: abc123")

    def test_secret_and_regular_vars_together(self):
        """Both secret and regular variables resolve correctly."""
        env = Environment(
            name="dev",
            variables=[
                KeyValue(key="BASE_URL", value="https://api.example.com"),
                KeyValue(key="API_KEY", value="secret123", secret=True),
            ],
        )
        self.svc.add_environment(env)
        self.svc.set_active_environment("dev")

        result = self.svc.resolve_variables("${BASE_URL}?key=${API_KEY}")

        assert_that(result).is_equal_to("https://api.example.com?key=secret123")

    def test_disabled_env_vars_not_resolved(self):
        env = Environment(
            name="dev",
            variables=[KeyValue(key="DISABLED", value="should_not_appear", enabled=False)],
        )
        self.svc.add_environment(env)
        self.svc.set_active_environment("dev")

        # strict=False to test "left as-is" behavior
        result = self.svc._environments.resolve("${DISABLED}", strict=False)

        assert_that(result).is_equal_to("${DISABLED}")  # Left as-is

    def test_unresolved_left_as_is(self):
        # strict=False to test "left as-is" behavior
        result = self.svc._environments.resolve("${UNKNOWN_VAR}", strict=False)
        assert_that(result).is_equal_to("${UNKNOWN_VAR}")


class TestWorkspaceServiceResolveRequest:
    def setup_method(self):
        self.tmp_dir = Path(tempfile.mkdtemp())
        self.svc = WorkspaceService()
        self.svc.create("Test", self.tmp_dir / "test")

        env = Environment(
            name="dev",
            variables=[
                KeyValue(key="BASE_URL", value="https://api.example.com"),
                KeyValue(key="TOKEN", value="secret123"),
            ],
        )
        self.svc.add_environment(env)
        self.svc.set_active_environment("dev")

    def test_resolve_url(self):
        req = Request(name="Test", url="${BASE_URL}/users")
        resolved = self.svc.resolve_request(req)

        assert_that(resolved.url).is_equal_to("https://api.example.com/users")

    def test_resolve_headers(self):
        req = Request(
            name="Test",
            url="https://example.com",
            headers=[KeyValue(key="Authorization", value="Bearer ${TOKEN}")],
        )
        resolved = self.svc.resolve_request(req)

        assert_that(resolved.headers[0].value).is_equal_to("Bearer secret123")

    def test_resolve_query_params(self):
        req = Request(
            name="Test",
            url="https://example.com",
            query_params=[KeyValue(key="token", value="${TOKEN}")],
        )
        resolved = self.svc.resolve_request(req)

        assert_that(resolved.query_params[0].value).is_equal_to("secret123")

    def test_resolve_body(self):
        req = Request(
            name="Test",
            url="https://example.com",
            body='{"url": "${BASE_URL}"}',
        )
        resolved = self.svc.resolve_request(req)

        assert_that(resolved.body).is_equal_to('{"url": "https://api.example.com"}')

    def test_original_unchanged(self):
        req = Request(name="Test", url="${BASE_URL}/users")
        self.svc.resolve_request(req)

        # Original should be unchanged
        assert_that(req.url).is_equal_to("${BASE_URL}/users")


class TestWorkspaceServicePersistence:
    def setup_method(self):
        self.tmp_dir = Path(tempfile.mkdtemp())
        self.svc = WorkspaceService()

    def test_full_round_trip(self):
        # Create with data
        self.svc.create("Full Project", self.tmp_dir / "project")
        self.svc.add_environment(Environment(name="dev", variables=[KeyValue(key="X", value="Y")]))
        api_coll = self.svc.add_collection("API")
        get_req = self.svc.add_request("Get", api_coll)
        get_req.method = HttpMethod.GET
        get_req.url = "/get"
        post_req = self.svc.add_request("Post", api_coll)
        post_req.method = HttpMethod.POST
        post_req.url = "/post"
        self.svc.set_active_environment("dev")
        self.svc.save()

        # Load fresh
        svc2 = WorkspaceService()
        ws = svc2.load(self.tmp_dir / "project")

        assert_that(ws.name).is_equal_to("Full Project")
        assert_that(ws.environments).is_length(1)
        assert_that(ws.environments[0].name).is_equal_to("dev")
        assert_that(ws.collections).is_length(1)
        assert_that(ws.collections[0].items).is_length(2)
        assert_that(ws.active_environment).is_equal_to("dev")


class TestWorkspaceServiceRename:
    def setup_method(self):
        self.tmp_dir = Path(tempfile.mkdtemp())
        self.svc = WorkspaceService()
        self.svc.create("Test", self.tmp_dir / "test")

    def test_rename_request(self):
        coll = self.svc.add_collection("API")
        req = self.svc.add_request("Get Users", coll)
        req.url = "https://example.com/users"
        self.svc.save_request(req)

        old_path = self.tmp_dir / "test" / "collections" / "api" / "get-users.yaml"
        assert_that(old_path.exists()).is_true()

        self.svc.rename_request(req, "List Users")

        assert_that(req.name).is_equal_to("List Users")
        new_path = self.tmp_dir / "test" / "collections" / "api" / "list-users.yaml"
        assert_that(new_path.exists()).is_true()
        assert_that(old_path.exists()).is_false()

    def test_rename_request_preserves_content(self):
        coll = self.svc.add_collection("API")
        req = self.svc.add_request("Get Users", coll)
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

    def test_rename_collection(self):
        coll = self.svc.add_collection("Users API")
        req = self.svc.add_request("Get Users", coll)
        self.svc.save_request(req)

        old_path = self.tmp_dir / "test" / "collections" / "users-api"
        assert_that(old_path.exists()).is_true()

        self.svc.rename_collection(coll, "People API")

        assert_that(coll.name).is_equal_to("People API")
        assert_that(coll.folder).is_equal_to("people-api")
        new_path = self.tmp_dir / "test" / "collections" / "people-api"
        assert_that(new_path.exists()).is_true()
        assert_that(old_path.exists()).is_false()

    def test_rename_collection_preserves_contents(self):
        coll = self.svc.add_collection("Users API")
        req = self.svc.add_request("Get Users", coll)
        req.url = "https://example.com/users"
        self.svc.save_request(req)

        self.svc.rename_collection(coll, "People API")

        # Verify request file still exists in new location
        req_path = self.tmp_dir / "test" / "collections" / "people-api" / "get-users.yaml"
        assert_that(req_path.exists()).is_true()

    def test_rename_nested_collection(self):
        parent = self.svc.add_collection("API")
        child = self.svc.add_collection("Users", parent=parent)
        req = self.svc.add_request("Get User", child)
        self.svc.save_request(req)

        old_path = self.tmp_dir / "test" / "collections" / "api" / "users"
        assert_that(old_path.exists()).is_true()

        self.svc.rename_collection(child, "People")

        assert_that(child.name).is_equal_to("People")
        assert_that(child.folder).is_equal_to("people")
        new_path = self.tmp_dir / "test" / "collections" / "api" / "people"
        assert_that(new_path.exists()).is_true()
        assert_that(old_path.exists()).is_false()

    def test_rename_item_request(self):
        coll = self.svc.add_collection("API")
        req = self.svc.add_request("Get Users", coll)
        self.svc.save_request(req)

        self.svc.rename_item(req, "List Users")

        assert_that(req.name).is_equal_to("List Users")

    def test_rename_item_collection(self):
        coll = self.svc.add_collection("Users API")
        req = self.svc.add_request("Get Users", coll)
        self.svc.save_request(req)

        self.svc.rename_item(coll, "People API")

        assert_that(coll.name).is_equal_to("People API")
        assert_that(coll.folder).is_equal_to("people-api")

    def test_rename_request_no_workspace_raises(self):
        import pytest

        self.svc.close()
        req = Request(name="Test")

        with pytest.raises(RuntimeError, match="No workspace"):
            self.svc.rename_request(req, "New Name")

    def test_rename_collection_no_workspace_raises(self):
        import pytest

        self.svc.close()
        coll = Collection(name="Test")

        with pytest.raises(RuntimeError, match="No workspace"):
            self.svc.rename_collection(coll, "New Name")

    def test_new_collection_persists_name_in_metadata(self):
        """New collections should save their name to _collection.yaml."""
        coll = self.svc.add_collection("My Cool API")
        req = self.svc.add_request("Get Users", coll)
        self.svc.save_request(req)

        # Reload workspace and verify the collection name comes back correctly
        self.svc.close()
        ws = self.svc.load(self.tmp_dir / "test")

        assert_that(ws.collections).is_length(1)
        assert_that(ws.collections[0].name).is_equal_to("My Cool API")

    def test_renamed_collection_persists_name_in_metadata(self):
        """Renaming a collection should update _collection.yaml with new name."""
        coll = self.svc.add_collection("Old Name")
        req = self.svc.add_request("Get Users", coll)
        self.svc.save_request(req)

        self.svc.rename_collection(coll, "New Name")

        # Reload workspace and verify the NEW name is persisted
        self.svc.close()
        ws = self.svc.load(self.tmp_dir / "test")

        assert_that(ws.collections).is_length(1)
        assert_that(ws.collections[0].name).is_equal_to("New Name")

    def test_renamed_nested_collection_persists_name_in_metadata(self):
        """Renaming a nested collection should update its _collection.yaml."""
        parent = self.svc.add_collection("Parent")
        child = self.svc.add_collection("Old Child Name", parent=parent)
        req = self.svc.add_request("Get User", child)
        self.svc.save_request(req)

        self.svc.rename_collection(child, "New Child Name")

        # Reload and verify
        self.svc.close()
        ws = self.svc.load(self.tmp_dir / "test")

        reloaded_child = ws.collections[0].items[0]
        assert isinstance(reloaded_child, Collection)
        assert_that(reloaded_child.name).is_equal_to("New Child Name")
