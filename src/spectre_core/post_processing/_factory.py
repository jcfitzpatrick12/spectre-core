# SPDX-FileCopyrightText: © 2024 Jimmy Fitzpatrick <jcfitzpatrick12@gmail.com>
# This file is part of SPECTRE
# SPDX-License-Identifier: GPL-3.0-or-later

from ._register import event_handler_map
from spectre_core.post_processing._base import BaseEventHandler
from spectre_core.capture_configs import CaptureConfig, PNames
from spectre_core.exceptions import EventHandlerNotFoundError


def _get_event_handler(event_handler_key: str) -> BaseEventHandler:
    EventHandler = event_handler_map.get(event_handler_key)
    if EventHandler is None:
        valid_event_handler_keys = list(event_handler_map.keys())
        raise EventHandlerNotFoundError((f"No event handler found for the event handler key '{event_handler_key}'. "
                                         f"Please specify one of the following event handler keys: {valid_event_handler_keys}"))
    return EventHandler


def get_event_handler_from_tag(tag: str) -> BaseEventHandler:
    capture_config = CaptureConfig(tag)
    event_handler_key = capture_config.get_parameter_value(PNames.EVENT_HANDLER_KEY)
    return _get_event_handler(event_handler_key)
