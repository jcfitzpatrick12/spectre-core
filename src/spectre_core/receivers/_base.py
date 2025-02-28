# SPDX-FileCopyrightText: © 2024 Jimmy Fitzpatrick <jcfitzpatrick12@gmail.com>
# This file is part of SPECTRE
# SPDX-License-Identifier: GPL-3.0-or-later

from abc import ABC, abstractmethod
from typing import Callable, Optional, Literal, overload, Any

from spectre_core.exceptions import ModeNotFoundError
from spectre_core.capture_configs import (
    CaptureTemplate, Parameters, CaptureConfig
)
from .plugins._receiver_names import ReceiverName
from ._spec_names import SpecName

class BaseReceiver(ABC):
    """Abstract base class for software-defined radio receivers."""
    def __init__(
        self, 
        name: ReceiverName, 
        mode: Optional[str] = None
    ) -> None:
        """Initialise an instance of `BaseReceiver`.

        :param name: The name of the receiver.
        :param mode: The initial active operating mode. Defaults to None.
        """
        self._name = name

        self._specs: dict[SpecName, float|int|list[float|int]] = {}
        self._add_specs()
        
        self._capture_methods: dict[str, Callable[[str, Parameters], None]] = {}
        self._add_capture_methods()
        
        self._capture_templates: dict[str, CaptureTemplate] = {}
        self._add_capture_templates()
    
        self._pvalidators: dict[str, Callable[[Parameters], None]] = {}
        self._add_pvalidators()

        self._mode = None
        if mode is not None:
            self.mode = mode


    @abstractmethod
    def _add_specs(
        self
    ) -> None:
        """Subclasses must use `add_spec` to add hardware specifications."""
    

    @abstractmethod
    def _add_capture_methods(
        self
    ) -> None:
        """Subclasses must use `add_capture_method` to specify which method is called to capture 
        data, for each operating mode."""
        

    @abstractmethod
    def _add_capture_templates(
        self
    ) -> None:
        """Subclasses must use `add_capture_template` to define a `CaptureTemplate` for each operating mode."""


    @abstractmethod
    def _add_pvalidators(
        self
    ) -> None:
        """Subclasses must use `add_pvalidator` to add a parameter validation function (pvalidator) 
        for each operating mode."""

    
    @property
    def name(
        self
    ) -> ReceiverName:
        """The name of the receiver."""
        return self._name
    

    @property
    def capture_methods(
        self
    ) -> dict[str, Callable[[str, Parameters], None]]:
        """For each operating mode, the method which is called to capture data."""
        return self._capture_methods
  
  
    @property
    def capture_templates(
        self
    ) -> dict[str, CaptureTemplate]:
        """For each operating mode, the corresponding `CaptureTemplate`."""
        return self._capture_templates  


    @property
    def pvalidators(
        self
    ) -> dict[str, Callable[[Parameters], None]]:
        """For each operating mode, the corresponding parameter validation function (pvalidator)."""
        return self._pvalidators


    @property
    def specs(
        self
    ) -> dict[SpecName, float|int|list[float|int]]:
        """The hardware specifications."""
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
        if self._mode is None:
            raise ValueError(f"The operating mode for the receiver `{self.name.value}` is not set.")
        return self._mode


    @mode.setter
    def mode(
        self, 
        value: str,
    ) -> None:
        """Set the active operating mode.

        :param value: The new operating mode to activate.
        :raises ModeNotFoundError: If the specified mode is not defined in `modes`.
        """
        if (value not in self.modes):
            raise ModeNotFoundError((f"{value} is not a defined mode for the receiver {self.name}. "
                                     f"Expected one of {self.modes}"))
        self._mode = value


    @property
    def capture_method(
        self
    ) -> Callable[[str, Parameters], None]:
        """Start capturing data under the active operating mode."""
        return self.capture_methods[self.mode]


    @property
    def pvalidator(
        self
    ) -> Callable[[Parameters], None]:
        """The parameter validation function for the active operating mode."""
        return self.pvalidators[self.mode]


    @property
    def capture_template(
        self
    ) -> CaptureTemplate:
        """The `CaptureTemplate` for the active operating mode."""
        return self._capture_templates[self.mode]


    def add_capture_method(
        self,
        mode: str,
        capture_method: Callable[[str, Parameters], None]
    ) -> None:
        """
        Add a capture method for a specific operating mode.

        :param mode: The operating mode.
        :param capture_method: The function which captures data.
        """
        self._capture_methods[mode] = capture_method


    def add_pvalidator(
        self,
        mode: str,
        pvalidator: Callable[[Parameters], None]
    ) -> None:
        """
        Add a parameter validation function for a specific operating mode.

        :param mode: The operating mode.
        :param pvalidator: The validation function.
        """
        self._pvalidators[mode] = pvalidator


    def add_capture_template(
        self,
        mode: str,
        capture_template: CaptureTemplate
    ) -> None:
        """
        Add a `CaptureTemplate` for a specific operating mode.

        :param mode: The operating mode.
        :param capture_template: The capture template, defining parameter requirements.
        """
        self._capture_templates[mode] = capture_template


    def add_spec(
        self,
        name: SpecName,
        value: Any 
    ) -> None:
        """
        Add a hardware specification.

        :param name: The specification's name.
        :param value: The specification's value.
        """
        self.specs[name] = value

    
    def get_spec(
        self, 
        spec_name: SpecName
    ) -> Any:
        """
        Retrieve a hardware specification.

        :param spec_name: The name of the specification.
        :raises KeyError: If the specification is not found.
        :return: The specification's value.
        """
        if spec_name not in self.specs:
            raise KeyError(f"Spec not found with name '{spec_name}' "
                           f"for the receiver '{self.name}'")
        return self.specs[spec_name]


    def start_capture(
        self, 
        tag: str
    ) -> None:
        """Start capturing data in the active operating mode.

        :param tag: The tag of the capture config to load.
        """
        self.capture_method( tag, self.load_parameters(tag) )


    def save_parameters(
        self,
        tag: str,
        parameters: Parameters,
        force: bool = False
    ) -> None:
        """Create a capture config according to the active operating mode and save the 
        input parameters.

        The input parameters are validated before being written to file.
        
        :param tag: The tag identifying the capture config.
        :param parameters: The parameters to save in the capture config.
        :param force: If True, overwrites the existing file if it already exists. Defaults to False.
        """
        parameters = self.capture_template.apply_template(parameters)
        self.pvalidator(parameters)

        capture_config = CaptureConfig(tag)
        capture_config.save_parameters(self.name.value,
                                       self.mode,
                                       parameters,
                                       force)

    def load_parameters(
        self,
        tag: str
    ) -> Parameters:
        """Load a capture config, and return the parameters it stores.

        The parameters are validated before being returned.

        :param tag: The tag identifying the capture config.
        :return: The validated parameters stored in the capture config.
        """
        capture_config = CaptureConfig(tag)

        parameters = self.capture_template.apply_template(capture_config.parameters)
        self.pvalidator(parameters)
        
        return parameters
