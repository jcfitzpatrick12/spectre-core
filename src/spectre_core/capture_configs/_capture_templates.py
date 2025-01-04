# SPDX-FileCopyrightText: © 2024 Jimmy Fitzpatrick <jcfitzpatrick12@gmail.com>
# This file is part of SPECTRE
# SPDX-License-Identifier: GPL-3.0-or-later

from copy import deepcopy
from typing import Any, Iterator

from ._capture_modes import CaptureModes
from ._parameters import Parameter, Parameters
from ._pconstraints import PConstraint
from ._ptemplates import PTemplate, get_base_ptemplate
from ._ptemplates import PNames

class CaptureTemplate:
    """A managed collection of parameter templates. Strictly outlines what parameters should exists
    in a capture configuration file, and what the values of those parameters should look like. 
    """
    def __init__(self) -> None:
        """Initialise a `CaptureTemplate` instance.
        """
        self._ptemplates: dict[PNames, PTemplate] = {}


    @property
    def name_list(self) -> list[PNames]:
        """The names of all allowed parameters in the capture template."""
        return list(self._ptemplates.keys())
    

    def add_ptemplate(self,
                      ptemplate: PTemplate) -> None:
        """Add a parameter template to the capture template.

        Arguments:
            ptemplate -- Describes a required parameter for this capture template.
        """
        self._ptemplates[ptemplate.name] = ptemplate


    def get_ptemplate(self,
                      parameter_name: PNames) -> PTemplate:
        """Get the parameter template corresponding to the parameter with the name `parameter_name`."""
        if parameter_name not in self._ptemplates:
            raise ValueError(f"Parameter with name '{parameter_name}' is not found in the template. "
                             f"Expected one of {self.name_list}")   
        return self._ptemplates[parameter_name]
      

    def __apply_parameter_template(self,
                                   parameter: Parameter):
        """Apply the corresponding parameter template to the input parameter."""
        ptemplate = self.get_ptemplate(parameter.name)
        parameter.value = ptemplate.apply_template(parameter.value)


    def __apply_parameter_templates(self,
                                    parameters: Parameters) -> None:
        """Apply the corresponding parameter template to each of the input parameters."""
        for parameter in parameters:
            self.__apply_parameter_template(parameter)

    
    def __fill_missing_with_defaults(self,
                                     parameters: Parameters) -> None:
        """For any missing parameters (with respect to the parameter template, use
        the default parameter."""
        for ptemplate in self:
            if ptemplate.name not in parameters.name_list:
                parameter = ptemplate.make_parameter()
                parameters.add_parameter(parameter.name, 
                                         parameter.value)


    def apply_template(self,
                       parameters: Parameters) -> Parameters:
        """Apply the capture template to the input parameters and return anew.
        
        Specifically, 
        - Missing parameters are replaced by the defaults as per the 
        stored parameter templates)
        - Each respective parameter template is applied to the corresponding parameter 
        to ensure types and constraints are satisfied.

        Arguments:
            parameters -- The parameters to apply this capture template to.

        Returns:
            A `Parameters` instance compliant with this template, in accordance with the stored
            parameter templates.
        """
        self.__fill_missing_with_defaults(parameters)
        self.__apply_parameter_templates(parameters)
        return parameters


    def __iter__(self) -> Iterator[PTemplate]:
        """Iterate over stored ptemplates"""
        yield from self._ptemplates.values() 


    def set_default(self, 
                    parameter_name: PNames, 
                    default: Any) -> None:
        """Set the default of an existing parameter template.

        Arguments:
            parameter_name -- The name of the parameter template to be updated.
            default -- The new default value.
        """
        self.get_ptemplate(parameter_name).default = default


    def set_defaults(self, 
                     *ptuples: tuple[PNames, Any]) -> None:
        """Update the defaults of multiple parameter templates.
        
        Each of `ptuples` should be of the form: 
        - (`parameter_name`, `new_default`)
        
        which will update the default of the parameter template with name 
        `parameter_name` to `new_default`.
        """
        for (parameter_name, default) in ptuples:
            self.set_default(parameter_name, default)


    def enforce_default(self,
                        parameter_name: PNames) -> None:
        """Set the `enforce_default` attribute of an existing parameter template to True.

        Arguments:
            parameter_name -- The name of the parameter template to have its `default` value enforced.
        """
        self.get_ptemplate(parameter_name).enforce_default = True


    def enforce_defaults(self, 
                         *parameter_names: PNames) -> None:
        """Set the `enforce_default` attribute of multiple existing parameter templates to True.
        
        Arguments:
            parameter_name -- The name of the parameter templates to have their `default` values enforced.
        """
        for name in parameter_names:
            self.enforce_default(name)


    def add_pconstraint(self,
                        parameter_name: PNames,
                        pconstraints: list[PConstraint]) -> None:
        """Add one or more `PConstraint` instance to an existing parameter template.
        
        Notably, the `pconstraints` are added in addition to those which already exist.

        Arguments:
            parameter_name -- The parameter template to add the `PConstraint` instances to.
            pconstraints -- The list of `PConstraint` instances to be added to the parameter template.
        """
        for pconstraint in pconstraints:
            self.get_ptemplate(parameter_name).add_pconstraint(pconstraint)


    def to_dict(self) -> dict[str, dict[str, str]]:
        """Convert the current instance to an equivalent dictionary representation.

        Returns:
            A dictionary representation of this capture template, 
            where all values are string-formatted for ease of serialisation.
        """
        return {ptemplate.name.value: ptemplate.to_dict() for ptemplate in self}
    
    

