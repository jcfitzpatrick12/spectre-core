# SPDX-FileCopyrightText: © 2024 Jimmy Fitzpatrick <jcfitzpatrick12@gmail.com>
# This file is part of SPECTRE
# SPDX-License-Identifier: GPL-3.0-or-later

from logging import getLogger
_LOGGER = getLogger(__name__)

import numpy as np
from typing import Tuple, cast
from datetime import timedelta

import os
import numpy.typing as npt
import numpy as np

from spectre_core.capture_configs import CaptureConfig, PName
from spectre_core.batches import IQStreamBatch
from spectre_core.spectrograms import Spectrogram, SpectrumUnit, time_average, frequency_average
from ._event_handler_keys import EventHandlerKey
from .._base import BaseEventHandler, make_sft_instance
from .._register import register_event_handler


def _do_stfft(
    iq_data: npt.NDArray[np.complex64],
    capture_config: CaptureConfig,
) -> Tuple[npt.NDArray[np.float32], npt.NDArray[np.float32], npt.NDArray[np.float32]]:
    """Do a Short-time Fast Fourier Transform on an array of complex IQ samples.
    
    The computation requires extra metadata, which is extracted from the detached header in the batch 
    and the capture config used to capture the data.
    
    The current implementation relies heavily on the `ShortTimeFFT` implementation from 
    `scipy.signal` (https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.ShortTimeFFT.html)
    which takes up a lot of the compute time.
    """

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
    frequencies = sft.f + cast(float, capture_config.get_parameter_value(PName.CENTER_FREQUENCY))

    return times.astype(np.float32), frequencies.astype(np.float32), dynamic_spectra.astype(np.float32)


def _build_spectrogram(
    batch: IQStreamBatch,
    capture_config: CaptureConfig
) -> Spectrogram:
    """Generate a spectrogram using `IQStreamBatch` IQ samples."""
    # read the data from the batch
    iq_metadata = batch.hdr_file.read()
    iq_samples  = batch.bin_file.read()

    times, frequencies, dynamic_spectra = _do_stfft(iq_samples,
                                                    capture_config)

    # compute the start datetime for the spectrogram by adding the millisecond component to the batch start time
    spectrogram_start_datetime = batch.start_datetime + timedelta(milliseconds=iq_metadata.millisecond_correction)
    
    return Spectrogram(dynamic_spectra,
                       times,
                       frequencies,
                       batch.tag,
                       SpectrumUnit.AMPLITUDE,
                       spectrogram_start_datetime)


@register_event_handler(EventHandlerKey.FIXED_CENTER_FREQUENCY)
class FixedEventHandler(BaseEventHandler):
    def process(
        self, 
        absolute_file_path: str
    ) -> None:
        """Compute a spectrogram using `IQStreamBatch` IQ samples, cache it, then save it to file in the FITS
        format. The IQ samples are assumed to have been collected at a fixed center frequency.
        
        The computed spectrogram is averaged in time and frequency as per the user-configured capture config.
        Once the spectrogram has been computed successfully, the `.bin` and `.hdr` files are removed.

        :param absolute_file_path: The absolute file path of the `.bin` file in the batch.
        """
        _LOGGER.info(f"Processing: {absolute_file_path}")
        file_name = os.path.basename(absolute_file_path)
        base_file_name, _ = os.path.splitext(file_name)
        batch_start_time, tag = base_file_name.split('_')

        batch = IQStreamBatch(batch_start_time, tag)

        _LOGGER.info("Creating spectrogram")
        spectrogram = _build_spectrogram(batch,
                                         self._capture_config)
        
        time_resolution = cast(float, self._capture_config.get_parameter_value(PName.TIME_RESOLUTION))
        spectrogram = time_average(spectrogram,
                                   resolution=time_resolution)

        frequency_resolution = cast(float, self._capture_config.get_parameter_value(PName.FREQUENCY_RESOLUTION))
        spectrogram = frequency_average(spectrogram,
                                        resolution=frequency_resolution)
        
        self._cache_spectrogram(spectrogram)

        _LOGGER.info(f"Deleting {batch.bin_file.file_path}")
        batch.bin_file.delete()

        _LOGGER.info(f"Deleting {batch.hdr_file.file_path}")
        batch.hdr_file.delete()
