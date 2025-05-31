# SPDX-FileCopyrightText: © 2024-2025 Jimmy Fitzpatrick <jcfitzpatrick12@gmail.com>
# This file is part of SPECTRE
# SPDX-License-Identifier: GPL-3.0-or-later

from enum import Enum


class ProcessType(Enum):
    """The origin of a `spectre` process.

    :ivar USER: A process is one initiated directly by the user, or part of the main user session.
    :ivar WORKER: A process is one which is created and managed internally by `spectre`.
    """

    USER = "user"
    WORKER = "worker"
