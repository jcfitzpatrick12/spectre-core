# SPDX-FileCopyrightText: © 2024 Jimmy Fitzpatrick <jcfitzpatrick12@gmail.com>
# This file is part of SPECTRE
# SPDX-License-Identifier: GPL-3.0-or-later

from abc import ABC, abstractmethod
from typing import Callable, Optional
from numbers import Number

from spectre_core.capture_configs import (
    CaptureTemplate, CaptureModes, Parameters, Bound, PValidators, PNames,
    get_base_capture_template, get_base_ptemplate, OneOf, CaptureConfig
)
from .._base import BaseReceiver
from .._spec_names import SpecNames

class SDRPlayReceiver(BaseReceiver):
    def _get_pvalidator_fixed_center_frequency(self) -> Callable:
        def pvalidator(parameters: Parameters):
            PValidators.fixed_center_frequency(parameters)
        return pvalidator


    def _get_pvalidator_swept_center_frequency(self) -> None:
        def pvalidator(parameters: Parameters):
            PValidators.swept_center_frequency(parameters,
                                               self.get_spec(SpecNames.API_RETUNING_LATENCY))
        return pvalidator


    def _get_capture_template_fixed_center_frequency(self) -> CaptureTemplate:
        #
        # Create the base template
        #
        capture_template = get_base_capture_template( CaptureModes.FIXED_CENTER_FREQUENCY )
        capture_template.add_ptemplate( get_base_ptemplate(PNames.BANDWIDTH) )
        capture_template.add_ptemplate( get_base_ptemplate(PNames.IF_GAIN) )
        capture_template.add_ptemplate( get_base_ptemplate(PNames.RF_GAIN) )

        #
        # Update the defaults
        #
        capture_template.set_defaults(
            (PNames.BATCH_SIZE,            3.0),
            (PNames.CENTER_FREQUENCY,      95800000),
            (PNames.SAMPLE_RATE,           600000),
            (PNames.BANDWIDTH,             600000),
            (PNames.WINDOW_HOP,            512),
            (PNames.WINDOW_SIZE,           1024),
            (PNames.WINDOW_TYPE,           "blackman"),
            (PNames.RF_GAIN,               -30),
            (PNames.IF_GAIN,               -30)
        )   

        #
        # Adding pconstraints
        #
        capture_template.add_pconstraint(
            PNames.CENTER_FREQUENCY,
            [
                Bound(
                    lower_bound=self.get_spec(SpecNames.FREQUENCY_LOWER_BOUND),
                    upper_bound=self.get_spec(SpecNames.FREQUENCY_UPPER_BOUND)
                )
            ]
        )
        capture_template.add_pconstraint(
            PNames.SAMPLE_RATE,
            [
                Bound(
                    lower_bound=self.get_spec(SpecNames.SAMPLE_RATE_LOWER_BOUND),
                    upper_bound=self.get_spec(SpecNames.SAMPLE_RATE_UPPER_BOUND)
                )
            ]
        )
        capture_template.add_pconstraint(
            PNames.BANDWIDTH,
            [
                OneOf(
                    self.get_spec( SpecNames.BANDWIDTH_OPTIONS )
                )
            ]
        )
        capture_template.add_pconstraint(
            PNames.IF_GAIN,
            [
                Bound(
                    upper_bound=self.get_spec(SpecNames.IF_GAIN_UPPER_BOUND)
                )
            ]
        )
        capture_template.add_pconstraint(
            PNames.RF_GAIN,
            [
                Bound(
                    upper_bound=self.get_spec(SpecNames.RF_GAIN_UPPER_BOUND)
                )
            ]
        )
        return capture_template


    def _get_capture_template_swept_center_frequency(self) -> CaptureTemplate:
        #
        # Create the base template
        #
        capture_template = get_base_capture_template( CaptureModes.SWEPT_CENTER_FREQUENCY )
        capture_template.add_ptemplate( get_base_ptemplate(PNames.BANDWIDTH) )
        capture_template.add_ptemplate( get_base_ptemplate(PNames.IF_GAIN) )
        capture_template.add_ptemplate( get_base_ptemplate(PNames.RF_GAIN) )


        #
        # Update the defaults
        #
        capture_template.set_defaults(
            (PNames.BATCH_SIZE,            4.0),
            (PNames.MIN_FREQUENCY,         95000000),
            (PNames.MAX_FREQUENCY,         100000000),
            (PNames.SAMPLES_PER_STEP,      80000),
            (PNames.FREQUENCY_STEP,        1536000),
            (PNames.SAMPLE_RATE,           1536000),
            (PNames.BANDWIDTH,             1536000),
            (PNames.WINDOW_HOP,            512),
            (PNames.WINDOW_SIZE,           1024),
            (PNames.WINDOW_TYPE,           "blackman"),
            (PNames.RF_GAIN,               -30),
            (PNames.IF_GAIN,               -30)
        )   


        #
        # Adding pconstraints
        #
        capture_template.add_pconstraint(
            PNames.MIN_FREQUENCY,
            [
                Bound(
                    lower_bound=self.get_spec(SpecNames.FREQUENCY_LOWER_BOUND),
                    upper_bound=self.get_spec(SpecNames.FREQUENCY_UPPER_BOUND)
                )
            ]
        )
        capture_template.add_pconstraint(
            PNames.MAX_FREQUENCY,
            [
                Bound(
                    lower_bound=self.get_spec(SpecNames.FREQUENCY_LOWER_BOUND),
                    upper_bound=self.get_spec(SpecNames.FREQUENCY_UPPER_BOUND)
                )
            ]
        )
        capture_template.add_pconstraint(
            PNames.SAMPLE_RATE,
            [
                Bound(
                    lower_bound=self.get_spec(SpecNames.SAMPLE_RATE_LOWER_BOUND),
                    upper_bound=self.get_spec(SpecNames.SAMPLE_RATE_UPPER_BOUND)
                )
            ]
        )
        capture_template.add_pconstraint(
            PNames.BANDWIDTH,
            [
                OneOf(
                    self.get_spec( SpecNames.BANDWIDTH_OPTIONS )
                )
            ]
        )
        capture_template.add_pconstraint(
            PNames.IF_GAIN,
            [
                Bound(
                    upper_bound=self.get_spec(SpecNames.IF_GAIN_UPPER_BOUND)
                )
            ]
        )
        capture_template.add_pconstraint(
            PNames.RF_GAIN,
            [
                Bound(
                    upper_bound=self.get_spec(SpecNames.RF_GAIN_UPPER_BOUND)
                )
            ]
        )
        return capture_template