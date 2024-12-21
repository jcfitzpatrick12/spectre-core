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
    
        self._pvalidators: dict[str, Callable] = {}
        self._init_pvalidators()

        self._capture_templates: dict[str, CaptureTemplate] = {}
        self._init_capture_templates()

        self.mode = mode



    @abstractmethod
    def _init_capture_methods(self) -> None:
        pass


    @abstractmethod
    def _init_pvalidators(self) -> None:
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
    def pvalidators(self) -> dict[str, Callable]:
        return self._pvalidators


    @property
    def capture_templates(self) -> dict[str, CaptureTemplate]:
        return self._capture_templates


    @property
    def specs(self) -> Parameters:
        return self._specs


    @property
    def modes(self) -> list[str]:
        capture_method_modes   = list(self.capture_methods.keys())
        pvalidator_modes        = list(self.pvalidators.keys())
        capture_template_modes = list(self.capture_templates.keys())

        if capture_method_modes == pvalidator_modes == capture_template_modes:
            return capture_method_modes
        else:
            raise ValueError(f"Mode mismatch for the receiver {self.name}.")


    @property
    def mode(self) -> str:
        return self._mode
    

    @mode.setter
    def mode(self, value: Optional[str]) -> None:
        if (value is not None) and value not in self.modes:
            raise ModeNotFoundError((f"{value} is not a defined mode for the receiver {self.name}. "
                                     f"Expected one of {self.modes}"))
        self._mode = value


    @property
    def capture_method(self) -> Callable:
        return self.capture_methods[self.mode]


    @property
    def pvalidator(self) -> Callable:
        return self.pvalidators[self.mode]


    @property
    def capture_template(self) -> CaptureTemplate:
        return self._capture_templates[self.mode]


    def add_capture_method(self,
                           mode: str,
                           capture_method: Callable) -> None:
        self._capture_methods[mode] = capture_method


    def add_pvalidator(self,
                      mode: str,
                      pvalidator: Callable) -> None:
        self._pvalidators[mode] = pvalidator


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
        self.capture_method( tag, self.load_parameters(tag) )


    def save_parameters(self,
                        tag: str,
                        parameters: Parameters,
                        force: bool = False) -> None:
        
        parameters = self.capture_template.apply_template(parameters)
        self.pvalidator(parameters)

        capture_config = CaptureConfig(tag)
        capture_config.save_parameters(self.name,
                                       self.mode,
                                       parameters,
                                       force=force)

    def load_parameters(self,
                        tag: str) -> Parameters:
        capture_config = CaptureConfig(tag)

        parameters = self.capture_template.apply_template(capture_config.parameters)
        self.pvalidator(parameters)
        
        return parameters
    


    # def _get_capture_template_fixed_center_frequency(self) -> CaptureTemplate:
    #     capture_template = CaptureTemplate()

    #     #
    #     # Add default ptemplates
    #     #
    #     capture_template.add_ptemplate(
    #         pstore.get_ptemplate(
    #             pstore.PNames.CENTER_FREQUENCY,
    #             default=95800000,
    #             pconstraints=[
    #                 self.enforce_freq_bound
    #             ]
    #         )
    #     )
    #     capture_template.add_ptemplate(
    #         pstore.get_ptemplate(
    #             pstore.PNames.BANDWIDTH,
    #             default=1000000,
    #             pconstraints=[
    #                 self.enforce_bandwidth_bound
    #             ]
    #         )
    #     )
    #     capture_template.add_ptemplate(
    #         pstore.get_ptemplate(
    #             pstore.PNames.RF_GAIN,
    #             default=-30
    #         )
    #     )
    #     capture_template.add_ptemplate(
    #         pstore.get_ptemplate(
    #            pstore.PNames.IF_GAIN,
    #            default=-30 
    #         )
    #     )
    #     capture_template.add_ptemplate(
    #         pstore.get_ptemplate(
    #             pstore.PNames.TIME_RESOLUTION,
    #             default=0.0
    #         )
    #     )
    #     capture_template.add_ptemplate(
    #         pstore.get_ptemplate(
    #             pstore.PNames.FREQUENCY_RESOLUTION,
    #             default=0.0
    #         )
    #     )
    #     capture_template.add_ptemplate(
    #         pstore.get_ptemplate(
    #             pstore.PNames.TIME_RANGE,
    #             default=0.0
    #         )
    #     )
    #     capture_template.add_ptemplate(
    #         pstore.get_ptemplate(
    #             pstore.PNames.SAMPLE_RATE,
    #             default=1000000,
    #             pconstraints = [
    #                 self.enforce_sample_rate_bound
    #             ]
    #         )
    #     )
    #     capture_template.add_ptemplate(
    #         pstore.get_ptemplate(
    #             pstore.PNames.BATCH_SIZE,
    #             default=3.0,
    #         )
    #     )
    #     capture_template.add_ptemplate(
    #         pstore.get_ptemplate(
    #             pstore.PNames.WINDOW_TYPE,
    #             default="blackman"
    #         )
    #     )
    #     capture_template.add_ptemplate(
    #         pstore.get_ptemplate(
    #             pstore.PNames.WINDOW_HOP,
    #             default=256
    #         )
    #     )
    #     capture_template.add_ptemplate(
    #         pstore.get_ptemplate(
    #             pstore.PNames.WINDOW_SIZE,
    #             default=512
    #         )
    #     )
    #     capture_template.add_ptemplate(
    #         pstore.get_ptemplate(
    #             pstore.PNames.EVENT_HANDLER_KEY,
    #             default="fixed-center-frequency",
    #             enforce_default=True
    #         )
    #     )
    #     capture_template.add_ptemplate(
    #         pstore.get_ptemplate(
    #             pstore.PNames.CHUNK_KEY,
    #             default="fixed-center-frequency",
    #             enforce_default=True
    #         )
    #     )
    #     capture_template.add_ptemplate(
    #         pstore.get_ptemplate(
    #             pstore.PNames.WATCH_EXTENSION,
    #             default="bin",
    #             enforce_default=True
    #         )
    #     )
    #     capture_template.add_ptemplate(
    #         pstore.get_ptemplate(
    #             pstore.PNames.ORIGIN
    #         )
    #     )
    #     capture_template.add_ptemplate(
    #         pstore.get_ptemplate(
    #             pstore.PNames.OBJECT
    #         )
    #     )
    #     capture_template.add_ptemplate(
    #         pstore.get_ptemplate(
    #             pstore.PNames.INSTRUMENT
    #         )
    #     )
    #     capture_template.add_ptemplate(
    #         pstore.get_ptemplate(
    #             pstore.PNames.TELESCOPE
    #         )
    #     )
    #     capture_template.add_ptemplate(
    #         pstore.get_ptemplate(
    #             pstore.PNames.OBSERVATION_LATITUDE
    #         )
    #     )
    #     capture_template.add_ptemplate(
    #         pstore.get_ptemplate(
    #             pstore.PNames.OBSERVATION_LONGITUDE
    #         )
    #     )
    #     capture_template.add_ptemplate(
    #         pstore.get_ptemplate(
    #             pstore.PNames.OBSERVATION_ALTITUDE
    #         )
    #     )
    #     return capture_template
    

    # def _get_capture_template_swept_center_frequency(self) -> CaptureTemplate:
    #     capture_template = CaptureTemplate()

    #     #
    #     # Add default ptemplates
    #     #
    #     capture_template.add_ptemplate(
    #         pstore.get_ptemplate(
    #             pstore.PNames.MIN_FREQUENCY,
    #             default=90000000,
    #             pconstraints=[
    #                 self.enforce_freq_bound
    #             ]
    #         )
    #     )
    #     capture_template.add_ptemplate(
    #         pstore.get_ptemplate(
    #             pstore.PNames.MAX_FREQUENCY,
    #             default=120000000,
    #             pconstraints=[
    #                 self.enforce_freq_bound
    #             ]
    #         )
    #     )
    #     capture_template.add_ptemplate(
    #         pstore.get_ptemplate(
    #             pstore.PNames.SAMPLES_PER_STEP,
    #             default=300000
    #         )
    #     )
    #     capture_template.add_ptemplate(
    #         pstore.get_ptemplate(
    #             pstore.PNames.FREQUENCY_STEP,
    #             default=1000000
    #         )
    #     )
    #     capture_template.add_ptemplate(
    #         pstore.get_ptemplate(
    #             pstore.PNames.BANDWIDTH,
    #             default=1000000,
    #             pconstraints=[
    #                 self.enforce_bandwidth_bound
    #             ]
    #         )
    #     )
    #     capture_template.add_ptemplate(
    #         pstore.get_ptemplate(
    #             pstore.PNames.RF_GAIN,
    #             default=-30
    #         )
    #     )
    #     capture_template.add_ptemplate(
    #         pstore.get_ptemplate(
    #            pstore.PNames.IF_GAIN,
    #            default=-20 
    #         )
    #     )
    #     capture_template.add_ptemplate(
    #         pstore.get_ptemplate(
    #             pstore.PNames.TIME_RESOLUTION,
    #             default=0.0
    #         )
    #     )
    #     capture_template.add_ptemplate(
    #         pstore.get_ptemplate(
    #             pstore.PNames.FREQUENCY_RESOLUTION,
    #             default=0.0
    #         )
    #     )
    #     capture_template.add_ptemplate(
    #         pstore.get_ptemplate(
    #             pstore.PNames.TIME_RANGE,
    #             default=0.0
    #         )
    #     )
    #     capture_template.add_ptemplate(
    #         pstore.get_ptemplate(
    #             pstore.PNames.SAMPLE_RATE,
    #             default=1000000,
    #             pconstraints = [
    #                 EnforceBounds(lower_bound=self.get_spec(pstore.SpecNames.SAMPLE_RATE_LOWER_BOUND),
    #                               upper_bound=self.get_spec(pstore.SpecNames.SAMPLE_RATE_UPPER_BOUND))
    #             ]
    #         )
    #     )
    #     capture_template.add_ptemplate(
    #         pstore.get_ptemplate(
    #             pstore.PNames.BATCH_SIZE,
    #             default=3.0,
    #         )
    #     )
    #     capture_template.add_ptemplate(
    #         pstore.get_ptemplate(
    #             pstore.PNames.WINDOW_TYPE,
    #             default="blackman"
    #         )
    #     )
    #     capture_template.add_ptemplate(
    #         pstore.get_ptemplate(
    #             pstore.PNames.WINDOW_HOP,
    #             default=256
    #         )
    #     )
    #     capture_template.add_ptemplate(
    #         pstore.get_ptemplate(
    #             pstore.PNames.WINDOW_SIZE,
    #             default=512
    #         )
    #     )
    #     capture_template.add_ptemplate(
    #         pstore.get_ptemplate(
    #             pstore.PNames.EVENT_HANDLER_KEY,
    #             default="swept-center-frequency",
    #             enforce_default=True
    #         )
    #     )
    #     capture_template.add_ptemplate(
    #         pstore.get_ptemplate(
    #             pstore.PNames.CHUNK_KEY,
    #             default="swept-center-frequency",
    #             enforce_default=True
    #         )
    #     )
    #     capture_template.add_ptemplate(
    #         pstore.get_ptemplate(
    #             pstore.PNames.WATCH_EXTENSION,
    #             default="bin",
    #             enforce_default=True
    #         )
    #     )
    #     capture_template.add_ptemplate(
    #         pstore.get_ptemplate(
    #             pstore.PNames.ORIGIN
    #         )
    #     )
    #     capture_template.add_ptemplate(
    #         pstore.get_ptemplate(
    #             pstore.PNames.OBJECT
    #         )
    #     )
    #     capture_template.add_ptemplate(
    #         pstore.get_ptemplate(
    #             pstore.PNames.INSTRUMENT
    #         )
    #     )
    #     capture_template.add_ptemplate(
    #         pstore.get_ptemplate(
    #             pstore.PNames.TELESCOPE
    #         )
    #     )
    #     capture_template.add_ptemplate(
    #         pstore.get_ptemplate(
    #             pstore.PNames.OBSERVATION_LATITUDE
    #         )
    #     )
    #     capture_template.add_ptemplate(
    #         pstore.get_ptemplate(
    #             pstore.PNames.OBSERVATION_LONGITUDE
    #         )
    #     )
    #     capture_template.add_ptemplate(
    #         pstore.get_ptemplate(
    #             pstore.PNames.OBSERVATION_ALTITUDE
    #         )
    #     )
    #     return capture_template


    # def _get_pvalidator_fixed_center_frequency(self) -> Callable:
    #     ...


    # def _get_pvalidator_swept_center_frequency(self) -> Callable:
    #     ...

