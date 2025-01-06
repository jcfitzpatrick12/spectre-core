# SPDX-FileCopyrightText: © 2024 Jimmy Fitzpatrick <jcfitzpatrick12@gmail.com>
# This file is part of SPECTRE
# SPDX-License-Identifier: GPL-3.0-or-later

from dataclasses import dataclass

@dataclass(frozen=True)
class TimeFormat:
    """Package-wide datetime formats."""
    DATE              = "%Y-%m-%d"
    TIME              = "%H:%M:%S"
    DATETIME          = f"{DATE}T{TIME}"
    PRECISE_TIME      = "%H:%M:%S.%f"
    PRECISE_DATETIME  = f"{DATE}T{PRECISE_TIME}"