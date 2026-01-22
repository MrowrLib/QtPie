"""Environment - a named set of variables for requests."""

from dataclasses import dataclass

from qtpie import State, Variable, new, state


@dataclass
class EnvironmentVariable:
    """An environment variable with optional enabled/secret flags."""

    value: str = ""
    enabled: bool = True
    secret: bool = False


@state
class Environment(State):
    ### Variables ###
    name: Variable[str] = new("")
    variables: Variable[dict[str, EnvironmentVariable]] = new({})
    filename: Variable[str | None] = new(None)
