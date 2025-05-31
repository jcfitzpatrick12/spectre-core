# SPDX-FileCopyrightText: © 2024-2025 Jimmy Fitzpatrick <jcfitzpatrick12@gmail.com>
# This file is part of SPECTRE
# SPDX-License-Identifier: GPL-3.0-or-later

from copy import deepcopy
from typing import Any, Iterator

from ._capture_modes import CaptureMode
from ._parameters import Parameter, Parameters
from ._pconstraints import BasePConstraint
from ._ptemplates import PTemplate, get_base_ptemplate
from ._ptemplates import PName


class CaptureTemplate:
    """A managed collection of parameter templates. Strictly defines what parameters are required
    in a capture config, and the values each parameter can take.
    """

    def __init__(self) -> None:
        """Initialise a `CaptureTemplate` instance."""
        self._ptemplates: dict[PName, PTemplate] = {}

    @property
    def name_list(self) -> list[PName]:
        """The names of all required parameters in the capture template."""
        return list(self._ptemplates.keys())

    def add_ptemplate(self, ptemplate: PTemplate) -> None:
        """Add a parameter template to the capture template.

        :param ptemplate: Describes a required parameter for this capture template.
        """
        self._ptemplates[ptemplate.name] = ptemplate

    def get_ptemplate(self, parameter_name: PName) -> PTemplate:
        """Get the parameter template corresponding to the parameter with the name `parameter_name`.

        :param parameter_name: The name of the parameter.
        :return: The corresponding `PTemplate` instance.
        :raises ValueError: If the parameter name is not found in the template.
        """
        if parameter_name not in self._ptemplates:
            raise ValueError(
                f"Parameter with name '{parameter_name}' is not found in the template. "
                f"Expected one of {self.name_list}"
            )
        return self._ptemplates[parameter_name]

    def __apply_parameter_template(self, parameter: Parameter) -> None:
        """Apply the corresponding parameter template to the input parameter.

        As a side effect, the value of the input parameter will be type cast
        according to the template.
        """
        ptemplate = self.get_ptemplate(parameter.name)
        parameter.value = ptemplate.apply_template(parameter.value)

    def __apply_parameter_templates(self, parameters: Parameters) -> None:
        """Apply the corresponding parameter template to each of the input parameters."""
        for parameter in parameters:
            self.__apply_parameter_template(parameter)

    def __fill_missing_with_defaults(self, parameters: Parameters) -> None:
        """Add default parameters to `parameters` for any missing entries.

        Missing parameters are identified by comparing `parameters` against the
        current capture template. Defaults are derived from the corresponding
        parameter templates.
        """
        for ptemplate in self:
            if ptemplate.name not in parameters.name_list:
                # no args for `make_parameter` implies the parameter with the default value will be used.
                parameter = ptemplate.make_parameter()
                parameters.add_parameter(parameter.name, parameter.value)

    def apply_template(self, parameters: Parameters) -> Parameters:
        """Apply the capture template to the input parameters. This involves:

        - Adding default parameters if they are missing with respect to this template.
        - Type casting the value of each input parameter according to the corresponding parameter template.
        - Validating the value of each input parameter against any corresponding pconstraints.

        :param parameters: The parameters to apply this capture template to.
        :return: A `Parameters` instance compliant with this template.
        """
        self.__fill_missing_with_defaults(parameters)
        self.__apply_parameter_templates(parameters)
        return parameters

    def __iter__(self) -> Iterator[PTemplate]:
        """Iterate over stored ptemplates."""
        yield from self._ptemplates.values()

    def set_default(self, parameter_name: PName, default: Any) -> None:
        """Set the default of an existing parameter template.

        :param parameter_name: The name of the parameter template to be updated.
        :param default: The new default value.
        """
        self.get_ptemplate(parameter_name).default = default

    def set_defaults(self, *ptuples: tuple[PName, Any]) -> None:
        """Update the defaults of multiple parameter templates.

        :param ptuples: Tuples of the form (`parameter_name`, `new_default`) to update defaults.
        """
        for parameter_name, default in ptuples:
            self.set_default(parameter_name, default)

    def enforce_default(self, parameter_name: PName) -> None:
        """Set the `enforce_default` attribute of an existing parameter template to True.

        :param parameter_name: The name of the parameter template to enforce its default value.
        """
        self.get_ptemplate(parameter_name).enforce_default = True

    def enforce_defaults(self, *parameter_names: PName) -> None:
        """Set the `enforce_default` attribute of multiple existing parameter templates to True.

        :param parameter_names: The names of the parameter templates to enforce their default values.
        """
        for name in parameter_names:
            self.enforce_default(name)

    def add_pconstraint(
        self, parameter_name: PName, pconstraints: list[BasePConstraint]
    ) -> None:
        """Add one or more `PConstraint` instances to an existing parameter template.

        :param parameter_name: The name of the parameter template to add constraints to.
        :param pconstraints: A list of `PConstraint` instances to be added.
        """
        for pconstraint in pconstraints:
            self.get_ptemplate(parameter_name).add_pconstraint(pconstraint)

    def to_dict(self) -> dict[str, dict[str, str]]:
        """Convert the current instance to a serialisable dictionary.

        :return: A dictionary representation of this capture template, where all values
        are formatted strings.
        """
        return {ptemplate.name.value: ptemplate.to_dict() for ptemplate in self}


