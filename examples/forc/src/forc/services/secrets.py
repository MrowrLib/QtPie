import os
import re
from pathlib import Path

from dotenv import dotenv_values, set_key, unset_key


class SecretsService:
    """Service for managing secrets via .env files.

    Resolution order:
    1. .env file in workspace
    2. System environment variables
    3. None (caller can prompt user)
    """

    def __init__(self, workspace_path: Path | None = None) -> None:
        self._workspace_path = workspace_path
        self._env_path: Path | None = None
        self._values: dict[str, str] = {}

        if workspace_path:
            self._env_path = workspace_path / ".env"
            self._load()

    def _load(self) -> None:
        """Load values from .env file."""
        if self._env_path and self._env_path.exists():
            raw = dotenv_values(self._env_path)
            self._values = {k: v for k, v in raw.items() if v is not None}

    def set_workspace(self, workspace_path: Path) -> None:
        """Set the workspace path and reload .env."""
        self._workspace_path = workspace_path
        self._env_path = workspace_path / ".env"
        self._load()

    def get(self, key: str) -> str | None:
        """Get a secret value.

        Resolution order:
        1. .env file
        2. System environment variable
        """
        # Check .env first
        if key in self._values:
            return self._values[key]

        # Fall back to system env
        return os.environ.get(key)

    def set(self, key: str, value: str) -> None:
        """Set a secret value in .env file."""
        if not self._env_path:
            raise RuntimeError("No workspace set")

        # Ensure .env exists
        if not self._env_path.exists():
            self._env_path.touch()

        set_key(str(self._env_path), key, value)
        self._values[key] = value

    def delete(self, key: str) -> None:
        """Remove a secret from .env file."""
        if not self._env_path:
            raise RuntimeError("No workspace set")

        if self._env_path.exists():
            unset_key(str(self._env_path), key)
            self._values.pop(key, None)

    def list_keys(self) -> list[str]:
        """List all keys in .env file."""
        return list(self._values.keys())

    def all(self) -> dict[str, str]:
        """Get all secrets from .env file."""
        return dict(self._values)

    def resolve(self, text: str) -> str:
        """Resolve ${VAR} placeholders in text.

        Args:
            text: Text containing ${VAR} placeholders

        Returns:
            Text with placeholders replaced by values.
            Unresolved placeholders are left as-is.
        """
        pattern = r"\$\{([^}]+)\}"

        def replace(match: re.Match[str]) -> str:
            key = match.group(1)
            value = self.get(key)
            if value is not None:
                return value
            # Leave unresolved placeholders as-is
            return match.group(0)

        return re.sub(pattern, replace, text)

    def find_placeholders(self, text: str) -> list[str]:
        """Find all ${VAR} placeholders in text.

        Args:
            text: Text to search

        Returns:
            List of variable names found
        """
        pattern = r"\$\{([^}]+)\}"
        return re.findall(pattern, text)

    def ensure_gitignore(self) -> None:
        """Ensure .env is in .gitignore."""
        if not self._workspace_path:
            return

        gitignore_path = self._workspace_path / ".gitignore"

        if gitignore_path.exists():
            content = gitignore_path.read_text()
            if ".env" in content:
                return
            # Append to existing
            with gitignore_path.open("a") as f:
                f.write("\n# Secrets\n.env\n")
        else:
            # Create new
            gitignore_path.write_text("# Secrets\n.env\n")

    def create_example(self, keys: list[str] | None = None) -> None:
        """Create .env.example with placeholder values."""
        if not self._workspace_path:
            return

        example_path = self._workspace_path / ".env.example"

        if keys is None:
            keys = self.list_keys()

        lines = [f"{key}=your-{key.lower()}-here" for key in keys]
        example_path.write_text("\n".join(lines) + "\n")
