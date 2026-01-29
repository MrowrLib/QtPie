# pyright: reportUnknownMemberType=false, reportUnnecessaryIsInstance=false
"""YAML serialization for Forc2 domain objects."""

from pathlib import Path
from typing import Any

from ruamel.yaml import YAML

from .domain import (
    ApiKeyAuth,
    ApiKeyLocation,
    Auth,
    AuthType,
    BasicAuth,
    BearerAuth,
    BodyType,
    Collection,
    Environment,
    EnvironmentVariable,
    HttpMethod,
    Request,
    RequestKeyValue,
    Workspace,
)

yaml = YAML()
yaml.preserve_quotes = True
yaml.default_flow_style = False


def load_workspace_config(workspace: Workspace, path: Path) -> None:
    """Load workspace config from forc.yaml and apply to workspace."""
    config_path = path / "forc.yaml"
    if not config_path.exists():
        return
    with config_path.open() as f:
        data = yaml.load(f)
    if not data:
        return
    if "name" in data:
        workspace.name = data["name"]
    if "active_environment" in data:
        workspace.active_environment_name = data["active_environment"]


def load_collection(path: Path) -> Collection:
    """Load a Collection from a directory.

    Directory structure:
        collection_dir/
            _collection.yaml    # {"name": "Collection Name"}
            request1.yaml       # Request files
            request2.yaml
            subcollection/      # Nested collections
                _collection.yaml
                ...
    """
    collection = Collection()

    # Track the folder name for save path resolution
    collection.filename = path.name

    # Load collection metadata
    meta_file = path / "_collection.yaml"
    if meta_file.exists():
        with meta_file.open() as f:
            data = yaml.load(f)
            if data and "name" in data:
                collection.name = data["name"]
    else:
        # Use folder name as collection name
        collection.name = path.name

    # Load items (requests and sub-collections)
    for item_path in sorted(path.iterdir()):
        if item_path.name.startswith("_"):
            continue  # Skip metadata files
        if item_path.name.startswith("."):
            continue  # Skip hidden files

        if item_path.is_dir():
            # Sub-collection
            sub = load_collection(item_path)
            collection.items.append(sub)
        elif item_path.suffix in (".yaml", ".yml"):
            # Request file
            req = load_request(item_path)
            collection.items.append(req)

    collection.reset_dirty()

    return collection


def load_request(path: Path) -> Request:
    """Load a Request from a YAML file."""
    request = Request()

    # Track the file stem for save path resolution
    request.filename = path.stem

    with path.open() as f:
        data = yaml.load(f)

    if not data:
        return request

    if "name" in data:
        request.name = data["name"]
    else:
        # Use filename as name
        request.name = path.stem

    if "method" in data:
        request.method = HttpMethod(data["method"])

    if "url" in data:
        request.url = data["url"]

    if "headers" in data:
        for h in data["headers"]:
            request.headers.append(
                RequestKeyValue(
                    name=h.get("name", ""),
                    value=h.get("value", ""),
                    enabled=h.get("enabled", True),
                )
            )

    if "query_params" in data:
        for p in data["query_params"]:
            request.query_params.append(
                RequestKeyValue(
                    name=p.get("name", ""),
                    value=p.get("value", ""),
                    enabled=p.get("enabled", True),
                )
            )

    if "body" in data:
        request.body = data["body"]

    if "body_type" in data:
        request.body_type = BodyType(data["body_type"])

    if "body_fields" in data:
        for f in data["body_fields"]:
            request.body_fields.append(
                RequestKeyValue(
                    name=f.get("name", ""),
                    value=f.get("value", ""),
                    enabled=f.get("enabled", True),
                )
            )

    if "auth" in data and data["auth"] is not None:
        auth_data = data["auth"]
        auth_type = AuthType(auth_data.get("type", "none"))
        match auth_type:
            case AuthType.NONE:
                request.auth = Auth()
            case AuthType.BASIC:
                request.auth = BasicAuth(
                    username=auth_data.get("username", ""),
                    password=auth_data.get("password", ""),
                )
            case AuthType.BEARER:
                request.auth = BearerAuth(token=auth_data.get("token", ""))
            case AuthType.API_KEY:
                request.auth = ApiKeyAuth(
                    name=auth_data.get("name", ""),
                    value=auth_data.get("value", ""),
                    location=ApiKeyLocation(auth_data.get("location", "header")),
                )
    else:
        # Default to Auth() instead of None so the UI has something to bind to
        request.auth = Auth()

    request.reset_dirty()

    return request


