# SPDX-FileCopyrightText: © 2024-2025 Jimmy Fitzpatrick <jcfitzpatrick12@gmail.com>
# This file is part of SPECTRE
# SPDX-License-Identifier: GPL-3.0-or-later

from typing import Callable, Optional
from enum import Enum

from spectre_core.exceptions import ModeNotFoundError
from spectre_core.capture_configs import CaptureTemplate, Parameters, CaptureConfig
from .plugins._receiver_names import ReceiverName


class SpecName(Enum):
    """Enumeration of hardware specification names for SDR receivers.

    :ivar FREQUENCY_LOWER_BOUND: The lower bound for the center frequency, in Hz.
    :ivar FREQUENCY_UPPER_BOUND: The upper bound for the center frequency, in Hz.
    :ivar SAMPLE_RATE_LOWER_BOUND: The lower bound for the sampling rate, in Hz.
    :ivar SAMPLE_RATE_UPPER_BOUND: The upper bound for the sampling rate, in Hz.
    :ivar BANDWIDTH_LOWER_BOUND: The lower bound for the bandwidth, in Hz.
    :ivar BANDWIDTH_UPPER_BOUND: The upper bound for the bandwidth, in Hz.
    :ivar BANDWIDTH_OPTIONS: The permitted bandwidths for the receiver, in Hz.
    :ivar IF_GAIN_UPPER_BOUND: The upper bound for the intermediate frequency gain, in dB.
    :ivar RF_GAIN_UPPER_BOUND: The upper bound for the radio frequency gain, in dB.
    :ivar GAIN_UPPER_BOUND: The upper bound for the gain, in dB.
    :ivar WIRE_FORMATS: Supported data types transferred over the bus/network.
    :ivar MASTER_CLOCK_RATE_LOWER_BOUND: The lower bound for the SDR reference clock rate, in Hz.
    :ivar MASTER_CLOCK_RATE_UPPER_BOUND: The upper bound for the SDR reference clock rate, in Hz.
    :ivar API_RETUNING_LATENCY: Estimated delay between issuing a retune command and the actual frequency update.
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


class Specs:
    """Encapsulation for hardware specifications."""

    def __init__(self) -> None:
        """Initialize an empty collection of specifications."""
        self._specs: dict[SpecName, float | int | list[float | int]] = {}

    def add(self, name: SpecName, value: float | int | list[float | int]) -> None:
        """Add a hardware specification.

        :param name: The specification's name.
        :param value: The specification's value.
        """
        self._specs[name] = value

    def get(self, name: SpecName) -> float | int | list[float | int]:
        """Get a hardware specification.

        :param name: The specification's name.
        :return: The specification's value.
        :raises KeyError: If the specification is not found.
        """
        if name not in self._specs:
            raise KeyError(f"Specification `{name}` not found.")
        return self._specs[name]

    def all(self) -> dict[SpecName, float | int | list[float | int]]:
        """Retrieve all hardware specifications.

        :return: A dictionary of all specifications.
        """
        return self._specs


def _ensure_mode_exists(mode: str, d: dict) -> None:
    """Ensure the mode exists in the collection.

    :param mode: The mode to check.
    :param collection: The dictionary containing modes.
    :raises ModeNotFoundError: If the mode is not found.
    """
    if mode not in d:
        raise ModeNotFoundError(
            f"Mode `{mode}` not found. Expected one of {list(d.keys())}"
        )


class CaptureMethods:
    """Defines data capture methods for each operating mode."""

    def __init__(self) -> None:
        """Initialise an empty collection of capture methods."""
        self._capture_methods: dict[str, Callable[[str, Parameters], None]] = {}

    def add(self, mode: str, capture_method: Callable[[str, Parameters], None]) -> None:
        """Add a capture method for a specific operating mode.

        :param mode: The operating mode for the receiver.
        :param capture_method: The function defining how data is captured in this mode.
        """
        self._capture_methods[mode] = capture_method

    def get(self, mode: str) -> Callable[[str, Parameters], None]:
        """Retrieve the capture method for a specific operating mode.

        :param mode: The operating mode for the receiver.
        :return: The function to capture data in this mode.
        """
        _ensure_mode_exists(mode, self._capture_methods)
        return self._capture_methods[mode]


class CaptureTemplates:
    """Defines parameter templates for each operating mode."""

    def __init__(self) -> None:
        """Initialise an empty collection of capture templates."""
        self._capture_templates: dict[str, CaptureTemplate] = {}

    def add(self, mode: str, capture_template: CaptureTemplate) -> None:
        """Add a capture template for a specific operating mode.

        :param mode: The operating mode for the receiver.
        :param capture_template: The template defining required parameters for this mode.
        """
        self._capture_templates[mode] = capture_template

    def get(self, mode: str) -> CaptureTemplate:
        """Retrieve the capture template for a specific operating mode.

        :param mode: The operating mode for the receiver.
        :return: The template for this mode.
        """
        _ensure_mode_exists(mode, self._capture_templates)
        return self._capture_templates[mode]


def default_pvalidator(parameters: Parameters) -> None:
    """Default, noop, parameter validator. Doesn't check anything at all."""


