# SPDX-FileCopyrightText: © 2024 Jimmy Fitzpatrick <jcfitzpatrick12@gmail.com>
# This file is part of SPECTRE
# SPDX-License-Identifier: GPL-3.0-or-later

from enum import Enum

class ProcessTypes(Enum):
    """Defines the origin of processes in `spectre`.

    USER -- Represents a process initiated directly by the user.
    WORKER -- Represents a process created internally by `spectre`.
    """
    USER   = "user"
    WORKER = "worker"