# SPDX-FileCopyrightText: © 2024 Jimmy Fitzpatrick <jcfitzpatrick12@gmail.com>
# This file is part of SPECTRE
# SPDX-License-Identifier: GPL-3.0-or-later

"""
Package-wide default datetime formats.
"""

DEFAULT_TIME_FORMAT = "%H:%M:%S"
DEFAULT_DATE_FORMAT = "%Y-%m-%d"
DEFAULT_DATETIME_FORMAT = f"{DEFAULT_DATE_FORMAT}T{DEFAULT_TIME_FORMAT}"