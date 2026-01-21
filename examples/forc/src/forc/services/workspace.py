"""Workspace service for loading and saving workspaces."""

import shutil
from pathlib import Path

from forc.domain.formats import YamlFormat
from forc.domain.models import Collection, KeyValue, Request, Workspace

from .environments import EnvironmentsService


class WorkspaceService:
    """Service for managing workspaces."""

    def __init__(
        self,
        format_handler: YamlFormat | None = None,
        environments: EnvironmentsService | None = None,
    ) -> None:
        self._format = format_handler or YamlFormat()
        self._environments = environments or EnvironmentsService(format_handler=self._format)
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
        self._path = path.resolve()
        self._environments.load(
            self._workspace.environments,
            self._path,
            self._workspace,
        )
        # Subscribe to active_environment changes to persist to disk
        from observant import get_proxies_for

        def on_proxy_available(target: object, proxy: object) -> None:
            if target is self._workspace:
                from observant import ObservableProxy

                if isinstance(proxy, ObservableProxy):
                    field_obs = proxy._get_or_create_field_observable("active_environment")
                    field_obs.on_change(lambda _: self._save_config())

        # Check if proxy already exists
        proxies = get_proxies_for(self._workspace)
        if proxies:
            from observant import ObservableProxy

            proxy = proxies[0]
            if isinstance(proxy, ObservableProxy):
                field_obs = proxy._get_or_create_field_observable("active_environment")
                field_obs.on_change(lambda _: self._save_config())
        else:
            # Wait for proxy to be created
            from observant import on_proxy_registered

            on_proxy_registered(on_proxy_available)
        return self._workspace

    def set_active_environment(self, name: str | None) -> None:
        """Set the active environment and persist to disk.

        Args:
            name: Environment name, or None to clear
        """
        if self._workspace is None:
            raise RuntimeError("No workspace loaded")
        if name is None:
            self._workspace.active_environment = None
        else:
            env = self._environments.get(name)
            if env is None:
                raise ValueError(f"Environment '{name}' not found")
            self._workspace.active_environment = env
        self._save_config()

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
        self._path = path.resolve()
        self._environments.load(
            self._workspace.environments,
            self._path,
            self._workspace,
        )
        self.save()
        return self._workspace

    def close(self) -> None:
        """Close the current workspace."""
        self._workspace = None
        self._path = None
        self._environments.clear()

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
        print(f"Saving request '{request.name}' to path: {path}")
        path.parent.mkdir(parents=True, exist_ok=True)
        self._format.save_request(request, path)

    def _get_request_path(self, request: Request) -> Path:
        """Get the file path for a request based on its collection hierarchy."""
        from forc.domain.formats.yaml_format import slugify

        if self._path is None:
            raise RuntimeError("No workspace path set")

        # Build collection path parts using folder (actual disk name) or fallback to slugified name
        parts: list[str] = []
        collection = request.collection
        while collection is not None:
            parts.append(collection.folder or slugify(collection.name))
            collection = collection.parent
        parts.reverse()

        # workspace/collections/coll1/coll2/request-name.yaml
        path = self._path / "collections"
        for part in parts:
            path = path / part
        filename = request.filename or slugify(request.name)
        return path / f"{filename}.yaml"

    # Collection operations

    def create_collection(self, name: str, parent: Collection | None = None) -> Collection:
        """Create a collection and write it to disk.

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

        # Write to disk immediately
        self._save_collection_metadata(collection)

        return collection

    def create_request(self, name: str, collection: Collection) -> Request:
        """Create a request and write it to disk.

        Args:
            name: Request name
            collection: Parent collection

        Returns:
            The created request

        Raises:
            RuntimeError: If no workspace is loaded or no path set
        """
        if self._workspace is None:
            raise RuntimeError("No workspace loaded")
        if self._path is None:
            raise RuntimeError("No workspace path set")

        request = Request(name=name, collection=collection)
        collection.items.append(request)

        # Write to disk immediately
        self.save_request(request)

        return request

    def delete_request(self, request: Request) -> None:
        """Delete a request and its file from disk.

        Args:
            request: The request to delete

        Raises:
            RuntimeError: If no workspace is loaded or no path set
        """
        if self._workspace is None:
            raise RuntimeError("No workspace loaded")
        if self._path is None:
            raise RuntimeError("No workspace path set")

        # Remove file from disk
        path = self._get_request_path(request)
        if path.exists():
            path.unlink()

        # Remove from model
        if request.collection is not None:
            request.collection.items.remove(request)
            request.collection = None

    def delete_collection(self, collection: Collection) -> None:
        """Delete a collection and its folder recursively from disk.

        Args:
            collection: The collection to delete

        Raises:
            RuntimeError: If no workspace is loaded or no path set
        """
        if self._workspace is None:
            raise RuntimeError("No workspace loaded")
        if self._path is None:
            raise RuntimeError("No workspace path set")

        # Remove folder recursively from disk
        path = self._get_collection_path(collection)
        if path.exists():
            shutil.rmtree(path)

        # Remove from model
        if collection.parent is not None:
            collection.parent.items.remove(collection)
            collection.parent = None
        else:
            self._workspace.collections.remove(collection)

    def delete_item(self, item: Request | Collection) -> None:
        """Delete a request or collection and its file/folder from disk.

        Args:
            item: The request or collection to delete

        Raises:
            RuntimeError: If no workspace is loaded or no path set
        """
        if isinstance(item, Request):
            self.delete_request(item)
        else:
            self.delete_collection(item)

    def rename_request(self, request: Request, new_name: str) -> None:
        """Rename a request and its file on disk.

        Args:
            request: The request to rename
            new_name: The new name for the request

        Raises:
            RuntimeError: If no workspace is loaded or no path set
        """
        from forc.domain.formats.yaml_format import slugify

        if self._workspace is None:
            raise RuntimeError("No workspace loaded")
        if self._path is None:
            raise RuntimeError("No workspace path set")

        # Get old path using current filename (preserves actual disk name)
        old_path = self._get_request_path(request)

        # Update name and filename
        request.name = new_name
        request.filename = slugify(new_name)

        new_path = self._get_request_path(request)

        if old_path.exists() and old_path != new_path:
            old_path.rename(new_path)

        self.save_request(request)

    def rename_collection(self, collection: Collection, new_name: str) -> None:
        """Rename a collection and its folder on disk.

        Args:
            collection: The collection to rename
            new_name: The new name for the collection

        Raises:
            RuntimeError: If no workspace is loaded or no path set
        """
        from forc.domain.formats.yaml_format import slugify

        if self._workspace is None:
            raise RuntimeError("No workspace loaded")
        if self._path is None:
            raise RuntimeError("No workspace path set")

        # Get old path using current folder (preserves actual disk name)
        old_path = self._get_collection_path(collection)

        # Update name and folder
        collection.name = new_name
        collection.folder = slugify(new_name)

        new_path = self._get_collection_path(collection)

        if old_path.exists() and old_path != new_path:
            old_path.rename(new_path)

        # Update _collection.yaml with the new name
        self._save_collection_metadata(collection)

    def _get_collection_path(self, collection: Collection) -> Path:
        """Get the folder path for a collection based on its hierarchy."""
        from forc.domain.formats.yaml_format import slugify

        if self._path is None:
            raise RuntimeError("No workspace path set")

        parts: list[str] = []
        current: Collection | None = collection
        while current is not None:
            parts.append(current.folder or slugify(current.name))
            current = current.parent
        parts.reverse()

        path = self._path / "collections"
        for part in parts:
            path = path / part
        return path

    def _save_collection_metadata(self, collection: Collection) -> None:
        """Save a collection's _collection.yaml metadata file."""
        path = self._get_collection_path(collection)
        path.mkdir(parents=True, exist_ok=True)
        meta_path = path / "_collection.yaml"
        self._format.save_collection_metadata(collection.name, meta_path)

    def _save_config(self) -> None:
        """Save workspace configuration (active environment, etc.)."""
        if self._workspace is None or self._path is None:
            return
        self._format.save_workspace_config(self._workspace, self._path)

    # Variable resolution (delegate to EnvironmentsService)

    def resolve_variables(self, text: str) -> str:
        """Resolve ${VAR} placeholders using active environment.

        Resolution order:
        1. Active environment variables (includes secrets)
        2. System environment variables (fallback)
        """
        if self._workspace is None:
            raise RuntimeError("No workspace loaded")
        env_name = self._workspace.active_environment.name if self._workspace.active_environment else None
        return self._environments.resolve(text, env_name)

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