def load_environment(path: Path) -> Environment:
    """Load an Environment from a YAML file."""
    env = Environment()

    # Track the file stem for save path resolution
    env.filename = path.stem

    with path.open() as f:
        data = yaml.load(f)

    if not data:
        # Use filename as name when file is empty
        env.name = path.stem
        return env

    if "name" in data:
        env.name = data["name"]
    else:
        # Use filename as name
        env.name = path.stem

    if "variables" in data:
        # Build the dict first, then assign to trigger reactivity
        variables: dict[str, EnvironmentVariable] = {}
        for key, v in data["variables"].items():
            variables[key] = EnvironmentVariable(
                value=v.get("value", ""),
                enabled=v.get("enabled", True),
                secret=v.get("secret", False),
            )
        env.variables = variables

    return env


def save_environment(environment: Environment, path: Path) -> None:
    """Save an Environment to a YAML file."""
    data: dict[str, Any] = {
        "name": environment.name.value,
    }

    if environment.variables.value:
        variables_data: dict[str, dict[str, Any]] = {}
        for key, var in environment.variables.value.items():
            var_data: dict[str, Any] = {"value": var.value}
            if var.secret:
                var_data["secret"] = True
            if not var.enabled:
                var_data["enabled"] = False
            variables_data[key] = var_data
        data["variables"] = variables_data

    with path.open("w") as f:
        yaml.dump(data, f)


def save_collection(collection: Collection, path: Path) -> None:
    """Save a Collection to a directory."""
    path.mkdir(parents=True, exist_ok=True)

    # Save collection metadata
    meta_file = path / "_collection.yaml"
    meta: dict[str, Any] = {"name": collection.name.value}
    with meta_file.open("w") as f:
        yaml.dump(meta, f)

    # Save items
    for item in collection.items.value:
        if isinstance(item, Collection):
            # Save sub-collection in subdirectory
            # Use existing filename if set, else slugify the name
            folder_name = item.filename.value or slugify(item.name.value)
            sub_path = path / folder_name
            save_collection(item, sub_path)
        elif isinstance(item, Request):
            # Save request as YAML file
            # Use existing filename if set, else slugify the name
            file_stem = item.filename.value or slugify(item.name.value)
            req_path = path / f"{file_stem}.yaml"
            save_request(item, req_path)

    collection.reset_dirty()


def save_request(request: Request, path: Path) -> None:
    """Save a Request to a YAML file."""
    data: dict[str, Any] = {
        "name": request.name.value,
        "method": request.method.value.value,  # Enum -> string
        "url": request.url.value,
    }

    if request.headers.value:
        data["headers"] = [{"name": h.name, "value": h.value} for h in request.headers.value if h.enabled]

    if request.query_params.value:
        data["query_params"] = [{"name": p.name, "value": p.value} for p in request.query_params.value if p.enabled]

    if request.body.value:
        data["body"] = request.body.value

    if request.body_type.value != BodyType.NONE:
        data["body_type"] = request.body_type.value.value

    if request.body_fields.value:
        data["body_fields"] = [{"name": f.name, "value": f.value} for f in request.body_fields.value if f.enabled]

    # Save auth if not NONE
    auth = request.auth.value
    if auth is not None and auth.type != AuthType.NONE:
        auth_data: dict[str, Any] = {"type": auth.type.value}
        match auth.type:
            case AuthType.BASIC:
                assert isinstance(auth, BasicAuth)
                auth_data["username"] = auth.username
                auth_data["password"] = auth.password
            case AuthType.BEARER:
                assert isinstance(auth, BearerAuth)
                auth_data["token"] = auth.token
            case AuthType.API_KEY:
                assert isinstance(auth, ApiKeyAuth)
                auth_data["name"] = auth.name
                auth_data["value"] = auth.value
                auth_data["location"] = auth.location.value
        data["auth"] = auth_data

    with path.open("w") as f:
        yaml.dump(data, f)

    request.reset_dirty()


def slugify(name: str) -> str:
    """Convert a name to a filesystem-safe slug."""
    import re
    import unicodedata

    # Normalize unicode
    name = unicodedata.normalize("NFKD", name)
    name = name.encode("ascii", "ignore").decode("ascii")

    # Lowercase and replace spaces
    name = name.lower().replace(" ", "-")

    # Remove special chars
    name = re.sub(r"[^a-z0-9\-]", "", name)

    # Collapse multiple hyphens
    name = re.sub(r"-+", "-", name)

    return name.strip("-") or "unnamed"
