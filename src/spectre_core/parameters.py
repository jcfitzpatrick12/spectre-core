# SPDX-FileCopyrightText: © 2024 Jimmy Fitzpatrick <jcfitzpatrick12@gmail.com>
# This file is part of SPECTRE
# SPDX-License-Identifier: GPL-3.0-or-later

from typing import Any, Optional, TypeVar
import json
from textwrap import dedent

from spectre_core.pconstraints import PConstraint

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
                 default: Optional[T] = None,
                 nullable: bool = False,
                 enforce_default: Optional[bool] = False,
                 help: Optional[str] = None,
                 pconstraints: Optional[list[PConstraint]] = None):
        if not callable(ptype):
            raise TypeError("ptype must be callable.")

        self._name = name
        self._ptype = ptype
        self._default = default
        self._nullable = nullable
        self._enforce_default = enforce_default
        self._help = dedent(help).strip().replace("\n", " ") if help else "No help has been provided."
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
    def default(self) -> Optional[T]:
        """The value of the parameter, if the value is unspecified."""
        return self._default
    

    @default.setter
    def default(self, value: T) -> None:
        """Update the default of a ptemplate"""
        self._default = value


    @property
    def nullable(self) -> bool:
        """Whether the value of the parameter is allowed to be of None type."""
        return self._nullable
    

    @property
    def enforce_default(self) -> bool:
        """Whether the provided default value is enforced."""
        return self._enforce_default
    

    @enforce_default.setter
    def enforce_default(self, value: bool) -> None:
        """Set whether the provided default value is enforced."""
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
            raise ValueError(f"The default value of '{self._default}' "
                             f"is required for the parameter '{self._name}'.")

        # apply existing pconstraints
        for constraint in self._pconstraints:
            try:
                constraint.constrain(value)
            except ValueError as e:
                raise ValueError(f"PConstraint '{constraint.__class__.__name__}' failed for the parameter '{self._name}': {e}")
            except Exception as e:
                raise RuntimeError(f"An unexpected error occurred while applying the pconstraint '{constraint.__class__.__name__}' to "
                                    f"'{self.name}': {e}")
        return value


    def apply_template(self, 
                       value: Optional[Any]) -> T:
        """Cast the value and constrain it according to this ptemplate."""
        if value is None:
            if self._default is not None:
                value = self._default
            elif not self._nullable:
                raise ValueError(f"The parameter '{self._name}' is not nullable, "
                                 f"but no value or default has been provided. "
                                 f"Either provide a value, or provide a default.")
            else:
                return None
        
        value = self._cast(value)
        value = self._constrain(value)
        return value


    def make_parameter(self, 
                       value: Optional[Any] = None) -> Parameter:
        value = self.apply_template(value)
        return Parameter(self._name, value)


    def to_dict(self) -> dict:
        """Convert the template to a dictionary representation."""
        return {
            "name": self._name,
            "type": str(self._ptype),
            "default": self._default,
            "enforce_default": self._enforce_default,
            "help": self._help,
            "constraints": [f"{constraint}" for constraint in self._pconstraints]
        }