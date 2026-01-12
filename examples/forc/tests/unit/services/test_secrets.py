"""Tests for secrets service."""

import os
import tempfile
from pathlib import Path

from assertpy import assert_that
from forc.services.secrets import SecretsService


class TestSecretsServiceBasic:
    def setup_method(self):
        self.tmp_dir = Path(tempfile.mkdtemp())

    def test_create_without_workspace(self):
        svc = SecretsService()
        assert_that(svc.get("SOME_KEY")).is_none()

    def test_create_with_workspace_no_env_file(self):
        svc = SecretsService(self.tmp_dir)
        assert_that(svc.list_keys()).is_empty()

    def test_create_with_existing_env_file(self):
        env_file = self.tmp_dir / ".env"
        env_file.write_text("API_KEY=secret123\nDB_URL=localhost\n")

        svc = SecretsService(self.tmp_dir)

        assert_that(svc.get("API_KEY")).is_equal_to("secret123")
        assert_that(svc.get("DB_URL")).is_equal_to("localhost")
        assert_that(svc.list_keys()).contains("API_KEY", "DB_URL")

    def test_set_workspace_later(self):
        svc = SecretsService()
        env_file = self.tmp_dir / ".env"
        env_file.write_text("FOO=bar\n")

        svc.set_workspace(self.tmp_dir)

        assert_that(svc.get("FOO")).is_equal_to("bar")


class TestSecretsServiceGet:
    def setup_method(self):
        self.tmp_dir = Path(tempfile.mkdtemp())
        self.svc = SecretsService(self.tmp_dir)

    def test_get_from_env_file(self):
        env_file = self.tmp_dir / ".env"
        env_file.write_text("MY_SECRET=from_file\n")
        self.svc.set_workspace(self.tmp_dir)  # Reload

        assert_that(self.svc.get("MY_SECRET")).is_equal_to("from_file")

    def test_get_from_system_env(self):
        os.environ["TEST_SECRET_123"] = "from_system"
        try:
            assert_that(self.svc.get("TEST_SECRET_123")).is_equal_to("from_system")
        finally:
            del os.environ["TEST_SECRET_123"]

    def test_env_file_takes_precedence(self):
        # Set system env
        os.environ["PRIORITY_TEST"] = "system_value"
        try:
            # Set in .env file
            env_file = self.tmp_dir / ".env"
            env_file.write_text("PRIORITY_TEST=file_value\n")
            self.svc.set_workspace(self.tmp_dir)

            # .env should win
            assert_that(self.svc.get("PRIORITY_TEST")).is_equal_to("file_value")
        finally:
            del os.environ["PRIORITY_TEST"]

    def test_get_nonexistent_returns_none(self):
        assert_that(self.svc.get("DOES_NOT_EXIST")).is_none()


class TestSecretsServiceSet:
    def setup_method(self):
        self.tmp_dir = Path(tempfile.mkdtemp())
        self.svc = SecretsService(self.tmp_dir)

    def test_set_creates_env_file(self):
        env_file = self.tmp_dir / ".env"
        assert_that(env_file.exists()).is_false()

        self.svc.set("NEW_KEY", "new_value")

        assert_that(env_file.exists()).is_true()
        assert_that(self.svc.get("NEW_KEY")).is_equal_to("new_value")

    def test_set_updates_existing_key(self):
        env_file = self.tmp_dir / ".env"
        env_file.write_text("EXISTING=old\n")
        self.svc.set_workspace(self.tmp_dir)

        self.svc.set("EXISTING", "new")

        assert_that(self.svc.get("EXISTING")).is_equal_to("new")

    def test_set_without_workspace_raises(self):
        svc = SecretsService()
        try:
            svc.set("KEY", "value")
            assert_that(False).is_true()  # Should not reach
        except RuntimeError as e:
            assert_that(str(e)).contains("No workspace set")


