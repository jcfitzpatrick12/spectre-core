# SPDX-FileCopyrightText: © 2024-2025 Jimmy Fitzpatrick <jcfitzpatrick12@gmail.com>
# This file is part of SPECTRE
# SPDX-License-Identifier: GPL-3.0-or-later

from dataclasses import dataclass

from ._receiver_names import ReceiverName
from .gr._rspduo import CaptureMethod
from .._spec_names import SpecName
from ._sdrplay_receiver import (
    get_pvalidator_fixed_center_frequency,
    get_pvalidator_swept_center_frequency,
    get_capture_template_fixed_center_frequency,
    get_capture_template_swept_center_frequency,
)
from .._base import BaseReceiver
from .._register import register_receiver


@dataclass
class Mode:
    """An operating mode for the `RSPduo` receiver."""

    TUNER_1_FIXED_CENTER_FREQUENCY = f"tuner_1_fixed_center_frequency"
    TUNER_2_FIXED_CENTER_FREQUENCY = f"tuner_2_fixed_center_frequency"
    TUNER_1_SWEPT_CENTER_FREQUENCY = f"tuner_1_swept_center_frequency"


@register_receiver(ReceiverName.RSPDUO)
class RSPduo(BaseReceiver):
    """Receiver implementation for the SDRPlay RSPduo (https://www.sdrplay.com/rspduo/)"""

    def _add_specs(self) -> None:
        self.add_spec(SpecName.SAMPLE_RATE_LOWER_BOUND, 200e3)
        self.add_spec(SpecName.SAMPLE_RATE_UPPER_BOUND, 10e6)
        self.add_spec(SpecName.FREQUENCY_LOWER_BOUND, 1e3)
        self.add_spec(SpecName.FREQUENCY_UPPER_BOUND, 2e9)
        self.add_spec(SpecName.IF_GAIN_UPPER_BOUND, -20)
        self.add_spec(SpecName.RF_GAIN_UPPER_BOUND, 0)
        self.add_spec(SpecName.API_RETUNING_LATENCY, 50 * 1e-3)
        self.add_spec(
            SpecName.BANDWIDTH_OPTIONS,
            [200000, 300000, 600000, 1536000, 5000000, 6000000, 7000000, 8000000],
        )

    def _add_capture_methods(self) -> None:
        self.add_capture_method(
            Mode.TUNER_1_FIXED_CENTER_FREQUENCY,
            CaptureMethod.tuner_1_fixed_center_frequency,
        )
        self.add_capture_method(
            Mode.TUNER_2_FIXED_CENTER_FREQUENCY,
            CaptureMethod.tuner_2_fixed_center_frequency,
        )
        self.add_capture_method(
            Mode.TUNER_1_SWEPT_CENTER_FREQUENCY,
            CaptureMethod.tuner_1_swept_center_frequency,
        )

    def _add_capture_templates(self) -> None:
        self.add_capture_template(
            Mode.TUNER_1_FIXED_CENTER_FREQUENCY,
            get_capture_template_fixed_center_frequency(self),
        )
        self.add_capture_template(
            Mode.TUNER_2_FIXED_CENTER_FREQUENCY,
            get_capture_template_fixed_center_frequency(self),
        )
        self.add_capture_template(
            Mode.TUNER_1_SWEPT_CENTER_FREQUENCY,
            get_capture_template_swept_center_frequency(self),
        )

    def _add_pvalidators(self) -> None:
        self.add_pvalidator(
            Mode.TUNER_1_FIXED_CENTER_FREQUENCY,
            get_pvalidator_fixed_center_frequency(self),
        )
        self.add_pvalidator(
            Mode.TUNER_2_FIXED_CENTER_FREQUENCY,
            get_pvalidator_fixed_center_frequency(self),
        )
        self.add_pvalidator(
            Mode.TUNER_1_SWEPT_CENTER_FREQUENCY,
            get_pvalidator_swept_center_frequency(self),
        )
