# SPDX-FileCopyrightText: © 2024 Jimmy Fitzpatrick <jcfitzpatrick12@gmail.com>
# This file is part of SPECTRE
# SPDX-License-Identifier: GPL-3.0-or-later

from typing import Any, Optional, TypeVar
import json
from textwrap import dedent

from spectre_core.pconstraints import PConstraint

T = TypeVar('T')

class Parameter:
    """Simple container for any named value.
    
    Both the name and value are non-optional.
    """
    def __init__(self, 
                 name: str,
                 value: T):
        self._name = name
        self._value: T = value


    @property
    def name(self) -> str:
        """The parameter name."""
        return self._name
    

    @property
    def value(self) -> T:
        """The parameter value."""
        return self._value
    
    
    @value.setter
    def value(self, v: T) -> None:
        """Update the parameter value."""
        self._value = v
 

class Parameters:
    """A collection of parameters."""
    def __init__(self):
        self._dict: dict[str, Parameter] = {}
    

    @property
    def name_list(self) -> list[str]:
        """List the names of stored parameters."""
        return list(self._dict.keys())


    def add_parameter(self, 
                      name: str,
                      value: T) -> None:
        """Add a new parameter."""
        if name in self._dict:
            raise ValueError(f"Parameter with name {name} already exists. "
                             f"Cannot add to parameters.")
        parameter = Parameter(name, value)
        self._dict[parameter.name] = parameter


    def get_parameter(self, 
                      name: str) -> Parameter:
        """Get the parameter with the corresponding name."""
        if name not in self._dict:
            raise KeyError(f"Parameter with name '{name}' does not exist. "
                           f"Expected one of {self.name_list}")      
        return self._dict[name]


    def get_parameter_value(self,
                            name: str) -> T:
        """Get the value of the parameter with the corresponding name."""
        parameter = self.get_parameter(name)
        return parameter.value 


    def __iter__(self):
        """Iterate over stored parameters"""
        yield from self._dict.values() 
    


def parse_string_parameter(string_parameter: str) -> list[str]:
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
        k, v = parse_string_parameter(string_parameter)
        d[k] = v
    return d
    

def make_parameters(d: dict[str, Any]):
    """Make an instance of parameters based on the input dictionary"""
    parameters = Parameters()
    for k, v in d.items():
        parameters.add_parameter(k, v)
    return parameters

class PTemplate:
    """A parameter template. 
    
    Constrain the value and type that a parameter can take.
    """
    def __init__(self,
                 name: str,
                 ptype: T,
                 default: T,
                 enforce_default: Optional[bool] = False,
                 help: Optional[str] = None,
                 pconstraints: Optional[list[PConstraint]] = None):
        if not callable(ptype):
            raise TypeError("ptype must be callable.")

        self._name = name
        self._ptype = ptype
        self.default = default
        self._enforce_default = enforce_default
        self._help = dedent(help).strip() if help else "No help has been provided."
        self._pconstraints: list[PConstraint] = pconstraints or []


    @property
    def name(self) -> str:
        """The name of the parameter."""
        return self._name
    

    @property
    def ptype(self) -> T:
        """The parameter type."""
        return self._ptype
    

    @property
    def default(self) -> T:
        """The value of the parameter, if the value is unspecified."""
        return self._default
    

    @default.setter
    def default(self, value: T) -> None:
        """Update the default of a ptemplate"""
        self._default = value


    @property
    def enforce_default(self) -> bool:
        """Whether the default value is enforced."""
        return self._enforce_default
    

    @enforce_default.setter
    def enforce_default(self, value: bool) -> None:
        self._enforce_default = value
    

    @property
    def help(self) -> str:
        """A description of what the parameter is, and the value it stores."""
        return self._help
    
    
    def add_pconstraint(self,
                        pconstraint: PConstraint) -> None:
        self._pconstraints.append(pconstraint)


    def _cast(self, 
              value: Any) -> T:
        """Cast the input value to the ptype of this template"""
        try:
            return self._ptype(value)
        except (TypeError, ValueError) as e:
            raise ValueError(f"Could not cast '{value}' to '{self._ptype.__name__}': {e}")


    def _constrain(self, 
                   value: T) -> T:
        """Constrain the input value according to constraints of the template."""
        if self._enforce_default and value != self._default:
            raise ValueError(f"The default value of '{self._default}' is required for the parameter '{self._name}'.")
        
        for constraint in self._pconstraints:
            try:
                constraint.constrain(value)
            except ValueError as e:
                raise ValueError(f"Constraint '{constraint.__class__.__name__}' failed for the parameter '{self._name}': {e}")
            except Exception as e:
                print(f"An unexpected error occurred while constraining '{self.name}': {e}")
                raise
        return value


    def apply_template(self, 
                       value: Optional[Any]) -> T:
        """Cast the value and constrain it according to this ptemplate."""
        if value is None:
            value = self._default
        
        value = self._cast(value)
        value = self._constrain(value)
        return value

    def make_parameter(self, 
                       value: Optional[Any] = None) -> Parameter:
        value = self.apply_template(value)
        return Parameter(self._name, value)


    def to_dict(self) -> dict[str, Any]:
        """Convert the template to a dictionary representation."""
        return {
            "name": self._name,
            "type": self._ptype.__name__ if hasattr(self._ptype, '__name__') else str(self._ptype),
            "default": self._default,
            "enforce_default": self._enforce_default,
            "help": self._help,
            "constraints": [f"{constraint}" for constraint in self._pconstraints]
        }


    def pretty_print(self) -> str:
        """Return a JSON-formatted string representation of the template."""
        return json.dumps(self.to_dict(), indent=4)