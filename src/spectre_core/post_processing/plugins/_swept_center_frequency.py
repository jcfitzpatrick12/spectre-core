# SPDX-FileCopyrightText: © 2024 Jimmy Fitzpatrick <jcfitzpatrick12@gmail.com>
# This file is part of SPECTRE
# SPDX-License-Identifier: GPL-3.0-or-later

from logging import getLogger
_LOGGER = getLogger(__name__)

import os
from typing import Optional, Tuple, cast
from datetime import timedelta
import numpy as np
import numpy.typing as npt

from scipy.signal import ShortTimeFFT

from spectre_core.spectrograms import Spectrogram, SpectrumUnit, time_average, frequency_average
from spectre_core.capture_configs import CaptureConfig, PName
from spectre_core.batches import IQStreamBatch
from spectre_core.exceptions import InvalidSweepMetadataError
from ._event_handler_keys import EventHandlerKey
from .._base import BaseEventHandler, make_sft_instance
from .._register import register_event_handler


def _stitch_steps(
    stepped_dynamic_spectra: npt.NDArray[np.float32],
    num_full_sweeps: int
) -> npt.NDArray[np.float32]:
    """For each full sweep, create a single spectrum by stitching together the spectrum at each step."""
    return stepped_dynamic_spectra.reshape((num_full_sweeps, -1)).T

    
def _average_over_steps(
    stepped_dynamic_spectra: npt.NDArray[np.float32]
) -> npt.NDArray[np.float32]:
    """Average the spectrums in each step totally in time."""
    return np.nanmean(stepped_dynamic_spectra[..., 1:], axis=-1)


def _fill_times(
    times: npt.NDArray[np.float32],
    num_samples: npt.NDArray[np.int32],
    sample_rate: int,
    num_full_sweeps: int,
    num_steps_per_sweep: int
) -> None:
        """Assign physical times to each swept spectrum. We use (by convention) the time of the first sample in each sweep"""
        sampling_interval = 1 / sample_rate
        cumulative_samples = 0
        for sweep_index in range(num_full_sweeps):
            # assign a physical time to the spectrum for this sweep
            times[sweep_index] = cumulative_samples * sampling_interval

            # find the total number of samples across the sweep
            start_step = sweep_index * num_steps_per_sweep
            end_step = (sweep_index + 1) * num_steps_per_sweep

            # update cumulative samples
            cumulative_samples += np.sum(num_samples[start_step:end_step])


def _fill_frequencies(
    frequencies: npt.NDArray[np.float32],
    center_frequencies: npt.NDArray[np.float32],
    baseband_frequencies: npt.NDArray[np.float32],
    window_size: int
) -> None:
    """Assign physical frequencies to each of the spectral components in the stitched spectrum."""
    for i, center_frequency in enumerate(np.unique(center_frequencies)):
        lower_bound = i * window_size
        upper_bound = (i + 1) * window_size
        frequencies[lower_bound:upper_bound] = (baseband_frequencies + center_frequency)


def _fill_stepped_dynamic_spectra(
    stepped_dynamic_spectra: npt.NDArray[np.float32],
    sft: ShortTimeFFT,
    iq_data: npt.NDArray[np.complex64],
    num_samples: npt.NDArray[np.int32],
    num_full_sweeps: int,
    num_steps_per_sweep: int
) -> None:
    """For each full sweep, compute the dynamic spectra by performing a Short-time Fast Fourier Transform
    on the IQ samples within each step.
    """
    # global_step_index will hold the step index over all sweeps (doesn't reset each sweep)
    # start_sample_index will hold the index of the first sample in the step
    global_step_index, start_sample_index = 0, 0
    for sweep_index in range(num_full_sweeps):
        for step_index in range(num_steps_per_sweep):
            # extract how many samples are in the current step from the metadata
            end_sample_index = start_sample_index + num_samples[global_step_index]
            # compute the number of slices in the current step based on the window we defined on the capture config
            num_slices = sft.upper_border_begin(num_samples[global_step_index])[1]
            # perform a short time fast fourier transform on the step
            complex_spectra = sft.stft(iq_data[start_sample_index:end_sample_index], 
                                       p0=0, 
                                       p1=num_slices)
            # and pack the absolute values into the stepped spectrogram where the step slot is padded to the maximum size for ease of processing later)
            stepped_dynamic_spectra[sweep_index, step_index, :, :num_slices] = np.abs(complex_spectra)
            # reassign the start_sample_index for the next step
            start_sample_index = end_sample_index
            # and increment the global step index
            global_step_index += 1
        

