"""Tests for environments service."""

import os
from unittest.mock import patch

from assertpy import assert_that
from forc.domain.models import Environment, KeyValue
from forc.services.environments import EnvironmentsService


class TestEnvironmentsServiceBasic:
    def setup_method(self):
        self.svc = EnvironmentsService()

    def test_initially_empty(self):
        assert_that(self.svc.environments).is_empty()
        assert_that(self.svc.active_name).is_none()
        assert_that(self.svc.active).is_none()

    def test_load_environments(self):
        envs = [
            Environment(name="dev", variables=[KeyValue(key="URL", value="localhost")]),
            Environment(name="prod", variables=[KeyValue(key="URL", value="example.com")]),
        ]
        self.svc.load(envs, "dev")

        assert_that(self.svc.environments).is_length(2)
        assert_that(self.svc.active_name).is_equal_to("dev")
        assert self.svc.active is not None
        assert_that(self.svc.active.name).is_equal_to("dev")

    def test_clear(self):
        self.svc.load([Environment(name="dev")], "dev")
        self.svc.clear()

        assert_that(self.svc.environments).is_empty()
        assert_that(self.svc.active_name).is_none()


class TestEnvironmentsServiceCrud:
    def setup_method(self):
        self.svc = EnvironmentsService()

    def test_add(self):
        env = Environment(name="dev")
        self.svc.add(env)

        assert_that(self.svc.environments).is_length(1)
        assert_that(self.svc.environments[0].name).is_equal_to("dev")

    def test_remove(self):
        self.svc.add(Environment(name="dev"))
        self.svc.add(Environment(name="prod"))
        self.svc.remove("dev")

        assert_that(self.svc.environments).is_length(1)
        assert_that(self.svc.environments[0].name).is_equal_to("prod")

    def test_remove_active_clears_active(self):
        self.svc.add(Environment(name="dev"))
        self.svc.set_active("dev")
        self.svc.remove("dev")

        assert_that(self.svc.active_name).is_none()

    def test_get(self):
        env = Environment(name="dev", variables=[KeyValue(key="X", value="Y")])
        self.svc.add(env)

        result = self.svc.get("dev")

        assert result is not None
        assert_that(result.name).is_equal_to("dev")
        assert_that(result.variables).is_length(1)

    def test_get_not_found(self):
        assert_that(self.svc.get("missing")).is_none()

    def test_names(self):
        self.svc.add(Environment(name="dev"))
        self.svc.add(Environment(name="staging"))
        self.svc.add(Environment(name="prod"))

        assert_that(self.svc.names()).contains_only("dev", "staging", "prod")


class TestEnvironmentsServiceVariables:
    def setup_method(self):
        self.svc = EnvironmentsService()
        self.svc.add(Environment(name="dev"))
        self.svc.add(Environment(name="prod"))

    def test_add_variable(self):
        self.svc.add_variable("dev", "API_KEY", "abc123", secret=True)

        env = self.svc.get("dev")
        assert env is not None
        assert_that(env.variables).is_length(1)
        assert_that(env.variables[0].key).is_equal_to("API_KEY")
        assert_that(env.variables[0].value).is_equal_to("abc123")
        assert_that(env.variables[0].secret).is_true()

    def test_add_variable_missing_env(self):
        try:
            self.svc.add_variable("missing", "X", "Y")
            raise AssertionError("Should have raised ValueError")
        except ValueError as e:
            assert_that(str(e)).contains("not found")

    def test_remove_variable(self):
        self.svc.add_variable("dev", "A", "1")
        self.svc.add_variable("dev", "B", "2")
        self.svc.remove_variable("dev", "A")

        env = self.svc.get("dev")
        assert env is not None
        assert_that(env.variables).is_length(1)
        assert_that(env.variables[0].key).is_equal_to("B")

    def test_set_variable_update(self):
        self.svc.add_variable("dev", "URL", "http://localhost")
        self.svc.set_variable("dev", "URL", "http://new.host")

        env = self.svc.get("dev")
        assert env is not None
        assert_that(env.variables[0].value).is_equal_to("http://new.host")

    def test_set_variable_create(self):
        self.svc.set_variable("dev", "NEW_VAR", "new_value")

        env = self.svc.get("dev")
        assert env is not None
        assert_that(env.variables).is_length(1)
        assert_that(env.variables[0].key).is_equal_to("NEW_VAR")


