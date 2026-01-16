"""Tests for HTTP client service."""

import json

import httpx
from assertpy import assert_that
from forc.domain.models import (
    ApiKeyAuth,
    ApiKeyLocation,
    BasicAuth,
    BearerAuth,
    BodyType,
    HttpMethod,
    KeyValue,
    Request,
)
from forc.services.http_client import HttpClientService


def make_mock_client(handler: httpx.MockTransport) -> httpx.Client:
    """Create a client with mock transport."""
    return httpx.Client(transport=handler)


class TestHttpClientBasic:
    def test_simple_get(self):
        def handler(request: httpx.Request) -> httpx.Response:
            assert request.method == "GET"
            assert str(request.url) == "https://api.example.com/users"
            return httpx.Response(200, json={"users": []})

        client = make_mock_client(httpx.MockTransport(handler))
        svc = HttpClientService(client=client)

        req = Request(name="Get Users", method=HttpMethod.GET, url="https://api.example.com/users")
        resp = svc.send(req)

        assert_that(resp.status_code).is_equal_to(200)
        assert_that(json.loads(resp.body)).is_equal_to({"users": []})

    def test_post_with_json_body(self):
        def handler(request: httpx.Request) -> httpx.Response:
            assert request.method == "POST"
            assert request.headers["Content-Type"] == "application/json"
            body = json.loads(request.content.decode())
            assert body == {"name": "Alice"}
            return httpx.Response(201, json={"id": 1, "name": "Alice"})

        client = make_mock_client(httpx.MockTransport(handler))
        svc = HttpClientService(client=client)

        req = Request(
            name="Create User",
            method=HttpMethod.POST,
            url="https://api.example.com/users",
            body='{"name": "Alice"}',
            body_type=BodyType.JSON,
        )
        resp = svc.send(req)

        assert_that(resp.status_code).is_equal_to(201)

    def test_response_timing(self):
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200)

        client = make_mock_client(httpx.MockTransport(handler))
        svc = HttpClientService(client=client)

        req = Request(name="Test", url="https://example.com")
        resp = svc.send(req)

        assert_that(resp.time_ms).is_greater_than_or_equal_to(0)

    def test_response_size(self):
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, content=b"Hello World")

        client = make_mock_client(httpx.MockTransport(handler))
        svc = HttpClientService(client=client)

        req = Request(name="Test", url="https://example.com")
        resp = svc.send(req)

        assert_that(resp.size_bytes).is_equal_to(11)
        assert_that(resp.body).is_equal_to(b"Hello World")


class TestHttpClientHeaders:
    def test_custom_headers(self):
        def handler(request: httpx.Request) -> httpx.Response:
            assert request.headers["X-Custom"] == "value"
            assert request.headers["X-Another"] == "other"
            return httpx.Response(200)

        client = make_mock_client(httpx.MockTransport(handler))
        svc = HttpClientService(client=client)

        req = Request(
            name="Test",
            url="https://example.com",
            headers=[
                KeyValue(key="X-Custom", value="value"),
                KeyValue(key="X-Another", value="other"),
            ],
        )
        resp = svc.send(req)

        assert_that(resp.status_code).is_equal_to(200)

    def test_disabled_headers_not_sent(self):
        def handler(request: httpx.Request) -> httpx.Response:
            assert "X-Disabled" not in request.headers
            assert request.headers["X-Enabled"] == "yes"
            return httpx.Response(200)

        client = make_mock_client(httpx.MockTransport(handler))
        svc = HttpClientService(client=client)

        req = Request(
            name="Test",
            url="https://example.com",
            headers=[
                KeyValue(key="X-Enabled", value="yes", enabled=True),
                KeyValue(key="X-Disabled", value="no", enabled=False),
            ],
        )
        svc.send(req)


class TestHttpClientQueryParams:
    def test_query_params(self):
        def handler(request: httpx.Request) -> httpx.Response:
            assert request.url.params["page"] == "1"
            assert request.url.params["limit"] == "10"
            return httpx.Response(200)

        client = make_mock_client(httpx.MockTransport(handler))
        svc = HttpClientService(client=client)

        req = Request(
            name="Test",
            url="https://example.com/items",
            query_params=[
                KeyValue(key="page", value="1"),
                KeyValue(key="limit", value="10"),
            ],
        )
        svc.send(req)

    def test_disabled_params_not_sent(self):
        def handler(request: httpx.Request) -> httpx.Response:
            assert "disabled" not in request.url.params
            assert request.url.params["enabled"] == "yes"
            return httpx.Response(200)

        client = make_mock_client(httpx.MockTransport(handler))
        svc = HttpClientService(client=client)

        req = Request(
            name="Test",
            url="https://example.com",
            query_params=[
                KeyValue(key="enabled", value="yes", enabled=True),
                KeyValue(key="disabled", value="no", enabled=False),
            ],
        )
        svc.send(req)


