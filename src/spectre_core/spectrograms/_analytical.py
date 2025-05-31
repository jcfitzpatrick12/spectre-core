# SPDX-FileCopyrightText: © 2024-2025 Jimmy Fitzpatrick <jcfitzpatrick12@gmail.com>
# This file is part of SPECTRE
# SPDX-License-Identifier: GPL-3.0-or-later

from typing import Callable, cast
from dataclasses import dataclass, field

import numpy as np

from spectre_core.capture_configs import CaptureConfig, PName
from spectre_core.exceptions import ModeNotFoundError
from ._spectrogram import Spectrogram, SpectrumUnit
from ._array_operations import is_close


@dataclass
class TestResults:
    """
    Summarise the validation results when comparing two spectrograms.

    :ivar times_validated: Whether the time arrays match.
    :ivar frequencies_validated: Whether the frequency arrays match.
    :ivar spectrum_validated: Maps the relative time of each spectrum to its match results.
    """

    times_validated: bool = False
    frequencies_validated: bool = False
    spectrum_validated: dict[float, bool] = field(default_factory=dict)

    @property
    def num_validated_spectrums(self) -> int:
        """Returns the count of spectrums that successfully passed validation."""
        return sum(is_validated for is_validated in self.spectrum_validated.values())

    @property
    def num_invalid_spectrums(self) -> int:
        """Returns the count of spectrums that failed validation."""
        return len(self.spectrum_validated) - self.num_validated_spectrums

    def to_dict(self) -> dict[str, bool | dict[float, bool]]:
        """Converts the instance into a serialisable dictionary."""
        return {
            "times_validated": self.times_validated,
            "frequencies_validated": self.frequencies_validated,
            "spectrum_validated": self.spectrum_validated,
        }


class _AnalyticalFactory:
    """Factory for creating analytical spectrograms."""

    def __init__(self) -> None:
        """Initialises an instance of the `_AnalyticalFactory` class."""
        self._builders: dict[str, Callable[[int, CaptureConfig], Spectrogram]] = {
            "cosine_signal_1": self._cosine_signal_1,
            "tagged_staircase": self._tagged_staircase,
        }

    @property
    def builders(self) -> dict[str, Callable[[int, CaptureConfig], Spectrogram]]:
        """
        Provides a mapping from each `Test` receiver mode to its corresponding builder method.

        Each builder method generates the expected spectrograms for a session run in the associated mode.
        """
        return self._builders

    @property
    def test_modes(self) -> list[str]:
        """Returns the available modes for the `Test` receiver."""
        return list(self.builders.keys())

    def get_spectrogram(
        self, num_spectrums: int, capture_config: CaptureConfig
    ) -> Spectrogram:
        """
        Generates an analytical spectrogram based on the capture config for a `Test` receiver.

        :param num_spectrums: The number of spectrums to include in the output spectrogram.
        :param capture_config: The capture config used for `Test` receiver data capture.
        :raises ValueError: Raised if the capture config is not associated with a `Test` receiver.
        :raises ModeNotFoundError: Raised if the specified `Test` mode in the capture config lacks
        a corresponding builder method.
        :return: The expected spectrogram for running a session with the `Test` receiver in the specified mode.
        """
        if capture_config.receiver_name != "test":
            raise ValueError(
                f"Input capture config must correspond to the test receiver"
            )

        builder_method = self.builders.get(capture_config.receiver_mode)
        if builder_method is None:
            raise ModeNotFoundError(
                f"Test mode not found. Expected one of '{self.test_modes}', but received '{capture_config.receiver_mode}'"
            )
        return builder_method(num_spectrums, capture_config)

    def _cosine_signal_1(
        self, num_spectrums: int, capture_config: CaptureConfig
    ) -> Spectrogram:
        """Creates the expected spectrogram for the `Test` receiver operating in the mode `cosine-signal-1`."""
        # Extract necessary parameters from the capture config.
        window_size = cast(int, capture_config.get_parameter_value(PName.WINDOW_SIZE))
        sample_rate = cast(int, capture_config.get_parameter_value(PName.SAMPLE_RATE))
        frequency = cast(int, capture_config.get_parameter_value(PName.FREQUENCY))
        window_hop = cast(int, capture_config.get_parameter_value(PName.WINDOW_HOP))
        amplitude = cast(float, capture_config.get_parameter_value(PName.AMPLITUDE))
        center_frequency = cast(
            float, capture_config.get_parameter_value(PName.CENTER_FREQUENCY)
        )

        # Calculate derived parameters a (sampling rate ratio) and p (sampled periods).
        a = int(sample_rate / frequency)
        p = int(window_size / a)

        # Create the analytical spectrum, which is constant in time.
        spectrum = np.zeros(window_size)
        spectral_amplitude = amplitude * window_size / 2
        spectrum[p] = spectral_amplitude
        spectrum[window_size - p] = spectral_amplitude

        # Align spectrum to naturally ordered frequency array.
        spectrum = np.fft.fftshift(spectrum)

        # Populate the spectrogram with identical spectra.
        analytical_dynamic_spectra = (
            np.ones((window_size, num_spectrums)) * spectrum[:, np.newaxis]
        )

        # Compute time array.
        sampling_interval = 1 / sample_rate
        times = np.arange(num_spectrums) * window_hop * sampling_interval

        # compute the frequency array.
        frequencies = (
            np.fft.fftshift(np.fft.fftfreq(window_size, sampling_interval))
            + center_frequency
        )

        # Return the spectrogram.
        return Spectrogram(
            analytical_dynamic_spectra,
            times,
            frequencies,
            "analytically-derived-spectrogram",
            SpectrumUnit.AMPLITUDE,
        )

    def _tagged_staircase(
        self, num_spectrums: int, capture_config: CaptureConfig
    ) -> Spectrogram:
        """Creates the expected spectrogram for the `Test` receiver operating in the mode `tagged-staircase`."""
        # Extract necessary parameters from the capture config.
        window_size = cast(int, capture_config.get_parameter_value(PName.WINDOW_SIZE))
        min_samples_per_step = cast(
            int, capture_config.get_parameter_value(PName.MIN_SAMPLES_PER_STEP)
        )
        max_samples_per_step = cast(
            int, capture_config.get_parameter_value(PName.MAX_SAMPLES_PER_STEP)
        )
        step_increment = cast(
            int, capture_config.get_parameter_value(PName.STEP_INCREMENT)
        )
        samp_rate = cast(int, capture_config.get_parameter_value(PName.SAMPLE_RATE))

        # Calculate step sizes and derived parameters.
        num_samples_per_step = np.arange(
            min_samples_per_step, max_samples_per_step + 1, step_increment
        )
        num_steps = len(num_samples_per_step)

        # Create the analytical spectrum, constant in time.
        spectrum = np.zeros(window_size * num_steps)
        step_count = 0
        for i in range(num_steps):
            step_count += 1
            spectral_amplitude = window_size * step_count
            spectrum[int(window_size / 2) + i * window_size] = spectral_amplitude

        # Populate the spectrogram with identical spectra.
        analytical_dynamic_spectra = (
            np.ones((window_size * num_steps, num_spectrums)) * spectrum[:, np.newaxis]
        )

        # Compute time array
        num_samples_per_sweep = sum(num_samples_per_step)
        sampling_interval = 1 / samp_rate
        # compute the sample index we are "assigning" to each spectrum
        # and multiply by the sampling interval to get the equivalent physical time
        times = (
            np.array([(i * num_samples_per_sweep) for i in range(num_spectrums)])
            * sampling_interval
        )

        # Compute the frequency array
        baseband_frequencies = np.fft.fftshift(
            np.fft.fftfreq(window_size, sampling_interval)
        )
        frequencies = np.empty((window_size * num_steps), dtype=np.float32)
        for i in range(num_steps):
            lower_bound = i * window_size
            upper_bound = (i + 1) * window_size
            frequencies[lower_bound:upper_bound] = (
                baseband_frequencies + (samp_rate / 2) + (samp_rate * i)
            )

        # Return the spectrogram.
        return Spectrogram(
            analytical_dynamic_spectra,
            times,
            frequencies,
            "analytically-derived-spectrogram",
            SpectrumUnit.AMPLITUDE,
        )


