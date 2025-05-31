# SPDX-FileCopyrightText: © 2024-2025 Jimmy Fitzpatrick <jcfitzpatrick12@gmail.com>
# This file is part of SPECTRE
# SPDX-License-Identifier: GPL-3.0-or-later

from typing import Any, Optional, TypeVar, Generic, Iterator, overload, cast

from ._pnames import PName

# value type
VT = TypeVar("VT")


class Parameter(Generic[VT]):
    """A simple container for a named value."""

    def __init__(self, name: PName, value: Optional[VT] = None) -> None:
        """Initialise a `Parameter` instance.

        :param name: The name of the parameter.
        :param value: The value of the parameter. Defaults to None.
        """
        self._name = name
        self._value: Optional[VT] = value

    @property
    def name(self) -> PName:
        """The parameter name."""
        return self._name

    @property
    def value(self) -> Optional[VT]:
        """The parameter value."""
        return self._value

    @value.setter
    def value(self, v: Optional[VT]) -> None:
        """Update the parameter value.

        :param v: The new value to set for the parameter.
        """
        self._value = v


class Parameters:
    """A managed collection of parameters."""

    def __init__(self) -> None:
        """Initialise a `Parameters` instance."""
        self._parameters: dict[PName, Parameter] = {}

    @property
    def name_list(self) -> list[PName]:
        """List the names of stored parameters."""
        return list(self._parameters.keys())

    def add_parameter(self, name: PName, value: Optional[VT]) -> None:
        """Add a `Parameter` instance to this `Parameters` instance with the input name and value.

        :param name: The name of the parameter.
        :param value: The value of the parameter.
        :raises KeyError: If a parameter already exists under the input name.
        """
        if name in self._parameters:
            raise KeyError(
                f"Cannot add a parameter with name '{name}', "
                f"since a parameter already exists with that name. "
            )
        self._parameters[name] = Parameter(name, value)

    def get_parameter(self, name: PName) -> Parameter:
        """Get the stored `Parameter` instance corresponding to the input name.

        :param name: The name of the parameter.
        :raises KeyError: If a parameter with the input name does not exist.
        :return: A `Parameter` instance with the input name, if it exists.
        """
        if name not in self._parameters:
            raise KeyError(
                f"Parameter with name '{name}' does not exist. "
                f"Expected one of {self.name_list}"
            )
        return self._parameters[name]

    def get_parameter_value(self, name: PName) -> Optional[VT]:
        """Get the value of the parameter with the corresponding name.

        :param name: The name of the parameter.
        :return: The value of the parameter with the input name.
        """
        return self.get_parameter(name).value

    def __iter__(self) -> Iterator[Parameter]:
        """Iterate over stored parameters."""
        yield from self._parameters.values()

    def to_dict(self) -> dict[str, Optional[Any]]:
        """Convert the `Parameters` instance to a serialisable dictionary.

        :return: A dictionary representation of the stored parameters.
        """
        return {p.name.value: p.value for p in self}


def _parse_string_parameter(string_parameter: str) -> list[str]:
    """Parse string of the form `a=b` into a list of the form `[a, b]`.

    :param string_parameter: A string representation of a capture config parameter.
    :raises ValueError: If the input parameter is not of the form `a=b`.
    :return: The parsed components of the input string parameter, using the `=` character as a separator.
    The return list will always contain two elements.
    """
    if not string_parameter or "=" not in string_parameter:
        raise ValueError(f"Invalid format: '{string_parameter}'. Expected 'KEY=VALUE'.")
    if string_parameter.startswith("=") or string_parameter.endswith("="):
        raise ValueError(f"Invalid format: '{string_parameter}'. Expected 'KEY=VALUE'.")
    # remove leading and trailing whitespace.
    string_parameter = string_parameter.strip()
    return string_parameter.split("=", 1)


def parse_string_parameters(string_parameters: list[str]) -> dict[str, str]:
    """Parses a list of strings of the form `a=b` into a dictionary mapping each `a` to each `b`.

    :param string_parameters: A list of strings, where each element is of the form `a=b`.
    :return: A dictionary mapping each `a` to each `b`, after parsing each element.
    """
    d = {}
    for string_parameter in string_parameters:
        k, v = _parse_string_parameter(string_parameter)
        d[k] = v
    return d


def make_parameters(d: dict[str, Any]) -> Parameters:
    """Create a `Parameters` instance from the given dictionary. Each key is interpreted as a valid `PName`.

    :param d: A dictionary where keys represent parameter names and values represent their corresponding values.
    :return: An instance of `Parameters` with each key-value pair in `d` added as a parameter.
    """
    parameters = Parameters()
    for k, v in d.items():
        parameters.add_parameter(PName(k), v)
    return parameters
