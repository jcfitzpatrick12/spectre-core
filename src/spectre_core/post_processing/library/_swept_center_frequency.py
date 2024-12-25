# SPDX-FileCopyrightText: © 2024 Jimmy Fitzpatrick <jcfitzpatrick12@gmail.com>
# This file is part of SPECTRE
# SPDX-License-Identifier: GPL-3.0-or-later

from logging import getLogger
_LOGGER = getLogger(__name__)

import os
from typing import Optional
from typing import Tuple
from datetime import timedelta, datetime
import numpy as np

from scipy.signal import ShortTimeFFT

from spectre_core.spectrograms import Spectrogram, time_average, frequency_average
from spectre_core.config import TimeFormats
from spectre_core.capture_configs import CaptureConfig, PNames, CaptureModes
from spectre_core.chunks import BaseChunk
from spectre_core.chunks import SweepMetadata
from spectre_core.exceptions import InvalidSweepMetadataError
from .._base import BaseEventHandler, make_sft_instance
from .._register import register_event_handler


def _stitch_steps(stepped_dynamic_spectra: np.ndarray,
                  num_full_sweeps: int) -> np.ndarray:
    """For each full sweep, create a swept spectrum by stitching together the spectrum at each of the steps."""
    return stepped_dynamic_spectra.reshape((num_full_sweeps, -1)).T

    
def _average_over_steps(stepped_dynamic_spectra: np.ndarray) -> None:
    """Average the spectrums in each step totally in time."""
    return np.nanmean(stepped_dynamic_spectra[..., 1:], axis=-1)


def _fill_times(times: np.ndarray,
                num_samples: np.ndarray,
                sample_rate: int,
                num_full_sweeps: int,
                num_steps_per_sweep: int) -> None:
        """Assign physical times to each swept spectrum. We use (by convention) the time of the first sample in eahc sweep"""

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


def _fill_frequencies(frequencies: np.ndarray,
                      center_frequencies: np.ndarray,
                      baseband_frequencies: np.ndarray,
                      window_size: int) -> None:
    """Assign physical frequencies to each of the swept spectral components."""
    for i, center_frequency in enumerate(np.unique(center_frequencies)):
        lower_bound = i * window_size
        upper_bound = (i + 1) * window_size
        frequencies[lower_bound:upper_bound] = (baseband_frequencies + center_frequency)


