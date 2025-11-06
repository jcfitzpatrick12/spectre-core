# SPDX-FileCopyrightText: © 2024-2025 Jimmy Fitzpatrick <jcfitzpatrick12@gmail.com>
# This file is part of SPECTRE
# SPDX-License-Identifier: GPL-3.0-or-later

import dataclasses
import dataclasses
import typing

import numpy as np
import numpy.typing as npt

import spectre_core.event_handlers
import spectre_core.flowgraphs
import spectre_core.models
import spectre_core.batches
import spectre_core.spectrograms

from ._register import register_receiver
from ._base import Base, ReceiverComponents
from ._names import ReceiverName
from ._config import Config


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


class Solvers(
    ReceiverComponents[
        typing.Callable[
            [int, dict[str, typing.Any]], spectre_core.spectrograms.Spectrogram
        ]
    ]
):
    """For each mode, produce an analytically-derived spectrogram."""


def cosine_wave_solver(
    num_spectrums: int, parameters: dict[str, typing.Any]
) -> spectre_core.spectrograms.Spectrogram:
    """Produces the analytically-derived spectrogram for the `SignalGenerator` receiver operating in the mode `cosine_wave`."""

    sample_rate = typing.cast(int, parameters["sample_rate"])
    window_size = typing.cast(int, parameters["window_size"])
    window_hop = typing.cast(int, parameters["window_hop"])
    frequency = typing.cast(float, parameters["frequency"])
    amplitude = typing.cast(float, parameters["amplitude"])
    center_frequency = typing.cast(float, parameters["center_frequency"])

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
    dynamic_spectra = np.ones((window_size, num_spectrums)) * spectrum[:, np.newaxis]

    # Compute time array.
    sampling_interval = np.float32(1 / sample_rate)
    times = np.arange(num_spectrums) * window_hop * sampling_interval

    # compute the frequency array.
    frequencies = (
        np.fft.fftshift(np.fft.fftfreq(window_size, sampling_interval))
        + center_frequency
    )

    # Return the spectrogram.
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
class SignalGenerator(Base):
    """An entirely software-defined receiver, which generates synthetic signals."""

    def __init__(
        self, *args, solvers: typing.Optional[Solvers] = None, **kwargs
    ) -> None:
        super().__init__(*args, **kwargs)

        self.__solvers = solvers or Solvers()

        self.add_mode(
            _Mode.COSINE_WAVE,
            spectre_core.models.CosineWaveModel,
            spectre_core.flowgraphs.CosineWave,
            spectre_core.event_handlers.FixedCenterFrequency,
            spectre_core.batches.IQStreamBatch,
        )
        self.add_solver(_Mode.COSINE_WAVE, cosine_wave_solver)

    @property
    def solver(
        self,
    ) -> typing.Callable[
        [int, dict[str, typing.Any]], spectre_core.spectrograms.Spectrogram
    ]:
        return self.__solvers.get(self.active_mode)

    def add_solver(
        self,
        mode: str,
        solver: typing.Callable[
            [int, dict[str, typing.Any]], spectre_core.spectrograms.Spectrogram
        ],
    ) -> None:
        self.__solvers.add(mode, solver)

    def validate_analytically(
        self,
        spectrogram: spectre_core.spectrograms.Spectrogram,
        config: Config,
        absolute_tolerance: float,
    ) -> dict[str, typing.Any]:
        """Validate a spectrogram generated during sessions with a `SignalGenerator` receiver operating
        in a particular mode.

        :param spectrogram: The spectrogram to be validated.
        :param absolute_tolerance: Tolerance level for numerical comparisons.
        :return: A dictionary summarising the validation outcome.
        """
        analytical_spectrogram = self.solver(spectrogram.num_times, config.parameters)

        # Validate times and frequencies.
        print(analytical_spectrogram.num_frequencies)
        print(spectrogram.num_frequencies)
        print(analytical_spectrogram.times)
        print(spectrogram.times)
        times_validated = _is_close(
            analytical_spectrogram.times, spectrogram.times, absolute_tolerance
        )
        frequencies_validated = _is_close(
            analytical_spectrogram.frequencies,
            spectrogram.frequencies,
            absolute_tolerance,
        )

        # Validate each spectrum.
        spectrum_validated = {
            spectrogram.times[i]: _is_close(
                analytical_spectrogram.dynamic_spectra[:, i],
                spectrogram.dynamic_spectra[:, i],
                absolute_tolerance,
            )
            for i in range(spectrogram.num_times)
        }

        # Summarise results
        num_validated_spectrums = sum(spectrum_validated.values())
        num_invalid_spectrums = len(spectrum_validated) - num_validated_spectrums

        return {
            "times_validated": times_validated,
            "frequencies_validated": frequencies_validated,
            "spectrum_validated": spectrum_validated,
            "num_validated_spectrums": num_validated_spectrums,
            "num_invalid_spectrums": num_invalid_spectrums,
        }
