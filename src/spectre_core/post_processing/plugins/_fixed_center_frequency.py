# SPDX-FileCopyrightText: © 2024 Jimmy Fitzpatrick <jcfitzpatrick12@gmail.com>
# This file is part of SPECTRE
# SPDX-License-Identifier: GPL-3.0-or-later

from logging import getLogger
_LOGGER = getLogger(__name__)

import numpy as np
from typing import Tuple
from datetime import timedelta

import os

from spectre_core.capture_configs import CaptureConfig, PName, CaptureMode
from spectre_core.batches import SPECTREBatch
from spectre_core.spectrograms import Spectrogram, time_average, frequency_average
from .._base import BaseEventHandler, make_sft_instance
from .._register import register_event_handler


def _do_stfft(iq_data: np.array,
              capture_config: CaptureConfig,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """For reference: https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.ShortTimeFFT.html"""

    sft = make_sft_instance(capture_config)

    # set p0=0, since by convention in the STFFT docs, p=0 corresponds to the slice centred at t=0
    p0=0

    # set p1 to the index of the first slice where the "midpoint" of the window is still inside the signal
    num_samples = len(iq_data)
    p1 = sft.upper_border_begin(num_samples)[1]
    
    # compute a ShortTimeFFT on the IQ samples
    complex_spectra = sft.stft(iq_data, 
                               p0 = p0, 
                               p1 = p1) 
    
    # compute the magnitude of each spectral component
    dynamic_spectra = np.abs(complex_spectra)


    # assign a physical time to each spectrum
    # p0 is defined to correspond with the first sample, at t=0 [s]
    times = sft.t(num_samples, 
                  p0 = p0, 
                  p1 = p1)
    # assign physical frequencies to each spectral component
    frequencies = sft.f + capture_config.get_parameter_value(PName.CENTER_FREQUENCY) 

    return times, frequencies, dynamic_spectra


def _build_spectrogram(batch: SPECTREBatch,
                       capture_config: CaptureConfig) -> Spectrogram:
    """Create a spectrogram by performing a Short Time FFT on the IQ samples for this batch."""

    # read the data from the batch
    iq_metadata = batch.hdr_file.read()
    iq_samples  = batch.bin_file.read()

    times, frequencies, dynamic_spectra = _do_stfft(iq_samples,
                                                    capture_config)

    # explicitly type cast data arrays to 32-bit floats
    times = np.array(times, dtype = 'float32')
    frequencies = np.array(frequencies, dtype = 'float32')
    dynamic_spectra = np.array(dynamic_spectra, dtype = 'float32')

    # compute the start datetime for the spectrogram by adding the millisecond component to the batch start time
    spectrogram_start_datetime = batch.start_datetime + timedelta(milliseconds=iq_metadata.millisecond_correction)
    return Spectrogram(dynamic_spectra,
                       times,
                       frequencies,
                       batch.tag,
                       spectrogram_start_datetime,
                       spectrum_type = "amplitude")


@register_event_handler(CaptureMode.FIXED_CENTER_FREQUENCY)
class FixedEventHandler(BaseEventHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def process(self, 
                absolute_file_path: str):
        _LOGGER.info(f"Processing: {absolute_file_path}")
        file_name = os.path.basename(absolute_file_path)
        base_file_name, _ = os.path.splitext(file_name)
        batch_start_time, tag = base_file_name.split('_')

        batch = SPECTREBatch(batch_start_time, tag)

        _LOGGER.info("Creating spectrogram")
        spectrogram = _build_spectrogram(batch,
                                        self._capture_config)

        spectrogram = time_average(spectrogram,
                                   resolution = self._capture_config.get_parameter_value(PName.TIME_RESOLUTION))

        spectrogram = frequency_average(spectrogram,
                                        resolution = self._capture_config.get_parameter_value(PName.FREQUENCY_RESOLUTION))
        
        self._cache_spectrogram(spectrogram)

        bin_file = batch.get_file('bin')
        _LOGGER.info(f"Deleting {bin_file.file_path}")
        bin_file.delete()

        hdr_file = batch.get_file('hdr')
        _LOGGER.info(f"Deleting {hdr_file.file_path}")
        hdr_file.delete()