def make_base_capture_template(*pnames: PNames):
    """Make a capture template composed entirely of base `PTemplate` instances.

    Returns:
        A capture template composed entirely of base parameter templates, to be configured
        according to the specific use-case.
    """
    capture_template = CaptureTemplate()
    for pname in pnames:
        capture_template.add_ptemplate( get_base_ptemplate(pname) )
    return capture_template


def _make_fixed_frequency_capture_template(
) -> CaptureTemplate:
    """The absolute minimum required parameters for any fixed frequency capture template."""
    capture_template = make_base_capture_template(
        PNames.BATCH_SIZE,
        PNames.CENTER_FREQUENCY,
        PNames.BATCH_KEY,
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
            (PNames.BATCH_KEY,             "IQStreamBatch"),
            (PNames.WATCH_EXTENSION,       "bin")
    )
    capture_template.enforce_defaults(
        PNames.EVENT_HANDLER_KEY,
        PNames.BATCH_KEY,
        PNames.WATCH_EXTENSION
    )
    return capture_template

def _make_swept_frequency_capture_template(
) -> CaptureTemplate:
    """The absolute minimum required parameters for any swept frequency capture template."""
    capture_template = make_base_capture_template(
        PNames.BATCH_SIZE,
        PNames.BATCH_KEY,
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
            (PNames.BATCH_KEY,             "IQStreamBatch"),
            (PNames.WATCH_EXTENSION,       "bin")
    )
    capture_template.enforce_defaults(
        PNames.EVENT_HANDLER_KEY,
        PNames.BATCH_KEY,
        PNames.WATCH_EXTENSION
    )
    return capture_template


_base_capture_templates: dict[CaptureModes, CaptureTemplate] = {
    CaptureModes.FIXED_CENTER_FREQUENCY: _make_fixed_frequency_capture_template(),
    CaptureModes.SWEPT_CENTER_FREQUENCY: _make_swept_frequency_capture_template()
}


def get_base_capture_template(
       capture_mode: CaptureModes
) -> CaptureTemplate:
    """Get a pre-defined capture template, to be configured according to the specific use case.

    Arguments:
        capture_mode -- The mode used to register the

    Raises:
        KeyError: _description_

    Returns:
        _description_
    """
    if capture_mode not in _base_capture_templates:
        raise KeyError(f"No capture template found for the capture mode '{capture_mode}'. "
                       f"Expected one of {list(_base_capture_templates.keys())}")
    return deepcopy( _base_capture_templates[capture_mode] )