"""Environment - a named set of variables for requests."""

from dataclasses import dataclass
from pathlib import Path

from qtpie import State, Var, new, state


@dataclass
class EnvironmentVariable:
    """An environment variable with optional enabled/secret flags."""

    value: str = ""
    enabled: bool = True
    secret: bool = False


@state
class Environment(State):
    ### Variables ###
    name: Var[str] = new("")
    variables: Var[dict[str, EnvironmentVariable]] = new({})
    filename: Var[str | None] = new(None)

    ### Methods ###
    def _get_full_path(self) -> Path | None:
        """Walk state_parent chain to build full path to this environment."""
        from .workspace import Workspace

        current: State | None = self.state_parent
        while current is not None:
            if isinstance(current, Workspace) and current.path.value:
                filename = self.filename.value or self.name.value
                return current.path.value / "environments" / f"{filename}.yaml"
            current = current.state_parent
        return None

    def save(self, path: Path | None = None) -> None:
        """Save this environment to disk.

        If path is not provided, walks the state_parent chain to determine it.
        """
        from ..format import save_environment

        if path is None:
            path = self._get_full_path()
        if path:
            path.parent.mkdir(parents=True, exist_ok=True)
            save_environment(self, path)
