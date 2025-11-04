# SPDX-FileCopyrightText: © 2024-2025 Jimmy Fitzpatrick <jcfitzpatrick12@gmail.com>
# This file is part of SPECTRE
# SPDX-License-Identifier: GPL-3.0-or-later

import dataclasses
import dataclasses
import typing

import numpy as np
import numpy.typing as npt

import spectre_core.post_processing
import spectre_core.batches
import spectre_core.spectrograms

from ._signal_generator_flowgraphs import CosineWave, CosineWaveModel
from .._register import register_receiver
from .._base import BaseReceiver, ReceiverComponents
from ._receiver_names import ReceiverName


def _is_close(
    ar: npt.NDArray[np.float32],
    ar_comparison: npt.NDArray[np.float32],
    absolute_tolerance: float,
) -> bool:
    """
    Checks if all elements in two arrays are element-wise close within a given tolerance.

    :param ar: First array for comparison.
    :param ar_comparison: Second array for comparison.
    :param absolute_tolerance: Absolute tolerance for element-wise comparison.
    :return: `True` if all elements are close within the specified tolerance, otherwise `False`.
    """
    return bool(np.all(np.isclose(ar, ar_comparison, atol=absolute_tolerance)))


@dataclasses.dataclass
class TestResults:
    """
    Summarise the validation results when comparing two spectrograms.

    :ivar times_validated: Whether the time arrays match.
    :ivar frequencies_validated: Whether the frequency arrays match.
    :ivar spectrum_validated: Maps the relative time of each spectrum to its match results.
    """

    times_validated: bool = False
    frequencies_validated: bool = False
    spectrum_validated: dict[float, bool] = dataclasses.field(default_factory=dict)

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


class Solvers(
    ReceiverComponents[
        typing.Callable[
            [int, dict[str, typing.Any]], spectre_core.spectrograms.Spectrogram
        ]
    ]
):
    """Produce an analytically-derived spectrogram."""


def cosine_wave_solver(
    num_spectrums: int, parameters: dict[str, typing.Any]
) -> spectre_core.spectrograms.Spectrogram:
    """Creates the expected spectrogram for the `SignalGenerator` receiver operating in the mode `cosine_wave`."""

    sample_rate = typing.cast(int, parameters.pop("sample_rate"))
    window_size = typing.cast(int, parameters.pop("window_size"))
    window_hop = typing.cast(int, parameters.pop("window_hop"))
    frequency = typing.cast(float, parameters.pop("frequency"))
    amplitude = typing.cast(float, parameters.pop("amplitude"))
    center_frequency = typing.cast(float, parameters.pop("center_frequency"))

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
    dynamic_spectra = np.ones((window_size, num_spectrums)) * spectrum[:, np.newaxis]

    # Compute times array.
    sampling_interval = np.float32(1 / sample_rate)
    times = np.arange(num_spectrums) * window_hop * sampling_interval

    # Compute the physical frequencies we'll assign to each spectrel component.
    frequencies = (
        np.fft.fftshift(np.fft.fftfreq(window_size, sampling_interval))
        + center_frequency
    )

    return spectre_core.spectrograms.Spectrogram(
        dynamic_spectra,
        times,
        frequencies,
        spectre_core.spectrograms.SpectrumUnit.AMPLITUDE,
    )


@dataclasses.dataclass(frozen=True)
class _Mode:
    """An operating mode for the `SignalGenerator` receiver."""

    COSINE_WAVE = "cosine_wave"


@register_receiver(ReceiverName.SIGNAL_GENERATOR)
class SignalGenerator(BaseReceiver):
    """An entirely software-defined receiver, which generates synthetic signals."""

    def add_solver(
        self,
        mode: str,
        solver: typing.Callable[
            [int, dict[str, typing.Any]], spectre_core.spectrograms.Spectrogram
        ],
    ) -> None:
        self.__solvers.add(mode, solver)

    @property
    def solver(
        self,
    ) -> typing.Callable[
        [int, dict[str, typing.Any]], spectre_core.spectrograms.Spectrogram
    ]:
        return self.__solvers.get(self.active_mode)

    def __init__(
        self, *args, solvers: typing.Optional[Solvers] = None, **kwargs
    ) -> None:
        super().__init__(*args, **kwargs)

        self.__solvers = solvers or Solvers()

        self.add_mode(
            _Mode.COSINE_WAVE,
            (
                CosineWave,
                CosineWaveModel,
            ),
            (
                spectre_core.post_processing.FixedEventHandler,
                spectre_core.post_processing.FixedEventHandlerModel,
            ),
            spectre_core.batches.IQStreamBatch,
        )
        self.add_solver(_Mode.COSINE_WAVE, cosine_wave_solver)


def get_analytical_spectrogram(
    mode: str, num_spectrums: int, **parameters: dict[str, typing.Any]
) -> spectre_core.spectrograms.Spectrogram:
    """Each mode of the `SignalGenerator` receiver generates a known synthetic signal. Based on this, we can
    derive an analytical solution that predicts the expected spectrogram for a session in that mode.

    This function constructs the analytical spectrogram using the capture config for a `SignalGenerator`
    receiver operating in a specific mode.

    :param num_spectrums: The number of spectrums in the output spectrogram.
    :param capture_config: The capture config used for data capture.
    :return: The expected, analytically derived spectrogram for the specified mode of the `SignalGenerator` receiver.
    """
    signal_generator = SignalGenerator(mode=mode)
    return signal_generator.solver(num_spectrums, parameters)


def validate_analytically(
    mode: str,
    spectrogram: spectre_core.spectrograms.Spectrogram,
    absolute_tolerance: float,
    **parameters: dict[str, typing.Any],
) -> TestResults:
    """Validate a spectrogram generated during sessions with a `SignalGenerator` receiver operating
    in a particular mode.

    :param spectrogram: The spectrogram to be validated.
    :param capture_config: The capture config used for data capture.
    :param absolute_tolerance: Tolerance level for numerical comparisons.
    :return: A `TestResults` object summarising the validation outcome.
    """
    analytical_spectrogram = get_analytical_spectrogram(
        mode, spectrogram.num_times, **parameters
    )

    test_results = TestResults()

    test_results.times_validated = bool(
        _is_close(analytical_spectrogram.times, spectrogram.times, absolute_tolerance)
    )

    test_results.frequencies_validated = bool(
        _is_close(
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
            _is_close(analytical_spectrum, spectrum, absolute_tolerance)
        )

    return test_results