def _fill_stepped_dynamic_spectra(stepped_dynamic_spectra: np.ndarray,
                                  sft: ShortTimeFFT,
                                  iq_data: np.ndarray,
                                  num_samples: np.ndarray,
                                  num_full_sweeps: int,
                                  num_steps_per_sweep: int) -> None:
    """Compute the dynamic spectra for the input IQ samples for each step.
    
    All IQ samples per step were collected at the same center frequency.
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
        

def _compute_num_max_slices_in_step(sft: ShortTimeFFT,
                                    num_samples: np.ndarray) -> int:
    """Compute the maximum number of slices over all steps, in all sweeps over the chunk."""
    return sft.upper_border_begin(np.max(num_samples))[1]


def _compute_num_full_sweeps(center_frequencies: np.ndarray) -> int:
    """Compute the total number of full sweeps over the chunk.

    Since the number of each samples in each step is variable, we only know a sweep is complete
    when there is a sweep after it. So we can define the total number of *full* sweeps as the number of 
    (freq_max, freq_min) pairs in center_frequencies. It is only at an instance of (freq_max, freq_min) pair 
    in center frequencies that the frequency decreases, so, we can compute the number of full sweeps by 
    counting the numbers of negative values in np.diff(center_frequencies)
    """
    return len(np.where(np.diff(center_frequencies) < 0)[0])


def _compute_num_steps_per_sweep(center_frequencies: np.ndarray) -> int:
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


def _validate_center_frequencies_ordering(center_frequencies: np.ndarray,
                                          freq_step: float) -> None:
    """Check that the center frequencies are well-ordered in the detached header"""
    min_frequency = np.min(center_frequencies)
    # Extract the expected difference between each step within a sweep. 
    for i, diff in enumerate(np.diff(center_frequencies)):
        # steps should either increase by freq_step or drop to the minimum
        if (diff != freq_step) and (center_frequencies[i + 1] != min_frequency):
            raise InvalidSweepMetadataError(f"Unordered center frequencies detected")


def _do_stfft(iq_data: np.ndarray,
              sweep_metadata: SweepMetadata,
              capture_config: CaptureConfig):
    """Perform a Short Time FFT on the input swept IQ samples."""

    sft = make_sft_instance(capture_config)

    frequency_step = capture_config.get_parameter_value(PNames.FREQUENCY_STEP)
    _validate_center_frequencies_ordering(sweep_metadata.center_frequencies,
                                          frequency_step)

    window_size = capture_config.get_parameter_value(PNames.WINDOW_SIZE)

    num_steps_per_sweep = _compute_num_steps_per_sweep(sweep_metadata.center_frequencies)
    num_full_sweeps = _compute_num_full_sweeps(sweep_metadata.center_frequencies)
    num_max_slices_in_step = _compute_num_max_slices_in_step(sft,
                                                             sweep_metadata.num_samples)
    
    stepped_dynamic_spectra_shape = (num_full_sweeps, 
                                     num_steps_per_sweep, 
                                     window_size, 
                                     num_max_slices_in_step)
    stepped_dynamic_spectra = np.full(stepped_dynamic_spectra_shape, np.nan)

    frequencies = np.empty(num_steps_per_sweep * window_size)
    times = np.empty(num_full_sweeps)

    _fill_stepped_dynamic_spectra(stepped_dynamic_spectra,
                                  sft,
                                  iq_data,
                                  sweep_metadata.num_samples,
                                  num_full_sweeps,
                                  num_steps_per_sweep)
    
    _fill_frequencies(frequencies,
                      sweep_metadata.center_frequencies,
                      sft.f,
                      window_size)
    
    sample_rate = capture_config.get_parameter_value(PNames.SAMPLE_RATE)
    _fill_times(times,
                sweep_metadata.num_samples,
                sample_rate,
                num_full_sweeps,
                num_steps_per_sweep)

    averaged_spectra = _average_over_steps(stepped_dynamic_spectra)
    dynamic_spectra = _stitch_steps(averaged_spectra,
                                    num_full_sweeps)

    return times, frequencies, dynamic_spectra


def _correct_timing(chunk_start_datetime: datetime,
                    millisecond_correction: int,
                    num_samples_prepended: int,
                    sample_rate: int):
    """Correct the start time for this chunk based on the number of samples we prepended reconstructing the initial sweep."""
    sample_interval = (1 / sample_rate)
    elapsed_time = num_samples_prepended * sample_interval
    corrected_datetime = chunk_start_datetime + timedelta(milliseconds = millisecond_correction) - timedelta(seconds = float(elapsed_time))
    return corrected_datetime.strftime(TimeFormats.DATETIME), corrected_datetime.microsecond * 1e-3


def _prepend_num_samples(carryover_num_samples: np.ndarray,
                         num_samples: np.ndarray,
                         final_step_spans_two_chunks: bool) -> np.ndarray:
    """Prepend the number of samples from the final sweep of the previous chunk."""
    if final_step_spans_two_chunks:
        # ensure the number of samples from the final step in the previous chunk are accounted for
        num_samples[0] += carryover_num_samples[-1]
        # and truncate as required
        carryover_num_samples = carryover_num_samples[:-1]
    return np.concatenate((carryover_num_samples, num_samples))


def _prepend_center_frequencies(carryover_center_frequencies: np.ndarray,
                                center_frequencies: np.ndarray,
                                final_step_spans_two_chunks: bool)-> np.ndarray:
    """Prepend the center frequencies from the final sweep of the previous chunk."""
    # in the case that the sweep has bled across chunks,
    # do not permit identical neighbours in the center frequency array
    if final_step_spans_two_chunks:
        # truncate the final frequency to prepend (as it already exists in the array we are appending to in this case)
        carryover_center_frequencies = carryover_center_frequencies[:-1]
    return np.concatenate((carryover_center_frequencies, center_frequencies))


def _prepend_iq_data(carryover_iq_data: np.ndarray,
                     iq_data: np.ndarray) -> np.ndarray:
    """Prepend the IQ samples from the final sweep of the previous chunk."""
    return np.concatenate((carryover_iq_data, iq_data))


def _get_final_sweep(previous_chunk: BaseChunk
) -> Tuple[np.ndarray, SweepMetadata]:
    """Get data from the final sweep of the previous chunk."""
    # unpack the data from the previous chunk
    previous_iq_data = previous_chunk.read_file("bin")
    _, previous_sweep_metadata = previous_chunk.read_file("hdr")
    # find the step index from the last sweep
    # [0] since the return of np.where is a 1 element Tuple, 
    # containing a list of step indices corresponding to the smallest center frequencies
    # [-1] since we want the final step index, where the center frequency is minimised
    final_sweep_start_step_index = np.where(previous_sweep_metadata.center_frequencies == np.min(previous_sweep_metadata.center_frequencies))[0][-1]
    # isolate the data from the final sweep
    final_center_frequencies = previous_sweep_metadata.center_frequencies[final_sweep_start_step_index:]
    final_num_samples = previous_sweep_metadata.num_samples[final_sweep_start_step_index:]
    final_sweep_iq_data = previous_iq_data[-np.sum(final_num_samples):]

    # sanity check on the number of samples in the final sweep
    if len(final_sweep_iq_data) != np.sum(final_num_samples):
        raise ValueError((f"Unexpected error! Mismatch in sample count for the final sweep data."
                            f"Expected {np.sum(final_num_samples)} based on sweep metadata, but found "
                            f" {len(final_sweep_iq_data)} IQ samples in the final sweep"))
    
    return final_sweep_iq_data, SweepMetadata(final_center_frequencies, final_num_samples)


def _reconstruct_initial_sweep(previous_chunk: BaseChunk,
                               iq_data: np.ndarray,
                               sweep_metadata: SweepMetadata) -> Tuple[np.ndarray, SweepMetadata, int]:
    """Reconstruct the initial sweep of the current chunk, using data from the previous chunk."""

    # carryover the final sweep of the previous chunk, and prepend that data to the current chunk data
    carryover_iq_data, carryover_sweep_metadata = _get_final_sweep(previous_chunk)

    # prepend the iq data that was carried over from the previous chunk
    iq_data = _prepend_iq_data(carryover_iq_data,
                               iq_data)
    
    # prepend the sweep metadata from the previous chunk
    final_step_spans_two_chunks = carryover_sweep_metadata.center_frequencies[-1] == sweep_metadata.center_frequencies[0]
    center_frequencies = _prepend_center_frequencies(carryover_sweep_metadata.center_frequencies,
                                                     sweep_metadata.center_frequencies,
                                                     final_step_spans_two_chunks)
    num_samples = _prepend_num_samples(carryover_sweep_metadata.num_samples,
                                       sweep_metadata.num_samples,
                                       final_step_spans_two_chunks)
    
    # keep track of how many samples we prepended (required to adjust timing later)
    num_samples_prepended = np.sum(carryover_sweep_metadata.num_samples)
    return iq_data, SweepMetadata(center_frequencies, num_samples), num_samples_prepended


def _build_spectrogram(chunk: BaseChunk,
                       capture_config: CaptureConfig,
                       previous_chunk: Optional[BaseChunk] = None) -> Spectrogram:
    """Create a spectrogram by performing a Short Time FFT on the (swept) IQ samples for this chunk."""
    iq_data = chunk.read_file("bin")
    millisecond_correction, sweep_metadata = chunk.read_file("hdr")

    # if a previous chunk has been specified, this indicates that the initial sweep spans
    # between two adjacent batched files. 
    if previous_chunk:
        # If this is the case, first reconstruct the initial sweep of the current chunk
        # by prepending the final sweep of the previous chunk
        iq_data, sweep_metadata, num_samples_prepended = _reconstruct_initial_sweep(previous_chunk,
                                                                                    iq_data,
                                                                                    sweep_metadata)
        # since we have prepended extra samples, we need to correct the chunk start time
        # appropriately
        chunk_start_time, millisecond_correction = _correct_timing(chunk.chunk_start_datetime,
                                                                   millisecond_correction,
                                                                   num_samples_prepended,
                                                                   capture_config.get_parameter_value(PNames.SAMPLE_RATE))
    # otherwise, no action is required
    else:
        chunk_start_time = chunk.chunk_start_time

    microsecond_correction = millisecond_correction * 1e3

    times, frequencies, dynamic_spectra = _do_stfft(iq_data, 
                                                    sweep_metadata,
                                                    capture_config)
    
    return Spectrogram(dynamic_spectra,
                       times,
                       frequencies,
                       chunk.tag,
                       chunk_start_time,
                       microsecond_correction,
                       spectrum_type = "amplitude")


@register_event_handler(CaptureModes.SWEPT_CENTER_FREQUENCY)
class _EventHandler(BaseEventHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # the previous chunk is stored in order to fetch the
        # data from the "final sweep" which was ignored during
        # processing.
        self._previous_chunk: BaseChunk = None 
        

    def process(self, 
                absolute_file_path: str):
        _LOGGER.info(f"Processing: {absolute_file_path}")
        file_name = os.path.basename(absolute_file_path)
        # discard the extension
        base_file_name, _ = os.path.splitext(file_name)
        chunk_start_time, tag = base_file_name.split('_')
        chunk = self._Chunk(chunk_start_time, tag)

        # ensure that the file which has been created has the expected tag
        if tag != self._tag:
            raise RuntimeError(f"Received an unexpected tag! Expected '{self._tag}', "
                               f"but a file has been created with tag '{tag}'")

        _LOGGER.info("Creating spectrogram")
        spectrogram = _build_spectrogram(chunk,
                                        self._capture_config,
                                        previous_chunk = self._previous_chunk)

        spectrogram = time_average(spectrogram,
                                   resolution = self._capture_config.get_parameter_value(PNames.TIME_RESOLUTION))

        spectrogram = frequency_average(spectrogram,
                                        resolution = self._capture_config.get_parameter_value(PNames.FREQUENCY_RESOLUTION))

        self._cache_spectrogram(spectrogram)

        # if the previous chunk has not yet been set, it means we are processing the first chunk
        # so we don't need to handle the previous chunk
        if self._previous_chunk is None:
            # instead, only set it for the next time this method is called
            self._previous_chunk = chunk
            
        # otherwise the previous chunk is defined (and by this point has already been processed)
        else:
            bin_chunk = self._previous_chunk.get_file('bin')
            _LOGGER.info(f"Deleting {bin_chunk.file_path}")
            bin_chunk.delete()

            hdr_chunk = self._previous_chunk.get_file('hdr')
            _LOGGER.info(f"Deleting {hdr_chunk.file_path}")
            hdr_chunk.delete()

            # and reassign the current chunk to be used as the previous chunk at the next call of this method
            self._previous_chunk = chunk
