# SPDX-FileCopyrightText: © 2024 Jimmy Fitzpatrick <jcfitzpatrick12@gmail.com>
# This file is part of SPECTRE
# SPDX-License-Identifier: GPL-3.0-or-later

from typing import Optional
from dataclasses import dataclass
from functools import partial

from spectre_core.capture_configs import (
    CaptureModes
)
from ..gr._rspduo import CaptureMethods
from .._spec_names import SpecNames
from ._sdrplay_receiver import SDRPlayReceiver
from .._register import register_receiver

@dataclass
class Modes:
    TUNER_1_FIXED_CENTER_FREQUENCY  = f"tuner-1-{CaptureModes.FIXED_CENTER_FREQUENCY}"
    TUNER_2_FIXED_CENTER_FREQUENCY  = f"tuner-2-{CaptureModes.FIXED_CENTER_FREQUENCY}"
    TUNER_1_SWEPT_CENTER_FREQUENCY  = f"tuner-1-{CaptureModes.SWEPT_CENTER_FREQUENCY}"


@register_receiver("rspduo")
class _Receiver(SDRPlayReceiver):
    def __init__(self, 
                 name: str,
                 mode: Optional[str]):
        super().__init__(name,
                         mode)
        

    def _add_specs(self) -> None:
        self.add_spec( SpecNames.SAMPLE_RATE_LOWER_BOUND, 200e3     ) # Hz
        self.add_spec( SpecNames.SAMPLE_RATE_UPPER_BOUND, 10e6      ) # Hz
        self.add_spec( SpecNames.FREQUENCY_LOWER_BOUND  , 1e3       ) # Hz
        self.add_spec( SpecNames.FREQUENCY_UPPER_BOUND  , 2e9       ) # Hz
        self.add_spec( SpecNames.IF_GAIN_UPPER_BOUND    , -20       ) # dB
        self.add_spec( SpecNames.RF_GAIN_UPPER_BOUND    , 0         ) # dB
        self.add_spec( SpecNames.API_RETUNING_LATENCY   , 50 * 1e-3 ) # s
        self.add_spec( SpecNames.BANDWIDTH_OPTIONS, 
                      [200000, 300000, 600000, 1536000, 5000000, 6000000, 7000000, 8000000])


    def _add_capture_methods(self) -> None:
        self.add_capture_method(Modes.TUNER_1_FIXED_CENTER_FREQUENCY, 
                                CaptureMethods.tuner_1_fixed_center_frequency)
        self.add_capture_method(Modes.TUNER_2_FIXED_CENTER_FREQUENCY, 
                                CaptureMethods.tuner_2_fixed_center_frequency)
        self.add_capture_method(Modes.TUNER_1_SWEPT_CENTER_FREQUENCY, 
                                CaptureMethods.tuner_1_swept_center_frequency)
    

    def _add_capture_templates(self):
        self.add_capture_template(Modes.TUNER_1_FIXED_CENTER_FREQUENCY,
                                  self._get_capture_template_fixed_center_frequency())
        self.add_capture_template(Modes.TUNER_2_FIXED_CENTER_FREQUENCY,
                                  self._get_capture_template_fixed_center_frequency())
        self.add_capture_template(Modes.TUNER_1_SWEPT_CENTER_FREQUENCY,
                                  self._get_capture_template_swept_center_frequency())
        
    
    def _add_pvalidators(self):
        self.add_pvalidator(Modes.TUNER_1_FIXED_CENTER_FREQUENCY,
                            self._get_pvalidator_fixed_center_frequency())
        self.add_pvalidator(Modes.TUNER_2_FIXED_CENTER_FREQUENCY,
                            self._get_pvalidator_fixed_center_frequency())
        self.add_pvalidator(Modes.TUNER_1_SWEPT_CENTER_FREQUENCY,
                            self._get_pvalidator_swept_center_frequency())
