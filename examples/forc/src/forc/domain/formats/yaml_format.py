from pathlib import Path
from typing import IO, Any, cast

import cattrs
from observant import ObservableList
from ruamel.yaml import YAML

from forc.domain.models import (
    ApiKeyAuth,
    ApiKeyLocation,
    Auth,
    AuthType,
    BasicAuth,
    BearerAuth,
    BodyType,
    Collection,
    Environment,
    HttpMethod,
    Request,
    Workspace,
)


def _yaml_load(yaml: YAML, stream: IO[str]) -> dict[str, Any]:
    """Load YAML with proper typing (ruamel.yaml lacks type stubs)."""
    result = yaml.load(stream)  # pyright: ignore[reportUnknownMemberType]
    return cast(dict[str, Any], result) if result else {}


def _yaml_dump(yaml: YAML, data: dict[str, Any], stream: IO[str]) -> None:
    """Dump YAML with proper typing (ruamel.yaml lacks type stubs)."""
    yaml.dump(data, stream)  # pyright: ignore[reportUnknownMemberType]


def _create_converter() -> cattrs.Converter:
    """Create a cattrs converter with custom hooks for our domain types."""
    converter = cattrs.Converter()

    # Enum hooks - serialize as string values
    converter.register_unstructure_hook(HttpMethod, lambda v: v.value)
    converter.register_structure_hook(HttpMethod, lambda v, _: HttpMethod(v))

    converter.register_unstructure_hook(BodyType, lambda v: v.value)
    converter.register_structure_hook(BodyType, lambda v, _: BodyType(v))

    converter.register_unstructure_hook(AuthType, lambda v: v.value)
    converter.register_structure_hook(AuthType, lambda v, _: AuthType(v))

    # Auth union - use 'type' field to discriminate
    def unstructure_auth(auth: Auth) -> dict[str, Any]:
        # Manually unstructure to avoid recursion through hooks
        result: dict[str, Any] = {"type": auth.type.value}
        if isinstance(auth, BasicAuth):
            result["username"] = auth.username
            result["password"] = auth.password
        elif isinstance(auth, BearerAuth):
            result["token"] = auth.token
        elif isinstance(auth, ApiKeyAuth):
            result["key"] = auth.key
            result["value"] = auth.value
            result["location"] = auth.location.value
        return result

    def structure_auth(data: dict[str, Any], _: type) -> Auth:
        if not data:
            return Auth()
        auth_type = AuthType(data.get("type", "none"))
        match auth_type:
            case AuthType.BASIC:
                return BasicAuth(
                    username=data.get("username", ""),
                    password=data.get("password", ""),
                )
            case AuthType.BEARER:
                return BearerAuth(token=data.get("token", ""))
            case AuthType.API_KEY:
                return ApiKeyAuth(
                    key=data.get("key", ""),
                    value=data.get("value", ""),
                    location=ApiKeyLocation(data.get("location", "header")),
                )
            case AuthType.NONE:
                return Auth()

    converter.register_unstructure_hook(Auth, unstructure_auth)
    converter.register_unstructure_hook(BasicAuth, unstructure_auth)
    converter.register_unstructure_hook(BearerAuth, unstructure_auth)
    converter.register_unstructure_hook(ApiKeyAuth, unstructure_auth)
    converter.register_structure_hook(Auth, structure_auth)
    converter.register_structure_hook(BasicAuth, structure_auth)
    converter.register_structure_hook(BearerAuth, structure_auth)
    converter.register_structure_hook(ApiKeyAuth, structure_auth)

    # Collection items - discriminate by presence of 'method' field
    def structure_collection_item(data: dict[str, Any], _: type) -> Request | Collection:
        if "method" in data:
            return converter.structure(data, Request)
        return converter.structure(data, Collection)

    converter.register_structure_hook(Request | Collection, structure_collection_item)

    # Request/Collection - exclude parent references to avoid circular serialization
    def unstructure_request(request: Request) -> dict[str, Any]:
        return {
            "name": request.name,
            "method": request.method.value,
            "url": request.url,
            "headers": converter.unstructure(request.headers),
            "query_params": converter.unstructure(request.query_params),
            "body": request.body,
            "body_fields": converter.unstructure(request.body_fields),
            "body_type": request.body_type.value,
            "auth": converter.unstructure(request.auth) if request.auth else None,
            # Exclude 'collection' - it's a runtime-only parent reference
        }

    def unstructure_collection(collection: Collection) -> dict[str, Any]:
        return {
            "name": collection.name,
            "items": [converter.unstructure(item) for item in collection.items],
            # Exclude 'parent' - it's a runtime-only parent reference
        }

    converter.register_unstructure_hook(Request, unstructure_request)
    converter.register_unstructure_hook(Collection, unstructure_collection)

    return converter


# Global converter instance
_converter = _create_converter()


