"""Workspace service for loading and saving workspaces."""

from pathlib import Path

from forc.domain.formats import YamlFormat
from forc.domain.models import Collection, Environment, KeyValue, Request, Workspace

from .environments import EnvironmentsService


class WorkspaceService:
    """Service for managing workspaces."""

    def __init__(
        self,
        format_handler: YamlFormat | None = None,
        environments: EnvironmentsService | None = None,
    ) -> None:
        self._format = format_handler or YamlFormat()
        self._environments = environments or EnvironmentsService()
        self._workspace: Workspace | None = None
        self._path: Path | None = None

    @property
    def environments(self) -> EnvironmentsService:
        """Get the environments service."""
        return self._environments

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
        self._environments.load(self._workspace.environments, self._workspace.active_environment)
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
        self.save()
        return self._workspace

    def close(self) -> None:
        """Close the current workspace."""
        self._workspace = None
        self._path = None
        self._environments.clear()

    # Environment operations (delegate to EnvironmentsService)

    def get_active_environment(self) -> Environment | None:
        """Get the active environment."""
        return self._environments.active

    def set_active_environment(self, name: str | None) -> None:
        """Set the active environment by name."""
        if self._workspace is None:
            raise RuntimeError("No workspace loaded")
        self._environments.set_active(name)
        self._workspace.active_environment = name

    def add_environment(self, environment: Environment) -> None:
        """Add an environment to the workspace."""
        if self._workspace is None:
            raise RuntimeError("No workspace loaded")
        self._environments.add(environment)
        self._workspace.environments.append(environment)

    def remove_environment(self, name: str) -> None:
        """Remove an environment by name."""
        if self._workspace is None:
            raise RuntimeError("No workspace loaded")
        self._environments.remove(name)
        self._workspace.environments = [e for e in self._workspace.environments if e.name != name]
        if self._workspace.active_environment == name:
            self._workspace.active_environment = None

    # Request operations

    def save_request(self, request: Request) -> None:
        """Save a single request to its YAML file.

        Args:
            request: The request to save

        Raises:
            RuntimeError: If no workspace path is set
        """
        if self._path is None:
            raise RuntimeError("No workspace path set")

        path = self._get_request_path(request)
        path.parent.mkdir(parents=True, exist_ok=True)
        self._format.save_request(request, path)

    def _get_request_path(self, request: Request) -> Path:
        """Get the file path for a request based on its collection hierarchy."""
        from forc.domain.formats.yaml_format import slugify

        if self._path is None:
            raise RuntimeError("No workspace path set")

        # Build collection path parts
        parts: list[str] = []
        collection = request.collection
        while collection is not None:
            parts.append(slugify(collection.name))
            collection = collection.parent
        parts.reverse()

        # workspace/collections/coll1/coll2/request-name.yaml
        path = self._path / "collections"
        for part in parts:
            path = path / part
        return path / f"{slugify(request.name)}.yaml"

    # Collection operations

    def add_collection(self, name: str, parent: Collection | None = None) -> Collection:
        """Create and add a collection.

        Args:
            name: Collection name
            parent: Optional parent collection (None = top-level)

        Returns:
            The created collection
        """
        if self._workspace is None:
            raise RuntimeError("No workspace loaded")
        collection = Collection(name=name, parent=parent)
        if parent is None:
            self._workspace.collections.append(collection)
        else:
            parent.items.append(collection)
        return collection

    def add_request(self, name: str, collection: Collection) -> Request:
        """Create and add a request to a collection.

        Args:
            name: Request name
            collection: Parent collection

        Returns:
            The created request
        """
        request = Request(name=name, collection=collection)
        collection.items.append(request)
        return request

    def remove_collection(self, name: str) -> None:
        """Remove a top-level collection by name."""
        if self._workspace is None:
            raise RuntimeError("No workspace loaded")
        for c in list(self._workspace.collections):
            if c.name == name:
                self._workspace.collections.remove(c)

    def remove_item(self, item: Request | Collection) -> None:
        """Remove an item from its parent collection or workspace.

        Args:
            item: The request or collection to remove
        """
        if self._workspace is None:
            raise RuntimeError("No workspace loaded")

        if isinstance(item, Request):
            if item.collection is not None:
                item.collection.items.remove(item)
                item.collection = None
        else:
            # It's a Collection
            if item.parent is not None:
                item.parent.items.remove(item)
                item.parent = None
            else:
                # Top-level collection
                self._workspace.collections.remove(item)

    # Variable resolution (delegate to EnvironmentsService)

    def resolve_variables(self, text: str) -> str:
        """Resolve ${VAR} placeholders using active environment.

        Resolution order:
        1. Active environment variables (includes secrets)
        2. System environment variables (fallback)
        """
        return self._environments.resolve(text)

    def resolve_request(self, request: Request) -> Request:
        """Create a copy of the request with all variables resolved."""
        resolved_headers = [
            KeyValue(key=kv.key, value=self.resolve_variables(kv.value), enabled=kv.enabled) for kv in request.headers
        ]
        resolved_params = [
            KeyValue(key=kv.key, value=self.resolve_variables(kv.value), enabled=kv.enabled)
            for kv in request.query_params
        ]
        resolved_body_fields = [
            KeyValue(key=kv.key, value=self.resolve_variables(kv.value), enabled=kv.enabled)
            for kv in request.body_fields
        ]

        return Request(
            name=request.name,
            method=request.method,
            url=self.resolve_variables(request.url),
            headers=resolved_headers,
            query_params=resolved_params,
            body=self.resolve_variables(request.body),
            body_fields=resolved_body_fields,
            body_type=request.body_type,
            auth=request.auth,
        )
