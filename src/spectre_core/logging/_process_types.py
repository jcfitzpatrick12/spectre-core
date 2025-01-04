# SPDX-FileCopyrightText: © 2024 Jimmy Fitzpatrick <jcfitzpatrick12@gmail.com>
# This file is part of SPECTRE
# SPDX-License-Identifier: GPL-3.0-or-later

from enum import Enum

class ProcessTypes(Enum):
    """Defines the origin of processes in `spectre`.
    
    A `USER` process is one initiated directly by the user. A `WORKER`
    process is one which is created internally by `spectre`.
    """
    USER   = "user"
    WORKER = "worker"