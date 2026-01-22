# pyright: reportUnknownMemberType=false, reportUnnecessaryIsInstance=false
"""YAML serialization for Forc2 domain objects."""

from pathlib import Path
from typing import Any

from ruamel.yaml import YAML

from .domain import Collection, Environment, EnvironmentVariable, Header, HttpMethod, Request, Workspace

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
        workspace.name.value = data["name"]
    if "active_environment" in data:
        workspace.active_environment_name.value = data["active_environment"]


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
    collection.filename.value = path.name

    # Load collection metadata
    meta_file = path / "_collection.yaml"
    if meta_file.exists():
        with meta_file.open() as f:
            data = yaml.load(f)
            if data and "name" in data:
                collection.name.value = data["name"]
    else:
        # Use folder name as collection name
        collection.name.value = path.name

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

    return collection


def load_request(path: Path) -> Request:
    """Load a Request from a YAML file."""
    request = Request()

    # Track the file stem for save path resolution
    request.filename.value = path.stem

    with path.open() as f:
        data = yaml.load(f)

    if not data:
        return request

    if "name" in data:
        request.name.value = data["name"]
    else:
        # Use filename as name
        request.name.value = path.stem

    if "method" in data:
        request.method.value = HttpMethod(data["method"])

    if "url" in data:
        request.url.value = data["url"]

    if "headers" in data:
        for h in data["headers"]:
            request.headers.append(
                Header(
                    key=h.get("key", ""),
                    value=h.get("value", ""),
                    enabled=h.get("enabled", True),
                )
            )

    if "query_params" in data:
        for p in data["query_params"]:
            request.query_params.append(
                Header(
                    key=p.get("key", ""),
                    value=p.get("value", ""),
                    enabled=p.get("enabled", True),
                )
            )

    if "body" in data:
        request.body.value = data["body"]

    return request


def load_environment(path: Path) -> Environment:
    """Load an Environment from a YAML file."""
    env = Environment()

    # Track the file stem for save path resolution
    env.filename.value = path.stem

    with path.open() as f:
        data = yaml.load(f)

    if not data:
        # Use filename as name when file is empty
        env.name.value = path.stem
        return env

    if "name" in data:
        env.name.value = data["name"]
    else:
        # Use filename as name
        env.name.value = path.stem

    if "variables" in data:
        # Build the dict first, then assign to trigger reactivity
        variables: dict[str, EnvironmentVariable] = {}
        for key, v in data["variables"].items():
            variables[key] = EnvironmentVariable(
                value=v.get("value", ""),
                enabled=v.get("enabled", True),
                secret=v.get("secret", False),
            )
        env.variables.value = variables

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
            folder_name = item.filename.value or _slugify(item.name.value)
            sub_path = path / folder_name
            save_collection(item, sub_path)
        elif isinstance(item, Request):
            # Save request as YAML file
            # Use existing filename if set, else slugify the name
            file_stem = item.filename.value or _slugify(item.name.value)
            req_path = path / f"{file_stem}.yaml"
            save_request(item, req_path)


def save_request(request: Request, path: Path) -> None:
    """Save a Request to a YAML file."""
    data: dict[str, Any] = {
        "name": request.name.value,
        "method": request.method.value.value,  # Enum -> string
        "url": request.url.value,
    }

    if request.headers.value:
        data["headers"] = [{"key": h.key, "value": h.value} for h in request.headers.value if h.enabled]

    if request.query_params.value:
        data["query_params"] = [{"key": p.key, "value": p.value} for p in request.query_params.value if p.enabled]

    if request.body.value:
        data["body"] = request.body.value

    with path.open("w") as f:
        yaml.dump(data, f)


def _slugify(name: str) -> str:
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
