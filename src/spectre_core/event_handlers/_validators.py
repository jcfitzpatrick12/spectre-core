# SPDX-FileCopyrightText: © 2024-2025 Jimmy Fitzpatrick <jcfitzpatrick12@gmail.com>
# This file is part of SPECTRE
# SPDX-License-Identifier: GPL-3.0-or-later


def validate_window_size(window_size: int):
    if window_size & (window_size - 1) != 0:
        raise ValueError("The window size must be a power of 2")
