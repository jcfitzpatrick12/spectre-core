# SPDX-FileCopyrightText: © 2024 Jimmy Fitzpatrick <jcfitzpatrick12@gmail.com>
# This file is part of SPECTRE
# SPDX-License-Identifier: GPL-3.0-or-later

from dataclasses import dataclass
from typing import Optional, Callable

from spectre_core.capture_config import CaptureTemplate
from spectre_core.pconstraints import enforce_positive, EnforceBounds
from spectre_core.parameters import PTemplate, Parameters
from spectre_core import pstore
from spectre_core.receivers import pvalidators
from spectre_core.receivers.spec_names import SpecNames
from spectre_core.receivers.base import BaseReceiver
from spectre_core.receivers.receiver_register import register_receiver
from spectre_core.receivers.library.test.gr import (
    cosine_signal_1,
    tagged_staircase
)
from spectre_core.pstore import (
    make_base_capture_template,
    get_base_capture_template,
    get_base_ptemplate,
    PNames,
    CaptureModes
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
        self.add_spec( SpecNames.SAMPLE_RATE_LOWER_BOUND, 64000  )
        self.add_spec( SpecNames.SAMPLE_RATE_UPPER_BOUND, 640000 )
        self.add_spec( SpecNames.FREQUENCY_LOWER_BOUND  , 16000  )
        self.add_spec( SpecNames.FREQUENCY_UPPER_BOUND  , 160000 )


    def __get_capture_method_cosine_signal_1(self) -> Callable:
        return cosine_signal_1.capture
    

    def __get_capture_method_tagged_staircase(self) -> Callable:
        return tagged_staircase.capture
        

    def __get_capture_template_cosine_signal_1(self) -> CaptureTemplate:
        #
        # Create the base template
        #
        capture_template = get_base_capture_template( CaptureModes.FIXED_CENTER_FREQUENCY )
        capture_template.add_ptemplate( get_base_ptemplate(PNames.COSINE_AMPLITUDE) )
        capture_template.add_ptemplate( get_base_ptemplate(PNames.COSINE_FREQUENCY) )

        #
        # Update the defaults
        #
        capture_template.set_defaults(
            (PNames.BATCH_SIZE,            3.0),
            (PNames.CENTER_FREQUENCY,      0.0),
            (PNames.COSINE_AMPLITUDE,      2.0),
            (PNames.COSINE_FREQUENCY,      32000),
            (PNames.FREQUENCY_RESOLUTION,  0.0),
            (PNames.SAMPLE_RATE,           128000),
            (PNames.TIME_RANGE,            0.0),
            (PNames.TIME_RESOLUTION,       0.0),
            (PNames.WINDOW_HOP,            512),
            (PNames.WINDOW_SIZE,           512),
            (PNames.WINDOW_TYPE,           "boxcar"),
            (PNames.EVENT_HANDLER_KEY,     CaptureModes.FIXED_CENTER_FREQUENCY)
            (PNames.CHUNK_KEY,             CaptureModes.FIXED_CENTER_FREQUENCY)
            (PNames.WATCH_EXTENSION,       "bin")
        )

        #
        # Enforce defaults
        #
        capture_template.enforce_defaults(
            PNames.CENTER_FREQUENCY,
            PNames.TIME_RESOLUTION,
            PNames.TIME_RANGE,
            PNames.FREQUENCY_RESOLUTION,
            PNames.WINDOW_TYPE,
            PNames.EVENT_HANDLER_KEY,
            PNames.CHUNK_KEY,
            PNames.WATCH_EXTENSION
        )


        #
        # Adding pconstraints
        #
        capture_template.add_pconstraint(
            PNames.SAMPLE_RATE,
            [
                EnforceBounds(
                    lower_bound=self.get_spec(SpecNames.SAMPLE_RATE_LOWER_BOUND),
                    upper_bound=self.get_spec(SpecNames.SAMPLE_RATE_UPPER_BOUND)
                )
            ]
        )
        capture_template.add_pconstraint(
            PNames.COSINE_FREQUENCY,
            [
                EnforceBounds(
                    lower_bound=self.get_spec(SpecNames.FREQUENCY_LOWER_BOUND),
                    upper_bound=self.get_spec(SpecNames.FREQUENCY_UPPER_BOUND)
                )
            ]
        )
        return capture_template


    def __make_capture_template_tagged_staircase(self) -> CaptureTemplate:
        #
        # Make the base template
        #
        capture_template = make_base_capture_template(
                PNames.TIME_RESOLUTION,
                PNames.FREQUENCY_RESOLUTION,
                PNames.TIME_RANGE,
                PNames.SAMPLE_RATE,
                PNames.BATCH_SIZE,
                PNames.WINDOW_TYPE,
                PNames.WINDOW_HOP,
                PNames.WINDOW_SIZE,
                PNames.EVENT_HANDLER_KEY,
                PNames.CHUNK_KEY,
                PNames.MIN_SAMPLES_PER_STEP,
                PNames.MAX_SAMPLES_PER_STEP,
                PNames.FREQUENCY_STEP,
                PNames.STEP_INCREMENT
        )

        #
        # Update the defaults
        #
        capture_template.set_defaults(
            (PNames.BATCH_SIZE,            3.0),
            (PNames.CHUNK_KEY,             CaptureModes.SWEPT_CENTER_FREQUENCY),
            (PNames.EVENT_HANDLER_KEY,     CaptureModes.SWEPT_CENTER_FREQUENCY),
            (PNames.FREQUENCY_RESOLUTION,  0.0),
            (PNames.FREQUENCY_STEP,        128000),
            (PNames.MAX_SAMPLES_PER_STEP,  5000),
            (PNames.MIN_SAMPLES_PER_STEP,  4000),
            (PNames.SAMPLE_RATE,           128000),
            (PNames.STEP_INCREMENT,        200),
            (PNames.TIME_RANGE,            0.0),
            (PNames.TIME_RESOLUTION,       0.0),
            (PNames.WATCH_EXTENSION,       "bin"),
            (PNames.WINDOW_HOP,            512),
            (PNames.WINDOW_SIZE,           512),
            (PNames.WINDOW_TYPE,           "boxcar"),
        )


        #
        # Enforce defaults
        #
        capture_template.enforce_defaults(
            PNames.CENTER_FREQUENCY,
            PNames.TIME_RESOLUTION,
            PNames.TIME_RANGE,
            PNames.FREQUENCY_RESOLUTION,
            PNames.WINDOW_TYPE,
            PNames.EVENT_HANDLER_KEY,
            PNames.CHUNK_KEY,
            PNames.WATCH_EXTENSION
        )

        return capture_template
    
    
    def __get_pvalidator_cosine_signal_1(self) -> Callable:

        def pvalidator_cosine_signal_1(parameters: Parameters):
            sample_rate          = parameters.get_parameter_value(PNames.SAMPLE_RATE)
            frequency            = parameters.get_parameter_value(PNames.FREQUENCY)
            window_size          = parameters.get_parameter_value(PNames.WINDOW_SIZE)

            pvalidators.validate_window(parameters)

            # check that the sample rate is an integer multiple of the underlying signal frequency
            if sample_rate % frequency != 0:
                raise ValueError("The sampling rate must be some integer multiple of frequency")


            a = sample_rate/frequency
            if a < 2:
                raise ValueError((f"The ratio of sampling rate over frequency must be greater than two. "
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
            freq_step            = parameters.get_parameter_value(PNames.FREQUENCY_STEP)
            sample_rate          = parameters.get_parameter_value(PNames.SAMPLE_RATE)
            min_samples_per_step = parameters.get_parameter_value(PNames.MIN_SAMPLES_PER_STEP)
            max_samples_per_step = parameters.get_parameter_value(PNames.MAX_SAMPLES_PER_STEP)
            
            if freq_step != sample_rate:
                raise ValueError(f"The frequency step must be equal to the sampling rate")
            
            
            if min_samples_per_step > max_samples_per_step:
                raise ValueError((f"Minimum samples per step cannot be greater than the maximum samples per step. "
                                f"Got {min_samples_per_step}, which is greater than {max_samples_per_step}"))
            
        return pvalidator_tagged_staircase
        