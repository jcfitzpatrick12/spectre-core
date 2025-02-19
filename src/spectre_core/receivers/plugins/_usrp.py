# SPDX-FileCopyrightText: © 2024 Jimmy Fitzpatrick <jcfitzpatrick12@gmail.com>
# This file is part of SPECTRE
# SPDX-License-Identifier: GPL-3.0-or-later

from typing import Callable, overload

from spectre_core.capture_configs import (
    CaptureTemplate, CaptureMode, Parameters, Bound, PName,
    get_base_capture_template, get_base_ptemplate, OneOf,
    validate_fixed_center_frequency, validate_swept_center_frequency
)
from .._base import BaseReceiver
from .._spec_names import SpecName


def get_pvalidator_fixed_center_frequency(
    usrp_receiver: BaseReceiver 
) -> Callable[[Parameters], None]:
    def pvalidator(parameters: Parameters) -> None:
        validate_fixed_center_frequency(parameters)
    return pvalidator


def get_capture_template_fixed_center_frequency(
    usrp_receiver: BaseReceiver
) -> CaptureTemplate:
    
    capture_template = get_base_capture_template( CaptureMode.FIXED_CENTER_FREQUENCY )
    capture_template.add_ptemplate( get_base_ptemplate(PName.BANDWIDTH) )
    capture_template.add_ptemplate( get_base_ptemplate(PName.NORMALISED_GAIN) )

    capture_template.set_defaults(
        (PName.BATCH_SIZE,            3.0),
        (PName.CENTER_FREQUENCY,      95800000),
        (PName.SAMPLE_RATE,           1000000),
        (PName.BANDWIDTH,             1000000),
        (PName.WINDOW_HOP,            512),
        (PName.WINDOW_SIZE,           1024),
        (PName.WINDOW_TYPE,           "blackman"),
        (PName.NORMALISED_GAIN,       0.3),
    )   

    capture_template.add_pconstraint(
        PName.CENTER_FREQUENCY,
        [
            Bound(
                lower_bound=usrp_receiver.get_spec(SpecName.FREQUENCY_LOWER_BOUND),
                upper_bound=usrp_receiver.get_spec(SpecName.FREQUENCY_UPPER_BOUND)
            )
        ]
    )
    capture_template.add_pconstraint(
        PName.SAMPLE_RATE,
        [
            Bound(
                lower_bound=usrp_receiver.get_spec(SpecName.SAMPLE_RATE_LOWER_BOUND),
                upper_bound=usrp_receiver.get_spec(SpecName.SAMPLE_RATE_UPPER_BOUND)
            )
        ]
    )
    capture_template.add_pconstraint(
        PName.BANDWIDTH,
        [
            Bound(
                lower_bound=usrp_receiver.get_spec( SpecName.BANDWIDTH_LOWER_BOUND ),
                upper_bound=usrp_receiver.get_spec( SpecName.BANDWIDTH_UPPER_BOUND )
            )
        ]
    )
    return capture_template
