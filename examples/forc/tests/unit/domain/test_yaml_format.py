"""Tests for YAML file format implementation."""

import tempfile
from pathlib import Path

from assertpy import assert_that
from forc.domain.formats import YamlFormat
from forc.domain.models import (
    ApiKeyAuth,
    ApiKeyLocation,
    BasicAuth,
    BearerAuth,
    BodyType,
    Collection,
    Environment,
    HttpMethod,
    KeyValue,
    Request,
    Workspace,
)
from observant import ObservableList


class TestYamlFormatRequest:
    def setup_method(self):
        self.fmt = YamlFormat()
        self.tmp_dir = tempfile.mkdtemp()

    def test_save_and_load_minimal_request(self):
        req = Request(name="Get Users")
        path = Path(self.tmp_dir) / "get_users.yaml"

        self.fmt.save_request(req, path)
        loaded = self.fmt.load_request(path)

        assert_that(loaded.name).is_equal_to("Get Users")
        assert_that(loaded.method).is_equal_to(HttpMethod.GET)
        assert_that(loaded.url).is_equal_to("")

    def test_save_and_load_full_request(self):
        req = Request(
            name="Create User",
            method=HttpMethod.POST,
            url="https://api.example.com/users",
            headers=[KeyValue(key="Content-Type", value="application/json")],
            query_params=[KeyValue(key="debug", value="true", enabled=False)],
            body='{"name": "Alice"}',
            body_type=BodyType.JSON,
        )
        path = Path(self.tmp_dir) / "create_user.yaml"

        self.fmt.save_request(req, path)
        loaded = self.fmt.load_request(path)

        assert_that(loaded.name).is_equal_to("Create User")
        assert_that(loaded.method).is_equal_to(HttpMethod.POST)
        assert_that(loaded.url).is_equal_to("https://api.example.com/users")
        assert_that(loaded.headers).is_length(1)
        assert_that(loaded.headers[0].key).is_equal_to("Content-Type")
        assert_that(loaded.query_params).is_length(1)
        assert_that(loaded.query_params[0].enabled).is_false()
        assert_that(loaded.body).is_equal_to('{"name": "Alice"}')
        assert_that(loaded.body_type).is_equal_to(BodyType.JSON)

    def test_save_and_load_request_with_basic_auth(self):
        req = Request(
            name="Login",
            method=HttpMethod.POST,
            url="https://api.example.com/login",
            auth=BasicAuth(username="user", password="pass"),
        )
        path = Path(self.tmp_dir) / "login.yaml"

        self.fmt.save_request(req, path)
        loaded = self.fmt.load_request(path)

        assert loaded.auth is not None
        assert isinstance(loaded.auth, BasicAuth)
        assert_that(loaded.auth.username).is_equal_to("user")
        assert_that(loaded.auth.password).is_equal_to("pass")

    def test_save_and_load_request_with_bearer_auth(self):
        req = Request(
            name="Get Profile",
            url="https://api.example.com/profile",
            auth=BearerAuth(token="secret-token"),
        )
        path = Path(self.tmp_dir) / "profile.yaml"

        self.fmt.save_request(req, path)
        loaded = self.fmt.load_request(path)

        assert loaded.auth is not None
        assert isinstance(loaded.auth, BearerAuth)
        assert_that(loaded.auth.token).is_equal_to("secret-token")

    def test_save_and_load_request_with_api_key_auth(self):
        req = Request(
            name="API Call",
            url="https://api.example.com/data",
            auth=ApiKeyAuth(key="X-API-Key", value="my-key", location=ApiKeyLocation.HEADER),
        )
        path = Path(self.tmp_dir) / "api_call.yaml"

        self.fmt.save_request(req, path)
        loaded = self.fmt.load_request(path)

        assert loaded.auth is not None
        assert isinstance(loaded.auth, ApiKeyAuth)
        assert_that(loaded.auth.key).is_equal_to("X-API-Key")
        assert_that(loaded.auth.value).is_equal_to("my-key")
        assert_that(loaded.auth.location).is_equal_to(ApiKeyLocation.HEADER)


class TestYamlFormatEnvironment:
    def setup_method(self):
        self.fmt = YamlFormat()
        self.tmp_dir = tempfile.mkdtemp()

    def test_save_and_load_environment(self):
        variables: ObservableList[KeyValue] = ObservableList()
        variables.append(KeyValue(key="API_URL", value="http://localhost:3000"))
        variables.append(KeyValue(key="DEBUG", value="true"))
        env = Environment(name="development", variables=variables)
        path = Path(self.tmp_dir) / "dev.yaml"

        self.fmt.save_environment(env, path)
        loaded = self.fmt.load_environment(path)

        assert_that(loaded.name).is_equal_to("development")
        assert_that(list(loaded.variables)).is_length(2)
        assert_that(loaded.variables[0].key).is_equal_to("API_URL")
        assert_that(loaded.variables[1].key).is_equal_to("DEBUG")


