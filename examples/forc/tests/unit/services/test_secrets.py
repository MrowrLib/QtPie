# pyright: reportPrivateUsage=false
"""Tests for SecretsService."""

from assertpy import assert_that
from forc.services.secrets import SecretsService


class TestSecretsServiceBasic:
    def setup_method(self) -> None:
        self.svc = SecretsService("test-workspace")

    def test_set_and_get_secret(self) -> None:
        self.svc.set_secret("dev", "API_KEY", "secret-123")

        result = self.svc.get_secret("dev", "API_KEY")

        assert_that(result).is_equal_to("secret-123")

    def test_get_nonexistent_secret_returns_none(self) -> None:
        result = self.svc.get_secret("dev", "MISSING")

        assert_that(result).is_none()

    def test_delete_secret(self) -> None:
        self.svc.set_secret("dev", "API_KEY", "secret-123")

        self.svc.delete_secret("dev", "API_KEY")

        assert_that(self.svc.get_secret("dev", "API_KEY")).is_none()

    def test_delete_nonexistent_secret_does_not_raise(self) -> None:
        # Should not raise
        self.svc.delete_secret("dev", "MISSING")

    def test_update_existing_secret(self) -> None:
        self.svc.set_secret("dev", "API_KEY", "old-value")

        self.svc.set_secret("dev", "API_KEY", "new-value")

        assert_that(self.svc.get_secret("dev", "API_KEY")).is_equal_to("new-value")


class TestSecretsServiceMultipleEnvironments:
    def setup_method(self) -> None:
        self.svc = SecretsService("test-workspace")

    def test_secrets_isolated_by_environment(self) -> None:
        self.svc.set_secret("dev", "API_KEY", "dev-key")
        self.svc.set_secret("prod", "API_KEY", "prod-key")

        assert_that(self.svc.get_secret("dev", "API_KEY")).is_equal_to("dev-key")
        assert_that(self.svc.get_secret("prod", "API_KEY")).is_equal_to("prod-key")

    def test_secrets_isolated_by_workspace(self) -> None:
        svc1 = SecretsService("workspace1")
        svc2 = SecretsService("workspace2")

        svc1.set_secret("dev", "KEY", "value1")
        svc2.set_secret("dev", "KEY", "value2")

        assert_that(svc1.get_secret("dev", "KEY")).is_equal_to("value1")
        assert_that(svc2.get_secret("dev", "KEY")).is_equal_to("value2")


class TestSecretsServiceRenameEnv:
    def setup_method(self) -> None:
        self.svc = SecretsService("test-workspace")

    def test_rename_env_moves_secrets(self) -> None:
        self.svc.set_secret("dev", "KEY1", "val1")
        self.svc.set_secret("dev", "KEY2", "val2")

        self.svc.rename_env("dev", "development", ["KEY1", "KEY2"])

        # Old env should not have secrets
        assert_that(self.svc.get_secret("dev", "KEY1")).is_none()
        assert_that(self.svc.get_secret("dev", "KEY2")).is_none()
        # New env should have secrets
        assert_that(self.svc.get_secret("development", "KEY1")).is_equal_to("val1")
        assert_that(self.svc.get_secret("development", "KEY2")).is_equal_to("val2")

    def test_rename_env_with_partial_keys(self) -> None:
        self.svc.set_secret("dev", "EXISTS", "val")
        # KEY2 doesn't exist in keychain

        self.svc.rename_env("dev", "development", ["EXISTS", "MISSING"])

        assert_that(self.svc.get_secret("development", "EXISTS")).is_equal_to("val")
        assert_that(self.svc.get_secret("development", "MISSING")).is_none()


class TestSecretsServiceDeleteEnv:
    def setup_method(self) -> None:
        self.svc = SecretsService("test-workspace")

    def test_delete_env_removes_all_secrets(self) -> None:
        self.svc.set_secret("dev", "KEY1", "val1")
        self.svc.set_secret("dev", "KEY2", "val2")

        self.svc.delete_env("dev", ["KEY1", "KEY2"])

        assert_that(self.svc.get_secret("dev", "KEY1")).is_none()
        assert_that(self.svc.get_secret("dev", "KEY2")).is_none()

    def test_delete_env_with_missing_keys_does_not_raise(self) -> None:
        self.svc.set_secret("dev", "EXISTS", "val")

        # Should not raise even with missing keys
        self.svc.delete_env("dev", ["EXISTS", "MISSING"])

        assert_that(self.svc.get_secret("dev", "EXISTS")).is_none()


class TestSecretsServiceKeyFormat:
    def test_key_format(self) -> None:
        svc = SecretsService("my-workspace")

        key = svc._key("production", "API_TOKEN")

        assert_that(key).is_equal_to("my-workspace:production:API_TOKEN")