class TestSecretsServiceDelete:
    def setup_method(self):
        self.tmp_dir = Path(tempfile.mkdtemp())

    def test_delete_removes_key(self):
        env_file = self.tmp_dir / ".env"
        env_file.write_text("TO_DELETE=value\nKEEP=other\n")
        svc = SecretsService(self.tmp_dir)

        svc.delete("TO_DELETE")

        assert_that(svc.get("TO_DELETE")).is_none()
        assert_that(svc.get("KEEP")).is_equal_to("other")

    def test_delete_nonexistent_is_safe(self):
        svc = SecretsService(self.tmp_dir)
        svc.delete("NONEXISTENT")  # Should not raise


class TestSecretsServiceResolve:
    def setup_method(self):
        self.tmp_dir = Path(tempfile.mkdtemp())
        env_file = self.tmp_dir / ".env"
        env_file.write_text("API_URL=https://api.example.com\nTOKEN=secret123\n")
        self.svc = SecretsService(self.tmp_dir)

    def test_resolve_single_placeholder(self):
        result = self.svc.resolve("URL: ${API_URL}")
        assert_that(result).is_equal_to("URL: https://api.example.com")

    def test_resolve_multiple_placeholders(self):
        result = self.svc.resolve("${API_URL}/auth?token=${TOKEN}")
        assert_that(result).is_equal_to("https://api.example.com/auth?token=secret123")

    def test_resolve_leaves_unknown_placeholders(self):
        result = self.svc.resolve("${UNKNOWN}/path")
        assert_that(result).is_equal_to("${UNKNOWN}/path")

    def test_resolve_no_placeholders(self):
        result = self.svc.resolve("plain text")
        assert_that(result).is_equal_to("plain text")


class TestSecretsServiceFindPlaceholders:
    def setup_method(self):
        self.svc = SecretsService()

    def test_find_single_placeholder(self):
        result = self.svc.find_placeholders("${FOO}")
        assert_that(result).is_equal_to(["FOO"])

    def test_find_multiple_placeholders(self):
        result = self.svc.find_placeholders("${FOO} and ${BAR}")
        assert_that(result).is_equal_to(["FOO", "BAR"])

    def test_find_no_placeholders(self):
        result = self.svc.find_placeholders("no placeholders here")
        assert_that(result).is_empty()


class TestSecretsServiceGitignore:
    def setup_method(self):
        self.tmp_dir = Path(tempfile.mkdtemp())
        self.svc = SecretsService(self.tmp_dir)

    def test_ensure_gitignore_creates_file(self):
        gitignore = self.tmp_dir / ".gitignore"
        assert_that(gitignore.exists()).is_false()

        self.svc.ensure_gitignore()

        assert_that(gitignore.exists()).is_true()
        assert_that(gitignore.read_text()).contains(".env")

    def test_ensure_gitignore_appends_to_existing(self):
        gitignore = self.tmp_dir / ".gitignore"
        gitignore.write_text("node_modules/\n")

        self.svc.ensure_gitignore()

        content = gitignore.read_text()
        assert_that(content).contains("node_modules/")
        assert_that(content).contains(".env")

    def test_ensure_gitignore_doesnt_duplicate(self):
        gitignore = self.tmp_dir / ".gitignore"
        gitignore.write_text(".env\n")

        self.svc.ensure_gitignore()

        assert_that(gitignore.read_text().count(".env")).is_equal_to(1)


class TestSecretsServiceExample:
    def setup_method(self):
        self.tmp_dir = Path(tempfile.mkdtemp())

    def test_create_example_from_existing_keys(self):
        env_file = self.tmp_dir / ".env"
        env_file.write_text("API_KEY=secret\nDB_URL=localhost\n")
        svc = SecretsService(self.tmp_dir)

        svc.create_example()

        example = self.tmp_dir / ".env.example"
        assert_that(example.exists()).is_true()
        content = example.read_text()
        assert_that(content).contains("API_KEY=")
        assert_that(content).contains("DB_URL=")
        assert_that(content).does_not_contain("secret")  # No real values

    def test_create_example_with_custom_keys(self):
        svc = SecretsService(self.tmp_dir)

        svc.create_example(["CUSTOM_KEY", "ANOTHER_KEY"])

        example = self.tmp_dir / ".env.example"
        content = example.read_text()
        assert_that(content).contains("CUSTOM_KEY=")
        assert_that(content).contains("ANOTHER_KEY=")
