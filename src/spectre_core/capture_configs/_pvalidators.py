# SPDX-FileCopyrightText: © 2024 Jimmy Fitzpatrick <jcfitzpatrick12@gmail.com>
# This file is part of SPECTRE
# SPDX-License-Identifier: GPL-3.0-or-later

from math import floor
from typing import Optional, cast

from scipy.signal import get_window

from ._parameters import Parameters
from ._pnames import PName

# ----------------------------------------------------------------------- # 
# Throughout this module, repeated calls to `cast` will be seen on using the
# `get_parameter_value` method. This is purely to signify intent and keep
# the static type checkers happy.
# 
# This is okay, as whenever the validators are called, the parameter values 
# have already been individually casted and constrained according to the 
# parameter templates. There is negligible runtime impact. Though a bit
# of a pain for maintenance.
# ----------------------------------------------------------------------- # 


def validate_window(
        parameters: Parameters
) -> None:
    """Ensure that the capture config describes a valid window.

    :param parameters: The parameters to be validated.
    :raises ValueError: If the window interval is greater than the batch size.
    :raises ValueError: If the specified window type cannot be fetched using 
    the SciPy `get_window` function.
    """
    window_size = cast(int, parameters.get_parameter_value(PName.WINDOW_SIZE))
    sample_rate = cast(int, parameters.get_parameter_value(PName.SAMPLE_RATE))
    batch_size  = cast(int, parameters.get_parameter_value(PName.BATCH_SIZE))
    window_type = cast(str, parameters.get_parameter_value(PName.WINDOW_TYPE))
    
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
    

def validate_nyquist_criterion(
        parameters: Parameters
) -> None:
    """Ensure that the Nyquist criterion is satisfied.

    :param parameters: The parameters to be validated.
    :raises ValueError: If the sample rate is less than the bandwidth.
    """
    sample_rate = cast(int, parameters.get_parameter_value(PName.SAMPLE_RATE))
    bandwidth   = cast(float, parameters.get_parameter_value(PName.BANDWIDTH))

    if sample_rate < bandwidth:
        raise ValueError((f"Nyquist criterion has not been satisfied. "
                          f"Sample rate must be greater than or equal to the bandwidth. "
                          f"Got sample rate {sample_rate} [Hz], and bandwidth {bandwidth} [Hz]"))
    

def _compute_num_steps_per_sweep(min_freq: float, 
                                 max_freq: float,
                                 freq_step: float) -> int:
    """Compute the number of steps in one frequency sweep.

    The center frequency starts at `min_freq` and increments in steps of `freq_step` 
    until the next step would exceed `max_freq`.

    :param min_freq: The minimum frequency of the sweep.
    :param max_freq: The maximum frequency of the sweep.
    :param freq_step: The frequency step size.
    :return: The number of steps in one frequency sweep.
    """
    return floor((max_freq - min_freq) / freq_step)


def validate_num_steps_per_sweep(
        parameters: Parameters
) -> None:
    """Ensure that there are at least two steps in frequency per sweep.

    :param parameters: The parameters to be validated.
    :raises ValueError: If the number of steps per sweep is less than or equal to one.
    """
    min_freq    = cast(float, parameters.get_parameter_value(PName.MIN_FREQUENCY))
    max_freq    = cast(float, parameters.get_parameter_value(PName.MAX_FREQUENCY))
    freq_step   = cast(float, parameters.get_parameter_value(PName.FREQUENCY_STEP))

    num_steps_per_sweep = _compute_num_steps_per_sweep(min_freq, 
                                                       max_freq, 
                                                       freq_step)
    if num_steps_per_sweep <= 1:
        raise ValueError((f"We need strictly greater than one step per sweep. "
                          f"Computed {num_steps_per_sweep} step per sweep"))
    

def validate_sweep_interval(
        parameters: Parameters
) -> None: 
    """Ensure that the sweep interval is greater than the batch size.

    :param parameters: The parameters to be validated.
    :raises ValueError: If the sweep interval is greater than the batch size.
    """
    min_freq         = cast(float, parameters.get_parameter_value(PName.MIN_FREQUENCY))
    max_freq         = cast(float, parameters.get_parameter_value(PName.MAX_FREQUENCY))
    freq_step        = cast(float, parameters.get_parameter_value(PName.FREQUENCY_STEP))
    samples_per_step = cast(int, parameters.get_parameter_value(PName.SAMPLES_PER_STEP))
    batch_size       = cast(int, parameters.get_parameter_value(PName.BATCH_SIZE))
    sample_rate      = cast(int, parameters.get_parameter_value(PName.SAMPLE_RATE))

    num_steps_per_sweep = _compute_num_steps_per_sweep(min_freq, 
                                                       max_freq, 
                                                       freq_step)
    num_samples_per_sweep = num_steps_per_sweep * samples_per_step
    sweep_interval = num_samples_per_sweep * 1/sample_rate
    if sweep_interval > batch_size:
        raise ValueError((f"Sweep interval must be less than the batch size. "
                          f"The computed sweep interval is {sweep_interval} [s], "
                          f"but the given batch size is {batch_size} [s]"))
    

