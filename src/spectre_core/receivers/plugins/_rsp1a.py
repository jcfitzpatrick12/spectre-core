# SPDX-FileCopyrightText: © 2024 Jimmy Fitzpatrick <jcfitzpatrick12@gmail.com>
# This file is part of SPECTRE
# SPDX-License-Identifier: GPL-3.0-or-later

from dataclasses import dataclass

from spectre_core.capture_configs import CaptureMode
from ._receiver_names import ReceiverName
from .gr._rsp1a import CaptureMethod
from .._spec_names import SpecName
from ._sdrplay_receiver import SDRPlayReceiver
from .._register import register_receiver

@dataclass(frozen=True)
class Mode:
    """Operating mode for the `RSP1A` receiver."""
    FIXED_CENTER_FREQUENCY  = CaptureMode.FIXED_CENTER_FREQUENCY
    SWEPT_CENTER_FREQUENCY  = CaptureMode.SWEPT_CENTER_FREQUENCY


@register_receiver(ReceiverName.RSP1A)
class RSP1A(SDRPlayReceiver):
    """Receiver implementation for the SDRPlay RSPduo (https://www.sdrplay.com/rsp1a/)"""
    def _add_specs(self) -> None:
        self.add_spec( SpecName.SAMPLE_RATE_LOWER_BOUND, 200e3     )
        self.add_spec( SpecName.SAMPLE_RATE_UPPER_BOUND, 10e6      )
        self.add_spec( SpecName.FREQUENCY_LOWER_BOUND  , 1e3       )
        self.add_spec( SpecName.FREQUENCY_UPPER_BOUND  , 2e9       )
        self.add_spec( SpecName.IF_GAIN_UPPER_BOUND    , -20       )
        self.add_spec( SpecName.RF_GAIN_UPPER_BOUND    , 0         )
        self.add_spec( SpecName.API_RETUNING_LATENCY   , 50 * 1e-3 )
        self.add_spec( SpecName.BANDWIDTH_OPTIONS, 
                      [200000, 300000, 600000, 1536000, 5000000, 6000000, 7000000, 8000000])


    def _add_capture_methods(self) -> None:
        self.add_capture_method(Mode.FIXED_CENTER_FREQUENCY, 
                                CaptureMethod.fixed_center_frequency)
        self.add_capture_method(Mode.SWEPT_CENTER_FREQUENCY,
                                CaptureMethod.swept_center_frequency)
    

    def _add_capture_templates(self):
        self.add_capture_template(Mode.FIXED_CENTER_FREQUENCY,
                                  self._get_capture_template_fixed_center_frequency())
        self.add_capture_template(Mode.SWEPT_CENTER_FREQUENCY,
                                  self._get_capture_template_swept_center_frequency())
        
    
    def _add_pvalidators(self):
        self.add_pvalidator(Mode.FIXED_CENTER_FREQUENCY,
                            self._get_pvalidator_fixed_center_frequency())
        self.add_pvalidator(Mode.SWEPT_CENTER_FREQUENCY,
                            self._get_pvalidator_swept_center_frequency())
