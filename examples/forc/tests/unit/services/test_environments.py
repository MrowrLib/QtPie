# pyright: reportPrivateUsage=false
"""Tests for environments service."""

import os
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from assertpy import assert_that
from forc.domain.models import Environment, KeyValue, Workspace
from forc.services.environments import EnvironmentsService
from observant import ObservableList


def _make_env(name: str, variables: list[KeyValue] | None = None) -> Environment:
    """Helper to create an Environment with ObservableList variables."""
    vars_list: ObservableList[KeyValue] = ObservableList()
    if variables:
        for v in variables:
            vars_list.append(v)
    return Environment(name=name, variables=vars_list)


def _make_envs(*envs: Environment) -> ObservableList[Environment]:
    """Helper to create an ObservableList of environments."""
    result: ObservableList[Environment] = ObservableList()
    for e in envs:
        result.append(e)
    return result


class TestEnvironmentsServiceBasic:
    def setup_method(self) -> None:
        self.svc = EnvironmentsService()

    def test_initially_empty(self) -> None:
        assert_that(list(self.svc.environments)).is_empty()

    def test_load_environments(self) -> None:
        with TemporaryDirectory() as tmpdir:
            path = Path(tmpdir)
            workspace = Workspace(name="test")
            envs = _make_envs(
                _make_env("dev", [KeyValue(key="URL", value="localhost")]),
                _make_env("prod", [KeyValue(key="URL", value="example.com")]),
            )
            workspace.environments = envs

            self.svc.load(envs, path, workspace)

            assert_that(list(self.svc.environments)).is_length(2)

    def test_clear(self) -> None:
        with TemporaryDirectory() as tmpdir:
            path = Path(tmpdir)
            workspace = Workspace(name="test")
            envs = _make_envs(_make_env("dev"))
            workspace.environments = envs

            self.svc.load(envs, path, workspace)
            self.svc.clear()

            assert_that(list(self.svc.environments)).is_empty()


class TestEnvironmentsServiceCrud:
    def setup_method(self) -> None:
        self.tmpdir = TemporaryDirectory()
        self.path = Path(self.tmpdir.name)
        self.workspace = Workspace(name="test")
        self.svc = EnvironmentsService()
        self.svc.load(self.workspace.environments, self.path, self.workspace)

    def teardown_method(self) -> None:
        self.tmpdir.cleanup()

    def test_create(self) -> None:
        self.svc.create("dev")

        assert_that(list(self.svc.environments)).is_length(1)
        assert_that(self.svc.environments[0].name).is_equal_to("dev")
        # Verify file was created
        env_file = self.path / "environments" / "dev.yaml"
        assert_that(env_file.exists()).is_true()

    def test_create_duplicate_raises(self) -> None:
        self.svc.create("dev")
        try:
            self.svc.create("dev")
            raise AssertionError("Should have raised ValueError")
        except ValueError as e:
            assert_that(str(e)).contains("already exists")

    def test_delete(self) -> None:
        self.svc.create("dev")
        self.svc.create("prod")
        env_file = self.path / "environments" / "dev.yaml"
        assert_that(env_file.exists()).is_true()

        self.svc.delete("dev")

        assert_that(list(self.svc.environments)).is_length(1)
        assert_that(self.svc.environments[0].name).is_equal_to("prod")
        assert_that(env_file.exists()).is_false()

    def test_delete_active_clears_active(self) -> None:
        self.svc.create("dev")
        self.workspace.active_environment.set("dev")
        self.svc.delete("dev")

        assert_that(self.workspace.active_environment.get()).is_none()

    def test_rename(self) -> None:
        self.svc.create("dev")
        old_file = self.path / "environments" / "dev.yaml"
        assert_that(old_file.exists()).is_true()

        self.svc.rename("dev", "development")

        new_file = self.path / "environments" / "development.yaml"
        assert_that(old_file.exists()).is_false()
        assert_that(new_file.exists()).is_true()
        assert_that(self.svc.get("development")).is_not_none()
        assert_that(self.svc.get("dev")).is_none()

    def test_rename_active_updates_active(self) -> None:
        self.svc.create("dev")
        self.workspace.active_environment.set("dev")
        self.svc.rename("dev", "development")

        assert_that(self.workspace.active_environment.get()).is_equal_to("development")

    def test_get(self) -> None:
        self.svc.create("dev")
        self.svc.add_variable("dev", "X", "Y")

        result = self.svc.get("dev")

        assert result is not None
        assert_that(result.name).is_equal_to("dev")
        assert_that(list(result.variables)).is_length(1)

    def test_get_not_found(self) -> None:
        assert_that(self.svc.get("missing")).is_none()

    def test_names(self) -> None:
        self.svc.create("dev")
        self.svc.create("staging")
        self.svc.create("prod")

        assert_that(self.svc.names()).contains_only("dev", "staging", "prod")


