# pyright: reportUnknownVariableType=false
"""Workspace - the root state that holds a collection and its path."""

from __future__ import annotations

from pathlib import Path

from qtpie import State, Var, new, state

from .collection import Collection
from .environment import Environment


@state
class Workspace(State):
    ### Variables ###
    name: Var[str] = new("")
    collection: Var[Collection | None] = new(None)
    environments: Var[list[Environment]] = new([])
    active_environment: Var[Environment | None] = new(None, onChange="_on_active_environment_changed")
    active_environment_name: Var[str | None] = new(None, onChange="_on_active_environment_name_changed")
    path: Var[Path | None] = new(None)

    ### Events ###
    # on_save: Event

    ### Static Methods ###
    @staticmethod
    def load(folder: Path) -> Workspace | None:
        return load_workspace(folder)

    ### Methods ###
    def _on_active_environment_name_changed(self) -> None:
        self._updating_active_environment = True  # Guard against recursion (for when changing active_environment_name)
        active_name = self.active_environment_name()
        if active_name is not None:
            for env in self.environments():
                if env.name.value == active_name:
                    self.active_environment = env
                    break
        self._updating_active_environment = False

    def _on_active_environment_changed(self) -> None:
        if self._updating_active_environment:
            # Guard against recursion (for when changing active_environment_name)
            return
        active_env = self.active_environment()
        if active_env is not None:
            self.active_environment_name = active_env.name.value

    # def _do_save(self) -> None:
    #     from ..format import save_collection

    #     if self.collection.value is not None and self.path.value is not None:
    #         # Save to 'collections/' subfolder within workspace path
    #         collections_path = self.path.value / "collections"
    #         save_collection(self.collection.value, collections_path)


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
