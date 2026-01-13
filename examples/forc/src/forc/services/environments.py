"""Service for managing environments and variable resolution."""

import os
import re

from forc.domain.models import Environment, KeyValue


class EnvironmentsService:
    """Service for managing environments.

    Handles:
    - Active environment selection
    - Variable resolution
    - Environment CRUD operations

    Works with a list of environments (typically from a Workspace).
    """

    def __init__(self) -> None:
        self._environments: list[Environment] = []
        self._active_name: str | None = None

    @property
    def environments(self) -> list[Environment]:
        """Get all environments."""
        return self._environments

    @property
    def active_name(self) -> str | None:
        """Get the name of the active environment."""
        return self._active_name

    @property
    def active(self) -> Environment | None:
        """Get the active environment."""
        if self._active_name is None:
            return None
        for env in self._environments:
            if env.name == self._active_name:
                return env
        return None

    def load(self, environments: list[Environment], active_name: str | None = None) -> None:
        """Load environments from a workspace.

        Args:
            environments: List of environments
            active_name: Name of the active environment
        """
        self._environments = environments
        self._active_name = active_name

    def clear(self) -> None:
        """Clear all environments."""
        self._environments = []
        self._active_name = None

    # CRUD operations

    def add(self, environment: Environment) -> None:
        """Add an environment."""
        self._environments.append(environment)

    def remove(self, name: str) -> None:
        """Remove an environment by name."""
        self._environments = [e for e in self._environments if e.name != name]
        if self._active_name == name:
            self._active_name = None

    def get(self, name: str) -> Environment | None:
        """Get an environment by name."""
        for env in self._environments:
            if env.name == name:
                return env
        return None

    def set_active(self, name: str | None) -> None:
        """Set the active environment by name."""
        self._active_name = name

    def names(self) -> list[str]:
        """Get list of environment names."""
        return [env.name for env in self._environments]

    # Variable operations

    def add_variable(self, env_name: str, key: str, value: str, secret: bool = False) -> None:
        """Add a variable to an environment."""
        env = self.get(env_name)
        if env is None:
            raise ValueError(f"Environment '{env_name}' not found")
        env.variables.append(KeyValue(key=key, value=value, secret=secret))

    def remove_variable(self, env_name: str, key: str) -> None:
        """Remove a variable from an environment."""
        env = self.get(env_name)
        if env is None:
            raise ValueError(f"Environment '{env_name}' not found")
        env.variables = [v for v in env.variables if v.key != key]

    def set_variable(self, env_name: str, key: str, value: str, secret: bool | None = None) -> None:
        """Set a variable value in an environment. Creates if doesn't exist."""
        env = self.get(env_name)
        if env is None:
            raise ValueError(f"Environment '{env_name}' not found")

        for var in env.variables:
            if var.key == key:
                var.value = value
                if secret is not None:
                    var.secret = secret
                return

        # Create new
        env.variables.append(KeyValue(key=key, value=value, secret=secret or False))

    # Variable resolution

    def resolve(self, text: str) -> str:
        """Resolve ${VAR} placeholders using active environment.

        Resolution order:
        1. Active environment variables
        2. System environment variables (fallback)
        """
        env = self.active

        pattern = r"\$\{([^}]+)\}"

        def replace(match: re.Match[str]) -> str:
            key = match.group(1)

            # Check active environment first
            if env:
                for kv in env.variables:
                    if kv.enabled and kv.key == key:
                        return kv.value

            # Fallback to system env
            sys_val = os.environ.get(key)
            if sys_val is not None:
                return sys_val

            # Leave unresolved
            return match.group(0)

        return re.sub(pattern, replace, text)

    def find_placeholders(self, text: str) -> list[str]:
        """Find all ${VAR} placeholders in text."""
        pattern = r"\$\{([^}]+)\}"
        return re.findall(pattern, text)

    def get_unresolved(self, text: str) -> list[str]:
        """Get list of placeholders that would not resolve."""
        env = self.active
        unresolved: list[str] = []

        for key in self.find_placeholders(text):
            resolved = False

            if env:
                for kv in env.variables:
                    if kv.enabled and kv.key == key:
                        resolved = True
                        break

            if not resolved and os.environ.get(key) is not None:
                resolved = True

            if not resolved:
                unresolved.append(key)

        return unresolved
