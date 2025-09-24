# SPDX-FileCopyrightText: © 2024-2025 Jimmy Fitzpatrick <jcfitzpatrick12@gmail.com>
# This file is part of SPECTRE
# SPDX-License-Identifier: GPL-3.0-or-later

from dataclasses import dataclass
from functools import partial
from typing import Callable, Optional

from spectre_core.capture_configs import (
    CaptureTemplate,
    CaptureMode,
    Parameters,
    PName,
    Bound,
    OneOf,
    validate_fixed_center_frequency,
    get_base_capture_template,
    get_base_ptemplate,
)

from ._receiver_names import ReceiverName
from ._hackrf_gr import fixed_center_frequency
from ._gr import capture
from .._receiver import Receiver
from .._register import register_receiver
from .._specs import SpecName


def _make_pvalidator_fixed_center_frequency(
    receiver: Receiver,
) -> Callable[[Parameters], None]:
    def pvalidator(parameters: Parameters) -> None:
        validate_fixed_center_frequency(parameters)

    return pvalidator


def _make_capture_template_fixed_center_frequency(
    receiver: Receiver,
) -> CaptureTemplate:

    capture_template = get_base_capture_template(CaptureMode.FIXED_CENTER_FREQUENCY)
    capture_template.add_ptemplate(get_base_ptemplate(PName.BANDWIDTH))
    capture_template.add_ptemplate(get_base_ptemplate(PName.VGA_GAIN))
    capture_template.add_ptemplate(get_base_ptemplate(PName.LNA_GAIN))
    capture_template.add_ptemplate(get_base_ptemplate(PName.AMP_ON))

    capture_template.set_defaults(
        (PName.BATCH_SIZE, 3.0),
        (PName.CENTER_FREQUENCY, 95800000),
        (PName.SAMPLE_RATE, 2e6),
        (PName.BANDWIDTH, 2e6),
        (PName.WINDOW_HOP, 1024),
        (PName.WINDOW_SIZE, 2048),
        (PName.WINDOW_TYPE, "blackman"),
        (PName.VGA_GAIN, 20),
        (PName.LNA_GAIN, 20),
        (PName.AMP_ON, False),
    )

    capture_template.add_pconstraint(
        PName.CENTER_FREQUENCY,
        [
            Bound(
                lower_bound=receiver.get_spec(SpecName.FREQUENCY_LOWER_BOUND),
                upper_bound=receiver.get_spec(SpecName.FREQUENCY_UPPER_BOUND),
            )
        ],
    )
    capture_template.add_pconstraint(
        PName.SAMPLE_RATE,
        [
            Bound(
                lower_bound=receiver.get_spec(SpecName.SAMPLE_RATE_LOWER_BOUND),
                upper_bound=receiver.get_spec(SpecName.SAMPLE_RATE_UPPER_BOUND),
            ),
            OneOf(
                [
                    1e6,
                    2e6,
                    3e6,
                    4e6,
                    5e6,
                    6e6,
                    7e6,
                    8e6,
                    9e6,
                    10e6,
                    11e6,
                    12e6,
                    13e6,
                    14e6,
                    15e6,
                    16e6,
                    17e6,
                    18e6,
                    19e6,
                    20e6,
                ]
            ),
        ],
    )
    capture_template.add_pconstraint(
        PName.LNA_GAIN,
        [
            Bound(
                lower_bound=receiver.get_spec(SpecName.LNA_GAIN_LOWER_BOUND),
                upper_bound=receiver.get_spec(SpecName.LNA_GAIN_UPPER_BOUND),
            )
        ],
    )
    capture_template.add_pconstraint(
        PName.VGA_GAIN,
        [
            Bound(
                lower_bound=receiver.get_spec(SpecName.VGA_GAIN_LOWER_BOUND),
                upper_bound=receiver.get_spec(SpecName.VGA_GAIN_UPPER_BOUND),
            )
        ],
    )

    return capture_template


@dataclass(frozen=True)
class _Mode:
    """An operating mode for the `HackRF One` receiver."""

    FIXED_CENTER_FREQUENCY = "fixed_center_frequency"


@register_receiver(ReceiverName.HACKRFONE)
class HackRFOne(Receiver):
    """Receiver implementation for the Hack RF One (https://greatscottgadgets.com/hackrf/one/)"""

    def __init__(self, name: ReceiverName, mode: Optional[str] = None) -> None:
        super().__init__(name, mode)

        self.add_spec(SpecName.FREQUENCY_LOWER_BOUND, 1e6)
        self.add_spec(SpecName.FREQUENCY_UPPER_BOUND, 6e9)
        self.add_spec(SpecName.SAMPLE_RATE_LOWER_BOUND, 1e6)
        self.add_spec(SpecName.SAMPLE_RATE_UPPER_BOUND, 20e6)
        self.add_spec(SpecName.LNA_GAIN_LOWER_BOUND, 0)
        self.add_spec(SpecName.LNA_GAIN_UPPER_BOUND, 40)
        self.add_spec(SpecName.VGA_GAIN_LOWER_BOUND, 0)
        self.add_spec(SpecName.VGA_GAIN_UPPER_BOUND, 62)
        self.add_spec(SpecName.AMP_ON, 14)

        self.add_mode(
            _Mode.FIXED_CENTER_FREQUENCY,
            partial(capture, top_block_cls=fixed_center_frequency),
            _make_capture_template_fixed_center_frequency(self),
            _make_pvalidator_fixed_center_frequency(self),
        )