# class SDRPlayReceiver(Base)

# def sdrplay_pvalidator(self, 
#                      capture_config: CaptureConfig) -> None:
#     # RSPduo specific validations in single tuner mode
#     center_frequency_lower_bound = get_spec("center_frequency_lower_bound")
#     center_frequency_upper_bound = get_spec("center_frequency_upper_bound")
#     center_frequency = capture_config.get("center_frequency")
#     min_frequency = capture_config.get("min_frequency")
#     max_frequency = capture_config.get("max_frequency")

#     if center_frequency:
#         pvalidators.closed_bound_center_frequency(center_frequency, 
#                                                   center_frequency_lower_bound, 
#                                                   center_frequency_upper_bound)
        
#     if min_frequency:
#         pvalidators.closed_bound_center_frequency(min_frequency, 
#                                                 center_frequency_lower_bound, 
#                                                 center_frequency_upper_bound)
#     if max_frequency:
#         pvalidators.closed_bound_center_frequency(max_frequency, 
#                                                 center_frequency_lower_bound, 
#                                                 center_frequency_upper_bound)

#     pvalidators.closed_bound_sample_rate(capture_config["sample_rate"], 
#                                         self.get_spec("sample_rate_lower_bound"), 
#                                         self.get_spec("sample_rate_upper_bound"))


#     pvalidators.closed_bound_bandwidth(capture_config["bandwidth"], 
#                                         self.get_spec("bandwidth_lower_bound"), 
#                                         self.get_spec("bandwidth_upper_bound"))

#     pvalidators.closed_upper_bound_if_gain(capture_config["if_gain"], 
#                                             self.get_spec("if_gain_upper_bound"))
    
#     pvalidators.closed_upper_bound_rf_gain(capture_config["rf_gain"], 
#                                             self.get_spec("rf_gain_upper_bound"))

        # # if the api latency is defined, raise a warning if the step interval is of the same order
        # api_latency = self.specs.get("api_latency")
        # if api_latency:
        #     pvalidators.step_interval(samples_per_step, 
        #                              sample_rate, 
        #                              api_latency)