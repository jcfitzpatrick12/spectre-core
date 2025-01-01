# SPDX-FileCopyrightText: © 2024 Jimmy Fitzpatrick <jcfitzpatrick12@gmail.com>
# This file is part of SPECTRE
# SPDX-License-Identifier: GPL-3.0-or-later

"""
Package-wide default datetime formats.
"""

from dataclasses import dataclass

@dataclass(frozen=True)
class TimeFormats:
    DATE             = "%Y-%m-%d"
    TIME             = "%H:%M:%S"
    PRECISE_TIME     = "%H:%M:%S.%f"
    DATETIME         = f"{DATE}T{TIME}"
    PRECISE_DATETIME = f"{DATE}T{PRECISE_TIME}"