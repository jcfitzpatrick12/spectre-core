# SPDX-FileCopyrightText: © 2024 Jimmy Fitzpatrick <jcfitzpatrick12@gmail.com>
# This file is part of SPECTRE
# SPDX-License-Identifier: GPL-3.0-or-later

from dataclasses import dataclass
from math import floor
from typing import Optional, cast

from scipy.signal import get_window

from ._parameters import Parameters
from ._ptemplates import PNames


# ----------------------------------------------------------------------- # 
# Throughout this module, repeated calls to `cast` will be seen on using the
# `get_parameter_value` method. This is purely to signify intent and keep
# the static type checkers happy.
# 
# This is okay, as whenever the validators are called, the parameter values 
# have already been individually casted and constrained according to the 
# parameter templates. There is negligible runtime impact.
# ----------------------------------------------------------------------- # 


def _validate_window(
        parameters: Parameters
) -> None:
    """Ensure that the capture configuration file describes a valid window.

    Arguments:
        parameters -- The parameters to be validated.

    Raises:
        ValueError: If the window interval is greater than the batch size.
        ValueError: If a window cannot be fetched via the `get_window` SciPy function.
    """
    window_size = cast(int, parameters.get_parameter_value(PNames.WINDOW_SIZE))
    sample_rate = cast(int, parameters.get_parameter_value(PNames.SAMPLE_RATE))
    batch_size  = cast(int, parameters.get_parameter_value(PNames.BATCH_SIZE))
    window_type = cast(str, parameters.get_parameter_value(PNames.WINDOW_TYPE))
    
    window_interval = window_size*(1 / sample_rate)
    if window_interval > batch_size:
        raise ValueError((f"The windowing interval must be strictly less than the batch size. "
                          f"Computed the windowing interval to be {window_interval} [s], "
                          f"but the batch size is {batch_size} [s]"))
    
    try:
        _ = get_window(window_type, window_size)
    except Exception as e:
        raise ValueError((f"An error has occurred while validating the window. "
                          f"Got {str(e)}"))
    

def _validate_nyquist_criterion(
        parameters: Parameters
) -> None:
    """Ensure that the Nyquist criterion is satisfied.

    Arguments:
        parameters -- The parameters to be validated.

    Raises:
        ValueError: If the sample rate is less than the bandwidth.
    """
    sample_rate = cast(int, parameters.get_parameter_value(PNames.SAMPLE_RATE))
    bandwidth   = cast(float, parameters.get_parameter_value(PNames.BANDWIDTH))

    if sample_rate < bandwidth:
        raise ValueError((f"Nyquist criterion has not been satisfied. "
                          f"Sample rate must be greater than or equal to the bandwidth. "
                          f"Got sample rate {sample_rate} [Hz], and bandwidth {bandwidth} [Hz]"))
    

def _compute_num_steps_per_sweep(min_freq: float, 
                                 max_freq: float,
                                 freq_step: float) -> int:
    """Compute the number of steps in one frequency sweep. We assume the center frequency starts at
    `min_freq`, and increments in steps of `freq_step` until the next step would take it greater than
    `max_freq`.
    """
    return floor((max_freq - min_freq) / freq_step)


def _validate_num_steps_per_sweep(
        parameters: Parameters
) -> None:
    """Ensure that there are at least two steps in frequency per sweep.

    Arguments:
        parameters -- The parameters to be validated.

    Raises:
        ValueError: If the number of steps per sweep is less than or equal to one.
    """
    min_freq    = cast(float, parameters.get_parameter_value(PNames.MIN_FREQUENCY))
    max_freq    = cast(float, parameters.get_parameter_value(PNames.MAX_FREQUENCY))
    freq_step   = cast(float, parameters.get_parameter_value(PNames.FREQUENCY_STEP))

    num_steps_per_sweep = _compute_num_steps_per_sweep(min_freq, 
                                                       max_freq, 
                                                       freq_step)
    if num_steps_per_sweep <= 1:
        raise ValueError((f"We need strictly greater than one step per sweep. "
                          f"Computed {num_steps_per_sweep} step per sweep"))
    

def _validate_sweep_interval(
        parameters: Parameters
) -> None: 
    """Ensure that the sweep interval (the time elapsed over one sweep) is greater than the batch size.
    Effectively, we make sure we have more than one total frequency sweep per batched file.

    Arguments:
        parameters -- The parameters to be validated.

    Raises:
        ValueError: If the time elapsed for one sweep is greater than the batch size.
    """
    min_freq         = cast(float, parameters.get_parameter_value(PNames.MIN_FREQUENCY))
    max_freq         = cast(float, parameters.get_parameter_value(PNames.MAX_FREQUENCY))
    freq_step        = cast(float, parameters.get_parameter_value(PNames.FREQUENCY_STEP))
    samples_per_step = cast(int, parameters.get_parameter_value(PNames.SAMPLES_PER_STEP))
    batch_size       = cast(int, parameters.get_parameter_value(PNames.BATCH_SIZE))
    sample_rate      = cast(int, parameters.get_parameter_value(PNames.SAMPLE_RATE))

    num_steps_per_sweep = _compute_num_steps_per_sweep(min_freq, 
                                                       max_freq, 
                                                       freq_step)
    num_samples_per_sweep = num_steps_per_sweep * samples_per_step
    sweep_interval = num_samples_per_sweep * 1/sample_rate
    if sweep_interval > batch_size:
        raise ValueError((f"Sweep interval must be less than the batch size. "
                          f"The computed sweep interval is {sweep_interval} [s], "
                          f"but the given batch size is {batch_size} [s]"))
    