def validate_num_samples_per_step(
        parameters: Parameters
) -> None:
    """Ensure that the number of samples per step is greater than the window size.

    :param parameters: The parameters to be validated.
    :raises ValueError: If the window size is greater than the number of samples per step.
    """
    window_size      = cast(int, parameters.get_parameter_value(PName.WINDOW_SIZE))
    samples_per_step = cast(int, parameters.get_parameter_value(PName.SAMPLES_PER_STEP))

    if window_size >= samples_per_step:
        raise ValueError((f"Window size must be strictly less than the number of samples per step. "
                          f"Got window size {window_size} [samples], which is more than or equal "
                          f"to the number of samples per step {samples_per_step}"))
    

def validate_non_overlapping_steps(
        parameters: Parameters
) -> None:
    """Ensure that the stepped spectrograms are non-overlapping in the frequency domain.

    :param parameters: The parameters to be validated.
    :raises NotImplementedError: If the spectrograms overlap in the frequency domain.
    """
    
    freq_step   = cast(float, parameters.get_parameter_value(PName.FREQUENCY_STEP))
    sample_rate = cast(int, parameters.get_parameter_value(PName.SAMPLE_RATE))

    if freq_step < sample_rate:
        raise NotImplementedError(f"SPECTRE does not yet support spectral steps overlapping in frequency. "
                                  f"Got frequency step {freq_step * 1e-6} [MHz] which is less than the sample "
                                  f"rate {sample_rate * 1e-6} [MHz]")
    

def validate_step_interval(
        parameters: Parameters,
        api_retuning_latency: float
) -> None:
    """Ensure that the time elapsed collecting samples at a fixed frequency is greater 
    than the empirically derived API retuning latency.

    :param parameters: The parameters to be validated.
    :param api_retuning_latency: The empirically derived API retuning latency (in seconds).
    :raises ValueError: If the time elapsed for a step is less than the API retuning latency.
    """
    samples_per_step = cast(int, parameters.get_parameter_value(PName.SAMPLES_PER_STEP))
    sample_rate      = cast(int, parameters.get_parameter_value(PName.SAMPLE_RATE))

    step_interval = samples_per_step * 1/ sample_rate # [s]
    if step_interval < api_retuning_latency:
        raise ValueError(f"The computed step interval of {step_interval} [s] is of the order of empirically "
                         f"derived api latency {api_retuning_latency} [s]; you may experience undefined behaviour!")


def validate_sample_rate_with_master_clock_rate(
    parameters: Parameters,
) -> None:
    """Ensure that the master clock rate is an integer multiple of the sample rate.

    :param parameters: The parameters to be validated.
    :raises ValueError: If the master clock rate is not an integer multiple of the sample rate
    """
    master_clock_rate = cast(int, parameters.get_parameter_value(PName.MASTER_CLOCK_RATE))
    sample_rate       = cast(int, parameters.get_parameter_value(PName.SAMPLE_RATE))

    if master_clock_rate % sample_rate != 0:
        raise ValueError(f"The master clock rate of {master_clock_rate} [Hz] is not an integer "
                         f"multiple of the sample rate {sample_rate} [Hz].")


def validate_fixed_center_frequency(
    parameters: Parameters
) -> None:
    """Apply validators for capture config parameters describing fixed center frequency capture.

    :param parameters: The parameters to be validated.
    """
    validate_nyquist_criterion(parameters)
    validate_window(parameters)


def validate_swept_center_frequency(
    parameters: Parameters,
    api_retuning_latency: Optional[float] = None,
) -> None:
    """Apply validators for capture config parameters describing swept center frequency capture.

    :param parameters: The parameters to be validated.
    :param api_retuning_latency: The empirically derived API retuning latency. Defaults to None.
    """
    validate_nyquist_criterion(parameters)
    validate_window(parameters)
    validate_non_overlapping_steps(parameters)
    validate_num_steps_per_sweep(parameters)
    validate_num_samples_per_step(parameters)
    validate_sweep_interval(parameters)
    
    if api_retuning_latency is not None:
        validate_step_interval(parameters, api_retuning_latency)