class TestEnvironmentsServiceResolution:
    def setup_method(self):
        self.svc = EnvironmentsService()
        dev = Environment(
            name="dev",
            variables=[
                KeyValue(key="BASE_URL", value="http://localhost:3000"),
                KeyValue(key="API_KEY", value="dev-key-123", secret=True),
                KeyValue(key="VERSION", value="v1"),
                KeyValue(key="DISABLED", value="should_not_appear", enabled=False),
            ],
        )
        prod = Environment(
            name="prod",
            variables=[
                KeyValue(key="BASE_URL", value="https://api.example.com"),
                KeyValue(key="API_KEY", value="prod-key-456", secret=True),
                KeyValue(key="VERSION", value="v2"),
            ],
        )
        self.svc.load([dev, prod], "dev")

    def test_resolve_simple(self):
        result = self.svc.resolve("${BASE_URL}/users")
        assert_that(result).is_equal_to("http://localhost:3000/users")

    def test_resolve_multiple(self):
        result = self.svc.resolve("${BASE_URL}/${VERSION}/users")
        assert_that(result).is_equal_to("http://localhost:3000/v1/users")

    def test_resolve_secret(self):
        result = self.svc.resolve("Bearer ${API_KEY}")
        assert_that(result).is_equal_to("Bearer dev-key-123")

    def test_resolve_disabled_not_resolved(self):
        result = self.svc.resolve("${DISABLED}", strict=False)
        assert_that(result).is_equal_to("${DISABLED}")

    def test_resolve_unresolved_left_as_is(self):
        result = self.svc.resolve("${UNKNOWN}", strict=False)
        assert_that(result).is_equal_to("${UNKNOWN}")

    def test_resolve_uses_active_environment(self):
        self.svc.set_active("prod")
        result = self.svc.resolve("${BASE_URL}/${VERSION}")
        assert_that(result).is_equal_to("https://api.example.com/v2")

    def test_resolve_no_active_environment(self):
        self.svc.set_active(None)
        result = self.svc.resolve("${BASE_URL}", strict=False)
        assert_that(result).is_equal_to("${BASE_URL}")

    def test_resolve_fallback_to_system_env(self):
        with patch.dict(os.environ, {"SYSTEM_VAR": "from_system"}):
            result = self.svc.resolve("${SYSTEM_VAR}")
            assert_that(result).is_equal_to("from_system")

    def test_env_takes_precedence_over_system(self):
        with patch.dict(os.environ, {"BASE_URL": "from_system"}):
            result = self.svc.resolve("${BASE_URL}")
            assert_that(result).is_equal_to("http://localhost:3000")


class TestEnvironmentsServicePlaceholders:
    def setup_method(self):
        self.svc = EnvironmentsService()
        self.svc.load([Environment(name="dev", variables=[KeyValue(key="X", value="1")])], "dev")

    def test_find_placeholders(self):
        result = self.svc.find_placeholders("${A} and ${B} and ${C}")
        assert_that(result).contains_only("A", "B", "C")

    def test_find_placeholders_empty(self):
        result = self.svc.find_placeholders("no variables here")
        assert_that(result).is_empty()

    def test_get_unresolved(self):
        result = self.svc.get_unresolved("${X} and ${UNKNOWN}")
        assert_that(result).contains_only("UNKNOWN")

    def test_get_unresolved_with_system_env(self):
        with patch.dict(os.environ, {"SYS": "val"}):
            result = self.svc.get_unresolved("${X} and ${SYS} and ${MISSING}")
            assert_that(result).contains_only("MISSING")