def _compute_num_max_slices_in_step(
    sft: ShortTimeFFT,
    num_samples: npt.NDArray[np.int32]
) -> int:
    """Compute the maximum number of slices over all steps (and all sweeps) in the batch."""
    return sft.upper_border_begin(np.max(num_samples))[1]


def _compute_num_full_sweeps(
    center_frequencies: npt.NDArray[np.float32]
) -> int:
    """Compute the total number of full sweeps in the batch.

    Since the number of each samples in each step is variable, we only know a sweep is complete
    when there is a sweep after it. So we can define the total number of *full* sweeps as the number of 
    (freq_max, freq_min) pairs in center_frequencies. It is only at an instance of (freq_max, freq_min) pair 
    in center frequencies that the frequency decreases, so, we can compute the number of full sweeps by 
    counting the numbers of negative values in np.diff(center_frequencies).
    """
    return len(np.where(np.diff(center_frequencies) < 0)[0])


def _compute_num_steps_per_sweep(
    center_frequencies: npt.NDArray[np.float32]
) -> int:
    """Compute the (ensured constant) number of steps in each sweep."""
    # find the (step) indices corresponding to the minimum frequencies
    min_freq_indices = np.where(center_frequencies == np.min(center_frequencies))[0]
    # then, we evaluate the number of steps that has occured between them via np.diff over the indices
    unique_num_steps_per_sweep = np.unique(np.diff(min_freq_indices))
    # we expect that the difference is always the same, so that the result of np.unique has a single element
    if len(unique_num_steps_per_sweep) != 1:
        raise InvalidSweepMetadataError(("Irregular step count per sweep, "
                                         "expected a consistent number of steps per sweep"))
    return int(unique_num_steps_per_sweep[0])


def _validate_center_frequencies_ordering(
    center_frequencies: npt.NDArray[np.float32],
    freq_step: float
) -> None:
    """Check that the center frequencies are well-ordered in the detached header."""
    min_frequency = np.min(center_frequencies)
    # Extract the expected difference between each step within a sweep. 
    for i, diff in enumerate(np.diff(center_frequencies)):
        # steps should either increase by freq_step or drop to the minimum
        if (diff != freq_step) and (center_frequencies[i + 1] != min_frequency):
            raise InvalidSweepMetadataError(f"Unordered center frequencies detected")


