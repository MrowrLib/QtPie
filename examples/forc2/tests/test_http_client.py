# pyright: reportPrivateUsage=false
# pyright: reportUnknownVariableType=false
# pyright: reportUnknownMemberType=false
# pyright: reportMissingImports=false
# pyright: reportUnknownParameterType=false
# pyright: reportUnknownArgumentType=false
"""Tests for HTTP client service."""

import json

import httpx
import pytest
from assertpy import assert_that
from forc2.domain import (
    ApiKeyAuth,
    ApiKeyLocation,
    BasicAuth,
    BearerAuth,
    BodyType,
    HttpMethod,
    Request,
    RequestKeyValue,
)
from forc2.services import HttpClient


def make_http_client(handler: httpx.MockTransport) -> HttpClient:
    """Create an HttpClient with mock transport."""
    http = HttpClient()
    http._httpx_client = httpx.AsyncClient(transport=handler)
    return http


class TestHttpClientBasic:
    @pytest.mark.asyncio
    async def test_simple_get(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            assert request.method == "GET"
            assert str(request.url) == "https://api.example.com/users"
            return httpx.Response(200, json={"users": []})

        http = make_http_client(httpx.MockTransport(handler))

        req = Request()
        req.method = HttpMethod.GET
        req.url = "https://api.example.com/users"

        resp = await http.send(req)

        assert_that(resp.status_code).is_equal_to(200)
        assert_that(json.loads(resp.body)).is_equal_to({"users": []})

    @pytest.mark.asyncio
    async def test_post_with_json_body(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            assert request.method == "POST"
            assert request.headers["Content-Type"] == "application/json"
            body = json.loads(request.content.decode())
            assert body == {"name": "Alice"}
            return httpx.Response(201, json={"id": 1, "name": "Alice"})

        http = make_http_client(httpx.MockTransport(handler))

        req = Request()
        req.method = HttpMethod.POST
        req.url = "https://api.example.com/users"
        req.body = '{"name": "Alice"}'
        req.body_type = BodyType.JSON

        resp = await http.send(req)

        assert_that(resp.status_code).is_equal_to(201)

    @pytest.mark.asyncio
    async def test_response_timing(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200)

        http = make_http_client(httpx.MockTransport(handler))

        req = Request()
        req.url = "https://example.com"

        resp = await http.send(req)

        assert_that(resp.time_ms).is_greater_than_or_equal_to(0)

    @pytest.mark.asyncio
    async def test_response_size(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, content=b"Hello World")

        http = make_http_client(httpx.MockTransport(handler))

        req = Request()
        req.url = "https://example.com"

        resp = await http.send(req)

        assert_that(resp.size_bytes).is_equal_to(11)
        assert_that(resp.body).is_equal_to(b"Hello World")


class TestHttpClientHeaders:
    @pytest.mark.asyncio
    async def test_custom_headers(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            assert request.headers["X-Custom"] == "value"
            assert request.headers["X-Another"] == "other"
            return httpx.Response(200)

        http = make_http_client(httpx.MockTransport(handler))

        req = Request()
        req.url = "https://example.com"
        req.headers.append(RequestKeyValue(name="X-Custom", value="value"))
        req.headers.append(RequestKeyValue(name="X-Another", value="other"))

        resp = await http.send(req)

        assert_that(resp.status_code).is_equal_to(200)

    @pytest.mark.asyncio
    async def test_disabled_headers_not_sent(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            assert "X-Disabled" not in request.headers
            assert request.headers["X-Enabled"] == "yes"
            return httpx.Response(200)

        http = make_http_client(httpx.MockTransport(handler))

        req = Request()
        req.url = "https://example.com"
        req.headers.append(RequestKeyValue(name="X-Enabled", value="yes", enabled=True))
        req.headers.append(RequestKeyValue(name="X-Disabled", value="no", enabled=False))

        await http.send(req)


class TestHttpClientQueryParams:
    @pytest.mark.asyncio
    async def test_query_params(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            assert request.url.params["page"] == "1"
            assert request.url.params["limit"] == "10"
            return httpx.Response(200)

        http = make_http_client(httpx.MockTransport(handler))

        req = Request()
        req.url = "https://example.com/items"
        req.query_params.append(RequestKeyValue(name="page", value="1"))
        req.query_params.append(RequestKeyValue(name="limit", value="10"))

        await http.send(req)

    @pytest.mark.asyncio
    async def test_disabled_params_not_sent(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            assert "disabled" not in request.url.params
            assert request.url.params["enabled"] == "yes"
            return httpx.Response(200)

        http = make_http_client(httpx.MockTransport(handler))

        req = Request()
        req.url = "https://example.com"
        req.query_params.append(RequestKeyValue(name="enabled", value="yes", enabled=True))
        req.query_params.append(RequestKeyValue(name="disabled", value="no", enabled=False))

        await http.send(req)


class TestHttpClientAuth:
    @pytest.mark.asyncio
    async def test_basic_auth(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            assert "Authorization" in request.headers
            auth_header = request.headers["Authorization"]
            assert auth_header.startswith("Basic ")
            return httpx.Response(200)

        http = make_http_client(httpx.MockTransport(handler))

        req = Request()
        req.url = "https://example.com"
        req.auth = BasicAuth(username="user", password="pass")

        await http.send(req)

    @pytest.mark.asyncio
    async def test_bearer_auth(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            assert request.headers["Authorization"] == "Bearer my-token"
            return httpx.Response(200)

        http = make_http_client(httpx.MockTransport(handler))

        req = Request()
        req.url = "https://example.com"
        req.auth = BearerAuth(token="my-token")

        await http.send(req)

    @pytest.mark.asyncio
    async def test_api_key_in_header(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            assert request.headers["X-API-Key"] == "secret-key"
            return httpx.Response(200)

        http = make_http_client(httpx.MockTransport(handler))

        req = Request()
        req.url = "https://example.com"
        req.auth = ApiKeyAuth(name="X-API-Key", value="secret-key", location=ApiKeyLocation.HEADER)

        await http.send(req)

    @pytest.mark.asyncio
    async def test_api_key_in_query(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            assert request.url.params["api_key"] == "secret-key"
            return httpx.Response(200)

        http = make_http_client(httpx.MockTransport(handler))

        req = Request()
        req.url = "https://example.com"
        req.auth = ApiKeyAuth(name="api_key", value="secret-key", location=ApiKeyLocation.QUERY)

        await http.send(req)


class TestHttpClientBodyTypes:
    @pytest.mark.asyncio
    async def test_form_content_type(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            assert request.headers["Content-Type"] == "application/x-www-form-urlencoded"
            return httpx.Response(200)

        http = make_http_client(httpx.MockTransport(handler))

        req = Request()
        req.method = HttpMethod.POST
        req.url = "https://example.com"
        req.body_fields.append(RequestKeyValue(name="key", value="value"))
        req.body_type = BodyType.FORM_URLENCODED

        await http.send(req)

    @pytest.mark.asyncio
    async def test_xml_content_type(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            assert request.headers["Content-Type"] == "application/xml"
            return httpx.Response(200)

        http = make_http_client(httpx.MockTransport(handler))

        req = Request()
        req.method = HttpMethod.POST
        req.url = "https://example.com"
        req.body = "<root/>"
        req.body_type = BodyType.XML

        await http.send(req)

    @pytest.mark.asyncio
    async def test_text_content_type(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            assert request.headers["Content-Type"] == "text/plain"
            return httpx.Response(200)

        http = make_http_client(httpx.MockTransport(handler))

        req = Request()
        req.method = HttpMethod.POST
        req.url = "https://example.com"
        req.body = "plain text"
        req.body_type = BodyType.TEXT

        await http.send(req)

    @pytest.mark.asyncio
    async def test_custom_content_type_not_overridden(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            assert request.headers["Content-Type"] == "application/custom"
            return httpx.Response(200)

        http = make_http_client(httpx.MockTransport(handler))

        req = Request()
        req.method = HttpMethod.POST
        req.url = "https://example.com"
        req.headers.append(RequestKeyValue(name="Content-Type", value="application/custom"))
        req.body = "data"
        req.body_type = BodyType.JSON

        await http.send(req)


class TestHttpClientBaseUrl:
    @pytest.mark.asyncio
    async def test_base_url_prepended(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            assert str(request.url) == "https://api.example.com/users"
            return httpx.Response(200)

        http = make_http_client(httpx.MockTransport(handler))

        req = Request()
        req.url = "/users"

        await http.send(req, base_url="https://api.example.com")

    @pytest.mark.asyncio
    async def test_absolute_url_ignores_base(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            assert str(request.url) == "https://other.com/path"
            return httpx.Response(200)

        http = make_http_client(httpx.MockTransport(handler))

        req = Request()
        req.url = "https://other.com/path"

        await http.send(req, base_url="https://api.example.com")


class TestHttpClientAllMethods:
    @pytest.mark.asyncio
    async def test_all_http_methods(self) -> None:
        for method in HttpMethod:

            def handler(request: httpx.Request, expected: str = method.value) -> httpx.Response:
                assert request.method == expected
                return httpx.Response(200)

            http = make_http_client(httpx.MockTransport(handler))

            req = Request()
            req.method = method
            req.url = "https://example.com"

            resp = await http.send(req)

            assert_that(resp.status_code).is_equal_to(200)