def make_base_capture_template(*pnames: PName) -> CaptureTemplate:
    """Make a capture template composed entirely of base `PTemplate` instances.

    :param pnames: The names of parameters to include in the capture template.
    :return: A capture template composed of base parameter templates.
    """
    capture_template = CaptureTemplate()
    for pname in pnames:
        capture_template.add_ptemplate(get_base_ptemplate(pname))
    return capture_template


def _make_fixed_frequency_capture_template() -> CaptureTemplate:
    """The absolute minimum required parameters for any fixed frequency capture template."""
    capture_template = make_base_capture_template(
        PName.BATCH_SIZE,
        PName.CENTER_FREQUENCY,
        PName.BATCH_KEY,
        PName.EVENT_HANDLER_KEY,
        PName.FREQUENCY_RESOLUTION,
        PName.INSTRUMENT,
        PName.OBS_ALT,
        PName.OBS_LAT,
        PName.OBS_LON,
        PName.OBJECT,
        PName.ORIGIN,
        PName.SAMPLE_RATE,
        PName.TELESCOPE,
        PName.TIME_RANGE,
        PName.TIME_RESOLUTION,
        PName.WATCH_EXTENSION,
        PName.WINDOW_HOP,
        PName.WINDOW_SIZE,
        PName.WINDOW_TYPE,
    )
    capture_template.set_defaults(
        (PName.EVENT_HANDLER_KEY, "fixed_center_frequency"),
        (PName.BATCH_KEY, "iq_stream"),
        (PName.WATCH_EXTENSION, "bin"),
    )
    capture_template.enforce_defaults(
        PName.EVENT_HANDLER_KEY, PName.BATCH_KEY, PName.WATCH_EXTENSION
    )
    return capture_template


def _make_swept_frequency_capture_template() -> CaptureTemplate:
    """The absolute minimum required parameters for any swept frequency capture template."""
    capture_template = make_base_capture_template(
        PName.BATCH_SIZE,
        PName.BATCH_KEY,
        PName.EVENT_HANDLER_KEY,
        PName.FREQUENCY_RESOLUTION,
        PName.FREQUENCY_STEP,
        PName.INSTRUMENT,
        PName.MAX_FREQUENCY,
        PName.MIN_FREQUENCY,
        PName.OBS_ALT,
        PName.OBS_LAT,
        PName.OBS_LON,
        PName.OBJECT,
        PName.ORIGIN,
        PName.SAMPLE_RATE,
        PName.SAMPLES_PER_STEP,
        PName.TELESCOPE,
        PName.TIME_RANGE,
        PName.TIME_RESOLUTION,
        PName.WATCH_EXTENSION,
        PName.WINDOW_HOP,
        PName.WINDOW_SIZE,
        PName.WINDOW_TYPE,
    )
    capture_template.set_defaults(
        (PName.EVENT_HANDLER_KEY, "swept_center_frequency"),
        (PName.BATCH_KEY, "iq_stream"),
        (PName.WATCH_EXTENSION, "bin"),
    )
    capture_template.enforce_defaults(
        PName.EVENT_HANDLER_KEY, PName.BATCH_KEY, PName.WATCH_EXTENSION
    )
    return capture_template


_base_capture_templates: dict[CaptureMode, CaptureTemplate] = {
    CaptureMode.FIXED_CENTER_FREQUENCY: _make_fixed_frequency_capture_template(),
    CaptureMode.SWEPT_CENTER_FREQUENCY: _make_swept_frequency_capture_template(),
}


def get_base_capture_template(capture_mode: CaptureMode) -> CaptureTemplate:
    """Get a pre-defined capture template, to be configured according to the specific use-case.

    :param capture_mode: The mode used to retrieve the capture template.
    :return: A deep copy of the template for the specified mode.
    :raises KeyError: If no capture template is found for the given mode.
    """
    if capture_mode not in _base_capture_templates:
        raise KeyError(
            f"No capture template found for the capture mode '{capture_mode}'. "
            f"Expected one of {list(_base_capture_templates.keys())}"
        )
    return deepcopy(_base_capture_templates[capture_mode])