def _do_stfft(
    iq_data: npt.NDArray[np.complex64],
    center_frequencies: npt.NDArray[np.float32],
    num_samples: npt.NDArray[np.int32],
    capture_config: CaptureConfig
) -> Tuple[npt.NDArray[np.float32], npt.NDArray[np.float32], npt.NDArray[np.float32]]:
    """Do a Short-time Fast Fourier Transform on an array of complex IQ samples.
    
    The computation requires extra metadata, which is extracted from the detached header in the batch 
    and the capture config used to capture the data. 
    
    The current implementation relies heavily on the `ShortTimeFFT` implementation from 
    `scipy.signal` (https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.ShortTimeFFT.html)
    which takes up a lot of the compute time.
    """

    sft = make_sft_instance(capture_config)

    frequency_step = cast(float, capture_config.get_parameter_value(PName.FREQUENCY_STEP))
    _validate_center_frequencies_ordering(center_frequencies,
                                          frequency_step)

    num_steps_per_sweep    = _compute_num_steps_per_sweep(center_frequencies)
    num_full_sweeps        = _compute_num_full_sweeps(center_frequencies)
    num_max_slices_in_step = _compute_num_max_slices_in_step(sft,
                                                             num_samples)
    
    window_size = cast(int, capture_config.get_parameter_value(PName.WINDOW_SIZE))
    stepped_dynamic_spectra_shape = (num_full_sweeps, 
                                     num_steps_per_sweep, 
                                     window_size, 
                                     num_max_slices_in_step)
    
    # pad with nan values up to the max number of slices to make computations simpler.
    # nans are required, so that they are easily ignored, e.g. in averaging operations.
    stepped_dynamic_spectra = np.full(stepped_dynamic_spectra_shape, np.nan, dtype=np.float32)
    frequencies             = np.empty(num_steps_per_sweep * window_size, dtype=np.float32)
    times                   = np.empty(num_full_sweeps, dtype=np.float32)

    _fill_stepped_dynamic_spectra(stepped_dynamic_spectra,
                                  sft,
                                  iq_data,
                                  num_samples,
                                  num_full_sweeps,
                                  num_steps_per_sweep)
    
    _fill_frequencies(frequencies,
                      center_frequencies,
                      sft.f,
                      window_size)
    
    sample_rate = cast(int, capture_config.get_parameter_value(PName.SAMPLE_RATE))
    _fill_times(times,
                num_samples,
                sample_rate,
                num_full_sweeps,
                num_steps_per_sweep)

    averaged_spectra = _average_over_steps(stepped_dynamic_spectra)
    dynamic_spectra = _stitch_steps(averaged_spectra,
                                    num_full_sweeps)

    return times, frequencies, dynamic_spectra


def _prepend_num_samples(
    carryover_num_samples: npt.NDArray[np.int32],
    num_samples: npt.NDArray[np.int32],
    final_step_spans_two_batches: bool
) -> npt.NDArray[np.int32]:
    """Prepend the number of samples from the final sweep of the previous batch, to the first
    sweep of the current batch."""
    if final_step_spans_two_batches:
        # ensure the number of samples from the final step in the previous batch are accounted for
        num_samples[0] += carryover_num_samples[-1]
        # and truncate as required
        carryover_num_samples = carryover_num_samples[:-1]
    return np.concatenate((carryover_num_samples, num_samples))


def _prepend_center_frequencies(
    carryover_center_frequencies: npt.NDArray[np.float32],
    center_frequencies: npt.NDArray[np.float32],
    final_step_spans_two_batches: bool
)-> npt.NDArray[np.float32]:
    """Prepend the center frequencies from the final sweep of the previous batch, to the first
    sweep of the current batch."""
    # in the case that the sweep has bled across batches,
    # do not permit identical neighbours in the center frequency array
    if final_step_spans_two_batches:
        # truncate the final frequency to prepend (as it already exists in the array we are appending to in this case)
        carryover_center_frequencies = carryover_center_frequencies[:-1]
    return np.concatenate((carryover_center_frequencies, center_frequencies))


def _prepend_iq_data(
    carryover_iq_data: npt.NDArray[np.complex64],
    iq_data: npt.NDArray[np.complex64]
) -> npt.NDArray[np.complex64]:
    """Prepend the IQ samples from the final sweep of the previous batch, to the first sweep
    of the current batch."""
    return np.concatenate((carryover_iq_data, iq_data))


