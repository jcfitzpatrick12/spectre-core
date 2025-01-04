# SPDX-FileCopyrightText: © 2024 Jimmy Fitzpatrick <jcfitzpatrick12@gmail.com>
# This file is part of SPECTRE
# SPDX-License-Identifier: GPL-3.0-or-later

from enum import Enum

class CaptureModes(Enum):
    """A collection of capture modes, where each corresponds to a pre-defined base capture template."""
    FIXED_CENTER_FREQUENCY = "fixed-center-frequency"
    SWEPT_CENTER_FREQUENCY = "swept-center-frequency"