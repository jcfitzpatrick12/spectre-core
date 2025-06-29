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
    Bound,
    PName,
    OneOf,
    get_base_capture_template,
    get_base_ptemplate,
    validate_fixed_center_frequency,
    validate_swept_center_frequency,
    validate_sample_rate_with_master_clock_rate,
)

from ._receiver_names import ReceiverName
from ._gr import capture
from ._b200mini_gr import fixed_center_frequency, swept_center_frequency
from .._receiver import Receiver
from .._specs import SpecName
from .._register import register_receiver


def _make_pvalidator_fixed_center_frequency(
    receiver: Receiver,
) -> Callable[[Parameters], None]:
    def pvalidator(parameters: Parameters) -> None:
        validate_fixed_center_frequency(parameters)
        validate_sample_rate_with_master_clock_rate(parameters)

    return pvalidator


def _make_pvalidator_swept_center_frequency(
    receiver: Receiver,
) -> Callable[[Parameters], None]:
    def pvalidator(parameters: Parameters) -> None:
        validate_swept_center_frequency(
            parameters, receiver.get_spec(SpecName.API_RETUNING_LATENCY)
        )
        validate_sample_rate_with_master_clock_rate(parameters)

    return pvalidator


def _make_capture_template_fixed_center_frequency(
    receiver: Receiver,
) -> CaptureTemplate:

    capture_template = get_base_capture_template(CaptureMode.FIXED_CENTER_FREQUENCY)
    capture_template.add_ptemplate(get_base_ptemplate(PName.BANDWIDTH))
    capture_template.add_ptemplate(get_base_ptemplate(PName.GAIN))
    capture_template.add_ptemplate(get_base_ptemplate(PName.WIRE_FORMAT))
    capture_template.add_ptemplate(get_base_ptemplate(PName.MASTER_CLOCK_RATE))

    capture_template.set_defaults(
        (PName.BATCH_SIZE, 4.0),
        (PName.CENTER_FREQUENCY, 95800000),
        (PName.SAMPLE_RATE, 2000000),
        (PName.BANDWIDTH, 2000000),
        (PName.WINDOW_HOP, 512),
        (PName.WINDOW_SIZE, 1024),
        (PName.WINDOW_TYPE, "blackman"),
        (PName.GAIN, 35),
        (PName.WIRE_FORMAT, "sc16"),
        (PName.MASTER_CLOCK_RATE, 40e6),
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
            )
        ],
    )
    capture_template.add_pconstraint(
        PName.BANDWIDTH,
        [
            Bound(
                lower_bound=receiver.get_spec(SpecName.BANDWIDTH_LOWER_BOUND),
                upper_bound=receiver.get_spec(SpecName.BANDWIDTH_UPPER_BOUND),
            )
        ],
    )
    capture_template.add_pconstraint(
        PName.GAIN,
        [
            Bound(
                lower_bound=0,
                upper_bound=receiver.get_spec(SpecName.GAIN_UPPER_BOUND),
            )
        ],
    )
    capture_template.add_pconstraint(
        PName.WIRE_FORMAT, [OneOf(receiver.get_spec(SpecName.WIRE_FORMATS))]
    )
    capture_template.add_pconstraint(
        PName.MASTER_CLOCK_RATE,
        [
            Bound(
                lower_bound=receiver.get_spec(SpecName.MASTER_CLOCK_RATE_LOWER_BOUND),
                upper_bound=receiver.get_spec(SpecName.MASTER_CLOCK_RATE_UPPER_BOUND),
            )
        ],
    )
    return capture_template


def _make_capture_template_swept_center_frequency(
    receiver: Receiver,
) -> CaptureTemplate:

    capture_template = get_base_capture_template(CaptureMode.SWEPT_CENTER_FREQUENCY)
    capture_template.add_ptemplate(get_base_ptemplate(PName.BANDWIDTH))
    capture_template.add_ptemplate(get_base_ptemplate(PName.GAIN))
    capture_template.add_ptemplate(get_base_ptemplate(PName.WIRE_FORMAT))
    capture_template.add_ptemplate(get_base_ptemplate(PName.MASTER_CLOCK_RATE))

    # TODO: Delegate defaults to receiver subclasses. Currently, these are sensible defaults for the b200mini
    capture_template.set_defaults(
        (PName.BATCH_SIZE, 4.0),
        (PName.MIN_FREQUENCY, 95000000),
        (PName.MAX_FREQUENCY, 105000000),
        (PName.SAMPLES_PER_STEP, 30000),
        (PName.FREQUENCY_STEP, 2000000),
        (PName.SAMPLE_RATE, 2000000),
        (PName.BANDWIDTH, 2000000),
        (PName.WINDOW_HOP, 512),
        (PName.WINDOW_SIZE, 1024),
        (PName.WINDOW_TYPE, "blackman"),
        (PName.GAIN, 35),
        (PName.WIRE_FORMAT, "sc16"),
        (PName.MASTER_CLOCK_RATE, 40e6),
    )

    capture_template.add_pconstraint(
        PName.MIN_FREQUENCY,
        [
            Bound(
                lower_bound=receiver.get_spec(SpecName.FREQUENCY_LOWER_BOUND),
                upper_bound=receiver.get_spec(SpecName.FREQUENCY_UPPER_BOUND),
            )
        ],
    )
    capture_template.add_pconstraint(
        PName.MAX_FREQUENCY,
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
            )
        ],
    )
    capture_template.add_pconstraint(
        PName.BANDWIDTH,
        [
            Bound(
                lower_bound=receiver.get_spec(SpecName.BANDWIDTH_LOWER_BOUND),
                upper_bound=receiver.get_spec(SpecName.BANDWIDTH_UPPER_BOUND),
            )
        ],
    )
    capture_template.add_pconstraint(
        PName.GAIN,
        [
            Bound(
                lower_bound=0,
                upper_bound=receiver.get_spec(SpecName.GAIN_UPPER_BOUND),
            )
        ],
    )
    capture_template.add_pconstraint(
        PName.WIRE_FORMAT, [OneOf(receiver.get_spec(SpecName.WIRE_FORMATS))]
    )
    capture_template.add_pconstraint(
        PName.MASTER_CLOCK_RATE,
        [
            Bound(
                lower_bound=receiver.get_spec(SpecName.MASTER_CLOCK_RATE_LOWER_BOUND),
                upper_bound=receiver.get_spec(SpecName.MASTER_CLOCK_RATE_UPPER_BOUND),
            )
        ],
    )
    return capture_template


@dataclass(frozen=True)
class _Mode:
    """An operating mode for the `B200mini` receiver."""

    FIXED_CENTER_FREQUENCY = "fixed_center_frequency"
    SWEPT_CENTER_FREQUENCY = "swept_center_frequency"


@register_receiver(ReceiverName.B200MINI)
class B200mini(Receiver):
    """Receiver implementation for the USRP B200mini (https://www.ettus.com/all-products/usrp-b200mini/)"""

    def __init__(self, name: ReceiverName, mode: Optional[str] = None) -> None:
        super().__init__(name, mode)

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

        self.add_mode(
            _Mode.FIXED_CENTER_FREQUENCY,
            partial(capture, top_block_cls=fixed_center_frequency),
            _make_capture_template_fixed_center_frequency(self),
            _make_pvalidator_fixed_center_frequency(self),
        )

        self.add_mode(
            _Mode.SWEPT_CENTER_FREQUENCY,
            partial(capture, top_block_cls=swept_center_frequency),
            _make_capture_template_swept_center_frequency(self),
            _make_pvalidator_swept_center_frequency(self),
        )
