# SPDX-FileCopyrightText: © 2024 Jimmy Fitzpatrick <jcfitzpatrick12@gmail.com>
# This file is part of SPECTRE
# SPDX-License-Identifier: GPL-3.0-or-later

from typing import Any, Optional, TypeVar, Generic, Iterator

from ._pnames import PNames

VT = TypeVar('VT')

class Parameter(Generic[VT]):
    """A simple container for a named value."""
    def __init__(self, 
                 name: PNames,
                 value: Optional[VT] = None):
        self._name = name
        self._value: Optional[VT] = value


    @property
    def name(self) -> PNames:
        """The parameter name."""
        return self._name
    

    @property
    def value(self) -> Optional[VT]:
        """The parameter value."""
        return self._value
    
    
    @value.setter
    def value(self, v: Optional[VT]) -> None:
        """Update the parameter value."""
        self._value = v


class Parameters:
    """A managed collection of parameters."""
    def __init__(self) -> None:
        """Initialise a `Parameters` instance.
        """
        self._parameters: dict[PNames, Parameter] = {}
    
    
    @property
    def name_list(self) -> list[PNames]:
        """List the names of stored parameters."""
        return list(self._parameters.keys())


    def add_parameter(self, 
                      name: PNames,
                      value: Optional[VT]) -> None:
        """Add a `Parameter` instance to this `Parameters` instance with the input name and value.

        Arguments:
            name -- The name of the parameter.
            value -- The value of the parameter.

        Raises:
            KeyError: If a parameter already exists under the input name.
        """
        if name in self._parameters:
            raise KeyError(f"Cannot add a parameter with name '{name}', "
                           f"since a parameter already exists with that name. ")
        self._parameters[name] = Parameter(name, value)


    def get_parameter(self, 
                      name: PNames) -> Parameter:
        """Get the stored `Parameter` instance corresponding to the input name.

        Arguments:
            name -- The name of the parameter.

        Raises:
            KeyError: If a parameter with the input name does not exist.

        Returns:
            A `Parameter` instance with the input name, if it exists.
        """
        if name not in self._parameters:
            raise KeyError(f"Parameter with name '{name}' does not exist. "
                           f"Expected one of {self.name_list}")      
        return self._parameters[name]


    def get_parameter_value(self,
                            name: PNames) -> Optional[VT]:
        """Get the value of the parameter with the corresponding name.

        Arguments:
            name -- The name of the parameter

        Returns:
            The value of the parameter with the input name.
        """
        return self.get_parameter(name).value
    

    def __iter__(self) -> Iterator[Parameter]:
        """Iterate over stored parameters."""
        yield from self._parameters.values() 

    
    def to_dict(self) -> dict[str, Optional[Any]]:
        """Convert the `Parameters` instance to an equivalent dictionary representation."""
        return {p.name.value: p.value for p in self}
    

def _parse_string_parameter(
    string_parameter: str
) -> list[str]:
    """Parse string of the form `a=b`; into a list of the form `[a, b]`

    Arguments:
        string_parameter -- A string representation of a capture configuration parameter.

    Raises:
        ValueError: If the input parameter is not of the form `a=b`

    Returns:
        The parsed components of the input string parameter, using the `=` character as a seperator.
    """
    if not string_parameter or '=' not in string_parameter:
        raise ValueError(f"Invalid format: '{string_parameter}'. Expected 'KEY=VALUE'.")
    if string_parameter.startswith('=') or string_parameter.endswith('='):
        raise ValueError(f"Invalid format: '{string_parameter}'. Expected 'KEY=VALUE'.")
    # remove leading and trailing whitespace.
    string_parameter = string_parameter.strip()
    return string_parameter.split('=', 1)
    
    
def parse_string_parameters(
    string_parameters: list[str]
) -> dict[str, str]:
    """Parses a list of strings of the form `a=b`; into a dictionary mapping each `a` to each `b`

    Arguments:
        string_parameters -- A list of strings, where each element is of the form `a=b`

    Returns:
        A dictionary mapping each `a` to each `b`, after parsing each element.
    """
    d = {}
    for string_parameter in string_parameters:
        k, v = _parse_string_parameter(string_parameter)
        d[k] = v
    return d
    

def make_parameters(
    d: dict[str, Any]
) -> Parameters:
    """Create a `Parameters` instance from the given dictionary.

    Args:
        d -- A dictionary where keys represent parameter names and values represent their corresponding values.

    Returns:
        An instance of `Parameters` with each key-value pair in `d` added as a parameter..
    """
    parameters = Parameters()
    for k, v in d.items():
        parameters.add_parameter(PNames(k), v)
    return parameters