# SPDX-FileCopyrightText: © 2024-2025 Jimmy Fitzpatrick <jcfitzpatrick12@gmail.com>
# This file is part of SPECTRE
# SPDX-License-Identifier: GPL-3.0-or-later

from typing import Callable, overload

from spectre_core.capture_configs import (
    CaptureTemplate,
    CaptureMode,
    Parameters,
    Bound,
    PName,
    get_base_capture_template,
    get_base_ptemplate,
    OneOf,
    validate_fixed_center_frequency,
    validate_swept_center_frequency,
)
from .._base import BaseReceiver
from .._spec_names import SpecName


def get_pvalidator_fixed_center_frequency(
    sdrplay_receiver: BaseReceiver,
) -> Callable[[Parameters], None]:
    def pvalidator(parameters: Parameters) -> None:
        validate_fixed_center_frequency(parameters)

    return pvalidator


def get_pvalidator_swept_center_frequency(
    sdrplay_receiver: BaseReceiver,
) -> Callable[[Parameters], None]:
    def pvalidator(parameters: Parameters) -> None:
        validate_swept_center_frequency(
            parameters, sdrplay_receiver.get_spec(SpecName.API_RETUNING_LATENCY)
        )

    return pvalidator


def get_capture_template_fixed_center_frequency(
    sdrplay_receiver: BaseReceiver,
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
                lower_bound=sdrplay_receiver.get_spec(SpecName.FREQUENCY_LOWER_BOUND),
                upper_bound=sdrplay_receiver.get_spec(SpecName.FREQUENCY_UPPER_BOUND),
            )
        ],
    )
    capture_template.add_pconstraint(
        PName.SAMPLE_RATE,
        [
            Bound(
                lower_bound=sdrplay_receiver.get_spec(SpecName.SAMPLE_RATE_LOWER_BOUND),
                upper_bound=sdrplay_receiver.get_spec(SpecName.SAMPLE_RATE_UPPER_BOUND),
            )
        ],
    )
    capture_template.add_pconstraint(
        PName.BANDWIDTH, [OneOf(sdrplay_receiver.get_spec(SpecName.BANDWIDTH_OPTIONS))]
    )
    capture_template.add_pconstraint(
        PName.IF_GAIN,
        [Bound(upper_bound=sdrplay_receiver.get_spec(SpecName.IF_GAIN_UPPER_BOUND))],
    )
    capture_template.add_pconstraint(
        PName.RF_GAIN,
        [Bound(upper_bound=sdrplay_receiver.get_spec(SpecName.RF_GAIN_UPPER_BOUND))],
    )
    return capture_template


def get_capture_template_swept_center_frequency(
    sdrplay_receiver: BaseReceiver,
) -> CaptureTemplate:

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
                lower_bound=sdrplay_receiver.get_spec(SpecName.FREQUENCY_LOWER_BOUND),
                upper_bound=sdrplay_receiver.get_spec(SpecName.FREQUENCY_UPPER_BOUND),
            )
        ],
    )
    capture_template.add_pconstraint(
        PName.MAX_FREQUENCY,
        [
            Bound(
                lower_bound=sdrplay_receiver.get_spec(SpecName.FREQUENCY_LOWER_BOUND),
                upper_bound=sdrplay_receiver.get_spec(SpecName.FREQUENCY_UPPER_BOUND),
            )
        ],
    )
    capture_template.add_pconstraint(
        PName.SAMPLE_RATE,
        [
            Bound(
                lower_bound=sdrplay_receiver.get_spec(SpecName.SAMPLE_RATE_LOWER_BOUND),
                upper_bound=sdrplay_receiver.get_spec(SpecName.SAMPLE_RATE_UPPER_BOUND),
            )
        ],
    )
    capture_template.add_pconstraint(
        PName.BANDWIDTH, [OneOf(sdrplay_receiver.get_spec(SpecName.BANDWIDTH_OPTIONS))]
    )
    capture_template.add_pconstraint(
        PName.IF_GAIN,
        [Bound(upper_bound=sdrplay_receiver.get_spec(SpecName.IF_GAIN_UPPER_BOUND))],
    )
    capture_template.add_pconstraint(
        PName.RF_GAIN,
        [Bound(upper_bound=sdrplay_receiver.get_spec(SpecName.RF_GAIN_UPPER_BOUND))],
    )
    return capture_template
