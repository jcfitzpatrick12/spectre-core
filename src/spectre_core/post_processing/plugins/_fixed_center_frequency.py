# SPDX-FileCopyrightText: © 2024-2025 Jimmy Fitzpatrick <jcfitzpatrick12@gmail.com>
# This file is part of SPECTRE
# SPDX-License-Identifier: GPL-3.0-or-later

import logging
import datetime
import typing

import pydantic
import numpy as np

import spectre_core.batches
import spectre_core.spectrograms
from .._base import BaseEventHandler, BaseEventHandlerModel
from .._stfft import (
    get_buffer,
    get_window,
    get_times,
    get_num_spectrums,
    get_frequencies,
    get_fftw_obj,
    stfft,
    WindowType,
)

_LOGGER = logging.getLogger(__name__)


class FixedEventHandlerModel(BaseEventHandlerModel):
    window_size: int = pydantic.Field(
        512,
        gt=0,
        description="The size of the window, in samples, when performing the Short Time FFT.",
    )
    window_hop: int = pydantic.Field(
        1024,
        gt=0,
        description="How much the window is shifted, in samples, when performing the Short Time FFT.",
    )
    window_type: typing.Literal[
        WindowType.BLACKMAN, WindowType.HANN, WindowType.BOXCAR
    ] = pydantic.Field(
        WindowType.BLACKMAN,
        description="The type of window applied when performing the Short Time FFT.",
    )
    center_frequency: float = pydantic.Field(
        95800000.0,
        gt=0.0,
        description="The center frequency of the SDR in Hz. This value determines the midpoint of the frequency range being processed.",
    )
    sample_rate: int = pydantic.Field(
        1000000, gt=0, description="The number of samples per second in Hz."
    )
    frequency_resolution: float = pydantic.Field(
        0,
        ge=0,
        description="Spectrograms are averaged up to the frequency resolution, in Hz.",
    )
    time_resolution: typing.Optional[float] = pydantic.Field(
        0,
        ge=0,
        description="Spectrograms are averaged up to the time resolution, in seconds.",
    )

    class ConfigDict:
        validate_assignment = True


class FixedEventHandler(BaseEventHandler[spectre_core.batches.IQStreamBatch]):
    def __init__(
        self,
        tag: str,
        parameters: dict[str, typing.Any],
        batch_cls: typing.Type[spectre_core.batches.IQStreamBatch],
    ) -> None:
        super().__init__(tag, parameters, batch_cls)
        self.__window_size = typing.cast(int, parameters["window_size"])
        self.__window_hop = typing.cast(int, parameters["window_hop"])
        self.__window_type = typing.cast(str, parameters["window_type"])
        self.__center_frequency = typing.cast(float, parameters["center_frequency"])
        self.__sample_rate = typing.cast(int, parameters["sample_rate"])
        self.__time_resolution = typing.cast(float, parameters["time_resolution"])
        self.__frequency_resolution = typing.cast(
            float, parameters["frequency_resolution"]
        )

        # Read all the required capture config parameters.
        self.__window = get_window(WindowType(self.__window_type), self.__window_size)

        # Pre-allocate the buffer.
        self.__buffer = get_buffer(self.__window_size)

        # Defer the expensive FFTW plan creation until the first batch is being processed.
        # With this approach, we avoid a bug where filesystem events are missed because
        # the watchdog observer isn't set up in time before the receiver starts capturing data.
        self.__fftw_obj = None

    @property
    def _watch_extension(self) -> str:
        return spectre_core.batches.IQStreamBatchExtension.BIN

    def process(
        self, batch: spectre_core.batches.IQStreamBatch
    ) -> spectre_core.spectrograms.Spectrogram:
        """Compute the spectrogram of IQ samples captured at a fixed center frequency, then save it to
        file in the FITS format.
        """
        _LOGGER.info(f"Reading {batch.bin_file.file_path}")
        iq_data = batch.bin_file.read()

        _LOGGER.info(f"Reading {batch.hdr_file.file_path}")
        iq_metadata = batch.hdr_file.read()

        if self.__fftw_obj is None:
            _LOGGER.info(f"Creating the FFTW plan")
            self.__fftw_obj = get_fftw_obj(self.__buffer)

        _LOGGER.info("Executing the short-time FFT")
        dynamic_spectra = stfft(
            self.__fftw_obj, self.__buffer, iq_data, self.__window, self.__window_hop
        )

        # Shift the zero-frequency component to the middle of the spectrum.
        dynamic_spectra = np.fft.fftshift(dynamic_spectra, axes=0)

        # Get the physical frequencies assigned to each spectral component, shift the zero frequency to the middle of the
        # spectrum, then translate the array up from the baseband.
        frequencies = (
            np.fft.fftshift(get_frequencies(self.__window_size, self.__sample_rate))
            + self.__center_frequency
        )

        # Compute the physical times we'll assign to each spectrum.
        num_spectrums = get_num_spectrums(
            iq_data.size, self.__window_size, self.__window_hop
        )
        times = get_times(num_spectrums, self.__sample_rate, self.__window_hop)

        # Account for the millisecond correction.
        start_datetime = batch.start_datetime + datetime.timedelta(
            milliseconds=iq_metadata.millisecond_correction
        )

        spectrogram = spectre_core.spectrograms.Spectrogram(
            dynamic_spectra,
            times,
            frequencies,
            spectre_core.spectrograms.SpectrumUnit.AMPLITUDE,
            start_datetime,
        )

        _LOGGER.info("Averaging the spectrogram")
        spectrogram = spectre_core.spectrograms.time_average(
            spectrogram, resolution=self.__time_resolution
        )
        spectrogram = spectre_core.spectrograms.frequency_average(
            spectrogram, resolution=self.__frequency_resolution
        )

        _LOGGER.info(f"Deleting {batch.bin_file.file_path}")
        batch.bin_file.delete()

        _LOGGER.info(f"Deleting {batch.hdr_file.file_path}")
        batch.hdr_file.delete()

        return spectrogram
