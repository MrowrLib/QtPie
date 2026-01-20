"""Secrets service for storing sensitive values in OS keychain."""

import keyring
import keyring.errors


class SecretsService:
    """Manages secret storage in OS keychain.

    Uses the system keychain (macOS Keychain, Windows Credential Locker,
    Linux Secret Service) to store sensitive environment variables securely.
    """

    APP_NAME = "forc"

    def __init__(self, workspace_name: str = "default") -> None:
        self._workspace = workspace_name

    def _key(self, env_name: str, var_key: str) -> str:
        """Build keychain key: workspace:env:key."""
        return f"{self._workspace}:{env_name}:{var_key}"

    def set_secret(self, env_name: str, key: str, value: str) -> None:
        """Store secret in keychain."""
        keyring.set_password(self.APP_NAME, self._key(env_name, key), value)

    def get_secret(self, env_name: str, key: str) -> str | None:
        """Retrieve secret from keychain."""
        return keyring.get_password(self.APP_NAME, self._key(env_name, key))

    def delete_secret(self, env_name: str, key: str) -> None:
        """Remove secret from keychain."""
        try:
            keyring.delete_password(self.APP_NAME, self._key(env_name, key))
        except keyring.errors.PasswordDeleteError:
            pass  # Already gone

    def rename_env(self, old_name: str, new_name: str, keys: list[str]) -> None:
        """Move secrets when environment is renamed."""
        for key in keys:
            value = self.get_secret(old_name, key)
            if value is not None:
                self.set_secret(new_name, key, value)
                self.delete_secret(old_name, key)

    def delete_env(self, env_name: str, keys: list[str]) -> None:
        """Delete all secrets for an environment."""
        for key in keys:
            self.delete_secret(env_name, key)
