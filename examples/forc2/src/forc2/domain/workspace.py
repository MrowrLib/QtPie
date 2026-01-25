# pyright: reportUnknownVariableType=false
"""Workspace - the root state that holds a collection and its path."""

from __future__ import annotations

from pathlib import Path

from qtpie import State, Var, new, state

from .collection import Collection
from .environment import Environment
from .http_client import HttpClient
from .request import Request


@state
class Workspace(State):
    ### Variables ###
    name: Var[str] = new("")
    collection: Var[Collection | None] = new(None)
    environments: Var[list[Environment]] = new([])
    active_environment: Var[Environment | None] = new(None, onChange="_on_active_environment_changed")
    active_environment_name: Var[str | None] = new(None, onChange="_on_active_environment_name_changed")
    path: Var[Path | None] = new(None)
    http_client: Var[HttpClient] = new()

    ### Static Methods ###
    @staticmethod
    def load(folder: Path) -> Workspace | None:
        return load_workspace(folder)

    ### Methods ###
    def _on_active_environment_name_changed(self) -> None:
        if getattr(self, "_updating_active_environment", False):
            return
        self._updating_active_environment = True
        active_name = self.active_environment_name()
        if active_name is not None:
            for env in self.environments():
                if env.name.value == active_name:
                    self.active_environment = env
                    break
        self._updating_active_environment = False

    def _on_active_environment_changed(self) -> None:
        if getattr(self, "_updating_active_environment", False):
            return
        self._updating_active_environment = True
        active_env = self.active_environment()
        if active_env is not None:
            self.active_environment_name = active_env.name.value
        self._updating_active_environment = False

    def _ensure_root_collection(self) -> Collection:
        """Ensure root collection exists, creating it if needed."""
        if self.collection() is None:
            root = Collection()
            root.name.value = "collections"
            root.filename.value = "collections"
            root.state_parent = self
            self.collection = root

        root = self.collection()
        assert root is not None
        return root

    def add_collection(self, name: str = "") -> Collection:
        """Create and add a new top-level Collection to this workspace."""
        root = self._ensure_root_collection()
        return root.add_collection(name)

    def add_request(self, name: str = "") -> Request:
        """Create and add a new top-level Request to this workspace."""
        root = self._ensure_root_collection()
        return root.add_request(name)

    def save(self) -> None:
        """Save the entire workspace to disk (collections + environments)."""
        from ..format import save_collection, save_environment

        if self.path() is None:
            return

        workspace_path = self.path()
        assert workspace_path is not None

        # Save collections
        collection = self.collection()
        if collection is not None:
            collections_path = workspace_path / "collections"
            save_collection(collection, collections_path)

        # Save environments
        if self.environments():
            environments_path = workspace_path / "environments"
            environments_path.mkdir(parents=True, exist_ok=True)
            for env in self.environments():
                filename = env.filename.value or env.name.value
                env_path = environments_path / f"{filename}.yaml"
                save_environment(env, env_path)


def load_workspace(folder: Path) -> Workspace | None:
    """Load a Workspace from a folder path. Returns None if folder doesn't exist."""
    from ..format import load_collection, load_environment, load_workspace_config

    if not folder.exists():
        return None

    workspace = Workspace()
    workspace.path = folder

    # Load collections from 'collections/' subfolder
    collections_path = folder / "collections"
    if collections_path.exists():
        collection = load_collection(collections_path)
        collection.state_parent = workspace
        workspace.collection = collection

    # Load environments from 'environments/' subfolder
    environments_path = folder / "environments"
    if environments_path.exists():
        envs: list[Environment] = []
        for env_file in sorted(environments_path.iterdir()):
            if env_file.suffix in (".yaml", ".yml"):
                env = load_environment(env_file)
                env.state_parent = workspace
                envs.append(env)
        workspace.environments = envs

    # Load workspace config from forc.yaml
    load_workspace_config(workspace, folder)

    return workspace
