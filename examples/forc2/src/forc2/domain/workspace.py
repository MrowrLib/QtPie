# pyright: reportUnknownVariableType=false
"""Workspace - the root state that holds a collection and its path."""

from pathlib import Path

from qtpie import Event, State, Var, new, state

from .collection import Collection
from .environment import Environment


@state(on_save="_do_save")
class Workspace(State):
    ### Variables ###
    name: Var[str] = new("")
    collection: Var[Collection | None] = new(None)
    environments: Var[list[Environment]] = new([])
    active_environment: Var[Environment | None] = new(None)
    active_environment_name: Var[str | None] = new(None, onChange="_on_active_environment_changed")
    path: Var[Path | None] = new(None, onChange="_on_path_changed")

    ### Events ###
    on_save: Event

    ### Methods ###
    def _on_active_environment_changed(self) -> None:
        print("On active environment changed to:", self.active_environment_name())
        active_name = self.active_environment_name()
        for env in self.environments():
            if env.name.value == active_name:
                self.active_environment = env
                return

    def _on_path_changed(self) -> None:
        """Load or unload collection and environments when path changes."""
        from ..format import load_collection, load_environment, load_workspace_config

        path = self.path.value
        if path is None or not path.exists():
            if self.collection() is not None:
                self.collection = None
            if self.environments():
                self.environments = []
            self.name = ""
            self.active_environment_name = None
            return

        # Load workspace config from forc.yaml
        load_workspace_config(self, path)

        # Load collections from 'collections/' subfolder
        collections_path = path / "collections"
        if collections_path.exists():
            collection = load_collection(collections_path)
            collection.state_parent = self
            self.collection = collection

        # Load environments from 'environments/' subfolder
        environments_path = path / "environments"
        if environments_path.exists():
            envs: list[Environment] = []
            for env_file in sorted(environments_path.iterdir()):
                if env_file.suffix in (".yaml", ".yml"):
                    env = load_environment(env_file)
                    env.state_parent = self
                    envs.append(env)
            self.environments = envs

        # print out the active environment after loading
        print("Loaded environments. Active environment is:", self.active_environment_name())

    def _do_save(self) -> None:
        """Save the collection to disk."""
        from ..format import save_collection

        if self.collection.value is not None and self.path.value is not None:
            # Save to 'collections/' subfolder within workspace path
            collections_path = self.path.value / "collections"
            save_collection(self.collection.value, collections_path)


def load_workspace(folder: Path) -> Workspace | None:
    """Load a Workspace from a folder path. Returns None if folder doesn't exist."""
    from ..format import load_collection, load_environment, load_workspace_config

    if not folder.exists():
        return None

    workspace = Workspace()
    workspace.path = folder

    # Load workspace config from forc.yaml
    load_workspace_config(workspace, folder)

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

    return workspace
