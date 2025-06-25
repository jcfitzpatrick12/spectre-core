# SPDX-FileCopyrightText: © 2024-2025 Jimmy Fitzpatrick <jcfitzpatrick12@gmail.com>
# This file is part of SPECTRE
# SPDX-License-Identifier: GPL-3.0-or-later

from dataclasses import dataclass
from typing import Optional, Callable
from functools import partial

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
)

from ._receiver_names import ReceiverName
from ._rspduo_gr import (
    tuner_1_fixed_center_frequency,
    tuner_2_fixed_center_frequency,
    tuner_1_swept_center_frequency,
)
from ._receiver_names import ReceiverName
from ._gr import capture
from .._receiver import Specs, SpecName


from .._receiver import SpecName, Receiver
from .._register import register_receiver


def _make_pvalidator_fixed_center_frequency(
    specs: Specs,
) -> Callable[[Parameters], None]:
    def pvalidator(parameters: Parameters) -> None:
        validate_fixed_center_frequency(parameters)

    return pvalidator


def _make_pvalidator_swept_center_frequency(
    specs: Specs,
) -> Callable[[Parameters], None]:
    def pvalidator(parameters: Parameters) -> None:
        validate_swept_center_frequency(
            parameters, specs.get(SpecName.API_RETUNING_LATENCY)
        )

    return pvalidator


def _make_capture_template_fixed_center_frequency(
    specs: Specs,
) -> CaptureTemplate:

    capture_template = get_base_capture_template(CaptureMode.FIXED_CENTER_FREQUENCY)
    capture_template.add_ptemplate(get_base_ptemplate(PName.BANDWIDTH))
    capture_template.add_ptemplate(get_base_ptemplate(PName.IF_GAIN))
    capture_template.add_ptemplate(get_base_ptemplate(PName.RF_GAIN))

    capture_template.set_defaults(
        (PName.BATCH_SIZE, 3.0),
        (PName.CENTER_FREQUENCY, 95800000),
        (PName.SAMPLE_RATE, 600000),
        (PName.BANDWIDTH, 600000),
        (PName.WINDOW_HOP, 512),
        (PName.WINDOW_SIZE, 1024),
        (PName.WINDOW_TYPE, "blackman"),
        (PName.RF_GAIN, -30),
        (PName.IF_GAIN, -30),
    )

    capture_template.add_pconstraint(
        PName.CENTER_FREQUENCY,
        [
            Bound(
                lower_bound=specs.get(SpecName.FREQUENCY_LOWER_BOUND),
                upper_bound=specs.get(SpecName.FREQUENCY_UPPER_BOUND),
            )
        ],
    )
    capture_template.add_pconstraint(
        PName.SAMPLE_RATE,
        [
            Bound(
                lower_bound=specs.get(SpecName.SAMPLE_RATE_LOWER_BOUND),
                upper_bound=specs.get(SpecName.SAMPLE_RATE_UPPER_BOUND),
            )
        ],
    )
    capture_template.add_pconstraint(
        PName.BANDWIDTH, [OneOf(specs.get(SpecName.BANDWIDTH_OPTIONS))]
    )
    capture_template.add_pconstraint(
        PName.IF_GAIN,
        [Bound(upper_bound=specs.get(SpecName.IF_GAIN_UPPER_BOUND))],
    )
    capture_template.add_pconstraint(
        PName.RF_GAIN,
        [Bound(upper_bound=specs.get(SpecName.RF_GAIN_UPPER_BOUND))],
    )
    return capture_template


