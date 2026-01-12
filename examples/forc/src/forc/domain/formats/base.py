from pathlib import Path
from typing import Protocol

from forc.domain.models import Collection, Environment, Request, Workspace


class FileFormat(Protocol):
    """Protocol for file format implementations."""

    extension: str

    def load_request(self, path: Path) -> Request:
        """Load a request from a file."""
        ...

    def save_request(self, request: Request, path: Path) -> None:
        """Save a request to a file."""
        ...

    def load_collection(self, path: Path) -> Collection:
        """Load a collection from a directory."""
        ...

    def save_collection(self, collection: Collection, path: Path) -> None:
        """Save a collection to a directory."""
        ...

    def load_environment(self, path: Path) -> Environment:
        """Load an environment from a file."""
        ...

    def save_environment(self, environment: Environment, path: Path) -> None:
        """Save an environment to a file."""
        ...

    def load_workspace(self, path: Path) -> Workspace:
        """Load a workspace from a directory."""
        ...

    def save_workspace(self, workspace: Workspace, path: Path) -> None:
        """Save a workspace to a directory."""
        ...
