# SPDX-FileCopyrightText: © 2024-2025 Jimmy Fitzpatrick <jcfitzpatrick12@gmail.com>
# This file is part of SPECTRE
# SPDX-License-Identifier: GPL-3.0-or-later


"""General `spectre` package configurations."""

import os

from ._paths import (
    get_spectre_data_dir_path,
    get_batches_dir_path,
    get_configs_dir_path,
    get_logs_dir_path,
    trim_spectre_data_dir_path,
)
from ._time_formats import TimeFormat

os.makedirs(get_batches_dir_path(), exist_ok=True)
os.makedirs(get_logs_dir_path(), exist_ok=True)
os.makedirs(get_configs_dir_path(), exist_ok=True)

__all__ = [
    "get_spectre_data_dir_path",
    "get_batches_dir_path",
    "get_configs_dir_path",
    "get_logs_dir_path",
    "TimeFormat",
    "trim_spectre_data_dir_path",
]
