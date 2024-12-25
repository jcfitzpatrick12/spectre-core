# SPDX-FileCopyrightText: © 2024 Jimmy Fitzpatrick <jcfitzpatrick12@gmail.com>
# This file is part of SPECTRE
# SPDX-License-Identifier: GPL-3.0-or-later

import numpy as np
from datetime import datetime, timedelta
from typing import Optional
from math import floor

from spectre_core.config import TimeFormats
from ._array_operations import find_closest_index, average_array
from ._spectrogram import Spectrogram

__all__ = [
    "frequency_chop",
    "time_chop",
    "frequency_average",
    "time_average",
    "join_spectrograms"
]

def frequency_chop(input_spectrogram: Spectrogram, 
                   start_frequency: float | int, 
                   end_frequency: float | int) -> Optional[Spectrogram]:
    
    is_entirely_below_frequency_range = (start_frequency < input_spectrogram.frequencies[0] and end_frequency < input_spectrogram.frequencies[0])
    is_entirely_above_frequency_range = (start_frequency > input_spectrogram.frequencies[-1] and end_frequency > input_spectrogram.frequencies[-1])
    # if the requested frequency range is out of bounds for the spectrogram return None
    if is_entirely_below_frequency_range or is_entirely_above_frequency_range:
        return None
    
    #find the index of the nearest matching frequency bins in the spectrogram
    start_index = find_closest_index(start_frequency, input_spectrogram.frequencies)
    end_index = find_closest_index(end_frequency, input_spectrogram.frequencies)
    
    # enforce distinct start and end indices
    if start_index == end_index:
        raise ValueError(f"Start and end indices are equal! Got start_index: {start_index} and end_index: {end_index}")  
    
    # if start index is more than end index, swap the ordering so to enforce start_index <= end_index
    if start_index > end_index:
        start_index, end_index = end_index, start_index
    
    # chop the spectrogram accordingly
    transformed_dynamic_spectra = input_spectrogram.dynamic_spectra[start_index:end_index+1, :]
    transformed_frequencies = input_spectrogram.frequencies[start_index:end_index+1]
    
    # return the spectrogram instance
    return Spectrogram(transformed_dynamic_spectra,
                       input_spectrogram.times,
                       transformed_frequencies,
                       input_spectrogram.tag,
                       chunk_start_time = input_spectrogram.chunk_start_time,
                       microsecond_correction = input_spectrogram.microsecond_correction,
                       spectrum_type = input_spectrogram.spectrum_type)


def time_chop(input_spectrogram: Spectrogram, 
              start_time: str, 
              end_time: str, 
              time_format: str = TimeFormats.DATETIME) -> Optional[Spectrogram]:
    
    # parse the strings as datetimes
    start_datetime = datetime.strptime(start_time, time_format)
    end_datetime = datetime.strptime(end_time, time_format)

    # if the requested time range is out of bounds for the spectrogram return None
    is_entirely_below_time_range = (start_datetime < input_spectrogram.datetimes[0] and end_datetime < input_spectrogram.datetimes[0])
    is_entirely_above_time_range = (start_datetime > input_spectrogram.datetimes[-1] and end_datetime > input_spectrogram.datetimes[-1])
    if is_entirely_below_time_range or is_entirely_above_time_range:
        return None
    
    start_index = find_closest_index(start_datetime, input_spectrogram.datetimes)
    end_index = find_closest_index(end_datetime, input_spectrogram.datetimes)
    
    if start_index == end_index:
        raise ValueError(f"Start and end indices are equal! Got start_index: {start_index} and end_index: {end_index}")
    
    if start_index > end_index:
        start_index, end_index = end_index, start_index

    # chop the spectrogram 
    transformed_dynamic_spectra = input_spectrogram.dynamic_spectra[:, start_index:end_index+1]

    # compute the new start datetime following the time chop
    transformed_start_datetime = input_spectrogram.datetimes[start_index]
    # compute the microsecond correction, and chunk start time
    transformed_chunk_start_time = datetime.strftime(transformed_start_datetime, TimeFormats.DATETIME)
    transformed_microsecond_correction = transformed_start_datetime.microsecond

    # chop the times array
    transformed_times = input_spectrogram.times[start_index:end_index+1]
    # assign the first spectrum to t=0 [s]
    transformed_times -= transformed_times[0]

    return Spectrogram(transformed_dynamic_spectra, 
                       transformed_times, 
                       input_spectrogram.frequencies, 
                       input_spectrogram.tag, 
                       chunk_start_time = transformed_chunk_start_time,
                       microsecond_correction = transformed_microsecond_correction,
                       spectrum_type = input_spectrogram.spectrum_type)


