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
import spectre_core.fields

from ._base import Base, BaseModel
from ._stfft import (
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


class FixedCenterFrequencyModel(BaseModel):
    window_size: spectre_core.fields.Field.window_size = 1024
    window_hop: spectre_core.fields.Field.window_hop = 1024
    window_type: spectre_core.fields.Field.window_type = "blackman"
    center_frequency: spectre_core.fields.Field.center_frequency = 95.8e6
    sample_rate: spectre_core.fields.Field.sample_rate = 1000000
    frequency_resolution: spectre_core.fields.Field.frequency_resolution = 0
    time_resolution: spectre_core.fields.Field.time_resolution = 0
    batch_size: spectre_core.fields.Field.batch_size = 3
    keep_signal: spectre_core.fields.Field.keep_signal = True

    @pydantic.model_validator(mode="after")
    def validate(self):
        window_interval = self.window_size * (1 / self.sample_rate)
        if window_interval > self.batch_size:
            raise ValueError(
                (
                    f"The windowing interval must be strictly less than the batch size. "
                    f"Computed the windowing interval to be {window_interval} [s], "
                    f"but the batch size is {self.batch_size} [s]"
                )
            )
        return self


class FixedCenterFrequency(Base[spectre_core.batches.IQStreamBatch]):
    def __init__(
        self,
        tag: str,
        parameters: dict[str, typing.Any],
        batch_cls: typing.Type[spectre_core.batches.IQStreamBatch],
    ) -> None:
        super().__init__(tag, parameters, batch_cls)

        # Unpack configurable parameters.
        self.__window_size = typing.cast(int, parameters["window_size"])
        self.__window_hop = typing.cast(int, parameters["window_hop"])
        self.__window_type = typing.cast(str, parameters["window_type"])
        self.__center_frequency = typing.cast(float, parameters["center_frequency"])
        self.__sample_rate = typing.cast(int, parameters["sample_rate"])
        self.__time_resolution = typing.cast(float, parameters["time_resolution"])
        self.__frequency_resolution = typing.cast(
            float, parameters["frequency_resolution"]
        )
        self.__keep_signal = typing.cast(bool, parameters["keep_signal"])

        # Make the window.
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
        """Compute the spectrogram of IQ samples captured at a fixed center frequency."""
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

        _LOGGER.info("Creating the spectrogram")
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

        spectrogram = spectre_core.spectrograms.time_average(
            spectrogram, resolution=self.__time_resolution
        )
        spectrogram = spectre_core.spectrograms.frequency_average(
            spectrogram, resolution=self.__frequency_resolution
        )

        _LOGGER.info("Spectrogram created successfully")

        if not self.__keep_signal:
            _LOGGER.info(f"Deleting {batch.bin_file.file_path}")
            batch.bin_file.delete()

            _LOGGER.info(f"Deleting {batch.hdr_file.file_path}")
            batch.hdr_file.delete()

        return spectrogram