def _get_final_sweep(
    previous_batch: IQStreamBatch
) -> Tuple[npt.NDArray[np.complex64], npt.NDArray[np.float32], npt.NDArray[np.int32]]:
    """Get IQ samples and metadata from the final sweep of the previous batch."""
    
    # unpack the data from the previous batch (using the cached values!)
    previous_iq_data     = previous_batch.bin_file.read()
    previous_iq_metadata = previous_batch.hdr_file.read()
    
    if previous_iq_metadata.center_frequencies is None or previous_iq_metadata.num_samples is None:
        raise ValueError(f"Expected non-empty IQ metadata!")
    
    # find the step index from the last sweep
    # [0] since the return of np.where is a 1 element Tuple, 
    # containing a list of step indices corresponding to the smallest center frequencies
    # [-1] since we want the final step index, where the center frequency is minimised
    final_sweep_start_step_index = np.where(previous_iq_metadata.center_frequencies == np.min(previous_iq_metadata.center_frequencies))[0][-1]
    # isolate the data from the final sweep
    final_center_frequencies = previous_iq_metadata.center_frequencies[final_sweep_start_step_index:]
    final_num_samples = previous_iq_metadata.num_samples[final_sweep_start_step_index:]
    final_sweep_iq_data = previous_iq_data[-np.sum(final_num_samples):]

    # sanity check on the number of samples in the final sweep
    if len(final_sweep_iq_data) != np.sum(final_num_samples):
        raise ValueError((f"Unexpected error! Mismatch in sample count for the final sweep data."
                          f"Expected {np.sum(final_num_samples)} based on sweep metadata, but found "
                          f" {len(final_sweep_iq_data)} IQ samples in the final sweep"))
    
    return final_sweep_iq_data, final_center_frequencies, final_num_samples


def _reconstruct_initial_sweep(
    previous_batch: IQStreamBatch,
    batch: IQStreamBatch
) -> Tuple[npt.NDArray[np.complex64], npt.NDArray[np.float32], npt.NDArray[np.int32], int]:
    """Reconstruct the initial sweep of the current batch, using data from the previous batch.
    
    Specifically, we extract the data from the final sweep of the previous batch and prepend
    it to the first sweep of the current batch. Additionally, we return how many IQ samples
    we prepended, which will allow us to correct the spectrogram start time of the current batch.
    """
    
    iq_data     = batch.bin_file.read()
    iq_metadata = batch.hdr_file.read()
    
    if iq_metadata.center_frequencies is None or iq_metadata.num_samples is None:
        raise ValueError(f"Expected non-empty IQ metadata!")
    
    # carryover the final sweep of the previous batch, and prepend that data to the current batch data
    carryover_iq_data, carryover_center_frequencies, carryover_num_samples = _get_final_sweep(previous_batch)

    # prepend the iq data that was carried over from the previous batch
    iq_data = _prepend_iq_data(carryover_iq_data,
                               iq_data)
    
    # prepend the sweep metadata from the previous batch
    final_step_spans_two_batches = carryover_center_frequencies[-1] == iq_metadata.center_frequencies[0]
    center_frequencies = _prepend_center_frequencies(carryover_center_frequencies,
                                                     iq_metadata.center_frequencies,
                                                     final_step_spans_two_batches)
    num_samples = _prepend_num_samples(carryover_num_samples,
                                       iq_metadata.num_samples,
                                       final_step_spans_two_batches)
    
    # keep track of how many samples we prepended (required to adjust timing later)
    num_samples_prepended = int(np.sum(carryover_num_samples))
    return (iq_data, center_frequencies, num_samples, num_samples_prepended)


