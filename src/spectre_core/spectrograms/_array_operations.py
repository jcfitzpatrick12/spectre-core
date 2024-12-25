# SPDX-FileCopyrightText: © 2024 Jimmy Fitzpatrick <jcfitzpatrick12@gmail.com>
# This file is part of SPECTRE
# SPDX-License-Identifier: GPL-3.0-or-later

from datetime import datetime

import numpy as np

def average_array(array: np.ndarray, average_over: int, axis=0) -> np.ndarray:

    # Check if average_over is an integer
    if type(average_over) != int:
        raise TypeError(f"average_over must be an integer. Got {type(average_over)}")

    # Get the size of the specified axis which we will average over
    axis_size = array.shape[axis]
    # Check if average_over is within the valid range
    if not 1 <= average_over <= axis_size:
        raise ValueError(f"average_over must be between 1 and the length of the axis ({axis_size})")
    
    max_axis_index = len(np.shape(array)) - 1
    if axis > max_axis_index: # zero indexing on specifying axis, so minus one
        raise ValueError(f"Requested axis is out of range of array dimensions. Axis: {axis}, max axis index: {max_axis_index}")

    # find the number of elements in the requested axis
    num_elements = array.shape[axis]

    # find the number of "full blocks" to average over
    num_full_blocks = num_elements // average_over
    # if num_elements is not exactly divisible by average_over, we will have some elements left over
    # these remaining elements will be padded with nans to become another full block
    remainder = num_elements % average_over
    
    # if there exists a remainder, pad the last block
    if remainder != 0:
        # initialise an array to hold the padding shape
        padding_shape = [(0, 0)] * array.ndim
        # pad after the last column in the requested axis
        padding_shape[axis] = (0, average_over - remainder)
        # pad with nan values (so to not contribute towards the mean computation)
        array = np.pad(array, padding_shape, mode='constant', constant_values=np.nan)
    
    # initalise a list to hold the new shape
    new_shape = list(array.shape)
    # update the shape on the requested access (to the number of blocks we will average over)
    new_shape[axis] = num_full_blocks + (1 if remainder else 0)
    # insert a new dimension, with the size of each block
    new_shape.insert(axis + 1, average_over)
    # and reshape the array to sort the array into the relevant blocks.
    reshaped_array = array.reshape(new_shape)
    # average over the newly created axis, essentially averaging over the blocks.
    averaged_array = np.nanmean(reshaped_array, axis=axis + 1)
    # return the averaged array
    return averaged_array


def is_close(ar: np.ndarray, 
             ar_comparison: np.ndarray,
             absolute_tolerance: float) -> bool:
    """Close enough accounts for wiggle-room equating floats."""
    return np.all(np.isclose(ar, 
                             ar_comparison, 
                             atol=absolute_tolerance))

def find_closest_index(
    target_value: float | datetime, 
    array: np.ndarray, 
    enforce_strict_bounds: bool = False
) -> int:
    # Ensure input array is a numpy array
    array = np.asarray(array)

    # Convert to datetime64 if necessary
    if isinstance(target_value, datetime) or np.issubdtype(array.dtype, np.datetime64):
        target_value = np.datetime64(target_value)
        array = array.astype('datetime64[ns]')
    else:
        target_value = float(target_value)
        array = array.astype(float)

    # Check bounds if strict enforcement is required
    if enforce_strict_bounds:
        max_value, min_value = np.nanmax(array), np.nanmin(array)
        if target_value > max_value:
            raise ValueError(f"Target value {target_value} exceeds max array value {max_value}")
        if target_value < min_value:
            raise ValueError(f"Target value {target_value} is less than min array value {min_value}")

    # Find the index of the closest value
    return np.argmin(np.abs(array - target_value))


def normalise_peak_intensity(array: np.ndarray) -> np.ndarray:
    return array/np.nanmax(array)


def compute_resolution(array: np.ndarray) -> float:
    # Check that the array is one-dimensional
    if array.ndim != 1:
        raise ValueError("Input array must be one-dimensional")
    
    if len(array) < 2:
        raise ValueError("Input array must contain at least two elements")
    
    # Calculate differences between consecutive elements.
    resolutions = np.diff(array)

    return np.nanmedian(resolutions)


def compute_range(array: np.ndarray) -> float:
    # Check that the array is one-dimensional
    if array.ndim != 1:
        raise ValueError("Input array must be one-dimensional")
    
    if len(array) < 2:
        raise ValueError("Input array must contain at least two elements")
    return array[-1] - array[0]


def subtract_background(array: np.ndarray, start_index: int, end_index: int) -> np.ndarray:
    array -= np.nanmean(array[start_index:end_index+1])
    return array