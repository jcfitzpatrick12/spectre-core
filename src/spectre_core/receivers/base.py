# SPDX-FileCopyrightText: © 2024 Jimmy Fitzpatrick <jcfitzpatrick12@gmail.com>
# This file is part of SPECTRE
# SPDX-License-Identifier: GPL-3.0-or-later

from abc import ABC, abstractmethod
from typing import Callable, Any, Optional

from spectre_core.capture_config import CaptureConfig
from spectre_core.exceptions import ModeNotFoundError
from spectre_core.capture_config import (
    CaptureTemplate, 
    Parameters,
    Parameter
)


class BaseReceiver(ABC):
    def __init__(self, 
                 name: str, 
                 mode: Optional[str] = None):
        self._name = name

        self._specs: Parameters = Parameters()
        self._init_specs()
        
        self._capture_methods: dict[str, Callable] = {}
        self._init_capture_methods()
    
        self._validators: dict[str, Callable] = {}
        self._init_validators()

        self._capture_templates: dict[str, CaptureTemplate] = {}
        self._init_capture_templates()

        self.mode = mode



    @abstractmethod
    def _init_capture_methods(self) -> None:
        pass


    @abstractmethod
    def _init_validators(self) -> None:
        pass


    @abstractmethod
    def _init_capture_templates(self) -> None:
        pass


    @abstractmethod
    def _init_specs(self) -> None:
        pass

    
    @property
    def name(self) -> str:
        return self._name
    

    @property
    def capture_methods(self) -> dict[str, Callable]:
        return self._capture_methods
    

    @property
    def validators(self) -> dict[str, Callable]:
        return self._validators


    @property
    def capture_templates(self) -> dict[str, CaptureTemplate]:
        return self._capture_templates


    @property
    def specs(self) -> Parameters:
        return self._specs


    @property
    def valid_modes(self) -> None:
        capture_method_modes   = list(self.capture_methods.keys())
        validator_modes        = list(self.validators.keys())
        capture_template_modes = list(self.capture_templates.keys())

        if capture_method_modes == validator_modes == capture_template_modes:
            return capture_method_modes
        else:
            raise ValueError(f"Mode mismatch for the receiver {self.name}. Could not define valid modes")


    @property
    def mode(self) -> str:
        return self._mode
    

    @mode.setter
    def mode(self, value: Optional[str]) -> None:
        if (value is not None) and value not in self.valid_modes:
            raise ModeNotFoundError((f"{value} is not a defined mode for the receiver {self.name}. "
                                     f"Expected one of {self.valid_modes}"))
        self._mode = value


    @property
    def capture_method(self) -> Callable:
        return self.capture_methods[self.mode]


    @property
    def validator(self) -> Callable:
        return self.validators[self.mode]


    @property
    def capture_template(self) -> CaptureTemplate:
        return self._capture_templates[self.mode]


    def add_capture_method(self,
                           mode: str,
                           capture_method: Callable) -> None:
        self._capture_methods[mode] = capture_method


    def add_validator(self,
                      mode: str,
                      validator: Callable) -> None:
        self._validators[mode] = validator


    def add_capture_template(self,
                             mode: str,
                             capture_template: CaptureTemplate) -> CaptureTemplate:
        self._capture_templates[mode] = capture_template


    def add_spec(self,
                 name: str,
                 value: Any) -> None:
        self.specs.add_parameter(name, value)


    def get_spec(self, 
                 spec_name: str) -> Parameter:
        return self.specs.get_parameter_value(spec_name)


    def start_capture(self, 
                      tag: str) -> None:
        capture_config = self.capture_template.load_capture_config(tag)
        self.capture_method(capture_config)


    def save_capture_config(self,
                            tag: str,
                            parameters: Parameters,
                            force: bool = False) -> False:
        parameters = self.capture_template.apply_template(parameters)
        self.validator(parameters)
        capture_config = CaptureConfig(tag)
        capture_config.save_parameters(self.name,
                                       self.mode,
                                       parameters,
                                       force=force)

    def load_capture_config(self,
                            tag: str) -> CaptureConfig:
        capture_config = CaptureConfig(tag)
        self.validator(capture_config.parameters)
        return capture_config
    
# class SDRPlayReceiver(Base)

# def sdrplay_validator(self, 
#                      capture_config: CaptureConfig) -> None:
#     # RSPduo specific validations in single tuner mode
#     center_frequency_lower_bound = get_spec("center_frequency_lower_bound")
#     center_frequency_upper_bound = get_spec("center_frequency_upper_bound")
#     center_frequency = capture_config.get("center_frequency")
#     min_frequency = capture_config.get("min_frequency")
#     max_frequency = capture_config.get("max_frequency")

#     if center_frequency:
#         validators.closed_bound_center_frequency(center_frequency, 
#                                                 center_frequency_lower_bound, 
#                                                 center_frequency_upper_bound)
        
#     if min_frequency:
#         validators.closed_bound_center_frequency(min_frequency, 
#                                                 center_frequency_lower_bound, 
#                                                 center_frequency_upper_bound)
#     if max_frequency:
#         validators.closed_bound_center_frequency(max_frequency, 
#                                                 center_frequency_lower_bound, 
#                                                 center_frequency_upper_bound)

#     validators.closed_bound_sample_rate(capture_config["sample_rate"], 
#                                         self.get_spec("sample_rate_lower_bound"), 
#                                         self.get_spec("sample_rate_upper_bound"))


#     validators.closed_bound_bandwidth(capture_config["bandwidth"], 
#                                         self.get_spec("bandwidth_lower_bound"), 
#                                         self.get_spec("bandwidth_upper_bound"))

#     validators.closed_upper_bound_if_gain(capture_config["if_gain"], 
#                                             self.get_spec("if_gain_upper_bound"))
    
#     validators.closed_upper_bound_rf_gain(capture_config["rf_gain"], 
#                                             self.get_spec("rf_gain_upper_bound"))

        # # if the api latency is defined, raise a warning if the step interval is of the same order
        # api_latency = self.specs.get("api_latency")
        # if api_latency:
        #     validators.step_interval(samples_per_step, 
        #                              sample_rate, 
        #                              api_latency)