class TestEnvironmentsServiceVariables:
    def setup_method(self) -> None:
        self.tmpdir = TemporaryDirectory()
        self.path = Path(self.tmpdir.name)
        self.workspace = Workspace(name="test")
        self.svc = EnvironmentsService()
        self.svc.load(self.workspace.environments, self.path, self.workspace)
        self.svc.create("dev")
        self.svc.create("prod")

    def teardown_method(self) -> None:
        self.tmpdir.cleanup()

    def test_add_variable(self) -> None:
        self.svc.add_variable("dev", "URL", "http://example.com")

        env = self.svc.get("dev")
        assert env is not None
        assert_that(list(env.variables)).is_length(1)
        assert_that(env.variables[0].key).is_equal_to("URL")
        assert_that(env.variables[0].value).is_equal_to("http://example.com")
        assert_that(env.variables[0].secret).is_false()

    def test_add_secret_variable_stored_in_keychain(self) -> None:
        self.svc.add_variable("dev", "API_KEY", "abc123", secret=True)

        env = self.svc.get("dev")
        assert env is not None
        assert_that(list(env.variables)).is_length(1)
        assert_that(env.variables[0].key).is_equal_to("API_KEY")
        # Secret value stored in keychain, YAML has empty value
        assert_that(env.variables[0].value).is_equal_to("")
        assert_that(env.variables[0].secret).is_true()
        # But we can resolve it (it comes from keychain)
        assert_that(self.svc.resolve("${API_KEY}", "dev")).is_equal_to("abc123")

    def test_add_variable_missing_env(self) -> None:
        try:
            self.svc.add_variable("missing", "X", "Y")
            raise AssertionError("Should have raised ValueError")
        except ValueError as e:
            assert_that(str(e)).contains("not found")

    def test_remove_variable(self) -> None:
        self.svc.add_variable("dev", "A", "1")
        self.svc.add_variable("dev", "B", "2")
        self.svc.remove_variable("dev", "A")

        env = self.svc.get("dev")
        assert env is not None
        assert_that(list(env.variables)).is_length(1)
        assert_that(env.variables[0].key).is_equal_to("B")

    def test_set_variable_update(self) -> None:
        self.svc.add_variable("dev", "URL", "http://localhost")
        self.svc.set_variable("dev", "URL", "http://new.host")

        env = self.svc.get("dev")
        assert env is not None
        assert_that(env.variables[0].value).is_equal_to("http://new.host")

    def test_set_variable_create(self) -> None:
        self.svc.set_variable("dev", "NEW_VAR", "new_value")

        env = self.svc.get("dev")
        assert env is not None
        assert_that(list(env.variables)).is_length(1)
        assert_that(env.variables[0].key).is_equal_to("NEW_VAR")


