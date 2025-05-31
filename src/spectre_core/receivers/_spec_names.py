# SPDX-FileCopyrightText: © 2024-2025 Jimmy Fitzpatrick <jcfitzpatrick12@gmail.com>
# This file is part of SPECTRE
# SPDX-License-Identifier: GPL-3.0-or-later

from enum import Enum


class SpecName(Enum):
    """A hardware specification name.

    :ivar FREQUENCY_LOWER_BOUND: The lower bound for the center frequency, in Hz.
    :ivar FREQUENCY_UPPER_BOUND: The upper bound for the center frequency, in Hz.
    :ivar SAMPLE_RATE_LOWER_BOUND: The lower bound for the sampling rate, in Hz.
    :ivar SAMPLE_RATE_UPPER_BOUND: The upper bound for the sampling rate, in Hz.
    :ivar BANDWIDTH_LOWER_BOUND: The lower bound for the bandwidth, in Hz.
    :ivar BANDWIDTH_UPPER_BOUND: The upper bound for the bandwidth, in Hz.
    :ivar BANDWIDTH_OPTIONS: The permitted bandwidths for the receiver, in Hz.
    :ivar IF_GAIN_UPPER_BOUND: The upper bound for the intermediate frequency gain, in dB.
    Negative values indicate attenuation.
    :ivar RF_GAIN_UPPER_BOUND: The upper bound for the radio frequency gain, in dB.
    Negative values indicate attenuation.
    :ivar GAIN_UPPER_BOUND: The upper bound for the gain, in dB.
    :ivar WIRE_FORMATS: Supported data types transferred over the bus/network.
    :ivar MASTER_CLOCK_RATE_LOWER_BOUND:  The lower bound for the SDR reference clock rate, in Hz.
    :ivar MASTER_CLOCK_RATE_UPPER_BOUND:  The upper bound for the SDR reference clock rate, in Hz.
    :ivar API_RETUNING_LATENCY: An empirical estimate of the delay between issuing a command
    for a receiver to retune its center frequency and the actual physical update of the center frequency.
    """

    FREQUENCY_LOWER_BOUND = "frequency_lower_bound"
    FREQUENCY_UPPER_BOUND = "frequency_upper_bound"
    SAMPLE_RATE_LOWER_BOUND = "sample_rate_lower_bound"
    SAMPLE_RATE_UPPER_BOUND = "sample_rate_upper_bound"
    BANDWIDTH_LOWER_BOUND = "bandwidth_lower_bound"
    BANDWIDTH_UPPER_BOUND = "bandwidth_upper_bound"
    BANDWIDTH_OPTIONS = "bandwidth_options"
    IF_GAIN_UPPER_BOUND = "if_gain_upper_bound"
    RF_GAIN_UPPER_BOUND = "rf_gain_upper_bound"
    GAIN_UPPER_BOUND = "gain_upper_bound"
    WIRE_FORMATS = "wire_formats"
    MASTER_CLOCK_RATE_LOWER_BOUND = "master_clock_rate_lower_bound"
    MASTER_CLOCK_RATE_UPPER_BOUND = "master_clock_rate_upper_bound"
    API_RETUNING_LATENCY = "api_retuning_latency"