class YamlFormat:
    """YAML file format implementation using ruamel.yaml for round-trip preservation."""

    extension = ".yaml"

    def __init__(self) -> None:
        self._yaml = YAML()
        self._yaml.preserve_quotes = True
        self._yaml.default_flow_style = False

    def load_request(self, path: Path) -> Request:
        """Load a request from a YAML file."""
        with path.open() as f:
            data = _yaml_load(self._yaml, f)
        return _converter.structure(data, Request)

    def save_request(self, request: Request, path: Path) -> None:
        """Save a request to a YAML file."""
        data: dict[str, Any] = _converter.unstructure(request)
        with path.open("w") as f:
            _yaml_dump(self._yaml, data, f)

    def load_environment(self, path: Path) -> Environment:
        """Load an environment from a YAML file."""
        with path.open() as f:
            data = _yaml_load(self._yaml, f)
        return _converter.structure(data, Environment)

    def save_environment(self, environment: Environment, path: Path) -> None:
        """Save an environment to a YAML file."""
        data: dict[str, Any] = _converter.unstructure(environment)
        with path.open("w") as f:
            _yaml_dump(self._yaml, data, f)

    def load_collection(self, path: Path) -> Collection:
        """Load a collection from a directory.

        Expected structure:
        collection_dir/
            _collection.yaml  # Collection metadata (name)
            request1.yaml
            request2.yaml
            subcollection/
                _collection.yaml
                ...
        """
        meta_path = path / "_collection.yaml"
        if meta_path.exists():
            with meta_path.open() as f:
                meta = _yaml_load(self._yaml, f)
            name = str(meta.get("name", path.name))
        else:
            name = path.name

        items: ObservableList[Request | Collection] = ObservableList()

        for item_path in sorted(path.iterdir()):
            if item_path.name.startswith("_"):
                continue
            if item_path.is_dir():
                items.append(self.load_collection(item_path))
            elif item_path.suffix == self.extension:
                items.append(self.load_request(item_path))

        collection = Collection(name=name, items=items, folder=path.name)
        # Set parent references
        for item in items:
            if isinstance(item, Request):
                item.collection = collection
            else:
                item.parent = collection
        return collection

    def save_collection(self, collection: Collection, path: Path) -> None:
        """Save a collection to a directory."""
        path.mkdir(parents=True, exist_ok=True)

        # Save collection metadata
        meta_path = path / "_collection.yaml"
        with meta_path.open("w") as f:
            _yaml_dump(self._yaml, {"name": collection.name}, f)

        # Save items
        for item in collection.items:
            if isinstance(item, Request):
                item_path = path / f"{slugify(item.name)}{self.extension}"
                self.save_request(item, item_path)
            else:
                item_path = path / slugify(item.name)
                self.save_collection(item, item_path)

    def load_workspace(self, path: Path) -> Workspace:
        """Load a workspace from a directory.

        Expected structure:
        workspace_dir/
            forc.yaml  # Workspace config
            collections/
                ...
            environments/
                dev.yaml
                prod.yaml
        """
        config_path = path / "forc.yaml"
        if config_path.exists():
            with config_path.open() as f:
                config = _yaml_load(self._yaml, f)
        else:
            config = {}

        name = str(config.get("name", path.name))
        active_environment_raw = config.get("active_environment")
        active_environment = str(active_environment_raw) if active_environment_raw else None

        # Load collections
        collections: ObservableList[Collection] = ObservableList()
        collections_path = path / "collections"
        if collections_path.exists():
            for coll_path in sorted(collections_path.iterdir()):
                if coll_path.is_dir():
                    collections.append(self.load_collection(coll_path))

        # Load environments
        environments: list[Environment] = []
        environments_path = path / "environments"
        if environments_path.exists():
            for env_path in sorted(environments_path.iterdir()):
                if env_path.suffix == self.extension:
                    environments.append(self.load_environment(env_path))

        return Workspace(
            name=name,
            collections=collections,
            environments=environments,
            active_environment=active_environment,
        )

    def save_workspace(self, workspace: Workspace, path: Path) -> None:
        """Save a workspace to a directory."""
        path.mkdir(parents=True, exist_ok=True)

        # Save workspace config
        config_path = path / "forc.yaml"
        config: dict[str, Any] = {
            "name": workspace.name,
        }
        if workspace.active_environment:
            config["active_environment"] = workspace.active_environment
        with config_path.open("w") as f:
            _yaml_dump(self._yaml, config, f)

        # Save collections
        collections_path = path / "collections"
        for collection in workspace.collections:
            coll_path = collections_path / slugify(collection.name)
            self.save_collection(collection, coll_path)

        # Save environments
        environments_path = path / "environments"
        environments_path.mkdir(parents=True, exist_ok=True)
        for environment in workspace.environments:
            env_path = environments_path / f"{slugify(environment.name)}{self.extension}"
            self.save_environment(environment, env_path)


def slugify(name: str) -> str:
    """Convert a name to a filesystem-safe slug."""
    import re
    import unicodedata

    # Normalize unicode (é -> e)
    name = unicodedata.normalize("NFKD", name)
    name = name.encode("ascii", "ignore").decode("ascii")
    # Lowercase, replace spaces with hyphens
    name = name.lower().replace(" ", "-")
    # Remove anything not alphanumeric or hyphen
    name = re.sub(r"[^a-z0-9\-]", "", name)
    # Collapse multiple hyphens
    name = re.sub(r"-+", "-", name)
    return name.strip("-")
