# SPDX-FileCopyrightText: © 2024-2025 Jimmy Fitzpatrick <jcfitzpatrick12@gmail.com>
# This file is part of SPECTRE
# SPDX-License-Identifier: GPL-3.0-or-later

from typing import Any
from enum import Enum


class SpecName(Enum):
    """Hardware specification names for SDR receivers.

    :ivar FREQUENCY_LOWER_BOUND: The lower bound for the center frequency, in Hz.
    :ivar FREQUENCY_UPPER_BOUND: The upper bound for the center frequency, in Hz.
    :ivar SAMPLE_RATE_LOWER_BOUND: The lower bound for the sampling rate, in Hz.
    :ivar SAMPLE_RATE_UPPER_BOUND: The upper bound for the sampling rate, in Hz.
    :ivar BANDWIDTH_LOWER_BOUND: The lower bound for the bandwidth, in Hz.
    :ivar BANDWIDTH_UPPER_BOUND: The upper bound for the bandwidth, in Hz.
    :ivar BANDWIDTH_OPTIONS: The permitted bandwidths for the receiver, in Hz.
    :ivar IF_GAIN_UPPER_BOUND: The upper bound for the intermediate frequency gain, in dB.
    :ivar IF_GAIN_LOWER_BOUND: The lower bound for the intermediate frequency gain, in dB.
    :ivar RF_GAIN_UPPER_BOUND: The upper bound for the radio frequency gain, in dB.
    :ivar RF_GAIN_LOWER_BOUND: The lower bound for the radio frequency gain, in dB.
    :ivar GAIN_UPPER_BOUND: The upper bound for the gain, in dB.
    :ivar WIRE_FORMATS: Supported data types transferred over the bus/network.
    :ivar MASTER_CLOCK_RATE_LOWER_BOUND: The lower bound for the SDR reference clock rate, in Hz.
    :ivar MASTER_CLOCK_RATE_UPPER_BOUND: The upper bound for the SDR reference clock rate, in Hz.
    :ivar API_RETUNING_LATENCY: Estimated delay between issuing a retune command and the actual center frequency update.
    """

    FREQUENCY_LOWER_BOUND = "frequency_lower_bound"
    FREQUENCY_UPPER_BOUND = "frequency_upper_bound"
    SAMPLE_RATE_LOWER_BOUND = "sample_rate_lower_bound"
    SAMPLE_RATE_UPPER_BOUND = "sample_rate_upper_bound"
    BANDWIDTH_LOWER_BOUND = "bandwidth_lower_bound"
    BANDWIDTH_UPPER_BOUND = "bandwidth_upper_bound"
    BANDWIDTH_OPTIONS = "bandwidth_options"
    IF_GAIN_UPPER_BOUND = "if_gain_upper_bound"
    IF_GAIN_LOWER_BOUND = "if_gain_lower_bound"
    RF_GAIN_UPPER_BOUND = "rf_gain_upper_bound"
    RF_GAIN_LOWER_BOUND = "rf_gain_lower_bound"
    GAIN_UPPER_BOUND = "gain_upper_bound"
    WIRE_FORMATS = "wire_formats"
    MASTER_CLOCK_RATE_LOWER_BOUND = "master_clock_rate_lower_bound"
    MASTER_CLOCK_RATE_UPPER_BOUND = "master_clock_rate_upper_bound"
    API_RETUNING_LATENCY = "api_retuning_latency"


class Specs:
    """Define hardware specifications."""

    def __init__(self) -> None:
        """Initialise an instance of `Specs`."""
        self._specs: dict[SpecName, Any] = {}

    def add(self, name: SpecName, value: Any) -> None:
        """Add a hardware specification.

        :param name: The specification's name.
        :param value: The specification's value.
        """
        self._specs[name] = value

    def get(self, name: SpecName) -> Any:
        """Get a hardware specification.

        :param name: The specification's name.
        :return: The specification's value.
        :raises KeyError: If the specification is not found.
        """
        if name not in self._specs:
            raise KeyError(
                f"Specification `{name}` not found. Expected one of {list(self._specs.keys())}"
            )
        return self._specs[name]

    def all(self) -> dict[SpecName, Any]:
        """Retrieve all hardware specifications."""
        return self._specs