class TestEnvironmentsServiceResolution:
    def setup_method(self) -> None:
        self.tmpdir = TemporaryDirectory()
        self.path = Path(self.tmpdir.name)
        self.workspace = Workspace(name="test")

        # Non-secret variables (value stored in YAML)
        dev = _make_env(
            "dev",
            [
                KeyValue(key="BASE_URL", value="http://localhost:3000"),
                KeyValue(key="VERSION", value="v1"),
                KeyValue(key="DISABLED", value="should_not_appear", enabled=False),
            ],
        )
        prod = _make_env(
            "prod",
            [
                KeyValue(key="BASE_URL", value="https://api.example.com"),
                KeyValue(key="VERSION", value="v2"),
            ],
        )
        envs = _make_envs(dev, prod)
        self.workspace.environments = envs

        self.svc = EnvironmentsService()
        self.svc.load(envs, self.path, self.workspace)

    def teardown_method(self) -> None:
        self.tmpdir.cleanup()

    def test_resolve_simple(self) -> None:
        result = self.svc.resolve("${BASE_URL}/users", "dev")
        assert_that(result).is_equal_to("http://localhost:3000/users")

    def test_resolve_multiple(self) -> None:
        result = self.svc.resolve("${BASE_URL}/${VERSION}/users", "dev")
        assert_that(result).is_equal_to("http://localhost:3000/v1/users")

    def test_resolve_disabled_not_resolved(self) -> None:
        result = self.svc.resolve("${DISABLED}", "dev", strict=False)
        assert_that(result).is_equal_to("${DISABLED}")

    def test_resolve_unresolved_left_as_is(self) -> None:
        result = self.svc.resolve("${UNKNOWN}", "dev", strict=False)
        assert_that(result).is_equal_to("${UNKNOWN}")

    def test_resolve_uses_specified_environment(self) -> None:
        result = self.svc.resolve("${BASE_URL}/${VERSION}", "prod")
        assert_that(result).is_equal_to("https://api.example.com/v2")

    def test_resolve_no_environment(self) -> None:
        result = self.svc.resolve("${BASE_URL}", None, strict=False)
        assert_that(result).is_equal_to("${BASE_URL}")

    def test_resolve_fallback_to_system_env(self) -> None:
        with patch.dict(os.environ, {"SYSTEM_VAR": "from_system"}):
            result = self.svc.resolve("${SYSTEM_VAR}", "dev")
            assert_that(result).is_equal_to("from_system")

    def test_env_takes_precedence_over_system(self) -> None:
        with patch.dict(os.environ, {"BASE_URL": "from_system"}):
            result = self.svc.resolve("${BASE_URL}", "dev")
            assert_that(result).is_equal_to("http://localhost:3000")


