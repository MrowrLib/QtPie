# pyright: reportPrivateUsage=false
"""Tests for workspace service."""

import tempfile
from pathlib import Path

from assertpy import assert_that
from forc.domain.models import Environment, HttpMethod, KeyValue, Request
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
