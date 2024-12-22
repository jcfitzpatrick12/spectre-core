# SPDX-FileCopyrightText: © 2024 Jimmy Fitzpatrick <jcfitzpatrick12@gmail.com>
# This file is part of SPECTRE
# SPDX-License-Identifier: GPL-3.0-or-later

from dataclasses import dataclass
from typing import Any

from spectre_core.paths import get_configs_dir_path
from spectre_core.exceptions import InvalidTagError
from spectre_core.file_handlers.json import JsonHandler
from spectre_core.pconstraints import PConstraint
from spectre_core.parameters import (
    PTemplate, 
    Parameter,
    Parameters, 
    make_parameters,
)


@dataclass
class CaptureConfigKeys:
    RECEIVER_NAME = "receiver_name"
    RECEIVER_MODE = "receiver_mode"
    PARAMETERS    = "parameters"


class CaptureConfig(JsonHandler):
    def __init__(self,
                 tag: str):
        self._validate_tag(tag)
        self._tag = tag
        super().__init__(get_configs_dir_path(),
                         f"capture_{tag}")
        
    @property
    def tag(self) -> str:
        """Unique identifier for the capture config."""
        return self._tag


    def _validate_tag(self, 
                      tag: str) -> None:
        if "_" in tag:
            raise InvalidTagError(f"Tags cannot contain an underscore. Received {tag}")
        if "callisto" in tag:
            raise InvalidTagError(f'"callisto" cannot be a substring in a native tag. Received "{tag}"')
    

    @property
    def receiver_name(self) -> str:
        """The name of the receiver which created the capture config."""
        return self.dict[CaptureConfigKeys.RECEIVER_NAME]
    

    @property
    def receiver_mode(self) -> str:
        """The mode of the receiver which created the capture config."""
        return self.dict[CaptureConfigKeys.RECEIVER_MODE]
    

    @property
    def parameters(self) -> Parameters:
        """The parameters stored inside the capture config."""
        return make_parameters( self.dict[CaptureConfigKeys.PARAMETERS] )


    def get_parameter(self, 
                      name: str) -> Parameter:
        return self.parameters.get_parameter(name)
    

    def get_parameter_value(self,
                            name: str) -> Parameter:
        return self.parameters.get_parameter_value(name)


    def save_parameters(self,
                        receiver_name: str,
                        receiver_mode: str,
                        parameters: Parameters,
                        force: bool = False):
        """Write the input parameters to file."""
        d = {
            CaptureConfigKeys.RECEIVER_MODE: receiver_mode,
            CaptureConfigKeys.RECEIVER_NAME: receiver_name,
            CaptureConfigKeys.PARAMETERS   : parameters.to_dict()
        }
        self.save(d,
                  force=force)


    def to_dict(self) -> dict:
        """Convert the instance to a dictionary representation."""
        return {
            "tag": self.tag,
            "receiver_name": self.receiver_name,
            "receiver_mode": self.receiver_mode,
            "parameters": self.parameters.to_dict()
        }
    

class CaptureTemplate:
    """A managed collection of PTemplates"""
    def __init__(self):
        self._ptemplates: dict[str, PTemplate] = {}


    @property
    def name_list(self) -> list[str]:
        """List the names of all stored PTemplates."""
        return list(self._ptemplates.keys())
    

    def add_ptemplate(self,
                      ptemplate: PTemplate) -> None:
        """Add a ptemplate to this capture template."""
        self._ptemplates[ptemplate.name] = ptemplate


    def get_ptemplate(self,
                      parameter_name: str) -> PTemplate:
        """Get the ptemplate corresponding with the parameter name."""
        if parameter_name not in self._ptemplates:
            raise ValueError(f"Parameter with name '{parameter_name}' is not found in the template. "
                             f"Expected one of {self.name_list}")   
        return self._ptemplates[parameter_name]
      

    def __apply_parameter_template(self,
                                   parameter: Parameter):
        """Apply the corresponding parameter template to the input parameter"""
        ptemplate = self.get_ptemplate(parameter.name)
        parameter.value = ptemplate.apply_template(parameter.value)


    def __apply_parameter_templates(self,
                                    parameters: Parameters) -> None:
        """Apply the corresponding parameter template to all explictly specified parameters"""
        for parameter in parameters:
            self.__apply_parameter_template(parameter)

    
    def __fill_missing_with_defaults(self,
                                     parameters: Parameters) -> None:
        """For any missing parameters (as per the capture template), use the corresponding default value."""
        for ptemplate in self:
            if ptemplate.name not in parameters.name_list:
                parameter = ptemplate.make_parameter()
                parameters.add_parameter(parameter.name, 
                                         parameter.value)


    def apply_template(self,
                       parameters: Parameters) -> Parameters:
        """Validate parameters, fill missing with defaults, and return anew."""
        self.__apply_parameter_templates(parameters)
        self.__fill_missing_with_defaults(parameters)
        return parameters


    def __iter__(self):
        """Iterate over stored ptemplates"""
        yield from self._ptemplates.values() 


    def set_default(self, 
                    parameter_name: str, 
                    default: Any) -> None:
        """Set the default of an existing ptemplate."""
        self.get_ptemplate(parameter_name).default = default


    def set_defaults(self, 
                     *ptuples: tuple[str, Any]) -> None:
        """Update defaults for multiple ptemplates."""
        for (parameter_name, default) in ptuples:
            self.set_default(parameter_name, default)


    def enforce_default(self,
                        parameter_name: str) -> None:
        """Enforce the default of an existing ptemplate"""
        self.get_ptemplate(parameter_name).enforce_default = True


    def enforce_defaults(self, 
                         *parameter_names: str) -> None:
        """Enforce defaults for multiple parameter names."""
        for name in parameter_names:
            self.enforce_default(name)


    def add_pconstraint(self,
                        parameter_name: str,
                        pconstraints: list[PConstraint]) -> None:
        """Add a pconstraint to an existing ptemplate"""
        for pconstraint in pconstraints:
            self.get_ptemplate(parameter_name).add_pconstraint(pconstraint)


    def to_dict(self) -> dict:
        return {ptemplate.name: ptemplate.to_dict() for ptemplate in self}
