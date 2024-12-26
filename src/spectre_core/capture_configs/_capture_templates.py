# SPDX-FileCopyrightText: © 2024 Jimmy Fitzpatrick <jcfitzpatrick12@gmail.com>
# This file is part of SPECTRE
# SPDX-License-Identifier: GPL-3.0-or-later

from copy import deepcopy
from typing import Any
from dataclasses import dataclass

from ._parameters import Parameter, Parameters
from ._pconstraints import PConstraint
from ._ptemplates import (
    PTemplate, 
    PNames,
    get_base_ptemplate
)

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


def make_base_capture_template(*parameter_names: str):
    """Make a capture template, composed entirely of base ptemplates."""
    capture_template = CaptureTemplate()
    for name in parameter_names:
        capture_template.add_ptemplate( get_base_ptemplate(name) )
    return capture_template


@dataclass(frozen=True)
class CaptureModes:
    """Pre-defined capture types"""
    FIXED_CENTER_FREQUENCY: str = "fixed-center-frequency"
    SWEPT_CENTER_FREQUENCY: str = "swept-center-frequency"


def _make_fixed_frequency_capture_template(
) -> CaptureTemplate:
    """The absolute minimum required parameters for any fixed frequency capture template."""
    capture_template = make_base_capture_template(
        PNames.BATCH_SIZE,
        PNames.CENTER_FREQUENCY,
        PNames.CHUNK_KEY,
        PNames.EVENT_HANDLER_KEY,
        PNames.FREQUENCY_RESOLUTION,
        PNames.INSTRUMENT,
        PNames.OBS_ALT,
        PNames.OBS_LAT,
        PNames.OBS_LON,
        PNames.OBJECT,
        PNames.ORIGIN,
        PNames.SAMPLE_RATE,
        PNames.TELESCOPE,
        PNames.TIME_RANGE,
        PNames.TIME_RESOLUTION,
        PNames.WATCH_EXTENSION,
        PNames.WINDOW_HOP,
        PNames.WINDOW_SIZE,
        PNames.WINDOW_TYPE,
    )
    capture_template.set_defaults(
            (PNames.EVENT_HANDLER_KEY,     CaptureModes.FIXED_CENTER_FREQUENCY),
            (PNames.CHUNK_KEY,             CaptureModes.FIXED_CENTER_FREQUENCY),
            (PNames.WATCH_EXTENSION,       "bin")
    )
    capture_template.enforce_defaults(
        PNames.EVENT_HANDLER_KEY,
        PNames.CHUNK_KEY,
        PNames.WATCH_EXTENSION
    )
    return capture_template

def _make_swept_frequency_capture_template(
) -> CaptureTemplate:
    """The absolute minimum required parameters for any swept frequency capture template."""
    capture_template = make_base_capture_template(
        PNames.BATCH_SIZE,
        PNames.CHUNK_KEY,
        PNames.EVENT_HANDLER_KEY,
        PNames.FREQUENCY_RESOLUTION,
        PNames.FREQUENCY_STEP,
        PNames.INSTRUMENT,
        PNames.MAX_FREQUENCY,
        PNames.MIN_FREQUENCY,
        PNames.OBS_ALT,
        PNames.OBS_LAT,
        PNames.OBS_LON,
        PNames.OBJECT,
        PNames.ORIGIN,
        PNames.SAMPLE_RATE,
        PNames.SAMPLES_PER_STEP,
        PNames.TELESCOPE,
        PNames.TIME_RANGE,
        PNames.TIME_RESOLUTION,
        PNames.WATCH_EXTENSION,
        PNames.WINDOW_HOP,
        PNames.WINDOW_SIZE,
        PNames.WINDOW_TYPE)
    capture_template.set_defaults(
            (PNames.EVENT_HANDLER_KEY,     CaptureModes.SWEPT_CENTER_FREQUENCY),
            (PNames.CHUNK_KEY,             CaptureModes.SWEPT_CENTER_FREQUENCY),
            (PNames.WATCH_EXTENSION,       "bin")
    )
    capture_template.enforce_defaults(
        PNames.EVENT_HANDLER_KEY,
        PNames.CHUNK_KEY,
        PNames.WATCH_EXTENSION
    )
    return capture_template


_base_capture_templates = {
    CaptureModes.FIXED_CENTER_FREQUENCY: _make_fixed_frequency_capture_template(),
    CaptureModes.SWEPT_CENTER_FREQUENCY: _make_swept_frequency_capture_template()
}

def get_base_capture_template(
       capture_mode: str
) -> CaptureTemplate:
    """Create a fresh deep copy of a pre-defined capture template"""
    if capture_mode not in _base_capture_templates:
        raise KeyError(f"No capture template found for the capture mode '{capture_mode}'. "
                       f"Expected one of {list(_base_capture_templates.keys())}")
    return deepcopy( _base_capture_templates[capture_mode] )