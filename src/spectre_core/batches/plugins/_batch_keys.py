# SPDX-FileCopyrightText: © 2024 Jimmy Fitzpatrick <jcfitzpatrick12@gmail.com>
# This file is part of SPECTRE
# SPDX-License-Identifier: GPL-3.0-or-later

from enum import Enum

class BatchKeys(Enum):  
    """Keys bound to `Batch` plugin classes."""
    IQ_STREAM  = "iq-stream"
    CALLISTO   = "callisto"
    
