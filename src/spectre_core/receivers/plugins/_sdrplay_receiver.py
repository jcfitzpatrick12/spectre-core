# SPDX-FileCopyrightText: © 2024-2025 Jimmy Fitzpatrick <jcfitzpatrick12@gmail.com>
# This file is part of SPECTRE
# SPDX-License-Identifier: GPL-3.0-or-later

from abc import ABC, abstractmethod
from typing import Callable, cast, Optional
from logging import getLogger

_LOGGER = getLogger(__name__)

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

from .._receiver import Receiver, ReceiverName
from .._specs import SpecName

LOW_IF_SAMPLE_RATE_CUTOFF = 2e6
LOW_IF_PERMITTED_SAMPLE_RATES = [LOW_IF_SAMPLE_RATE_CUTOFF / (2**i) for i in range(6)]


class SDRplayReceiver(ABC, Receiver):
    """An abstract base class for SDRplay devices."""

    def __init__(self, name: ReceiverName, mode: Optional[str]):
        """Initialise an instance of an `SDRplayReceiver`."""
        super().__init__(name, mode)

        self.add_spec(SpecName.SAMPLE_RATE_LOWER_BOUND, 62.5e3)
        self.add_spec(SpecName.SAMPLE_RATE_UPPER_BOUND, 10.66e6)
        self.add_spec(SpecName.FREQUENCY_LOWER_BOUND, 1e3)
        self.add_spec(SpecName.FREQUENCY_UPPER_BOUND, 2e9)
        self.add_spec(SpecName.IF_GAIN_UPPER_BOUND, -20)
        self.add_spec(SpecName.IF_GAIN_LOWER_BOUND, -59)
        self.add_spec(SpecName.API_RETUNING_LATENCY, 25 * 1e-3)

        # bandwidth == 0 means 'AUTO', i.e. the largest bandwidth compatible with the sample rate
        self.add_spec(
            SpecName.BANDWIDTH_OPTIONS,
            [0, 200e3, 300e3, 600e3, 1.536e6, 5e6, 6e6, 7e6, 8e6],
        )

    @abstractmethod
    def get_rf_gains(self, center_frequency: float) -> list[int]:
        """Get an ordered list of RF gain values corresponding to each LNA state at the specified center frequency.

        The values are taken from the gain reduction tables documented in the SDRplay API specification, and are
        unique to each model. Note that negative gain values represent positive gain reduction.
        """


def _validate_rf_gain(rf_gain: int, expected_rf_gains: list[int]):
    """Validate the RF gain value against the expected values for the current LNA state.

    The RF gain is determined by the LNA state and can only take specific values as documented in the
    gain reduction tables of the SDRplay API specification.

    For implementation details, refer to the `gr-sdrplay3` OOT module:
    https://github.com/fventuri/gr-sdrplay3/blob/v3.11.0.9/lib/rsp_impl.cc#L378-L387
    """
    if rf_gain not in expected_rf_gains:
        raise ValueError(
            f"The value of RF gain must be one of {expected_rf_gains}. "
            f"Got {rf_gain}."
        )


def _validate_low_if_sample_rate(sample_rate: int) -> None:
    """Validate the sample rate if the receiver is operating in low IF mode.

    The minimum physical sampling rate of the SDRplay hardware is 2 MHz. Lower effective rates can be achieved
    through decimation, as handled by the `gr-sdrplay3` OOT module. This function ensures that the sample rate
    is not silently adjusted by the backend.

    For implementation details, refer to:
    https://github.com/fventuri/gr-sdrplay3/blob/v3.11.0.9/lib/rsp_impl.cc#L140-L179
    """
    if sample_rate <= LOW_IF_SAMPLE_RATE_CUTOFF:
        if sample_rate not in LOW_IF_PERMITTED_SAMPLE_RATES:
            raise ValueError(
                f"If the requested sample rate is less than or equal to {LOW_IF_SAMPLE_RATE_CUTOFF}, "
                f"the receiver will be operating in low IF mode. "
                f"So, the sample rate must be exactly one of {LOW_IF_PERMITTED_SAMPLE_RATES}. "
                f"Got sample rate {sample_rate} Hz"
            )


def make_pvalidator_fixed_center_frequency(
    receiver: SDRplayReceiver,
) -> Callable[[Parameters], None]:
    def pvalidator(parameters: Parameters) -> None:
        validate_fixed_center_frequency(parameters)

        # Validate the sample rate, in the case the receiver will be operating in low if mode.
        sample_rate = cast(int, parameters.get_parameter_value(PName.SAMPLE_RATE))
        _validate_low_if_sample_rate(sample_rate)

        # Validate the rf gain value, which is a function of center frequency.
        rf_gain = cast(int, parameters.get_parameter_value(PName.RF_GAIN))
        center_frequency = cast(
            float, parameters.get_parameter_value(PName.CENTER_FREQUENCY)
        )
        _validate_rf_gain(rf_gain, receiver.get_rf_gains(center_frequency))

    return pvalidator