class TestHttpClientAuth:
    def test_basic_auth(self):
        def handler(request: httpx.Request) -> httpx.Response:
            # httpx adds Authorization header for BasicAuth
            assert "Authorization" in request.headers
            auth_header = request.headers["Authorization"]
            assert auth_header.startswith("Basic ")
            return httpx.Response(200)

        client = make_mock_client(httpx.MockTransport(handler))
        svc = HttpClientService(client=client)

        req = Request(
            name="Test",
            url="https://example.com",
            auth=BasicAuth(username="user", password="pass"),
        )
        svc.send(req)

    def test_bearer_auth(self):
        def handler(request: httpx.Request) -> httpx.Response:
            assert request.headers["Authorization"] == "Bearer my-token"
            return httpx.Response(200)

        client = make_mock_client(httpx.MockTransport(handler))
        svc = HttpClientService(client=client)

        req = Request(
            name="Test",
            url="https://example.com",
            auth=BearerAuth(token="my-token"),
        )
        svc.send(req)

    def test_api_key_in_header(self):
        def handler(request: httpx.Request) -> httpx.Response:
            assert request.headers["X-API-Key"] == "secret-key"
            return httpx.Response(200)

        client = make_mock_client(httpx.MockTransport(handler))
        svc = HttpClientService(client=client)

        req = Request(
            name="Test",
            url="https://example.com",
            auth=ApiKeyAuth(key="X-API-Key", value="secret-key", location=ApiKeyLocation.HEADER),
        )
        svc.send(req)

    def test_api_key_in_query(self):
        def handler(request: httpx.Request) -> httpx.Response:
            assert request.url.params["api_key"] == "secret-key"
            return httpx.Response(200)

        client = make_mock_client(httpx.MockTransport(handler))
        svc = HttpClientService(client=client)

        req = Request(
            name="Test",
            url="https://example.com",
            auth=ApiKeyAuth(key="api_key", value="secret-key", location=ApiKeyLocation.QUERY),
        )
        svc.send(req)


class TestHttpClientBodyTypes:
    def test_form_content_type(self):
        def handler(request: httpx.Request) -> httpx.Response:
            assert request.headers["Content-Type"] == "application/x-www-form-urlencoded"
            return httpx.Response(200)

        client = make_mock_client(httpx.MockTransport(handler))
        svc = HttpClientService(client=client)

        req = Request(
            name="Test",
            method=HttpMethod.POST,
            url="https://example.com",
            body="key=value",
            body_type=BodyType.FORM_URLENCODED,
        )
        svc.send(req)

    def test_xml_content_type(self):
        def handler(request: httpx.Request) -> httpx.Response:
            assert request.headers["Content-Type"] == "application/xml"
            return httpx.Response(200)

        client = make_mock_client(httpx.MockTransport(handler))
        svc = HttpClientService(client=client)

        req = Request(
            name="Test",
            method=HttpMethod.POST,
            url="https://example.com",
            body="<root/>",
            body_type=BodyType.XML,
        )
        svc.send(req)

    def test_text_content_type(self):
        def handler(request: httpx.Request) -> httpx.Response:
            assert request.headers["Content-Type"] == "text/plain"
            return httpx.Response(200)

        client = make_mock_client(httpx.MockTransport(handler))
        svc = HttpClientService(client=client)

        req = Request(
            name="Test",
            method=HttpMethod.POST,
            url="https://example.com",
            body="plain text",
            body_type=BodyType.TEXT,
        )
        svc.send(req)

    def test_custom_content_type_not_overridden(self):
        def handler(request: httpx.Request) -> httpx.Response:
            assert request.headers["Content-Type"] == "application/custom"
            return httpx.Response(200)

        client = make_mock_client(httpx.MockTransport(handler))
        svc = HttpClientService(client=client)

        req = Request(
            name="Test",
            method=HttpMethod.POST,
            url="https://example.com",
            headers=[KeyValue(key="Content-Type", value="application/custom")],
            body="data",
            body_type=BodyType.JSON,
        )
        svc.send(req)


class TestHttpClientBaseUrl:
    def test_base_url_prepended(self):
        def handler(request: httpx.Request) -> httpx.Response:
            assert str(request.url) == "https://api.example.com/users"
            return httpx.Response(200)

        client = make_mock_client(httpx.MockTransport(handler))
        svc = HttpClientService(client=client)

        req = Request(name="Test", url="/users")
        svc.send(req, base_url="https://api.example.com")

    def test_absolute_url_ignores_base(self):
        def handler(request: httpx.Request) -> httpx.Response:
            assert str(request.url) == "https://other.com/path"
            return httpx.Response(200)

        client = make_mock_client(httpx.MockTransport(handler))
        svc = HttpClientService(client=client)

        req = Request(name="Test", url="https://other.com/path")
        svc.send(req, base_url="https://api.example.com")


class TestHttpClientAllMethods:
    def test_all_http_methods(self):
        for method in HttpMethod:

            def handler(request: httpx.Request, expected: str = method.value) -> httpx.Response:
                assert request.method == expected
                return httpx.Response(200)

            client = make_mock_client(httpx.MockTransport(handler))
            svc = HttpClientService(client=client)

            req = Request(name="Test", method=method, url="https://example.com")
            resp = svc.send(req)

            assert_that(resp.status_code).is_equal_to(200)
