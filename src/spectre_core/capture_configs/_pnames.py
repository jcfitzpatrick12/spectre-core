# SPDX-FileCopyrightText: © 2024 Jimmy Fitzpatrick <jcfitzpatrick12@gmail.com>
# This file is part of SPECTRE
# SPDX-License-Identifier: GPL-3.0-or-later

from enum import Enum

class PNames(Enum):
    """A centralised store of parameter names"""
    CENTER_FREQUENCY     = "center_frequency"
    MIN_FREQUENCY        = "min_frequency"
    MAX_FREQUENCY        = "max_frequency"
    FREQUENCY_STEP       = "frequency_step"
    FREQUENCY            = "frequency"
    BANDWIDTH            = "bandwidth"
    SAMPLE_RATE          = "sample_rate"
    IF_GAIN              = "if_gain"
    RF_GAIN              = "rf_gain"
    AMPLITUDE            = "amplitude"
    TIME_RESOLUTION      = "time_resolution"
    FREQUENCY_RESOLUTION = "frequency_resolution"
    TIME_RANGE           = "time_range"
    BATCH_SIZE           = "batch_size"
    WINDOW_TYPE          = "window_type"
    WINDOW_HOP           = "window_hop"
    WINDOW_SIZE          = "window_size"
    EVENT_HANDLER_KEY    = "event_handler_key"
    WATCH_EXTENSION      = "watch_extension"
    BATCH_KEY            = "batch_key"
    SAMPLES_PER_STEP     = "samples_per_step"
    MIN_SAMPLES_PER_STEP = "min_samples_per_step"
    MAX_SAMPLES_PER_STEP = "max_samples_per_step"
    STEP_INCREMENT       = "step_increment"
    ORIGIN               = "origin"
    TELESCOPE            = "telescope"
    INSTRUMENT           = "instrument"
    OBJECT               = "object"
    OBS_LAT              = "obs_lat"
    OBS_LON              = "obs_lon"
    OBS_ALT              = "obs_alt"