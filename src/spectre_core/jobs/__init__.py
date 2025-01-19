# SPDX-FileCopyrightText: © 2024 Jimmy Fitzpatrick <jcfitzpatrick12@gmail.com>
# This file is part of SPECTRE
# SPDX-License-Identifier: GPL-3.0-or-later

"""A simple wrapper for multi-processing."""

from ._jobs import capture, post_process
from ._worker import (
    Worker, monitor_workers, terminate_workers, as_worker, calculate_total_runtime
)

__all__ = [
    "capture", "post_process", "Worker", "monitor_workers", "terminate_workers", "as_worker",
    "calculate_total_runtime"
]