# SPDX-FileCopyrightText: © 2024 Jimmy Fitzpatrick <jcfitzpatrick12@gmail.com>
# This file is part of SPECTRE
# SPDX-License-Identifier: GPL-3.0-or-later

from typing import Any, Optional, TypeVar

T = TypeVar('T')

class Parameter:
    """A named value."""
    def __init__(self, 
                 name: str,
                 value: Optional[T] = None):
        self._name = name
        self._value: Optional[T] = value


    @property
    def name(self) -> str:
        """The parameter name."""
        return self._name
    

    @property
    def value(self) -> Optional[T]:
        """The parameter value."""
        return self._value
    
    
    @value.setter
    def value(self, v: Optional[T]) -> None:
        """Update the parameter value."""
        self._value = v


class Parameters:
    """A collection of parameters."""
    def __init__(self):
        self._parameters: dict[str, Parameter] = {}
    

    @property
    def name_list(self) -> list[str]:
        """List the names of stored parameters."""
        return list(self._parameters.keys())


    def add_parameter(self, 
                      name: str,
                      value: Optional[T] = None,
                      force: bool = False) -> None:
        """Add a new parameter."""
        if name in self._parameters and not force:
            raise ValueError(f"Cannot add a parameter with name '{name}', "
                             f"since a parameter already exists with that name. "
                             f"You can overrride this functionality with 'force', "
                             f"to overwrite the existing parameter.")
        self._parameters[name] = Parameter(name, value)


    def get_parameter(self, 
                      name: str) -> Parameter:
        """Get the parameter with the corresponding name."""
        if name not in self._parameters:
            raise KeyError(f"Parameter with name '{name}' does not exist. "
                           f"Expected one of {self.name_list}")      
        return self._parameters[name]


    def get_parameter_value(self,
                            name: str) -> Optional[T]:
        """Get the value of the parameter with the corresponding name."""
        return self.get_parameter(name).value
    

    def __iter__(self):
        """Iterate over stored parameters"""
        yield from self._parameters.values() 

    
    def to_dict(self) -> dict:
        """Convert the class instance to an equivalent dictionary representation"""
        return {p.name: p.value for p in self}
    
def _parse_string_parameter(string_parameter: str) -> list[str]:
    """Parse string of the form 'a=b; into a list of the form [a, b]"""
    if not string_parameter or '=' not in string_parameter:
        raise ValueError(f"Invalid format: '{string_parameter}'. Expected 'KEY=VALUE'.")
    if string_parameter.startswith('=') or string_parameter.endswith('='):
        raise ValueError(f"Invalid format: '{string_parameter}'. Expected 'KEY=VALUE'.")
    # remove leading and trailing whitespace.
    string_parameter = string_parameter.strip()
    return string_parameter.split('=', 1)
    

def parse_string_parameters(string_parameters: list[str]) -> dict[str, str]:
    """Parses a list of strings of the form 'a=b'; into a dictionary mapping each 'a' to each 'b'"""
    d = {}
    for string_parameter in string_parameters:
        k, v = _parse_string_parameter(string_parameter)
        d[k] = v
    return d
    

def make_parameters(d: dict[str, Any]):
    """Make an instance of parameters based on the input dictionary"""
    parameters = Parameters()
    for k, v in d.items():
        parameters.add_parameter(k, v)
    return parameters