# SPDX-FileCopyrightText: © 2024-2025 Jimmy Fitzpatrick <jcfitzpatrick12@gmail.com>
# This file is part of SPECTRE
# SPDX-License-Identifier: GPL-3.0-or-later

"""Real-time, extensible post-processing of SDR data into spectrograms."""

from ._base import BaseEventHandler, BaseEventHandlerModel
from .plugins._fixed_center_frequency import (
    FixedEventHandler,
    FixedEventHandlerModel,
)

# from .plugins._swept_center_frequency import SweptEventHandler
from ._stfft import (
    get_buffer,
    get_cosine_signal,
    get_fftw_obj,
    get_frequencies,
    get_num_spectrums,
    get_times,
    get_window,
    stfft,
    WindowType,
)

__all__ = [
    "BaseEventHandler",
    "BaseEventHandlerModel",
    "FixedEventHandler",
    "FixedEventHandlerModel",
    "get_buffer",
    "get_cosine_signal",
    "get_fftw_obj",
    "get_frequencies",
    "get_times",
    "get_num_spectrums",
    "get_windows",
    "stfft",
    "get_window",
    "WindowType",
]
