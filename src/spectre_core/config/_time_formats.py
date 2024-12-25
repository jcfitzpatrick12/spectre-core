# SPDX-FileCopyrightText: © 2024 Jimmy Fitzpatrick <jcfitzpatrick12@gmail.com>
# This file is part of SPECTRE
# SPDX-License-Identifier: GPL-3.0-or-later

"""
Package-wide default datetime formats.
"""

from dataclasses import dataclass

@dataclass(frozen=True)
class TimeFormats:
    TIME     = "%H:%M:%S"
    DATE     = "%Y-%m-%d"
    DATETIME = f"{DATE}T{TIME}"