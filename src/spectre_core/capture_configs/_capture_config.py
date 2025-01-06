# SPDX-FileCopyrightText: © 2024 Jimmy Fitzpatrick <jcfitzpatrick12@gmail.com>
# This file is part of SPECTRE
# SPDX-License-Identifier: GPL-3.0-or-later

from dataclasses import dataclass
from typing import Optional

from spectre_core._file_io import JsonHandler
from spectre_core.config import get_configs_dir_path
from spectre_core.exceptions import InvalidTagError
from ._ptemplates import PName
from ._parameters import (
    Parameter, 
    Parameters,
    make_parameters
)

@dataclass(frozen=True)
class _CaptureConfigKey:
    """Defined JSON keys for capture configuration files."""
    RECEIVER_NAME = "receiver_name"
    RECEIVER_MODE = "receiver_mode"
    PARAMETERS    = "parameters"


class CaptureConfig(JsonHandler):
    """Simple IO interface for a capture configuration file under a particular tag"""
    def __init__(self,
                 tag: str) -> None:
        """Initialise an instance of `CaptureConfig`.

        :param tag: The tag identifier for the capture configuration file.
        """
        self._validate_tag(tag)
        self._tag = tag
        super().__init__(get_configs_dir_path(),
                         f"capture_{tag}")
        
    @property
    def tag(self) -> str:
        """The tag identifier for the capture configuration file."""
        return self._tag


    def _validate_tag(self, 
                      tag: str) -> None:
        """Validate the tag of the capture configuration files.
        
        Some substrings are reserved for externally generated batch files.
        """
        if "_" in tag:
            raise InvalidTagError(f"Tags cannot contain an underscore. Received {tag}")
        if "callisto" in tag:
            raise InvalidTagError(f"'callisto' cannot be a substring in a capture config tag. "
                                  f"Received '{tag}'")
    

    @property
    def receiver_name(self) -> str:
        """The name of the receiver to be used for capture."""
        d = self.read()
        return d[_CaptureConfigKey.RECEIVER_NAME]
    

    @property
    def receiver_mode(self) -> str:
        """The operating mode for the receiver to be used for capture."""
        d = self.read()
        return d[_CaptureConfigKey.RECEIVER_MODE]
    

    @property
    def parameters(self) -> Parameters:
        """The user-configured parameters provided to the receiver at the time of capture"""
        d = self.read()
        return make_parameters( d[_CaptureConfigKey.PARAMETERS] )


    def get_parameter(self, 
                      name: PName) -> Parameter:
        """Get a parameter stored by the capture config.

        :param name: The name of the parameter.
        :return: A `Parameter` instance with `name` and `value` retrieved from the capture
                configuration file.
        """
        return self.parameters.get_parameter(name)
    

    def get_parameter_value(self,
                            name: PName) -> Optional[Parameter]:
        """Get the value of a parameter stored by the capture config.

        :param name: The name of the parameter.
        :return: The value of the parameter corresponding to `name`.
        """
        return self.parameters.get_parameter_value(name)


    def save_parameters(self,
                        receiver_name: str,
                        receiver_mode: str,
                        parameters: Parameters,
                        force: bool = False):
        """Write the input parameters to a capture configuration file.

        :param receiver_name: The name of the receiver to be used for capture.
        :param receiver_mode: The operating mode for the receiver to be used for capture.
        :param parameters: The user-configured parameters provided to the receiver at the time of capture.
        :param force: If true, force the write if the file already exists in the file system. Defaults to False.
        """
        d = {
            _CaptureConfigKey.RECEIVER_MODE: receiver_mode,
            _CaptureConfigKey.RECEIVER_NAME: receiver_name,
            _CaptureConfigKey.PARAMETERS   : parameters.to_dict()
        }
        self.save(d,
                  force=force)