def _make_capture_template_swept_center_frequency(specs: Specs) -> CaptureTemplate:

    capture_template = get_base_capture_template(CaptureMode.SWEPT_CENTER_FREQUENCY)
    capture_template.add_ptemplate(get_base_ptemplate(PName.BANDWIDTH))
    capture_template.add_ptemplate(get_base_ptemplate(PName.IF_GAIN))
    capture_template.add_ptemplate(get_base_ptemplate(PName.RF_GAIN))

    capture_template.set_defaults(
        (PName.BATCH_SIZE, 4.0),
        (PName.MIN_FREQUENCY, 95000000),
        (PName.MAX_FREQUENCY, 100000000),
        (PName.SAMPLES_PER_STEP, 80000),
        (PName.FREQUENCY_STEP, 1536000),
        (PName.SAMPLE_RATE, 1536000),
        (PName.BANDWIDTH, 1536000),
        (PName.WINDOW_HOP, 512),
        (PName.WINDOW_SIZE, 1024),
        (PName.WINDOW_TYPE, "blackman"),
        (PName.RF_GAIN, -30),
        (PName.IF_GAIN, -30),
    )

    capture_template.add_pconstraint(
        PName.MIN_FREQUENCY,
        [
            Bound(
                lower_bound=specs.get(SpecName.FREQUENCY_LOWER_BOUND),
                upper_bound=specs.get(SpecName.FREQUENCY_UPPER_BOUND),
            )
        ],
    )
    capture_template.add_pconstraint(
        PName.MAX_FREQUENCY,
        [
            Bound(
                lower_bound=specs.get(SpecName.FREQUENCY_LOWER_BOUND),
                upper_bound=specs.get(SpecName.FREQUENCY_UPPER_BOUND),
            )
        ],
    )
    capture_template.add_pconstraint(
        PName.SAMPLE_RATE,
        [
            Bound(
                lower_bound=specs.get(SpecName.SAMPLE_RATE_LOWER_BOUND),
                upper_bound=specs.get(SpecName.SAMPLE_RATE_UPPER_BOUND),
            )
        ],
    )
    capture_template.add_pconstraint(
        PName.BANDWIDTH, [OneOf(specs.get(SpecName.BANDWIDTH_OPTIONS))]
    )
    capture_template.add_pconstraint(
        PName.IF_GAIN,
        [Bound(upper_bound=specs.get(SpecName.IF_GAIN_UPPER_BOUND))],
    )
    capture_template.add_pconstraint(
        PName.RF_GAIN,
        [Bound(upper_bound=specs.get(SpecName.RF_GAIN_UPPER_BOUND))],
    )
    return capture_template


@dataclass
class _Mode:
    """An operating mode for the `RSPduo` receiver."""

    TUNER_1_FIXED_CENTER_FREQUENCY = f"tuner_1_fixed_center_frequency"
    TUNER_2_FIXED_CENTER_FREQUENCY = f"tuner_2_fixed_center_frequency"
    TUNER_1_SWEPT_CENTER_FREQUENCY = f"tuner_1_swept_center_frequency"


@register_receiver(ReceiverName.RSPDUO)
class RSPduo(Receiver):
    """Receiver implementation for the SDRPlay RSPduo (https://www.sdrplay.com/rspduo/)"""

    def __init__(self, name: ReceiverName, mode: Optional[str] = None) -> None:
        super().__init__(name, mode)

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

        self.add_mode(
            _Mode.TUNER_1_FIXED_CENTER_FREQUENCY,
            partial(capture, top_block_cls=tuner_1_fixed_center_frequency),
            _make_capture_template_fixed_center_frequency(self.specs),
            _make_pvalidator_fixed_center_frequency(self.specs),
        )

        self.add_mode(
            _Mode.TUNER_2_FIXED_CENTER_FREQUENCY,
            partial(capture, top_block_cls=tuner_2_fixed_center_frequency),
            _make_capture_template_fixed_center_frequency(self.specs),
            _make_pvalidator_fixed_center_frequency(self.specs),
        )

        self.add_mode(
            _Mode.TUNER_1_SWEPT_CENTER_FREQUENCY,
            partial(capture, top_block_cls=tuner_1_swept_center_frequency),
            _make_capture_template_swept_center_frequency(self.specs),
            _make_pvalidator_swept_center_frequency(self.specs),
        )
