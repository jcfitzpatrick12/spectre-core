# SPDX-FileCopyrightText: © 2024 Jimmy Fitzpatrick <jcfitzpatrick12@gmail.com>
# This file is part of SPECTRE
# SPDX-License-Identifier: GPL-3.0-or-later

from logging import getLogger
_LOGGER = getLogger(__name__)

from dataclasses import dataclass
from math import floor
from scipy.signal import get_window
from numbers import Number
from warnings import warn
from typing import Optional

from ._parameters import Parameters
from ._ptemplates import PNames


def _validate_window(
        parameters: Parameters
) -> None:
    window_size = parameters.get_parameter_value(PNames.WINDOW_SIZE)
    window_type = parameters.get_parameter_value(PNames.WINDOW_TYPE)
    sample_rate = parameters.get_parameter_value(PNames.SAMPLE_RATE)
    batch_size  = parameters.get_parameter_value(PNames.BATCH_SIZE)
    
    window_interval = window_size*(1 / sample_rate)
    if window_interval > batch_size:
        raise ValueError((f"The windowing interval must be strictly less than the chunk size. "
                          f"Computed the windowing interval to be {window_interval} [s], "
                          f"but the chunk size is {batch_size} [s]"))
    
    try:
        _ = get_window(window_type, window_size)
    except Exception as e:
        raise Exception((f"An error has occurred while validating the window. "
                         f"Got {str(e)}"))
    

def _validate_nyquist_criterion(
        parameters: Parameters
) -> None:
    sample_rate = parameters.get_parameter_value(PNames.SAMPLE_RATE)
    bandwidth   = parameters.get_parameter_value(PNames.BANDWIDTH)

    if sample_rate < bandwidth:
        raise ValueError((f"Nyquist criterion has not been satisfied. "
                          f"Sample rate must be greater than or equal to the bandwidth. "
                          f"Got sample rate {sample_rate} [Hz], and bandwidth {bandwidth} [Hz]"))
    

def _compute_num_steps_per_sweep(min_freq: float, 
                                 max_freq: float,
                                 samp_rate: int,
                                 freq_step: float) -> int:
     return floor((max_freq - min_freq + samp_rate/2) / freq_step)


def _validate_num_steps_per_sweep(
        parameters: Parameters
) -> None:
    min_freq    = parameters.get_parameter_value(PNames.MIN_FREQUENCY)
    max_freq    = parameters.get_parameter_value(PNames.MAX_FREQUENCY)
    sample_rate = parameters.get_parameter_value(PNames.SAMPLE_RATE)
    freq_step   = parameters.get_parameter_value(PNames.FREQUENCY_STEP)

    num_steps_per_sweep = _compute_num_steps_per_sweep(min_freq, 
                                                       max_freq, 
                                                       sample_rate, 
                                                       freq_step)
    if num_steps_per_sweep <= 1:
        raise ValueError((f"We need strictly greater than one step per sweep. "
                          f"Computed {num_steps_per_sweep} step per sweep"))
    

def _validate_sweep_interval(
        parameters: Parameters
) -> None: 
    min_freq         = parameters.get_parameter_value(PNames.MIN_FREQUENCY)
    max_freq         = parameters.get_parameter_value(PNames.MAX_FREQUENCY)
    sample_rate      = parameters.get_parameter_value(PNames.SAMPLE_RATE)
    freq_step        = parameters.get_parameter_value(PNames.FREQUENCY_STEP)
    samples_per_step = parameters.get_parameter_value(PNames.SAMPLES_PER_STEP)
    batch_size       = parameters.get_parameter_value(PNames.BATCH_SIZE)

    num_steps_per_sweep = _compute_num_steps_per_sweep(min_freq, 
                                                       max_freq, 
                                                       sample_rate, 
                                                       freq_step)
    num_samples_per_sweep = num_steps_per_sweep * samples_per_step
    sweep_interval = num_samples_per_sweep * 1/sample_rate
    if sweep_interval > batch_size:
        raise ValueError((f"Sweep interval must be less than the chunk size. "
                          f"The computed sweep interval is {sweep_interval} [s], "
                          f"but the given chunk size is {batch_size} [s]"))
    

def _validate_num_samples_per_step(
        parameters: Parameters
) -> None:

    window_size      = parameters.get_parameter_value(PNames.WINDOW_SIZE)
    samples_per_step = parameters.get_parameter_value(PNames.SAMPLES_PER_STEP)

    if window_size >= samples_per_step:
        raise ValueError((f"Window size must be strictly less than the number of samples per step. "
                          f"Got window size {window_size} [samples], which is more than or equal "
                          f"to the number of samples per step {samples_per_step}"))
    

def _validate_non_overlapping_steps(
        parameters: Parameters
) -> None:
    
    freq_step = parameters.get_parameter_value(PNames.FREQUENCY_STEP)
    sample_rate = parameters.get_parameter_value(PNames.SAMPLE_RATE)

    if freq_step < sample_rate:
        raise NotImplementedError(f"SPECTRE does not yet support spectral steps overlapping in frequency. "
                                  f"Got frequency step {freq_step * 1e-6} [MHz] which is less than the sample "
                                  f"rate {sample_rate * 1e-6} [MHz]")
    

def _validate_step_interval(
        parameters: Parameters,
        api_latency: Number
) -> None:
    
    samples_per_step = parameters.get_parameter_value(PNames.SAMPLES_PER_STEP)
    sample_rate      = parameters.get_parameter_value(PNames.SAMPLE_RATE)

    step_interval = samples_per_step * 1/ sample_rate # [s]
    if step_interval < api_latency:
        raise ValueError(f"The computed step interval of {step_interval} [s] is of the order of empirically "
                         f"derived api latency {api_latency} [s]; you may experience undefined behaviour!")


def _validate_fixed_center_frequency_parameters(
    parameters: Parameters
) -> None:
    _validate_nyquist_criterion(parameters)
    _validate_window(parameters)


def _validate_swept_center_frequency_parameters(
    parameters: Parameters,
    api_retuning_latency: Optional[Number] = None,
) -> None:
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