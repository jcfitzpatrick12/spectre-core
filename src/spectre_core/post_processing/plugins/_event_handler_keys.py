# SPDX-FileCopyrightText: © 2024 Jimmy Fitzpatrick <jcfitzpatrick12@gmail.com>
# This file is part of SPECTRE
# SPDX-License-Identifier: GPL-3.0-or-later

from enum import Enum

class EventHandlerKey(Enum):  
    """Key bound to a `BaseEventHandler` plugin class.
    
    :ivar FIXED_CENTER_FREQUENCY: Postprocess data capture at a fixed center frequency.
    :ivar SWEPT_CENTER_FREQUENCY: Postprocess data capture where the center frequency is continually sweeping
    in fixed increments.
    """
    FIXED_CENTER_FREQUENCY = "fixed_center_frequency"
    SWEPT_CENTER_FREQUENCY = "swept_center_frequency"
    
