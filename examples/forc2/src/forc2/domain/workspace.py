# pyright: reportUnknownVariableType=false
"""Workspace - the root state that holds a collection and its path."""

from pathlib import Path

from qtpie import Event, State, Variable, new, state

from .collection import Collection
from .environment import Environment


@state(on_save="_do_save")
class Workspace(State):
    ### Variables ###
    name: Variable[str] = new("")
    collection: Variable[Collection | None] = new(None)
    environments: Variable[list[Environment]] = new([])
    active_environment: Variable[str | None] = new(None, onChange="_on_active_environment_changed")
    path: Variable[Path | None] = new(None, onChange="_on_path_changed")

    ### Events ###
    on_save: Event  # Fires to trigger save

    ### Methods ###
    def _on_active_environment_changed(self) -> None:
        print("On active environment changed to:", self.active_environment())

    def _on_path_changed(self) -> None:
        """Load or unload collection and environments when path changes."""
        from ..format import load_collection, load_environment, load_workspace_config

        path = self.path.value
        if path is None or not path.exists():
            if self.collection() is not None:
                self.collection = None
            if self.environments():
                self.environments.value = []
            self.name.value = ""
            self.active_environment.value = None
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
            self.environments.value = envs

        # print out the active environment after loading
        print("Loaded environments. Active environment is:", self.active_environment())

    # TODO REMOVE THIS STUPID USELESS FUNCTION
    def get_environment(self, name: str) -> Environment | None:
        """Get an environment by name."""
        for env in self.environments.value:
            if env.name.value == name:
                return env
        return None

    # TODO REMOVE THIS STUPID USELESS FUNCTION
    def get_active_environment(self) -> Environment | None:
        """Get the currently active environment."""
        if self.active_environment.value:
            return self.get_environment(self.active_environment.value)
        return None

    def _do_save(self) -> None:
        """Save the collection to disk."""
        from ..format import save_collection

        if self.collection.value is not None and self.path.value is not None:
            # Save to 'collections/' subfolder within workspace path
            collections_path = self.path.value / "collections"
            save_collection(self.collection.value, collections_path)
