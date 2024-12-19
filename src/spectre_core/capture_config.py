# SPDX-FileCopyrightText: © 2024 Jimmy Fitzpatrick <jcfitzpatrick12@gmail.com>
# This file is part of SPECTRE
# SPDX-License-Identifier: GPL-3.0-or-later

from dataclasses import dataclass

from spectre_core.paths import get_configs_dir_path
from spectre_core.exceptions import InvalidTagError
from spectre_core.file_handlers.json import JsonHandler
from spectre_core.parameters import (
    PTemplate, 
    Parameter,
    Parameters, 
    make_parameters,
)


@dataclass
class CaptureConfigKeys:
    TAG           = "tag"
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
        """The name of the receiver which created this capture config."""
        return self.dict[CaptureConfigKeys.RECEIVER_NAME]
    

    @property
    def receiver_mode(self) -> str:
        """The mode of the receiver which created this capture config."""
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
            CaptureConfigKeys.TAG: self.tag,
            CaptureConfigKeys.RECEIVER_MODE: receiver_mode,
            CaptureConfigKeys.RECEIVER_NAME: receiver_name,
            CaptureConfigKeys.PARAMETERS: {parameter.name: parameter.value for parameter in parameters}
        }
        self.save(d,
                  force=force)


class CaptureTemplate:
    """A managed collection of PTemplates"""
    def __init__(self):
        self._dict: dict[str, PTemplate] = {}


    @property
    def name_list(self) -> list[str]:
        """List the names of all stored PTemplates."""
        return list(self._dict.keys())
    

    def add_ptemplate(self,
                      ptemplate: PTemplate) -> None:
        """Add a ptemplate to this capture template."""
        self._dict[ptemplate.name] = ptemplate


    def get_ptemplate(self,
                      parameter_name: str) -> PTemplate:
        """Get the ptemplate corresponding with the parameter name."""
        if parameter_name not in self._dict:
            raise ValueError(f"Parameter with name '{parameter_name}' is not found in the template. "
                             f"Expected one of {self.name_list}")   
        return self._dict[parameter_name]
      

    def __cast_and_constrain_parameter(self,
                                      parameter: Parameter):
        """Validate a parameter against the corresponding ptemplate"""
        ptemplate = self.get_ptemplate(parameter.name)
        parameter.value = ptemplate.cast_and_constrain(parameter.value)


    def __cast_and_constrain_parameters(self,
                                        parameters: Parameters) -> None:
        """Explicity cast and constrain all explictly specified parameters"""
        for parameter in parameters:
            self.__cast_and_constrain_parameter(parameter)

    
    def __fill_missing_with_defaults(self,
                                     parameters: Parameters) -> None:
        """For any missing parameters (as per the capture template), use the corresponding default value."""
        for ptemplate in self:
            if ptemplate.name not in parameters.name_list:
                parameter = ptemplate.make_parameter()
                parameters.add_parameter(parameter.name, 
                                         parameter.value)


    def apply_template(self,
                       parameters: Parameters) -> None:
        """Validate parameters, fill missing with defaults, and return anew."""
        self.__cast_and_constrain_parameters(parameters)
        self.__fill_missing_with_defaults(parameters)
        return parameters


    def __iter__(self):
        """Iterate over stored ptemplates"""
        yield from self._dict.values()





