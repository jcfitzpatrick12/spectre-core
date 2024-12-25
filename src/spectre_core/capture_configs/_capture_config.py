# SPDX-FileCopyrightText: © 2024 Jimmy Fitzpatrick <jcfitzpatrick12@gmail.com>
# This file is part of SPECTRE
# SPDX-License-Identifier: GPL-3.0-or-later

from dataclasses import dataclass

from spectre_core._file_io import JsonHandler
from spectre_core.config import get_configs_dir_path
from spectre_core.exceptions import InvalidTagError
from ._parameters import (
    Parameter, 
    Parameters,
    make_parameters
)

@dataclass
class _CaptureConfigKeys:
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
        return self.dict[_CaptureConfigKeys.RECEIVER_NAME]
    

    @property
    def receiver_mode(self) -> str:
        """The mode of the receiver which created the capture config."""
        return self.dict[_CaptureConfigKeys.RECEIVER_MODE]
    

    @property
    def parameters(self) -> Parameters:
        """The parameters stored inside the capture config."""
        return make_parameters( self.dict[_CaptureConfigKeys.PARAMETERS] )


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
            _CaptureConfigKeys.RECEIVER_MODE: receiver_mode,
            _CaptureConfigKeys.RECEIVER_NAME: receiver_name,
            _CaptureConfigKeys.PARAMETERS   : parameters.to_dict()
        }
        self.save(d,
                  force=force)