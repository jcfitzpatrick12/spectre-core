# SPDX-FileCopyrightText: © 2024-2025 Jimmy Fitzpatrick <jcfitzpatrick12@gmail.com>
# This file is part of SPECTRE
# SPDX-License-Identifier: GPL-3.0-or-later

from logging import getLogger

_LOGGER = getLogger(__name__)

from typing import cast
from datetime import timedelta

import os
import numpy as np

from spectre_core.capture_configs import PName
from spectre_core.batches import IQStreamBatch
from spectre_core.spectrograms import (
    Spectrogram,
    SpectrumUnit,
    time_average,
    frequency_average,
)
from ._event_handler_keys import EventHandlerKey
from .._base import BaseEventHandler
from .._register import register_event_handler
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


@register_event_handler(EventHandlerKey.FIXED_CENTER_FREQUENCY)
class FixedEventHandler(BaseEventHandler):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        # Read all the required capture config parameters.
        self._window_size = cast(
            int, self._capture_config.get_parameter_value(PName.WINDOW_SIZE)
        )
        self._window_type = cast(
            str, self._capture_config.get_parameter_value(PName.WINDOW_TYPE)
        )
        self._window_hop = cast(
            int, self._capture_config.get_parameter_value(PName.WINDOW_HOP)
        )
        self._center_frequency = cast(
            float, self._capture_config.get_parameter_value(PName.CENTER_FREQUENCY)
        )
        self._sample_rate = cast(
            int, self._capture_config.get_parameter_value(PName.SAMPLE_RATE)
        )
        self._time_resolution = cast(
            float,
            self._capture_config.get_parameter_value(PName.TIME_RESOLUTION) or 0.0,
        )
        self._frequency_resolution = cast(
            float,
            self._capture_config.get_parameter_value(PName.FREQUENCY_RESOLUTION) or 0.0,
        )
        self._window = get_window(WindowType(self._window_type), self._window_size)

        # Pre-allocate the buffer.
        self._buffer = get_buffer(self._window_size)

        # Defer the expensive FFTW plan creation until the first batch is being processed.
        # With this approach, we avoid a bug where filesystem events are missed because
        # the watchdog observer isn't set up in time before the receiver starts capturing data.
        self._fftw_obj = None

    def process(self, absolute_file_path: str) -> None:
        """Compute the spectrogram of IQ samples captured at a fixed center frequency, then save it to
        file in the FITS format.

        :param absolute_file_path: The absolute file path of the `.bin` file in the batch.
        """
        _LOGGER.info(f"Processing {absolute_file_path}")
        file_name = os.path.basename(absolute_file_path)
        base_file_name, _ = os.path.splitext(file_name)
        batch_start_time, tag = base_file_name.split("_")
        batch = IQStreamBatch(batch_start_time, tag)

        _LOGGER.info(f"Reading {batch.bin_file.file_path}")
        iq_data = batch.bin_file.read()

        _LOGGER.info(f"Reading {batch.hdr_file.file_path}")
        iq_metadata = batch.hdr_file.read()

        if self._fftw_obj is None:
            _LOGGER.info(f"Creating the FFTW plan")
            self._fftw_obj = get_fftw_obj(self._buffer)

        _LOGGER.info("Executing the short-time FFT")
        dynamic_spectra = stfft(
            self._fftw_obj, self._buffer, iq_data, self._window, self._window_hop
        )

        # Shift the zero-frequency component to the middle of the spectrum.
        dynamic_spectra = np.fft.fftshift(dynamic_spectra, axes=0)

        # Get the physical frequencies assigned to each spectral component, shift the zero frequency to the middle of the
        # spectrum, then translate the array up from the baseband.
        frequencies = (
            np.fft.fftshift(get_frequencies(self._window_size, self._sample_rate))
            + self._center_frequency
        )

        # Compute the physical times we'll assign to each spectrum.
        num_spectrums = get_num_spectrums(
            iq_data.size, self._window_size, self._window_hop
        )
        times = get_times(num_spectrums, self._sample_rate, self._window_hop)

        # Account for the millisecond correction.
        start_datetime = batch.start_datetime + timedelta(
            milliseconds=iq_metadata.millisecond_correction
        )

        spectrogram = Spectrogram(
            dynamic_spectra,
            times,
            frequencies,
            self._tag,
            SpectrumUnit.AMPLITUDE,
            start_datetime,
        )

        _LOGGER.info("Averaging the spectrogram")
        spectrogram = time_average(spectrogram, resolution=self._time_resolution)
        spectrogram = frequency_average(
            spectrogram, resolution=self._frequency_resolution
        )

        self._cache_spectrogram(spectrogram)

        _LOGGER.info(f"Deleting {batch.bin_file.file_path}")
        batch.bin_file.delete()

        _LOGGER.info(f"Deleting {batch.hdr_file.file_path}")
        batch.hdr_file.delete()
