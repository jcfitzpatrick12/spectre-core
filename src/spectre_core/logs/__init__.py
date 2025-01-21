# SPDX-FileCopyrightText: © 2024 Jimmy Fitzpatrick <jcfitzpatrick12@gmail.com>
# This file is part of SPECTRE
# SPDX-License-Identifier: GPL-3.0-or-later


"""`spectre` logging configurations."""

from ._process_types import ProcessType
from ._decorators import log_call
from ._configure import configure_root_logger, get_root_logger_state
from ._logs import Log, Logs


__all__ = [
    "log_call", "configure_root_logger", "Log", "Logs", "ProcessType",
    "get_root_logger_state"
]