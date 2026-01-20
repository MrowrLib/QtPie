"""Service for managing environments and variable resolution."""

import os
import re
from pathlib import Path

from observant import ObservableList

from forc.domain.formats import YamlFormat
from forc.domain.models import Environment, KeyValue, Workspace
from forc.services.secrets import SecretsService


class EnvironmentsService:
    """Service for managing environments.

    Handles:
    - Environment CRUD operations with immediate persistence
    - Variable resolution (given an environment name)
    - Secret variable storage in OS keychain

    Works with an ObservableList of environments (from a Workspace).
    Secret variables (secret=True) are stored in the OS keychain, not in YAML.

    Note: Active environment selection is managed by the Workspace, not this service.
    """

    def __init__(self, format_handler: YamlFormat | None = None) -> None:
        self._format = format_handler or YamlFormat()
        self._environments: ObservableList[Environment] = ObservableList()
        self._path: Path | None = None
        self._workspace: Workspace | None = None
        self._secrets: SecretsService | None = None

    # Properties

    @property
    def environments(self) -> ObservableList[Environment]:
        """Get all environments (observable for UI binding)."""
        return self._environments

    # Lifecycle

    def load(
        self,
        environments: ObservableList[Environment],
        path: Path,
        workspace: Workspace,
    ) -> None:
        """Load environments from a workspace.

        Args:
            environments: The workspace's ObservableList of environments
            path: Path to the workspace directory (for persistence)
            workspace: The workspace object (for persistence)
        """
        self._environments = environments
        self._path = path
        self._workspace = workspace
        self._secrets = SecretsService(workspace.name)

    def clear(self) -> None:
        """Clear all environments."""
        self._environments = ObservableList()
        self._path = None
        self._workspace = None
        self._secrets = None

    # Environment CRUD operations (persist immediately)

    def _get_env_path(self, env: Environment) -> Path:
        """Get the file path for an environment."""
        from forc.domain.formats.yaml_format import slugify

        if self._path is None:
            raise RuntimeError("No workspace path set")

        filename = env.filename or slugify(env.name)
        return self._path / "environments" / f"{filename}.yaml"

    def _save_env(self, env: Environment) -> None:
        """Save an environment to disk."""
        path = self._get_env_path(env)
        path.parent.mkdir(parents=True, exist_ok=True)
        self._format.save_environment(env, path)

    def _save_workspace_config(self) -> None:
        """Save the workspace config (forc.yaml) to persist active_environment."""
        if self._workspace is None or self._path is None:
            return
        self._format.save_workspace_config(self._workspace, self._path)

    def create(self, name: str) -> Environment:
        """Create a new environment and save it to disk.

        Args:
            name: Name of the new environment

        Returns:
            The created environment

        Raises:
            RuntimeError: If no workspace is loaded
            ValueError: If an environment with this name already exists
        """
        from forc.domain.formats.yaml_format import slugify

        if self._path is None:
            raise RuntimeError("No workspace path set")

        # Check for duplicate name
        for env in self._environments:
            if env.name == name:
                raise ValueError(f"Environment '{name}' already exists")

        env = Environment(name=name, filename=slugify(name))
        self._environments.append(env)
        self._save_env(env)
        return env

    def rename(self, old_name: str, new_name: str) -> None:
        """Rename an environment and update the file on disk.

        Args:
            old_name: Current name of the environment
            new_name: New name for the environment

        Raises:
            RuntimeError: If no workspace is loaded
            ValueError: If environment not found or new name already exists
        """
        from forc.domain.formats.yaml_format import slugify

        if self._path is None:
            raise RuntimeError("No workspace path set")

        env = self.get(old_name)
        if env is None:
            raise ValueError(f"Environment '{old_name}' not found")

        # Check for duplicate name
        for e in self._environments:
            if e.name == new_name and e is not env:
                raise ValueError(f"Environment '{new_name}' already exists")

        # Move secrets in keychain before renaming
        if self._secrets:
            secret_keys = [v.key for v in env.variables if v.secret]
            self._secrets.rename_env(old_name, new_name, secret_keys)

        # Get old path
        old_path = self._get_env_path(env)

        # Update name and filename
        env.name = new_name
        env.filename = slugify(new_name)

        # Get new path and rename/save
        new_path = self._get_env_path(env)
        if old_path.exists() and old_path != new_path:
            old_path.unlink()
        self._save_env(env)

        # Update active environment if it was renamed
        if self._workspace is not None and self._workspace.active_environment.get() == old_name:
            self._workspace.active_environment.set(new_name)
            self._save_workspace_config()

    def delete(self, name: str) -> None:
        """Delete an environment and its file from disk.

        Args:
            name: Name of the environment to delete

        Raises:
            RuntimeError: If no workspace is loaded
            ValueError: If environment not found
        """
        if self._path is None:
            raise RuntimeError("No workspace path set")

        env = self.get(name)
        if env is None:
            raise ValueError(f"Environment '{name}' not found")

        # Delete secrets from keychain
        if self._secrets:
            secret_keys = [v.key for v in env.variables if v.secret]
            self._secrets.delete_env(name, secret_keys)

        # Remove file from disk
        path = self._get_env_path(env)
        if path.exists():
            path.unlink()

        # Remove from list
        self._environments.remove(env)

        # Clear active if it was deleted
        if self._workspace is not None and self._workspace.active_environment.get() == name:
            self._workspace.active_environment.set(None)
            self._save_workspace_config()

    def get(self, name: str) -> Environment | None:
        """Get an environment by name."""
        for env in self._environments:
            if env.name == name:
                return env
        return None

    def names(self) -> list[str]:
        """Get list of environment names."""
        return [env.name for env in self._environments]

    # Variable CRUD operations (persist immediately)

    def add_variable(self, env_name: str, key: str, value: str, secret: bool = False) -> None:
        """Add a variable to an environment and save.

        Args:
            env_name: Name of the environment
            key: Variable key
            value: Variable value
            secret: Whether the variable is secret (stored in keychain if True)
        """
        env = self.get(env_name)
        if env is None:
            raise ValueError(f"Environment '{env_name}' not found")

        if secret and self._secrets:
            # Store value in keychain, YAML gets empty value
            self._secrets.set_secret(env_name, key, value)
            env.variables.append(KeyValue(key=key, value="", secret=True))
        else:
            env.variables.append(KeyValue(key=key, value=value, secret=secret))

        self._save_env(env)

    def remove_variable(self, env_name: str, key: str) -> None:
        """Remove a variable from an environment and save.

        Args:
            env_name: Name of the environment
            key: Variable key to remove
        """
        env = self.get(env_name)
        if env is None:
            raise ValueError(f"Environment '{env_name}' not found")

        for var in env.variables:
            if var.key == key:
                # Delete from keychain if it's a secret
                if var.secret and self._secrets:
                    self._secrets.delete_secret(env_name, key)
                env.variables.remove(var)
                self._save_env(env)
                return

        raise ValueError(f"Variable '{key}' not found in environment '{env_name}'")

    def update_variable(
        self,
        env_name: str,
        key: str,
        value: str | None = None,
        secret: bool | None = None,
        enabled: bool | None = None,
    ) -> None:
        """Update a variable in an environment and save.

        Args:
            env_name: Name of the environment
            key: Variable key to update
            value: New value (if provided)
            secret: New secret flag (if provided)
            enabled: New enabled flag (if provided)
        """
        env = self.get(env_name)
        if env is None:
            raise ValueError(f"Environment '{env_name}' not found")

        for var in env.variables:
            if var.key == key:
                was_secret = var.secret
                new_secret = secret if secret is not None else was_secret

                # Handle secret flag change
                if self._secrets:
                    if was_secret and not new_secret:
                        # Moving from secret to non-secret: get value from keychain
                        keychain_value = self._secrets.get_secret(env_name, key)
                        self._secrets.delete_secret(env_name, key)
                        if value is None and keychain_value:
                            value = keychain_value
                    elif not was_secret and new_secret:
                        # Moving from non-secret to secret: move value to keychain
                        val_to_store = value if value is not None else var.value
                        self._secrets.set_secret(env_name, key, val_to_store)
                        var.value = ""  # Clear from YAML
                        value = None  # Don't set value below
                    elif was_secret and new_secret and value is not None:
                        # Updating a secret value: update in keychain
                        self._secrets.set_secret(env_name, key, value)
                        value = None  # Don't set value in YAML

                if value is not None:
                    var.value = value
                if secret is not None:
                    var.secret = secret
                if enabled is not None:
                    var.enabled = enabled
                self._save_env(env)
                return

        raise ValueError(f"Variable '{key}' not found in environment '{env_name}'")

    def set_variable(self, env_name: str, key: str, value: str, secret: bool | None = None) -> None:
        """Set a variable value in an environment. Creates if doesn't exist.

        Args:
            env_name: Name of the environment
            key: Variable key
            value: Variable value
            secret: Whether the variable is secret (only used for new variables)
        """
        env = self.get(env_name)
        if env is None:
            raise ValueError(f"Environment '{env_name}' not found")

        for var in env.variables:
            if var.key == key:
                if var.secret and self._secrets:
                    # Update secret in keychain, keep YAML value empty
                    self._secrets.set_secret(env_name, key, value)
                else:
                    var.value = value
                if secret is not None:
                    var.secret = secret
                self._save_env(env)
                return

        # Create new
        is_secret = secret or False
        if is_secret and self._secrets:
            self._secrets.set_secret(env_name, key, value)
            env.variables.append(KeyValue(key=key, value="", secret=True))
        else:
            env.variables.append(KeyValue(key=key, value=value, secret=is_secret))
        self._save_env(env)

    # Variable resolution

    def resolve(self, text: str, env_name: str | None = None, *, strict: bool = True) -> str:
        """Resolve ${VAR} placeholders using the specified environment.

        Resolution order:
        1. Environment variables (secrets from keychain, others from YAML)
        2. System environment variables (fallback)

        Args:
            text: Text containing ${VAR} placeholders
            env_name: Name of the environment to use for resolution (None = system env only)
            strict: If True, raise error for unresolved placeholders

        Raises:
            RuntimeError: If strict=True and placeholders cannot be resolved
        """
        env = self.get(env_name) if env_name else None
        unresolved_vars: list[str] = []

        pattern = r"\$\{([^}]+)\}"

        def replace(match: re.Match[str]) -> str:
            key = match.group(1)

            # Check environment first
            if env:
                for kv in env.variables:
                    if kv.enabled and kv.key == key:
                        if kv.secret and self._secrets:
                            # Get secret value from keychain
                            secret_val = self._secrets.get_secret(env.name, key)
                            if secret_val is not None:
                                return secret_val
                        else:
                            return kv.value

            # Fallback to system env
            sys_val = os.environ.get(key)
            if sys_val is not None:
                return sys_val

            # Track unresolved
            unresolved_vars.append(key)
            return match.group(0)

        result = re.sub(pattern, replace, text)

        if strict and unresolved_vars:
            env_display = env_name or "(no environment)"
            raise RuntimeError(
                f"Cannot resolve variables: {unresolved_vars}. Environment: {env_display}. Original text: {text}"
            )

        return result

    def find_placeholders(self, text: str) -> list[str]:
        """Find all ${VAR} placeholders in text."""
        pattern = r"\$\{([^}]+)\}"
        return re.findall(pattern, text)

    def get_unresolved(self, text: str, env_name: str | None = None) -> list[str]:
        """Get list of placeholders that would not resolve.

        Args:
            text: Text containing ${VAR} placeholders
            env_name: Name of the environment to check against (None = system env only)
        """
        env = self.get(env_name) if env_name else None
        unresolved: list[str] = []

        for key in self.find_placeholders(text):
            resolved = False

            if env:
                for kv in env.variables:
                    if kv.enabled and kv.key == key:
                        if kv.secret and self._secrets:
                            # Check if secret exists in keychain
                            if self._secrets.get_secret(env.name, key) is not None:
                                resolved = True
                        else:
                            resolved = True
                        break

            if not resolved and os.environ.get(key) is not None:
                resolved = True

            if not resolved:
                unresolved.append(key)

        return unresolved