def _validate_num_samples_per_step(
        parameters: Parameters
) -> None:
    """Ensure that the number of samples per step is greater than the window size. This is so that the 
    ShortTimeFFT is well-defined for the samples of each step in the sweep.

    Arguments:
        parameters -- The parameters to be validated.

    Raises:
        ValueError: If the window size is greater than the number of samples per step.
    """
    window_size      = cast(int, parameters.get_parameter_value(PNames.WINDOW_SIZE))
    samples_per_step = cast(int, parameters.get_parameter_value(PNames.SAMPLES_PER_STEP))

    if window_size >= samples_per_step:
        raise ValueError((f"Window size must be strictly less than the number of samples per step. "
                          f"Got window size {window_size} [samples], which is more than or equal "
                          f"to the number of samples per step {samples_per_step}"))
    

def _validate_non_overlapping_steps(
        parameters: Parameters
) -> None:
    """Ensure that on performing the ShortTimeFFT, the generated stepped spectrogram are non-overlapping
    in the frequency domain.

    Arguments:
        parameters -- The parameters to be validated.

    Raises:
        NotImplementedError: If the stepped spectrogram generated would be overlapping in the frequency domain.
    """
    
    freq_step   = cast(float, parameters.get_parameter_value(PNames.FREQUENCY_STEP))
    sample_rate = cast(int, parameters.get_parameter_value(PNames.SAMPLE_RATE))

    if freq_step < sample_rate:
        raise NotImplementedError(f"SPECTRE does not yet support spectral steps overlapping in frequency. "
                                  f"Got frequency step {freq_step * 1e-6} [MHz] which is less than the sample "
                                  f"rate {sample_rate * 1e-6} [MHz]")
    

def _validate_step_interval(
        parameters: Parameters,
        api_retuning_latency: float
) -> None:
    """Ensure that time elapsed collecting samples at some fixed frequency is greater than the empirically derived
    API retuning latency. This is to prevent undefined behaviour resulting from trying to retune the center frequency
    faster than the receivers API can handle.

    Arguments:
        parameters -- The parameters to be validated.
        api_retuning_latency -- The empirically derived API retuning latency.

    Raises:
        ValueError: If the time elapsed for some step in the sweep is less than the API retuning latency.
    """
    samples_per_step = cast(int, parameters.get_parameter_value(PNames.SAMPLES_PER_STEP))
    sample_rate      = cast(int, parameters.get_parameter_value(PNames.SAMPLE_RATE))

    step_interval = samples_per_step * 1/ sample_rate # [s]
    if step_interval < api_retuning_latency:
        raise ValueError(f"The computed step interval of {step_interval} [s] is of the order of empirically "
                         f"derived api latency {api_retuning_latency} [s]; you may experience undefined behaviour!")


def _validate_fixed_center_frequency_parameters(
    parameters: Parameters
) -> None:
    """Apply a group of validators designed specifically for capture config parameters describing fixed center
    frequency capture.

    Arguments:
        parameters -- The parameters to be validated.
    """
    _validate_nyquist_criterion(parameters)
    _validate_window(parameters)


def _validate_swept_center_frequency_parameters(
    parameters: Parameters,
    api_retuning_latency: Optional[float] = None,
) -> None:
    """Apply a group of validators designed specifically for capture config parameters describing swept center
    frequency capture.

    Arguments:
        parameters -- The parameters to be validated.
    """
    _validate_nyquist_criterion(parameters)
    _validate_window(parameters)
    _validate_non_overlapping_steps(parameters)
    _validate_num_steps_per_sweep(parameters)
    _validate_num_samples_per_step(parameters)
    _validate_sweep_interval(parameters)
    
    if api_retuning_latency is not None:
        _validate_step_interval(parameters, api_retuning_latency)
    

@dataclass(frozen=True)
class PValidators:
    """Ready-made parameter validating functions."""
    window                 = _validate_window
    nyquist_criterion      = _validate_nyquist_criterion
    step_interval          = _validate_step_interval
    non_overlapping_steps  = _validate_non_overlapping_steps
    num_steps_per_sweep    = _validate_num_steps_per_sweep
    num_samples_per_step   = _validate_num_samples_per_step
    sweep_interval         = _validate_sweep_interval
    step_interval          = _validate_step_interval
    fixed_center_frequency = _validate_fixed_center_frequency_parameters
    swept_center_frequency = _validate_swept_center_frequency_parameters