def make_pvalidator_swept_center_frequency(
    receiver: SDRplayReceiver,
) -> Callable[[Parameters], None]:
    def pvalidator(parameters: Parameters) -> None:
        validate_swept_center_frequency(
            parameters, receiver.get_spec(SpecName.API_RETUNING_LATENCY)
        )

        # Validate the sample rate, in the case the receiver will be operating in low if mode.
        sample_rate = cast(int, parameters.get_parameter_value(PName.SAMPLE_RATE))
        _validate_low_if_sample_rate(sample_rate)

        # Validate the rf gain value, which is a function of center frequency.
        rf_gain = cast(int, parameters.get_parameter_value(PName.RF_GAIN))
        min_frequency = cast(float, parameters.get_parameter_value(PName.MIN_FREQUENCY))
        max_frequency = cast(float, parameters.get_parameter_value(PName.MAX_FREQUENCY))
        _validate_rf_gain(rf_gain, receiver.get_rf_gains(min_frequency))
        _validate_rf_gain(rf_gain, receiver.get_rf_gains(max_frequency))

        # Check that we are not cross a threshold where the LNA state has to change
        if receiver.get_rf_gains(min_frequency) != receiver.get_rf_gains(max_frequency):
            _LOGGER.warning(
                "Crossing a threshold where the LNA state has to change. Performance may be reduced."
            )

    return pvalidator


def make_capture_template_fixed_center_frequency(
    receiver: SDRplayReceiver,
) -> CaptureTemplate:

    capture_template = get_base_capture_template(CaptureMode.FIXED_CENTER_FREQUENCY)
    capture_template.add_ptemplate(get_base_ptemplate(PName.BANDWIDTH))
    capture_template.add_ptemplate(get_base_ptemplate(PName.IF_GAIN))
    capture_template.add_ptemplate(get_base_ptemplate(PName.RF_GAIN))

    capture_template.set_defaults(
        (PName.BATCH_SIZE, 3.0),
        (PName.CENTER_FREQUENCY, 95800000),
        (PName.SAMPLE_RATE, 500000),
        (PName.BANDWIDTH, 300000),
        (PName.WINDOW_HOP, 512),
        (PName.WINDOW_SIZE, 1024),
        (PName.WINDOW_TYPE, "blackman"),
        (PName.RF_GAIN, 0),
        (PName.IF_GAIN, -30),
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
        PName.BANDWIDTH, [OneOf(receiver.get_spec(SpecName.BANDWIDTH_OPTIONS))]
    )
    capture_template.add_pconstraint(
        PName.IF_GAIN,
        [
            Bound(
                lower_bound=receiver.get_spec(SpecName.IF_GAIN_LOWER_BOUND),
                upper_bound=receiver.get_spec(SpecName.IF_GAIN_UPPER_BOUND),
            )
        ],
    )
    return capture_template


def make_capture_template_swept_center_frequency(
    receiver: Receiver,
) -> CaptureTemplate:

    capture_template = get_base_capture_template(CaptureMode.SWEPT_CENTER_FREQUENCY)
    capture_template.add_ptemplate(get_base_ptemplate(PName.BANDWIDTH))
    capture_template.add_ptemplate(get_base_ptemplate(PName.IF_GAIN))
    capture_template.add_ptemplate(get_base_ptemplate(PName.RF_GAIN))

    capture_template.set_defaults(
        (PName.BATCH_SIZE, 3.0),
        (PName.MIN_FREQUENCY, 95000000),
        (PName.MAX_FREQUENCY, 100000000),
        (PName.SAMPLES_PER_STEP, 80000),
        (PName.FREQUENCY_STEP, 2000000),
        (PName.SAMPLE_RATE, 2e6),
        (PName.BANDWIDTH, 1536000),
        (PName.WINDOW_HOP, 512),
        (PName.WINDOW_SIZE, 1024),
        (PName.WINDOW_TYPE, "blackman"),
        (PName.RF_GAIN, 0),
        (PName.IF_GAIN, -30),
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
        PName.BANDWIDTH, [OneOf(receiver.get_spec(SpecName.BANDWIDTH_OPTIONS))]
    )
    capture_template.add_pconstraint(
        PName.IF_GAIN,
        [
            Bound(
                lower_bound=receiver.get_spec(SpecName.IF_GAIN_LOWER_BOUND),
                upper_bound=receiver.get_spec(SpecName.IF_GAIN_UPPER_BOUND),
            )
        ],
    )
    return capture_template
