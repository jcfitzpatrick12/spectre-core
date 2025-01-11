# SPDX-FileCopyrightText: © 2024 Jimmy Fitzpatrick <jcfitzpatrick12@gmail.com>
# This file is part of SPECTRE
# SPDX-License-Identifier: GPL-3.0-or-later

from dataclasses import dataclass


@dataclass(frozen=True)
class TimeFormat:
    """Package-wide datetime formats.

    :ivar DATE: Format for dates (e.g., '2025-01-11').
    :ivar TIME: Format for times (e.g., '23:59:59').
    :ivar DATETIME: Combined date and time format (e.g., '2025-01-11T23:59:59').
    :ivar PRECISE_TIME: Format for times with microseconds (e.g., '23:59:59.123456').
    :ivar PRECISE_DATETIME: Combined date and precise time format (e.g., '2025-01-11T23:59:59.123456').
    """
    DATE              = "%Y-%m-%d"
    TIME              = "%H:%M:%S"
    DATETIME          = f"{DATE}T{TIME}"
    PRECISE_TIME      = "%H:%M:%S.%f"
    PRECISE_DATETIME  = f"{DATE}T{PRECISE_TIME}"