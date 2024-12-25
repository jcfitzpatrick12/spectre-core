
# SPDX-FileCopyrightText: © 2024 Jimmy Fitzpatrick <jcfitzpatrick12@gmail.com>
# This file is part of SPECTRE
# SPDX-License-Identifier: GPL-3.0-or-later

from dataclasses import dataclass

@dataclass(frozen=True)
class PNames:
    """A centralised store of default parameter template names"""
    CENTER_FREQUENCY        : str = "center_frequency"
    MIN_FREQUENCY           : str = "min_frequency"
    MAX_FREQUENCY           : str = "max_frequency"
    FREQUENCY_STEP          : str = "frequency_step"
    FREQUENCY               : str = "frequency"
    BANDWIDTH               : str = "bandwidth"
    SAMPLE_RATE             : str = "sample_rate"
    IF_GAIN                 : str = "if_gain"
    RF_GAIN                 : str = "rf_gain"
    AMPLITUDE               : str = "amplitude"
    FREQUENCY               : str = "frequency"
    TIME_RESOLUTION         : str = "time_resolution"
    FREQUENCY_RESOLUTION    : str = "frequency_resolution"
    TIME_RANGE              : str = "time_range"
    BATCH_SIZE              : str = "batch_size"
    WINDOW_TYPE             : str = "window_type"
    WINDOW_HOP              : str = "window_hop"
    WINDOW_SIZE             : str = "window_size"
    EVENT_HANDLER_KEY       : str = "event_handler_key"
    WATCH_EXTENSION         : str = "watch_extension"
    CHUNK_KEY               : str = "chunk_key"
    SAMPLES_PER_STEP        : str = "samples_per_step"
    MIN_SAMPLES_PER_STEP    : str = "min_samples_per_step"
    MAX_SAMPLES_PER_STEP    : str = "max_samples_per_step"
    STEP_INCREMENT          : str = "step_increment"
    ORIGIN                  : str = "origin"
    TELESCOPE               : str = "telescope"
    INSTRUMENT              : str = "instrument"
    OBJECT                  : str = "object"
    OBS_LAT                 : str = "obs_lat"
    OBS_LON                 : str = "obs_lon"
    OBS_ALT                 : str = "obs_alt"