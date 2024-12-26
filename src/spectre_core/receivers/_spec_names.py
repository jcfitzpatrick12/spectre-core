# SPDX-FileCopyrightText: © 2024 Jimmy Fitzpatrick <jcfitzpatrick12@gmail.com>
# This file is part of SPECTRE
# SPDX-License-Identifier: GPL-3.0-or-later

from dataclasses import dataclass

@dataclass(frozen=True)
class SpecNames:
    """A centralised store of specification names"""
    FREQUENCY_LOWER_BOUND   : str = "frequency_lower_bound"
    FREQUENCY_UPPER_BOUND   : str = "frequency_upper_bound"
    SAMPLE_RATE_LOWER_BOUND : str = "sample_rate_lower_bound"
    SAMPLE_RATE_UPPER_BOUND : str = "sample_rate_upper_bound"
    BANDWIDTH_LOWER_BOUND   : str = "bandwidth_lower_bound"
    BANDWIDTH_UPPER_BOUND   : str = "bandwidth_upper_bound"
    BANDWIDTH_OPTIONS       : str = "bandwidth_options"
    DEFINED_BANDWIDTHS      : str = "defined_bandwidths"
    IF_GAIN_UPPER_BOUND     : str = "if_gain_upper_bound"
    RF_GAIN_UPPER_BOUND     : str = "rf_gain_upper_bound"
    API_RETUNING_LATENCY    : str = "api_retuning_latency"