def get_analytical_spectrogram(
    num_spectrums: int, capture_config: CaptureConfig
) -> Spectrogram:
    """Each mode of the `Test` receiver generates a known synthetic signal. Based on this, we can
    derive an analytical solution that predicts the expected spectrogram for a session in that mode.

    This function constructs the analytical spectrogram using the capture config for a `Test`
    receiver operating in a specific mode.

    :param num_spectrums: The number of spectrums in the output spectrogram.
    :param capture_config: The capture config used for data capture.
    :return: The expected, analytically derived spectrogram for the specified mode of the `Test` receiver.
    """
    factory = _AnalyticalFactory()
    return factory.get_spectrogram(num_spectrums, capture_config)


def validate_analytically(
    spectrogram: Spectrogram, capture_config: CaptureConfig, absolute_tolerance: float
) -> TestResults:
    """Validate a spectrogram generated during sessions with a `Test` receiver operating
    in a particular mode.

    :param spectrogram: The spectrogram to be validated.
    :param capture_config: The capture config used for data capture.
    :param absolute_tolerance: Tolerance level for numerical comparisons.
    :return: A `TestResults` object summarising the validation outcome.
    """
    analytical_spectrogram = get_analytical_spectrogram(
        spectrogram.num_times, capture_config
    )

    test_results = TestResults()

    test_results.times_validated = bool(
        is_close(analytical_spectrogram.times, spectrogram.times, absolute_tolerance)
    )

    test_results.frequencies_validated = bool(
        is_close(
            analytical_spectrogram.frequencies,
            spectrogram.frequencies,
            absolute_tolerance,
        )
    )

    test_results.spectrum_validated = {}
    for i in range(spectrogram.num_times):
        time = spectrogram.times[i]
        analytical_spectrum = analytical_spectrogram.dynamic_spectra[:, i]
        spectrum = spectrogram.dynamic_spectra[:, i]
        test_results.spectrum_validated[time] = bool(
            is_close(analytical_spectrum, spectrum, absolute_tolerance)
        )

    return test_results
