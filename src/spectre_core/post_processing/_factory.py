# SPDX-FileCopyrightText: © 2024-2025 Jimmy Fitzpatrick <jcfitzpatrick12@gmail.com>
# This file is part of SPECTRE
# SPDX-License-Identifier: GPL-3.0-or-later

from typing import Type, cast

from spectre_core.post_processing._base import BaseEventHandler
from spectre_core.capture_configs import CaptureConfig, PName
from spectre_core.exceptions import EventHandlerNotFoundError
from .plugins._event_handler_keys import EventHandlerKey
from ._register import event_handler_map


def _get_event_handler_cls_from_key(
    event_handler_key: EventHandlerKey,
) -> Type[BaseEventHandler]:
    """Get a registered `BaseEventHandler` subclass.

    :param event_handler_key: The key used to register the `BaseEventHandler` subclass.
    :raises EventHandlerNotFoundError: If an invalid `event_handler_key` is provided.
    :return: The `BaseEventHandler` subclass registered under `event_handler_key`.
    """
    event_handler_cls = event_handler_map.get(event_handler_key)
    if event_handler_cls is None:
        event_handler_keys = list(event_handler_map.keys())
        raise EventHandlerNotFoundError(
            (
                f"No event handler found for the capture mode '{event_handler_key}'. "
                f"Please specify one of the following capture modes: {event_handler_keys}"
            )
        )
    return event_handler_cls


def get_event_handler_cls_from_tag(tag: str) -> Type[BaseEventHandler]:
    """
    Retrieve the event handler class, using the event handler key stored in a capture config.

    :param tag: The capture config tag.
    :return: The event handler class specified in the capture config.
    """
    capture_config = CaptureConfig(tag)
    event_handler_key = cast(
        str, capture_config.get_parameter_value(PName.EVENT_HANDLER_KEY)
    )
    return _get_event_handler_cls_from_key(EventHandlerKey(event_handler_key))


def get_event_handler(tag: str) -> BaseEventHandler:
    """Create an event handler class instance, using the event handler key stored in a capture config.

    :param tag: The capture config tag.
    :return: An instance of the event handler class.
    """
    event_handler_cls = get_event_handler_cls_from_tag(tag)
    return event_handler_cls(tag)
