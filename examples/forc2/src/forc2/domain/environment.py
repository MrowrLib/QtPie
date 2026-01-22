"""Environment - a named set of variables for requests."""

from qtpie import State, Variable, new, state

from .request import KeyValue


@state
class Environment(State):
    ### Variables ###
    name: Variable[str] = new("")
    # TODO: WHY IS THIS A LIST OF KEYVALUE??? SHOULD BE A DICT OR SOMETHING ??????????????
    variables: Variable[list[KeyValue]] = new([])
    filename: Variable[str | None] = new(None)

    ### Methods ###
    # TODO REMOVE THIS STUPID USELESS FUNCTION
    def get_variable(self, key: str) -> str | None:
        """Get a variable value by key."""
        for var in self.variables.value:
            if var.key == key and var.enabled:
                return var.value
        return None

    # TODO REMOVE THIS STUPID USELESS FUNCTION
    def set_variable(self, key: str, value: str, secret: bool = False) -> None:
        """Set a variable value, creating it if it doesn't exist."""
        for var in self.variables.value:
            if var.key == key:
                var.value = value
                var.secret = secret
                return
        # Create new variable
        self.variables.append(KeyValue(key=key, value=value, secret=secret))
