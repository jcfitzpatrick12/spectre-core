# SPDX-FileCopyrightText: © 2024 Jimmy Fitzpatrick <jcfitzpatrick12@gmail.com>
# This file is part of SPECTRE
# SPDX-License-Identifier: GPL-3.0-or-later

from enum import Enum

class CaptureModes(Enum):
    """A centralised store of capture modes.
    
    Each of `CaptureModes` has an associated base capture template, which can be fetched using: 
    
    `spectre_core.capture_configs.get_base_capture_template`
    
    All base capture templates must be registered by one of `CaptureModes`. To introduce a new
    base capture template, you need to create a new `CaptureModes` constant.
    """
    FIXED_CENTER_FREQUENCY = "fixed-center-frequency"
    SWEPT_CENTER_FREQUENCY = "swept-center-frequency"