class PValidators:
    """Defines parameter validation functions for each operating mode."""

    def __init__(self) -> None:
        """Initialise an empty collection of parameter validators."""
        self._pvalidators: dict[str, Callable[[Parameters], None]] = {}

    def add(self, mode: str, pvalidator: Callable[[Parameters], None]) -> None:
        """Add a parameter validator for a specific operating mode.

        :param mode: The operating mode for the receiver.
        :param pvalidator: The function to validate parameters for this mode.
        """
        self._pvalidators[mode] = pvalidator

    def get(self, mode: str) -> Callable[[Parameters], None]:
        """Retrieve the parameter validator for a specific operating mode.

        :param mode: The operating mode for the receiver.
        :return: The function to validate parameters for this mode.
        """
        _ensure_mode_exists(mode, self._pvalidators)
        return self._pvalidators[mode]


class Receiver:
    """Abstraction layer for software-defined radio receivers."""

    def __init__(self, name: ReceiverName, mode: Optional[str] = None) -> None:
        """Initialise a receiver instance.

        :param name: The name of the receiver.
        :param capture_methods: Defines how the receiver captures data per mode.
        :param capture_templates: Defines required parameters per mode.
        :param pvalidators: Defines parameter validation functions per mode.
        :param specs: Hardware specifications for the receiver.
        :param mode: The initial active operating mode. Defaults to None.
        """
        self._name = name
        self._mode = mode
        self._specs = Specs()
        self._capture_methods = CaptureMethods()
        self._capture_templates = CaptureTemplates()
        self._pvalidators = PValidators()

    @property
    def name(self) -> ReceiverName:
        """Retrieve the receiver's name."""
        return self._name

    @property
    def mode(self) -> Optional[str]:
        """Retrieve the active operating mode."""
        return self._mode

    @mode.setter
    def mode(self, value: str) -> None:
        """Set the active operating mode.

        :param value: The new operating mode to activate.
        """
        self._mode = value

    @property
    def active_mode(self) -> str:
        """Retrieve the active operating mode, raising an error if not set.

        :raises ValueError: If no mode is currently set.
        :return: The active operating mode.
        """
        if self._mode is None:
            raise ValueError(
                f"This operation requires an active mode for receiver `{self.name.value}`. Currently, the mode is {self._mode}"
            )
        return self._mode

    @property
    def capture_method(self) -> Callable[[str, Parameters], None]:
        """Retrieve the capture method for the active operating mode."""
        return self._capture_methods.get(self.active_mode)

    @property
    def capture_template(self) -> CaptureTemplate:
        """Retrieve the capture template for the active operating mode."""
        return self._capture_templates.get(self.active_mode)

    @property
    def pvalidator(self) -> Callable[[Parameters], None]:
        """Retrieve the parameter validator for the active operating mode."""
        return self._pvalidators.get(self.active_mode)

    @property
    def specs(self) -> Specs:
        """Retrieve all hardware specifications.

        :return: A dictionary of all specifications.
        """
        return self._specs

    def start_capture(self, tag: str) -> None:
        """Start capturing data using the active operating mode.

        :param tag: The tag identifying the capture configuration.
        :raises ValueError: If no mode is currently set.
        """
        self.capture_method(tag, self.load_parameters(tag))

    def save_parameters(
        self,
        tag: str,
        parameters: Parameters,
        force: bool = False,
        validate: bool = False,
    ) -> None:
        """Save parameters to a capture configuration.

        :param tag: The tag identifying the capture configuration.
        :param parameters: The parameters to save.
        :param force: If True, overwrite existing configuration if it exists.
        :param pvalidate: If True, apply the capture template and pvalidator.
        :raises ValueError: If no mode is currently set.
        """
        if validate:
            parameters = self.capture_template.apply_template(parameters)
            self.pvalidator(parameters)

        capture_config = CaptureConfig(tag)
        capture_config.save_parameters(
            self.name.value, self.active_mode, parameters, force
        )

    def load_parameters(self, tag: str, validate: bool = True) -> Parameters:
        """Load parameters from a capture configuration.

        :param tag: The tag identifying the capture configuration.
        :param pvalidate: If True, apply the capture template and pvalidator.
        :raises ValueError: If no mode is currently set.
        :return: The validated parameters stored in the configuration.
        """
        capture_config = CaptureConfig(tag)

        if validate:
            parameters = self.capture_template.apply_template(capture_config.parameters)
            self.pvalidator(parameters)
            return parameters
        else:
            return capture_config.parameters

    def add_mode(
        self,
        mode: str,
        capture_method: Callable[[str, Parameters], None],
        capture_template: CaptureTemplate,
        pvalidator: Callable[[Parameters], None] = default_pvalidator,
    ) -> None:
        """Add a new mode to the receiver.

        :param mode: The name of the new mode.
        :param capture_method: The function defining how data is captured in this mode.
        :param capture_template: The template defining required parameters for this mode.
        :param pvalidator: The function to validate parameters for this mode.
        """
        self._capture_methods.add(mode, capture_method)
        self._capture_templates.add(mode, capture_template)
        self._pvalidators.add(mode, pvalidator)

    def add_spec(self, name: SpecName, value: float | int | list[float | int]) -> None:
        """Add a hardware specification.

        :param name: The specification's name.
        :param value: The specification's value.
        """
        self._specs.add(name, value)

    def get_spec(self, name: SpecName) -> float | int | list[float | int]:
        """Retrieve a specific hardware specification.

        :param name: The specification's name.
        :return: The specification's value.
        """
        return self.specs.get(name)