def _build_spectrogram(
    batch: IQStreamBatch,
    capture_config: CaptureConfig,
    previous_batch: Optional[IQStreamBatch] = None
) -> Spectrogram:
    """Generate a spectrogram using `IQStreamBatch` IQ samples."""
    # read the batch files.
    iq_data     = batch.bin_file.read()
    iq_metadata = batch.hdr_file.read()
    
    # extract the center frequencies and num samples
    center_frequencies, num_samples = iq_metadata.center_frequencies, iq_metadata.num_samples
    
    if center_frequencies is None or num_samples is None:
        raise ValueError(f"An unexpected error has occured, expected frequency tag metadata "
                         f"in the detached header.")
    
    # correct the batch start datetime with the millisecond correction stored in the detached header
    spectrogram_start_datetime = batch.start_datetime + timedelta(milliseconds=iq_metadata.millisecond_correction)

    # if a previous batch has been specified, this indicates that the initial sweep spans between two adjacent batched files. 
    if previous_batch:
        # If this is the case, first reconstruct the initial sweep of the current batch
        # by prepending the final sweep of the previous batch
        iq_data, center_frequencies, num_samples, num_samples_prepended = _reconstruct_initial_sweep(previous_batch,
                                                                                                     batch)
        
        # since we have prepended extra samples, we need to correct the spectrogram start time appropriately
        sample_rate = cast(int, capture_config.get_parameter_value(PName.SAMPLE_RATE))
        elapsed_time = num_samples_prepended * (1 / sample_rate)
        spectrogram_start_datetime -= timedelta(seconds = float(elapsed_time))
    


    times, frequencies, dynamic_spectra = _do_stfft(iq_data, 
                                                    center_frequencies,
                                                    num_samples,
                                                    capture_config)
    
    return Spectrogram(dynamic_spectra,
                       times,
                       frequencies,
                       batch.tag,
                       SpectrumUnit.AMPLITUDE,
                       spectrogram_start_datetime)


@register_event_handler(EventHandlerKey.SWEPT_CENTER_FREQUENCY)
class SweptEventHandler(BaseEventHandler):
    def __init__(
        self, 
        *args, 
        **kwargs
    ) -> None:
        super().__init__(*args, **kwargs)
        self._previous_batch: Optional[IQStreamBatch] = None 
        
        
    def process(
        self, 
        absolute_file_path: str
    ) -> None:
        """
        Compute a spectrogram using IQ samples from an `IQStreamBatch`, cache the results, and save them in the
        FITS format. The IQ samples are assumed to be collected at a center frequency periodically swept in
        fixed increments. Neighbouring IQ samples collected at the same frequency constitute a "step." Neighbouring 
        steps collected at incrementally increasing center frequencies form a "sweep." A new sweep begins when the 
        center frequency resets to its minimum value.

        The computed spectrogram is averaged in time and frequency based on user-configured settings in the capture 
        config. The batch is cached after computation for use in subsequent processing steps.

        :param absolute_file_path: The absolute path to the `.bin` file containing the IQ sample batch.
        """
        _LOGGER.info(f"Processing: {absolute_file_path}")
        file_name = os.path.basename(absolute_file_path)
        # discard the extension
        base_file_name, _ = os.path.splitext(file_name)
        batch_start_time, tag = base_file_name.split('_')
        batch = IQStreamBatch(batch_start_time, tag)

        _LOGGER.info("Creating spectrogram")
        spectrogram = _build_spectrogram(batch,
                                         self._capture_config,
                                         previous_batch = self._previous_batch)

        spectrogram = time_average(spectrogram,
                                   resolution = self._capture_config.get_parameter_value(PName.TIME_RESOLUTION))

        spectrogram = frequency_average(spectrogram,
                                        resolution = self._capture_config.get_parameter_value(PName.FREQUENCY_RESOLUTION))

        self._cache_spectrogram(spectrogram)

        # if the previous batch has not yet been set, it means we are processing the first batch
        # so we don't need to handle the previous batch
        if self._previous_batch is None:
            # instead, only set it for the next time this method is called
            self._previous_batch = batch
            
        # otherwise the previous batch is defined (and by this point has already been processed)
        else:
            _LOGGER.info(f"Deleting {self._previous_batch.bin_file.file_path}")
            self._previous_batch.bin_file.delete()

            _LOGGER.info(f"Deleting {self._previous_batch.hdr_file.file_path}")
            self._previous_batch.hdr_file.delete()

            # and reassign the current batch to be used as the previous batch at the next call of this method
            self._previous_batch = batch
