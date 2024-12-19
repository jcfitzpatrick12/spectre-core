# SPDX-FileCopyrightText: © 2024 Jimmy Fitzpatrick <jcfitzpatrick12@gmail.com>
# This file is part of SPECTRE
# SPDX-License-Identifier: GPL-3.0-or-later

from dataclasses import dataclass
from typing import Optional, Callable

from spectre_core.capture_config import CaptureTemplate
from spectre_core.pconstraints import enforce_positive, EnforceBounds
from spectre_core.parameters import PTemplate, Parameters
from spectre_core.receivers import pstore, pvalidators
from spectre_core.receivers.base import BaseReceiver
from spectre_core.receivers.receiver_register import register_receiver
from spectre_core.receivers.library.test.gr import (
    cosine_signal_1,
    tagged_staircase
)

@dataclass
class Modes:
    COSINE_SIGNAL_1  = "cosine-signal-1"
    TAGGED_STAIRCASE = "tagged-staircase"


@register_receiver("test")
class Receiver(BaseReceiver):
    def __init__(self, 
                 name: str,
                 mode: Optional[str]):
        super().__init__(name,
                         mode)

    def _init_capture_methods(self) -> None:
        self.add_capture_method( Modes.COSINE_SIGNAL_1 , self.__get_capture_method_cosine_signal_1() )
        self.add_capture_method( Modes.TAGGED_STAIRCASE, self.__get_capture_method_tagged_staircase())
    

    def _init_pvalidators(self) -> None:
        self.add_pvalidator( Modes.COSINE_SIGNAL_1 , self.__get_pvalidator_cosine_signal_1()  )
        self.add_pvalidator( Modes.TAGGED_STAIRCASE, self.__get_pvalidator_tagged_staircase() )

    

    def _init_capture_templates(self) -> None:
        self.add_capture_template( Modes.COSINE_SIGNAL_1 , self.__get_capture_template_cosine_signal_1()  )
        self.add_capture_template( Modes.TAGGED_STAIRCASE, self.__make_capture_template_tagged_staircase() )
    
    
    def _init_specs(self) -> None:
        self.add_spec( pstore.SpecNames.SAMPLE_RATE_LOWER_BOUND, 64000  )
        self.add_spec( pstore.SpecNames.SAMPLE_RATE_UPPER_BOUND, 640000 )
        self.add_spec( pstore.SpecNames.FREQUENCY_LOWER_BOUND  , 16000  )
        self.add_spec( pstore.SpecNames.FREQUENCY_UPPER_BOUND  , 160000 )


    def __get_capture_method_cosine_signal_1(self) -> Callable:
        return cosine_signal_1.capture
    

    def __get_capture_method_tagged_staircase(self) -> Callable:
        return tagged_staircase.capture
        

    def __get_capture_template_cosine_signal_1(self) -> CaptureTemplate:
        capture_template = CaptureTemplate()

        #
        # Add default ptemplates
        #
        capture_template.add_ptemplate(
            pstore.get_ptemplate(
                pstore.PNames.TIME_RESOLUTION,
                default=0.0,
                enforce_default=True
            )
        )
        capture_template.add_ptemplate(
            pstore.get_ptemplate(
                pstore.PNames.FREQUENCY_RESOLUTION,
                default=0.0,
                enforce_default=True
            )
        )
        capture_template.add_ptemplate(
            pstore.get_ptemplate(
                pstore.PNames.TIME_RANGE,
                default=0.0,
                enforce_default=True
            )
        )
        capture_template.add_ptemplate(
            pstore.get_ptemplate(
                pstore.PNames.SAMPLE_RATE,
                default=128000,
                add_pconstraints = [
                    EnforceBounds(lower_bound=self.get_spec(pstore.SpecNames.SAMPLE_RATE_LOWER_BOUND),
                                  upper_bound=self.get_spec(pstore.SpecNames.SAMPLE_RATE_UPPER_BOUND))
                ]
            )
        )
        capture_template.add_ptemplate(
            pstore.get_ptemplate(
                pstore.PNames.BATCH_SIZE,
                default=3.0,
                enforce_default=False
            )
        )
        capture_template.add_ptemplate(
            pstore.get_ptemplate(
                pstore.PNames.WINDOW_TYPE,
                default="boxcar",
                enforce_default=True
            )
        )
        capture_template.add_ptemplate(
            pstore.get_ptemplate(
                pstore.PNames.WINDOW_HOP,
                default=512
            )
        )
        capture_template.add_ptemplate(
            pstore.get_ptemplate(
                pstore.PNames.WINDOW_SIZE,
                default=512
            )
        )
        capture_template.add_ptemplate(
            pstore.get_ptemplate(
                pstore.PNames.EVENT_HANDLER_KEY,
                default="fixed-center-frequency",
                enforce_default=True
            )
        )
        capture_template.add_ptemplate(
            pstore.get_ptemplate(
                pstore.PNames.CHUNK_KEY,
                default="fixed-center-frequency",
                enforce_default=True
            )
        )
        capture_template.add_ptemplate(
            pstore.get_ptemplate(
                pstore.PNames.WATCH_EXTENSION,
                default="bin",
                enforce_default=True
            )
        )

        #
        # Add custom ptemplates
        #
        capture_template.add_ptemplate(
            PTemplate(
                pstore.PNames.AMPLITUDE,
                float,
                default=2.0
            )
        )
        capture_template.add_ptemplate(
            PTemplate(
                pstore.PNames.FREQUENCY,
                int,
                default=32000,
                add_pconstraints=[
                    EnforceBounds(lower_bound=self.get_spec(pstore.SpecNames.FREQUENCY_LOWER_BOUND),
                                  upper_bound=self.get_spec(pstore.SpecNames.FREQUENCY_UPPER_BOUND))
                ]
            )
        )
        return capture_template


    def __make_capture_template_tagged_staircase(self) -> CaptureTemplate:
        capture_template = CaptureTemplate()
        #
        # Add default ptemplates
        #
        capture_template.add_ptemplate(
            pstore.get_ptemplate(
                pstore.PNames.TIME_RESOLUTION,
                default=0.0,
                enforce_default=True
            )
        )
        capture_template.add_ptemplate(
            pstore.get_ptemplate(
                pstore.PNames.FREQUENCY_RESOLUTION,
                default=0.0,
                enforce_default=True
            )
        )
        capture_template.add_ptemplate(
            pstore.get_ptemplate(
                pstore.PNames.TIME_RANGE,
                default=0.0,
                enforce_default=True
            )
        )
        capture_template.add_ptemplate(
            pstore.get_ptemplate(
                pstore.PNames.SAMPLE_RATE,
                default=128000,
                add_pconstraints = [
                    EnforceBounds(lower_bound=self.get_spec(pstore.SpecNames.SAMPLE_RATE_LOWER_BOUND),
                                  upper_bound=self.get_spec(pstore.SpecNames.SAMPLE_RATE_UPPER_BOUND))
                ]
            )
        )
        capture_template.add_ptemplate(
            pstore.get_ptemplate(
                pstore.PNames.BATCH_SIZE,
                default=3.0,
                enforce_default=False
            )
        )
        capture_template.add_ptemplate(
            pstore.get_ptemplate(
                pstore.PNames.WINDOW_TYPE,
                default="boxcar",
                enforce_default=True
            )
        )
        capture_template.add_ptemplate(
            pstore.get_ptemplate(
                pstore.PNames.WINDOW_HOP,
                default=512
            )
        )
        capture_template.add_ptemplate(
            pstore.get_ptemplate(
                pstore.PNames.WINDOW_SIZE,
                default=512
            )
        )
        capture_template.add_ptemplate(
            pstore.get_ptemplate(
                pstore.PNames.EVENT_HANDLER_KEY,
                default="swept-center-frequency",
                enforce_default=True
            )
        )
        capture_template.add_ptemplate(
            pstore.get_ptemplate(
                pstore.PNames.CHUNK_KEY,
                default="swept-center-frequency",
                enforce_default=True
            )
        )
        capture_template.add_ptemplate(
            pstore.get_ptemplate(
                pstore.PNames.WATCH_EXTENSION,
                default="bin",
                enforce_default=True
            )
        )

        #
        # Add custom ptemplates
        #
        capture_template.add_ptemplate(
            PTemplate(
                pstore.PNames.MIN_SAMPLES_PER_STEP,
                int,
                default=4000,
                add_pconstraints=[
                    enforce_positive
                ]
            )
        )
        capture_template.add_ptemplate(
            PTemplate(
                pstore.PNames.MAX_SAMPLES_PER_STEP,
                int,
                default=5000,
                add_pconstraints=[
                    enforce_positive
                ]
            )
        )
        capture_template.add_ptemplate(
            PTemplate(
                pstore.PNames.FREQ_STEP,
                int,
                default=128000,
                add_pconstraints=[
                    enforce_positive
                ]
            )
        )
        capture_template.add_ptemplate(
            PTemplate(
                pstore.PNames.STEP_INCREMENT,
                int,
                default=200,
                add_pconstraints=[
                    enforce_positive
                ]
            )
        )
        return capture_template
    
    
    def __get_pvalidator_cosine_signal_1(self) -> Callable:

        def pvalidator_cosine_signal_1(parameters: Parameters):
            sample_rate          = parameters.get_parameter_value(pstore.PNames.SAMPLE_RATE)
            frequency            = parameters.get_parameter_value(pstore.PNames.FREQUENCY)
            window_size          = parameters.get_parameter_value(pstore.PNames.WINDOW_SIZE)

            pvalidators.validate_window(parameters)

            # check that the sample rate is an integer multiple of the underlying signal frequency
            if sample_rate % frequency != 0:
                raise ValueError("The sampling rate must be some integer multiple of frequency")


            a = sample_rate/frequency
            if a < 2:
                raise ValueError((f"The ratio of sampling rate over frequency must be a natural number greater than two. "
                                f"Got {a}"))
            

            # analytical requirement
            # if p is the number of sampled cycles, we can find that p = window_size / a
            # the number of sampled cycles must be a positive natural number.
            p = window_size / a
            if window_size % a != 0:
                raise ValueError((f"The number of sampled cycles must be a positive natural number. "
                                f"Computed that p={p}"))
            
        return pvalidator_cosine_signal_1


    def __get_pvalidator_tagged_staircase(self) -> None:

        def pvalidator_tagged_staircase(parameters: Parameters):
            freq_step            = parameters.get_parameter_value(pstore.PNames.FREQ_STEP)
            sample_rate          = parameters.get_parameter_value(pstore.PNames.SAMPLE_RATE)
            min_samples_per_step = parameters.get_parameter_value(pstore.PNames.MIN_SAMPLES_PER_STEP)
            max_samples_per_step = parameters.get_parameter_value(pstore.PNames.MAX_SAMPLES_PER_STEP)
            
            if freq_step != sample_rate:
                raise ValueError(f"The frequency step must be equal to the sampling rate")
            
            
            if min_samples_per_step > max_samples_per_step:
                raise ValueError((f"Minimum samples per step cannot be greater than the maximum samples per step. "
                                f"Got {min_samples_per_step}, which is greater than {max_samples_per_step}"))
            
        return pvalidator_tagged_staircase
        