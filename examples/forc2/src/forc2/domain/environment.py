"""Environment - a named set of variables for requests."""

from dataclasses import dataclass

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
