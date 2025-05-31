# SPDX-FileCopyrightText: © 2024-2025 Jimmy Fitzpatrick <jcfitzpatrick12@gmail.com>
# This file is part of SPECTRE
# SPDX-License-Identifier: GPL-3.0-or-later

"""Real-time, extensible post-processing of SDR data into spectrograms."""

from .plugins._fixed_center_frequency import FixedEventHandler
from .plugins._swept_center_frequency import SweptEventHandler

from ._factory import get_event_handler, get_event_handler_cls_from_tag
from ._post_processor import start_post_processor

__all__ = [
    "FixedEventHandler",
    "SweptEventHandler",
    "start_post_processor",
    "get_event_handler",
    "get_event_handler_cls_from_tag",
]