def time_average(input_spectrogram: Spectrogram, 
                 resolution: Optional[float] = None,
                 average_over: Optional[int] = None) -> Spectrogram:

    # spectre does not currently support averaging of non-datetime assigned spectrograms
    if input_spectrogram.chunk_start_time is None:
        raise ValueError(f"Input spectrogram is missing chunk start time. Averaging is not yet supported for non-datetime assigned spectrograms")
    
    # if nothing is specified, do nothing
    if (resolution is None) and (average_over is None):
        average_over = 1

    if not (resolution is not None) ^ (average_over is not None):
        raise ValueError(f"Exactly one of 'resolution' or 'average_over' "
                         f"must be specified.")
    
    # if the resolution is specified, compute the appropriate number of spectrums to average over
    # and recall the same function
    if resolution is not None:
        average_over = max(1, floor(resolution / input_spectrogram.time_resolution))
        return time_average(input_spectrogram, average_over=average_over)
    
    # No averaging is required, if we have to average over every one spectrum
    if average_over == 1:
        return input_spectrogram

    # average the dynamic spectra array
    transformed_dynamic_spectra = average_array(input_spectrogram.dynamic_spectra, 
                                                 average_over, 
                                                 axis=1)

    # We need to assign timestamps to the averaged spectrums in the spectrograms. 
    # The natural way to do this is to assign the i'th averaged spectrogram 
    # to the i'th averaged time
    transformed_times = average_array(input_spectrogram.times, average_over)
    
    # find the new chunk start time, which we will assign to the first spectrum after averaging
    corrected_start_datetime = input_spectrogram.datetimes[0] + timedelta(seconds = float(transformed_times[0]))
    transformed_chunk_start_time = corrected_start_datetime.strftime(TimeFormats.DATETIME)
    transformed_microsecond_correction = corrected_start_datetime.microsecond

    # finally, translate the averaged time seconds to begin at t=0 [s]
    transformed_times -= transformed_times[0]
    return Spectrogram(transformed_dynamic_spectra, 
                       transformed_times, 
                       input_spectrogram.frequencies, 
                       input_spectrogram.tag,
                       chunk_start_time = transformed_chunk_start_time,
                       microsecond_correction = transformed_microsecond_correction,
                       spectrum_type = input_spectrogram.spectrum_type)



def frequency_average(input_spectrogram: Spectrogram, 
                      resolution: Optional[float] = None,
                      average_over: Optional[int] = None) -> Spectrogram:
    
    # if nothing is specified, do nothing
    if (resolution is None) and (average_over is None):
        average_over = 1

    if not (resolution is not None) ^ (average_over is not None):
        raise ValueError(f"Exactly one of 'resolution' or 'average_over' "
                         f"must be specified.")
    
    # if the resolution is specified, compute the appropriate number of spectrums to average over
    # and recall the same function
    if resolution is not None:
        average_over = max(1, floor(resolution / input_spectrogram.frequency_resolution))
        return frequency_average(input_spectrogram, average_over=average_over)
    
    # No averaging is required, if we have to average over every one spectrum
    if average_over == 1:
        return input_spectrogram
    
    # We need to assign physical frequencies to the averaged spectrums in the spectrograms.
    # is to assign the i'th averaged spectral component to the i'th averaged frequency.
    # average the dynamic spectra array
    transformed_dynamic_spectra = average_array(input_spectrogram.dynamic_spectra, 
                                                 average_over, 
                                                 axis=0)
    transformed_frequencies = average_array(input_spectrogram.frequencies, average_over)

    return Spectrogram(transformed_dynamic_spectra, 
                       input_spectrogram.times, 
                       transformed_frequencies, 
                       input_spectrogram.tag,
                       chunk_start_time = input_spectrogram.chunk_start_time, 
                       microsecond_correction = input_spectrogram.microsecond_correction,
                       spectrum_type = input_spectrogram.spectrum_type)


def _time_elapsed(datetimes: np.ndarray) -> np.ndarray:
    # Extract the first datetime to use as the reference point
    base_time = datetimes[0]
    # Calculate elapsed time in seconds for each datetime in the list
    elapsed_time = [(dt - base_time).total_seconds() for dt in datetimes]
    # Convert the list of seconds to a NumPy array of type float32
    return np.array(elapsed_time, dtype=np.float32)


# we assume that the spectrogram list is ORDERED chronologically
# we assume there is no time overlap in any of the spectrograms in the list
def join_spectrograms(spectrograms: list[Spectrogram]) -> Spectrogram:

    # check that the length of the list is non-zero
    num_spectrograms = len(spectrograms)
    if num_spectrograms == 0:
        raise ValueError(f"Input list of spectrograms is empty!")
    
    # extract the first element of the list, and use this as a reference for comparison
    # input validations.
    reference_spectrogram = spectrograms[0] 

    # perform checks on each spectrogram in teh list
    for spectrogram in spectrograms:
        if not np.all(np.equal(spectrogram.frequencies, reference_spectrogram.frequencies)):
            raise ValueError(f"All spectrograms must have identical frequency ranges")
        if spectrogram.tag != reference_spectrogram.tag:
            raise ValueError(f"All tags must be equal for each spectrogram in the input list!")
        if spectrogram.spectrum_type != reference_spectrogram.spectrum_type:
            raise ValueError(f"All units must be equal for each spectrogram in the input list!")
        if spectrogram.chunk_start_time is None:
            raise ValueError(f"All spectrograms must have chunk_start_time set. Received {spectrogram.chunk_start_time}")


    # build a list of the time array of each spectrogram in the list
    conc_datetimes = np.concatenate([s.datetimes for s in spectrograms])
    # find the total number of time stamps
    num_total_time_bins = len(conc_datetimes)
    # find the total number of frequency bins (we can safely now use the first)
    num_total_freq_bins = len(reference_spectrogram.frequencies)
    # create an empty numpy array to hold the joined spectrograms
    transformed_dynamic_spectra = np.empty((num_total_freq_bins, num_total_time_bins))

    start_index = 0
    for spectrogram in spectrograms:
        end_index = start_index + len(spectrogram.times)
        transformed_dynamic_spectra[:, start_index:end_index] = spectrogram.dynamic_spectra
        start_index = end_index

    transformed_times = _time_elapsed(conc_datetimes)

    return Spectrogram(transformed_dynamic_spectra, 
                       transformed_times, 
                       reference_spectrogram.frequencies, 
                       reference_spectrogram.tag, 
                       chunk_start_time = reference_spectrogram.chunk_start_time,
                       microsecond_correction = reference_spectrogram.microsecond_correction,
                       spectrum_type = reference_spectrogram.spectrum_type) 