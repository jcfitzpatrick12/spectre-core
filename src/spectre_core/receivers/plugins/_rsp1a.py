# SPDX-FileCopyrightText: © 2024-2025 Jimmy Fitzpatrick <jcfitzpatrick12@gmail.com>
# This file is part of SPECTRE
# SPDX-License-Identifier: GPL-3.0-or-later

from dataclasses import dataclass
from typing import Optional
from functools import partial

from ._receiver_names import ReceiverName
from .gr._gr_rsp1a import swept_center_frequency, fixed_center_frequency
from .gr._base import capture
from ._sdrplay_receiver import (
    get_pvalidator_fixed_center_frequency,
    get_pvalidator_swept_center_frequency,
    get_capture_template_fixed_center_frequency,
    get_capture_template_swept_center_frequency,
)
from .._receiver import SpecName, Receiver
from .._register import register_receiver
from ._receiver_names import ReceiverName


@dataclass(frozen=True)
class Mode:
    """An operating mode for the `RSP1A` receiver."""

    FIXED_CENTER_FREQUENCY = "fixed_center_frequency"
    SWEPT_CENTER_FREQUENCY = "swept_center_frequency"


@register_receiver(ReceiverName.RSP1A)
class RSP1A(Receiver):
    """Receiver implementation for the SDRPlay RSP1A (https://www.sdrplay.com/rsp1a/)"""

    def __init__(self, name: ReceiverName, mode: Optional[str] = None) -> None:
        super().__init__(name, mode)

        self.add_spec(SpecName.SAMPLE_RATE_LOWER_BOUND, 200e3)
        self.add_spec(SpecName.SAMPLE_RATE_UPPER_BOUND, 10e6)
        self.add_spec(SpecName.FREQUENCY_LOWER_BOUND, 1e3)
        self.add_spec(SpecName.FREQUENCY_UPPER_BOUND, 2e9)
        self.add_spec(SpecName.IF_GAIN_UPPER_BOUND, -20)
        self.add_spec(SpecName.RF_GAIN_UPPER_BOUND, 0)
        self.add_spec(SpecName.API_RETUNING_LATENCY, 25 * 1e-3)
        self.add_spec(
            SpecName.BANDWIDTH_OPTIONS,
            [200000, 300000, 600000, 1536000, 5000000, 6000000, 7000000, 8000000],
        )

        self.add_mode(
            Mode.FIXED_CENTER_FREQUENCY,
            partial(capture, top_block_cls=fixed_center_frequency),
            get_capture_template_fixed_center_frequency(self.specs),
            get_pvalidator_fixed_center_frequency(self.specs),
        )
        self.add_mode(
            Mode.SWEPT_CENTER_FREQUENCY,
            partial(
                capture, top_block_cls=swept_center_frequency, max_noutput_items=1024
            ),
            get_capture_template_swept_center_frequency(self.specs),
            get_pvalidator_swept_center_frequency(self.specs),
        )
