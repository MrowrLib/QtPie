"""Workspace service for loading and saving workspaces."""

from pathlib import Path

from forc.domain.formats import YamlFormat
from forc.domain.models import Collection, Environment, Request, Workspace

from .secrets import SecretsService


class WorkspaceService:
    """Service for managing workspaces."""

    def __init__(
        self,
        format_handler: YamlFormat | None = None,
        secrets: SecretsService | None = None,
    ) -> None:
        self._format = format_handler or YamlFormat()
        self._secrets = secrets or SecretsService()
        self._workspace: Workspace | None = None
        self._path: Path | None = None

    @property
    def workspace(self) -> Workspace | None:
        """Get the current workspace."""
        return self._workspace

    @property
    def path(self) -> Path | None:
        """Get the current workspace path."""
        return self._path

    @property
    def is_loaded(self) -> bool:
        """Check if a workspace is loaded."""
        return self._workspace is not None

    def load(self, path: Path) -> Workspace:
        """Load a workspace from disk.

        Args:
            path: Path to workspace directory

        Returns:
            The loaded workspace
        """
        self._workspace = self._format.load_workspace(path)
        self._path = path
        self._secrets.set_workspace(path)
        return self._workspace

    def save(self, path: Path | None = None) -> None:
        """Save the current workspace to disk.

        Args:
            path: Optional path to save to (uses current path if not provided)

        Raises:
            RuntimeError: If no workspace is loaded or no path provided
        """
        if self._workspace is None:
            raise RuntimeError("No workspace loaded")

        save_path = path or self._path
        if save_path is None:
            raise RuntimeError("No path specified")

        self._format.save_workspace(self._workspace, save_path)
        self._path = save_path

    def create(self, name: str, path: Path) -> Workspace:
        """Create a new workspace.

        Args:
            name: Workspace name
            path: Path to save the workspace

        Returns:
            The created workspace
        """
        self._workspace = Workspace(name=name)
        self._path = path
        self._secrets.set_workspace(path)
        self.save()
        return self._workspace

    def close(self) -> None:
        """Close the current workspace."""
        self._workspace = None
        self._path = None

    # Environment operations

    def get_active_environment(self) -> Environment | None:
        """Get the active environment."""
        if self._workspace is None:
            return None
        if self._workspace.active_environment is None:
            return None
        for env in self._workspace.environments:
            if env.name == self._workspace.active_environment:
                return env
        return None

    def set_active_environment(self, name: str | None) -> None:
        """Set the active environment by name."""
        if self._workspace is None:
            raise RuntimeError("No workspace loaded")
        self._workspace.active_environment = name

    def add_environment(self, environment: Environment) -> None:
        """Add an environment to the workspace."""
        if self._workspace is None:
            raise RuntimeError("No workspace loaded")
        self._workspace.environments.append(environment)

    def remove_environment(self, name: str) -> None:
        """Remove an environment by name."""
        if self._workspace is None:
            raise RuntimeError("No workspace loaded")
        self._workspace.environments = [e for e in self._workspace.environments if e.name != name]
        if self._workspace.active_environment == name:
            self._workspace.active_environment = None

    # Collection operations

    def add_collection(self, collection: Collection) -> None:
        """Add a collection to the workspace."""
        if self._workspace is None:
            raise RuntimeError("No workspace loaded")
        self._workspace.collections.append(collection)

    def remove_collection(self, name: str) -> None:
        """Remove a collection by name."""
        if self._workspace is None:
            raise RuntimeError("No workspace loaded")
        self._workspace.collections = [c for c in self._workspace.collections if c.name != name]

    # Variable resolution

    def resolve_variables(self, text: str) -> str:
        """Resolve ${VAR} placeholders using active environment and secrets.

        Resolution order:
        1. Active environment variables
        2. Secrets (.env file)
        3. System environment variables
        """
        env = self.get_active_environment()
        if env:
            for kv in env.variables:
                if kv.enabled:
                    text = text.replace(f"${{{kv.key}}}", kv.value)

        # Remaining placeholders resolved by secrets service
        return self._secrets.resolve(text)

    def resolve_request(self, request: Request) -> Request:
        """Create a copy of the request with all variables resolved."""
        from forc.domain.models import KeyValue

        resolved_headers = [KeyValue(key=kv.key, value=self.resolve_variables(kv.value), enabled=kv.enabled) for kv in request.headers]
        resolved_params = [KeyValue(key=kv.key, value=self.resolve_variables(kv.value), enabled=kv.enabled) for kv in request.query_params]

        return Request(
            name=request.name,
            method=request.method,
            url=self.resolve_variables(request.url),
            headers=resolved_headers,
            query_params=resolved_params,
            body=self.resolve_variables(request.body),
            body_type=request.body_type,
            auth=request.auth,
        )
