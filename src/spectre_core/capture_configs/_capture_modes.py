# SPDX-FileCopyrightText: © 2024 Jimmy Fitzpatrick <jcfitzpatrick12@gmail.com>
# This file is part of SPECTRE
# SPDX-License-Identifier: GPL-3.0-or-later

from enum import Enum

class CaptureMode(Enum):
    """A default capture mode for `spectre`.
    
    Each `CaptureMode` has an associated base capture template, which can be fetched using: 
    
    `get_base_capture_template`
    
    All base capture templates must be registered by one of `CaptureMode`. To introduce a new
    base capture template, you need to create a new `CaptureMode` constant.
    
    :ivar FIXED_CENTER_FREQUENCY: Indicates data capture at a fixed center frequency.
    :ivar SWEPT_CENTER_FREQUENCY: Indicates data capture where the center frequency is continually sweeping
    in fixed increments.
    """
    FIXED_CENTER_FREQUENCY = "fixed_center_frequency"
    SWEPT_CENTER_FREQUENCY = "swept_center_frequency"