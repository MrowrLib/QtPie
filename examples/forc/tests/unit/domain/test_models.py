"""Tests for forc domain models."""

from assertpy import assert_that
from forc.domain.models import (
    ApiKeyAuth,
    ApiKeyLocation,
    Auth,
    AuthType,
    BasicAuth,
    BearerAuth,
    BodyType,
    Collection,
    Environment,
    HttpMethod,
    KeyValue,
    Request,
    Response,
    Workspace,
)
from observant import ObservableList


class TestKeyValue:
    def test_create_with_defaults(self):
        kv = KeyValue(key="foo", value="bar")
        assert_that(kv.key).is_equal_to("foo")
        assert_that(kv.value).is_equal_to("bar")
        assert_that(kv.enabled).is_true()

    def test_create_disabled(self):
        kv = KeyValue(key="foo", value="bar", enabled=False)
        assert_that(kv.enabled).is_false()


class TestHttpMethod:
    def test_all_methods_exist(self):
        methods = [m.value for m in HttpMethod]
        assert_that(methods).contains("GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS")

    def test_method_values(self):
        assert_that(HttpMethod.GET.value).is_equal_to("GET")
        assert_that(HttpMethod.POST.value).is_equal_to("POST")


class TestBodyType:
    def test_all_types_exist(self):
        types = [t.value for t in BodyType]
        assert_that(types).contains("none", "json", "form_urlencoded", "form_data", "text", "xml")


class TestAuth:
    def test_base_auth_defaults_to_none(self):
        auth = Auth()
        assert_that(auth.type).is_equal_to(AuthType.NONE)

    def test_basic_auth_sets_type(self):
        auth = BasicAuth(username="user", password="pass")
        assert_that(auth.type).is_equal_to(AuthType.BASIC)
        assert_that(auth.username).is_equal_to("user")
        assert_that(auth.password).is_equal_to("pass")

    def test_bearer_auth_sets_type(self):
        auth = BearerAuth(token="secret-token")
        assert_that(auth.type).is_equal_to(AuthType.BEARER)
        assert_that(auth.token).is_equal_to("secret-token")

    def test_api_key_auth_sets_type(self):
        auth = ApiKeyAuth(key="X-API-Key", value="my-key", location=ApiKeyLocation.HEADER)
        assert_that(auth.type).is_equal_to(AuthType.API_KEY)
        assert_that(auth.key).is_equal_to("X-API-Key")
        assert_that(auth.value).is_equal_to("my-key")
        assert_that(auth.location).is_equal_to(ApiKeyLocation.HEADER)

    def test_api_key_defaults_to_header(self):
        auth = ApiKeyAuth(key="key", value="val")
        assert_that(auth.location).is_equal_to(ApiKeyLocation.HEADER)


class TestRequest:
    def test_create_minimal(self):
        req = Request(name="Get Users")
        assert_that(req.name).is_equal_to("Get Users")
        assert_that(req.method).is_equal_to(HttpMethod.GET)
        assert_that(req.url).is_equal_to("")
        assert_that(req.headers).is_empty()
        assert_that(req.query_params).is_empty()
        assert_that(req.body).is_equal_to("")
        assert_that(req.body_type).is_equal_to(BodyType.NONE)
        assert_that(req.auth).is_none()

    def test_create_full(self):
        req = Request(
            name="Create User",
            method=HttpMethod.POST,
            url="https://api.example.com/users",
            headers=[KeyValue(key="Content-Type", value="application/json")],
            query_params=[KeyValue(key="debug", value="true")],
            body='{"name": "Alice"}',
            body_type=BodyType.JSON,
            auth=BearerAuth(token="token123"),
        )
        assert_that(req.name).is_equal_to("Create User")
        assert_that(req.method).is_equal_to(HttpMethod.POST)
        assert_that(req.url).is_equal_to("https://api.example.com/users")
        assert_that(req.headers).is_length(1)
        assert_that(req.headers[0].key).is_equal_to("Content-Type")
        assert_that(req.query_params).is_length(1)
        assert_that(req.body).is_equal_to('{"name": "Alice"}')
        assert_that(req.body_type).is_equal_to(BodyType.JSON)
        assert_that(req.auth).is_instance_of(BearerAuth)


class TestCollection:
    def test_create_empty(self):
        coll = Collection(name="My API")
        assert_that(coll.name).is_equal_to("My API")
        assert_that(coll.items).is_empty()

    def test_create_with_requests(self):
        coll = Collection(
            name="Users",
            items=ObservableList(
                [
                    Request(name="Get Users"),
                    Request(name="Create User", method=HttpMethod.POST),
                ]
            ),
        )
        assert_that(coll.items).is_length(2)

    def test_nested_collections(self):
        inner = Collection(name="Auth", items=ObservableList([Request(name="Login")]))
        outer = Collection(name="API", items=ObservableList([inner, Request(name="Health")]))
        assert_that(outer.items).is_length(2)
        assert_that(outer.items[0]).is_instance_of(Collection)
        assert_that(outer.items[1]).is_instance_of(Request)


class TestEnvironment:
    def test_create_empty(self):
        env = Environment(name="dev")
        assert_that(env.name).is_equal_to("dev")
        assert_that(env.variables).is_empty()

    def test_create_with_variables(self):
        variables: ObservableList[KeyValue] = ObservableList()
        variables.append(KeyValue(key="API_URL", value="https://api.example.com"))
        variables.append(KeyValue(key="TIMEOUT", value="30"))
        env = Environment(name="prod", variables=variables)
        assert_that(list(env.variables)).is_length(2)


class TestWorkspace:
    def test_create_empty(self):
        ws = Workspace(name="My Workspace")
        assert_that(ws.name).is_equal_to("My Workspace")
        assert_that(ws.collections).is_empty()
        assert_that(ws.environments).is_empty()
        assert_that(ws.active_environment.get()).is_none()

    def test_create_full(self):
        envs: ObservableList[Environment] = ObservableList()
        envs.append(Environment(name="dev"))
        envs.append(Environment(name="prod"))
        ws = Workspace(
            name="Project",
            collections=ObservableList([Collection(name="API")]),
            environments=envs,
        )
        ws.active_environment.set("dev")
        assert_that(list(ws.collections)).is_length(1)
        assert_that(list(ws.environments)).is_length(2)
        assert_that(ws.active_environment.get()).is_equal_to("dev")


class TestResponse:
    def test_create_response(self):
        resp = Response(
            status_code=200,
            status_text="OK",
            headers={"Content-Type": "application/json"},
            body=b'{"success": true}',
            time_ms=125.5,
            size_bytes=17,
        )
        assert_that(resp.status_code).is_equal_to(200)
        assert_that(resp.status_text).is_equal_to("OK")
        assert_that(resp.headers).contains_key("Content-Type")
        assert_that(resp.body).is_equal_to(b'{"success": true}')
        assert_that(resp.time_ms).is_equal_to(125.5)
        assert_that(resp.size_bytes).is_equal_to(17)
