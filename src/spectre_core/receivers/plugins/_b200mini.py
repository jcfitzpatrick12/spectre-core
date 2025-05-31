# SPDX-FileCopyrightText: © 2024-2025 Jimmy Fitzpatrick <jcfitzpatrick12@gmail.com>
# This file is part of SPECTRE
# SPDX-License-Identifier: GPL-3.0-or-later

from dataclasses import dataclass

from ._receiver_names import ReceiverName
from ._usrp import (
    get_pvalidator_fixed_center_frequency,
    get_pvalidator_swept_center_frequency,
    get_capture_template_fixed_center_frequency,
    get_capture_template_swept_center_frequency,
)
from .gr._usrp import CaptureMethod
from .._spec_names import SpecName
from .._base import BaseReceiver
from .._register import register_receiver


@dataclass(frozen=True)
class Mode:
    """An operating mode for the `B200mini` receiver."""

    FIXED_CENTER_FREQUENCY = "fixed_center_frequency"
    SWEPT_CENTER_FREQUENCY = "swept_center_frequency"


@register_receiver(ReceiverName.B200MINI)
class B200mini(BaseReceiver):
    """Receiver implementation for the USRP B200mini (https://www.ettus.com/all-products/usrp-b200mini/)"""

    def _add_specs(self) -> None:
        self.add_spec(SpecName.SAMPLE_RATE_LOWER_BOUND, 200e3)
        self.add_spec(SpecName.SAMPLE_RATE_UPPER_BOUND, 56e6)
        self.add_spec(SpecName.FREQUENCY_LOWER_BOUND, 70e6)
        self.add_spec(SpecName.FREQUENCY_UPPER_BOUND, 6e9)
        self.add_spec(SpecName.BANDWIDTH_LOWER_BOUND, 200e3)
        self.add_spec(SpecName.BANDWIDTH_UPPER_BOUND, 56e6)
        self.add_spec(SpecName.GAIN_UPPER_BOUND, 76)
        self.add_spec(SpecName.WIRE_FORMATS, ["sc8", "sc12", "sc16"])
        self.add_spec(SpecName.MASTER_CLOCK_RATE_LOWER_BOUND, 5e6)
        self.add_spec(SpecName.MASTER_CLOCK_RATE_UPPER_BOUND, 61.44e6)
        self.add_spec(
            SpecName.API_RETUNING_LATENCY, 1e-5
        )  # TODO: This is a ballpark, pending empirical testing

    def _add_capture_methods(self) -> None:
        self.add_capture_method(
            Mode.FIXED_CENTER_FREQUENCY, CaptureMethod.fixed_center_frequency
        )
        self.add_capture_method(
            Mode.SWEPT_CENTER_FREQUENCY, CaptureMethod.swept_center_frequency
        )

    def _add_capture_templates(self) -> None:
        self.add_capture_template(
            Mode.FIXED_CENTER_FREQUENCY,
            get_capture_template_fixed_center_frequency(self),
        )
        self.add_capture_template(
            Mode.SWEPT_CENTER_FREQUENCY,
            get_capture_template_swept_center_frequency(self),
        )

    def _add_pvalidators(self) -> None:
        self.add_pvalidator(
            Mode.FIXED_CENTER_FREQUENCY, get_pvalidator_fixed_center_frequency(self)
        )
        self.add_pvalidator(
            Mode.SWEPT_CENTER_FREQUENCY, get_pvalidator_swept_center_frequency(self)
        )
