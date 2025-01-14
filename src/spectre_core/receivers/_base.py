# SPDX-FileCopyrightText: © 2024 Jimmy Fitzpatrick <jcfitzpatrick12@gmail.com>
# This file is part of SPECTRE
# SPDX-License-Identifier: GPL-3.0-or-later

from abc import ABC, abstractmethod
from typing import Callable, Optional
from numbers import Number

from spectre_core.exceptions import ModeNotFoundError
from spectre_core.capture_configs import (
    CaptureTemplate, Parameters, CaptureConfig
)
from ._spec_names import SpecName

class BaseReceiver(ABC):
    """Abstract base class for software-defined radio receivers.

    Subclasses must implement the following:
    - `_add_specs`: Use `add_spec` to set hardware specifications.
    - `_add_capture_methods`: Define data capture methods for each operating mode.
    - `_add_capture_templates`: Add a `CaptureTemplate` outlining required parameters 
    for each mode, and what values each parameter can take.
    - `_add_pvalidators`: Define methods which validate the capture config parameters 
    for each operating mode.
    """
    def __init__(
        self, 
        name: str, 
        mode: Optional[str] = None
    ) -> None:
        """Initialise an instance of `BaseReceiver`.

        :param name: The name of the receiver.
        :param mode: The initial operating mode. Defaults to None.
        """
        self._name = name

        self._specs: dict[SpecName, Number | list[Number]] = {}
        self._add_specs()
        
        self._capture_methods: dict[str, Callable[[str, Parameters], None]] = {}
        self._add_capture_methods()
        
        self._capture_templates: dict[str, CaptureTemplate] = {}
        self._add_capture_templates()
    
        self._pvalidators: dict[str, Callable[[Parameters], None]] = {}
        self._add_pvalidators()

        self.mode = mode


    @abstractmethod
    def _add_specs(
        self
    ) -> None:
        """Define hardware specifications for the receiver.

        Subclasses must use `add_spec` to populate the specifications.
        """
    

    @abstractmethod
    def _add_capture_methods(
        self
    ) -> None:
        """Define data capture methods for each operating mode.

        Subclasses must use `add_capture_method` to specify the 
        function which is invoked to collect data.
        """

    @abstractmethod
    def _add_capture_templates(
        self
    ) -> None:
        """Add a `CaptureTemplate` for each operating mode.

        Subclasses must use `add_capture_template` to specify required capture config parameters, 
        and what values each of the parameters can take.
        """

    @abstractmethod
    def _add_pvalidators(
        self
    ) -> None:
        """Define parameter validation methods for each operating mode.

        Subclasses must use `add_pvalidator` to add functions which validate capture config parameters 
        as a whole.
        """

    
    @property
    def name(
        self
    ) -> str:
        """The name of the receiver."""
        return self._name
    

    @property
    def capture_methods(
        self
    ) -> dict[str, Callable[[str, Parameters], None]]:
        """For each operating mode, the method which invokes data capture."""
        return self._capture_methods
  
  
    @property
    def capture_templates(
        self
    ) -> dict[str, CaptureTemplate]:
        """For each operating mode, the corresponding `CaptureTemplate` which describes
        what parameters are expected in the capture config."""
        return self._capture_templates  


    @property
    def pvalidators(
        self
    ) -> dict[str, Callable[[Parameters], None]]:
        """For each operating mode, the function which validates capture config
        parameters as a whole."""
        return self._pvalidators


    @property
    def specs(
        self
    ) -> dict[SpecName, Number | list[Number]]:
        """The hardware specifications for the receiver."""
        return self._specs


    @property
    def modes(
        self
    ) -> list[str]:
        """The operating modes for the receiver.

        :raises ValueError: If the modes are inconsistent between `capture_methods`,
        `pvalidators` and `capture_templates`.
        """
        capture_method_modes    = list(self.capture_methods.keys())
        pvalidator_modes        = list(self.pvalidators.keys())
        capture_template_modes  = list(self.capture_templates.keys())
        
        if not capture_method_modes == pvalidator_modes == capture_template_modes:
            raise ValueError(f"Mode mismatch for the receiver {self.name}.")
        return capture_method_modes


    @property
    def mode(
        self
    ) -> str:
        """The active operating mode for the receiver."""
        return self._mode


    @mode.setter
    def mode(
        self, 
        value: Optional[str]
    ) -> None:
        """Set the active operating mode of the receiver.

        :param value: The new operating mode to activate.
        :raises ModeNotFoundError: If the specified mode is not defined in `modes`.
        """
        if (value is not None) and value not in self.modes:
            raise ModeNotFoundError((f"{value} is not a defined mode for the receiver {self.name}. "
                                     f"Expected one of {self.modes}"))
        self._mode = value


    @property
    def capture_method(
        self
    ) -> Callable[[str, Parameters], None]:
        """Invoke data capture under the active operating mode."""
        return self.capture_methods[self.mode]


    @property
    def pvalidator(
        self
    ) -> Callable[[Parameters], None]:
        """Validate parameters for the active operating mode."""
        return self.pvalidators[self.mode]


    @property
    def capture_template(
        self
    ) -> CaptureTemplate:
        """The capture template for the active operating mode."""
        return self._capture_templates[self.mode]


    def add_capture_method(
        self,
        mode: str,
        capture_method: Callable[[str, Parameters], None]
    ) -> None:
        """Add a data capture method for a specific operating mode.

        Each capture method takes two arguments: the capture config tag and the stored parameters. 
        When `start_capture` is called, the capture method for the active operating mode is invoked with 
        the input parameters loaded from the capture config.

        :param mode: The operating mode for which the capture method is added.
        :param capture_method: The function to invoke data capture.
        """
        self._capture_methods[mode] = capture_method


    def add_pvalidator(
        self,
        mode: str,
        pvalidator: Callable[[Parameters], None]
    ) -> None:
        """Add a parameter validation function for a specific operating mode.

        When `start_capture` is called, the parameters in the capture config are validated 
        using the specified function before being passed to the capture method.

        :param mode: The operating mode for which the validation function is added.
        :param pvalidator: The function used to validate the capture config parameters.
        """
        self._pvalidators[mode] = pvalidator


    def add_capture_template(
        self,
        mode: str,
        capture_template: CaptureTemplate
    ) -> None:
        """Add a `CaptureTemplate` for a specific operating mode.

        The `CaptureTemplate` outlines the required parameters for the capture config 
        and specifies what values each parameter can take.

        :param mode: The operating mode for which the template is added.
        :param capture_template: The `CaptureTemplate` defining the parameter requirements.
        """
        self._capture_templates[mode] = capture_template


    def add_spec(
        self,
        name: SpecName,
        value: Number
    ) -> None:
        """Add a hardware specification to the receiver.

        :param name: The name of the specification.
        :param value: The value of the specification.
        """
        self.specs[name] = value


    def get_spec(
        self, 
        spec_name: SpecName
    ) -> Number | list[Number]:
        """Retrieve a hardware specification by name.

        :param spec_name: The name of the specification to retrieve.
        :raises KeyError: If the name does not exist in the receiver's specifications.
        :return: The value of the specification.
        """
        if spec_name not in self.specs:
            raise KeyError(f"Spec not found with name '{spec_name}' "
                           f"for the receiver '{self.name}'")
        return self.specs[spec_name]


    def start_capture(
        self, 
        tag: str
    ) -> None:
        """Initiate data capture for the active operating mode.

        Loads the capture config for the specified tag, validates its parameters 
        then starts data capture.

        :param tag: The tag identifying the capture configuration to use.
        """
        self.capture_method( tag, self.load_parameters(tag) )


    def save_parameters(
        self,
        tag: str,
        parameters: Parameters,
        force: bool = False
    ) -> None:
        """Creates a capture config for the active operating mode and saves the parameters.

        Validates the parameters against the active `capture_template` and `pvalidator` before saving.

        :param tag: The tag identifying the capture configuration.
        :param parameters: The parameters to save in the capture config.
        :param force: If True, overwrites the existing file if it already exists. Defaults to False.
        """
        parameters = self.capture_template.apply_template(parameters)
        self.pvalidator(parameters)

        capture_config = CaptureConfig(tag)
        capture_config.save_parameters(self.name,
                                       self.mode,
                                       parameters,
                                       force=force)

    def load_parameters(
        self,
        tag: str
    ) -> Parameters:
        """Loads a capture config and validates its stored parameters.

        Validates the parameters using the active `capture_template` and `pvalidator` 
        before returning.

        :param tag: The tag identifying the capture configuration.
        :return: The validated parameters stored in the capture config.
        """
        capture_config = CaptureConfig(tag)

        parameters = self.capture_template.apply_template(capture_config.parameters)
        self.pvalidator(parameters)
        
        return parameters