class TestYamlFormatCollection:
    def setup_method(self):
        self.fmt = YamlFormat()
        self.tmp_dir = tempfile.mkdtemp()

    def test_save_and_load_empty_collection(self):
        coll = Collection(name="My API")
        path = Path(self.tmp_dir) / "my-api"

        self.fmt.save_collection(coll, path)
        loaded = self.fmt.load_collection(path)

        assert_that(loaded.name).is_equal_to("My API")
        assert_that(loaded.items).is_empty()

    def test_save_and_load_collection_with_requests(self):
        coll = Collection(
            name="Users",
            items=ObservableList(
                [
                    Request(name="Get Users", url="/users"),
                    Request(name="Create User", method=HttpMethod.POST, url="/users"),
                ]
            ),
        )
        path = Path(self.tmp_dir) / "users"

        self.fmt.save_collection(coll, path)
        loaded = self.fmt.load_collection(path)

        assert_that(loaded.name).is_equal_to("Users")
        assert_that(loaded.items).is_length(2)
        assert_that(loaded.items[0]).is_instance_of(Request)
        assert_that(loaded.items[0].name).is_equal_to("Create User")  # sorted alphabetically
        assert_that(loaded.items[1].name).is_equal_to("Get Users")

    def test_save_and_load_nested_collection(self):
        inner = Collection(
            name="Auth",
            items=ObservableList([Request(name="Login", method=HttpMethod.POST)]),
        )
        outer = Collection(
            name="API",
            items=ObservableList([inner, Request(name="Health")]),
        )
        path = Path(self.tmp_dir) / "api"

        self.fmt.save_collection(outer, path)
        loaded = self.fmt.load_collection(path)

        assert_that(loaded.name).is_equal_to("API")
        assert_that(loaded.items).is_length(2)
        # Items are sorted: 'auth' directory comes before 'health.yaml'
        inner_coll = loaded.items[0]
        assert isinstance(inner_coll, Collection)
        assert_that(inner_coll.name).is_equal_to("Auth")
        assert_that(inner_coll.items).is_length(1)
        assert isinstance(loaded.items[1], Request)
        assert_that(loaded.items[1].name).is_equal_to("Health")


class TestYamlFormatWorkspace:
    def setup_method(self):
        self.fmt = YamlFormat()
        self.tmp_dir = tempfile.mkdtemp()

    def test_save_and_load_empty_workspace(self):
        ws = Workspace(name="My Workspace")
        path = Path(self.tmp_dir) / "workspace"

        self.fmt.save_workspace(ws, path)
        loaded = self.fmt.load_workspace(path)

        assert_that(loaded.name).is_equal_to("My Workspace")
        assert_that(loaded.collections).is_empty()
        assert_that(loaded.environments).is_empty()
        assert_that(loaded.active_environment.get()).is_none()

    def test_save_and_load_workspace_with_environments(self):
        dev_vars: ObservableList[KeyValue] = ObservableList()
        dev_vars.append(KeyValue(key="URL", value="localhost"))
        prod_vars: ObservableList[KeyValue] = ObservableList()
        prod_vars.append(KeyValue(key="URL", value="api.example.com"))
        envs: ObservableList[Environment] = ObservableList()
        envs.append(Environment(name="dev", variables=dev_vars))
        envs.append(Environment(name="prod", variables=prod_vars))
        ws = Workspace(
            name="Project",
            environments=envs,
        )
        ws.active_environment.set("dev")
        path = Path(self.tmp_dir) / "project"

        self.fmt.save_workspace(ws, path)
        loaded = self.fmt.load_workspace(path)

        assert_that(loaded.name).is_equal_to("Project")
        assert_that(list(loaded.environments)).is_length(2)
        assert_that(loaded.active_environment.get()).is_equal_to("dev")

    def test_save_and_load_full_workspace(self):
        envs: ObservableList[Environment] = ObservableList()
        envs.append(Environment(name="dev"))
        ws = Workspace(
            name="Full Project",
            collections=ObservableList(
                [
                    Collection(
                        name="Users API",
                        items=ObservableList(
                            [
                                Request(name="Get Users"),
                                Request(name="Create User", method=HttpMethod.POST),
                            ]
                        ),
                    ),
                ]
            ),
            environments=envs,
        )
        ws.active_environment.set("dev")
        path = Path(self.tmp_dir) / "full-project"

        self.fmt.save_workspace(ws, path)
        loaded = self.fmt.load_workspace(path)

        assert_that(loaded.name).is_equal_to("Full Project")
        assert_that(loaded.collections).is_length(1)
        assert_that(loaded.collections[0].name).is_equal_to("Users API")
        assert_that(loaded.collections[0].items).is_length(2)
        assert_that(loaded.environments).is_length(1)
        assert_that(loaded.active_environment.get()).is_equal_to("dev")

    def test_load_workspace_without_config(self):
        # Create a workspace directory without forc.yaml
        path = Path(self.tmp_dir) / "no-config"
        path.mkdir()

        loaded = self.fmt.load_workspace(path)

        assert_that(loaded.name).is_equal_to("no-config")  # Falls back to directory name
        assert_that(loaded.collections).is_empty()
        assert_that(loaded.environments).is_empty()