class TestEnvironmentsServiceSecrets:
    """Tests for secret variable handling with keychain."""

    def setup_method(self) -> None:
        self.tmpdir = TemporaryDirectory()
        self.path = Path(self.tmpdir.name)
        self.workspace = Workspace(name="test")
        self.svc = EnvironmentsService()
        self.svc.load(self.workspace.environments, self.path, self.workspace)
        self.svc.create("dev")

    def teardown_method(self) -> None:
        self.tmpdir.cleanup()

    def test_secret_resolved_from_keychain(self) -> None:
        self.svc.add_variable("dev", "API_KEY", "secret-value", secret=True)

        result = self.svc.resolve("Bearer ${API_KEY}", "dev")

        assert_that(result).is_equal_to("Bearer secret-value")

    def test_secret_yaml_value_is_empty(self) -> None:
        self.svc.add_variable("dev", "API_KEY", "secret-value", secret=True)

        env = self.svc.get("dev")
        assert env is not None
        # YAML stores empty value, keychain stores actual value
        assert_that(env.variables[0].value).is_equal_to("")
        assert_that(env.variables[0].secret).is_true()

    def test_update_secret_value(self) -> None:
        self.svc.add_variable("dev", "API_KEY", "old-secret", secret=True)

        self.svc.set_variable("dev", "API_KEY", "new-secret")

        assert_that(self.svc.resolve("${API_KEY}", "dev")).is_equal_to("new-secret")

    def test_remove_secret_deletes_from_keychain(self) -> None:
        self.svc.add_variable("dev", "API_KEY", "secret-value", secret=True)

        self.svc.remove_variable("dev", "API_KEY")

        result = self.svc.resolve("${API_KEY}", "dev", strict=False)
        assert_that(result).is_equal_to("${API_KEY}")

    def test_rename_env_moves_secrets(self) -> None:
        self.svc.add_variable("dev", "SECRET", "my-secret", secret=True)

        self.svc.rename("dev", "development")

        assert_that(self.svc.resolve("${SECRET}", "development")).is_equal_to("my-secret")

    def test_delete_env_removes_secrets(self) -> None:
        self.svc.add_variable("dev", "SECRET", "my-secret", secret=True)

        self.svc.delete("dev")

        # Create new env with same name - should not have old secret
        self.svc.create("dev")
        result = self.svc.resolve("${SECRET}", "dev", strict=False)
        assert_that(result).is_equal_to("${SECRET}")

    def test_convert_to_secret(self) -> None:
        # Add as non-secret
        self.svc.add_variable("dev", "KEY", "plaintext")

        # Convert to secret
        self.svc.update_variable("dev", "KEY", secret=True)

        env = self.svc.get("dev")
        assert env is not None
        # Value moved to keychain, YAML is empty
        assert_that(env.variables[0].value).is_equal_to("")
        assert_that(env.variables[0].secret).is_true()
        # But still resolvable
        assert_that(self.svc.resolve("${KEY}", "dev")).is_equal_to("plaintext")

    def test_convert_from_secret(self) -> None:
        # Add as secret
        self.svc.add_variable("dev", "KEY", "was-secret", secret=True)

        # Convert to non-secret
        self.svc.update_variable("dev", "KEY", secret=False)

        env = self.svc.get("dev")
        assert env is not None
        # Value moved from keychain to YAML
        assert_that(env.variables[0].value).is_equal_to("was-secret")
        assert_that(env.variables[0].secret).is_false()

    def test_unresolved_secret_without_keychain_value(self) -> None:
        # Manually add a secret variable without putting value in keychain
        # (simulates loading from YAML on a new machine)
        env = self.svc.get("dev")
        assert env is not None
        env.variables.append(KeyValue(key="MISSING_SECRET", value="", secret=True))

        result = self.svc.get_unresolved("${MISSING_SECRET}", "dev")
        assert_that(result).contains("MISSING_SECRET")


class TestEnvironmentsServicePlaceholders:
    def setup_method(self) -> None:
        self.tmpdir = TemporaryDirectory()
        self.path = Path(self.tmpdir.name)
        self.workspace = Workspace(name="test")

        envs = _make_envs(_make_env("dev", [KeyValue(key="X", value="1")]))
        self.workspace.environments = envs

        self.svc = EnvironmentsService()
        self.svc.load(envs, self.path, self.workspace)

    def teardown_method(self) -> None:
        self.tmpdir.cleanup()

    def test_find_placeholders(self) -> None:
        result = self.svc.find_placeholders("${A} and ${B} and ${C}")
        assert_that(result).contains_only("A", "B", "C")

    def test_find_placeholders_empty(self) -> None:
        result = self.svc.find_placeholders("no variables here")
        assert_that(result).is_empty()

    def test_get_unresolved(self) -> None:
        result = self.svc.get_unresolved("${X} and ${UNKNOWN}", "dev")
        assert_that(result).contains_only("UNKNOWN")

    def test_get_unresolved_with_system_env(self) -> None:
        with patch.dict(os.environ, {"SYS": "val"}):
            result = self.svc.get_unresolved("${X} and ${SYS} and ${MISSING}", "dev")
            assert_that(result).contains_only("MISSING")
