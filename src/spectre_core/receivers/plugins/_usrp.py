# SPDX-FileCopyrightText: © 2024 Jimmy Fitzpatrick <jcfitzpatrick12@gmail.com>
# This file is part of SPECTRE
# SPDX-License-Identifier: GPL-3.0-or-later

from typing import Callable, overload

from spectre_core.capture_configs import (
    CaptureTemplate, CaptureMode, Parameters, Bound, PName,
    get_base_capture_template, get_base_ptemplate, OneOf,
    validate_sample_rate_with_master_clock_rate,
    validate_fixed_center_frequency, validate_swept_center_frequency
)
from .._base import BaseReceiver
from .._spec_names import SpecName


def get_pvalidator_fixed_center_frequency(
    usrp_receiver: BaseReceiver 
) -> Callable[[Parameters], None]:
    def pvalidator(parameters: Parameters) -> None:
        validate_fixed_center_frequency(parameters)
        validate_sample_rate_with_master_clock_rate(parameters)
    return pvalidator


def get_pvalidator_swept_center_frequency(
    usrp_receiver: BaseReceiver 
) -> Callable[[Parameters], None]:
    def pvalidator(parameters: Parameters) -> None:
        validate_swept_center_frequency(parameters,
                                        usrp_receiver.get_spec(SpecName.API_RETUNING_LATENCY))
        validate_sample_rate_with_master_clock_rate(parameters)
    return pvalidator


def get_capture_template_fixed_center_frequency(
    usrp_receiver: BaseReceiver
) -> CaptureTemplate:
    
    capture_template = get_base_capture_template( CaptureMode.FIXED_CENTER_FREQUENCY )
    capture_template.add_ptemplate( get_base_ptemplate(PName.BANDWIDTH) )
    capture_template.add_ptemplate( get_base_ptemplate(PName.GAIN) )
    capture_template.add_ptemplate( get_base_ptemplate(PName.WIRE_FORMAT) )
    capture_template.add_ptemplate( get_base_ptemplate(PName.MASTER_CLOCK_RATE) ) 

    # TODO: Delegate defaults to receiver subclasses. Currently, these are sensible defaults for the b200mini
    capture_template.set_defaults(
        (PName.BATCH_SIZE,            4.0),
        (PName.CENTER_FREQUENCY,      95800000),
        (PName.SAMPLE_RATE,           2000000),
        (PName.BANDWIDTH,             2000000),
        (PName.WINDOW_HOP,            512),
        (PName.WINDOW_SIZE,           1024),
        (PName.WINDOW_TYPE,           "blackman"),
        (PName.GAIN,                  35),
        (PName.WIRE_FORMAT,           "sc16"),
        (PName.MASTER_CLOCK_RATE,     40e6)
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
    capture_template.add_pconstraint(
        PName.GAIN,
        [
            Bound(
                lower_bound=0,
                upper_bound=usrp_receiver.get_spec( SpecName.GAIN_UPPER_BOUND )
            )
        ]
    )
    capture_template.add_pconstraint(
        PName.WIRE_FORMAT,
        [
            OneOf(
                usrp_receiver.get_spec( SpecName.WIRE_FORMATS )
            )
        ]
    )
    capture_template.add_pconstraint(
        PName.MASTER_CLOCK_RATE,
        [
            Bound(
                lower_bound=usrp_receiver.get_spec( SpecName.MASTER_CLOCK_RATE_LOWER_BOUND ),
                upper_bound=usrp_receiver.get_spec( SpecName.MASTER_CLOCK_RATE_UPPER_BOUND )
            )
        ]
    )
    return capture_template


def get_capture_template_swept_center_frequency(
    usrp_receiver: BaseReceiver
) -> CaptureTemplate:

    capture_template = get_base_capture_template( CaptureMode.SWEPT_CENTER_FREQUENCY )
    capture_template.add_ptemplate( get_base_ptemplate(PName.BANDWIDTH) )
    capture_template.add_ptemplate( get_base_ptemplate(PName.GAIN) )
    capture_template.add_ptemplate( get_base_ptemplate(PName.WIRE_FORMAT) )
    capture_template.add_ptemplate( get_base_ptemplate(PName.MASTER_CLOCK_RATE) ) 

    # TODO: Delegate defaults to receiver subclasses. Currently, these are sensible defaults for the b200mini
    capture_template.set_defaults(
        (PName.BATCH_SIZE,            4.0),
        (PName.MIN_FREQUENCY,         95000000),
        (PName.MAX_FREQUENCY,         105000000),
        (PName.SAMPLES_PER_STEP,      30000),
        (PName.FREQUENCY_STEP,        2000000),
        (PName.SAMPLE_RATE,           2000000),
        (PName.BANDWIDTH,             2000000),
        (PName.WINDOW_HOP,            512),
        (PName.WINDOW_SIZE,           1024),
        (PName.WINDOW_TYPE,           "blackman"),
        (PName.GAIN,                  35),
        (PName.WIRE_FORMAT,           "sc16"),
        (PName.MASTER_CLOCK_RATE,     40e6)
    )   

    capture_template.add_pconstraint(
        PName.MIN_FREQUENCY,
        [
            Bound(
                lower_bound=usrp_receiver.get_spec(SpecName.FREQUENCY_LOWER_BOUND),
                upper_bound=usrp_receiver.get_spec(SpecName.FREQUENCY_UPPER_BOUND)
            )
        ]
    )
    capture_template.add_pconstraint(
        PName.MAX_FREQUENCY,
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
                lower_bound=usrp_receiver.get_spec(SpecName.BANDWIDTH_LOWER_BOUND),
                upper_bound=usrp_receiver.get_spec(SpecName.BANDWIDTH_UPPER_BOUND),
            )
        ]
    )
    capture_template.add_pconstraint(
        PName.GAIN,
        [
            Bound(
                lower_bound=0,
                upper_bound=usrp_receiver.get_spec( SpecName.GAIN_UPPER_BOUND )
            )
        ]
    )
    capture_template.add_pconstraint(
        PName.WIRE_FORMAT,
        [
            OneOf(
                usrp_receiver.get_spec( SpecName.WIRE_FORMATS )
            )
        ]
    )
    capture_template.add_pconstraint(                                                           
        PName.MASTER_CLOCK_RATE,
        [
            Bound(                                                                              
                lower_bound=usrp_receiver.get_spec( SpecName.MASTER_CLOCK_RATE_LOWER_BOUND ),   
                upper_bound=usrp_receiver.get_spec( SpecName.MASTER_CLOCK_RATE_UPPER_BOUND )    
            )                                                                                   
        ]                                                                                       
    )                                                                                           
    return capture_template
