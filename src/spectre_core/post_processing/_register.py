# SPDX-FileCopyrightText: © 2024-2025 Jimmy Fitzpatrick <jcfitzpatrick12@gmail.com>
# This file is part of SPECTRE
# SPDX-License-Identifier: GPL-3.0-or-later

from typing import Type, Callable, TypeVar

from .plugins._event_handler_keys import EventHandlerKey
from ._base import BaseEventHandler

# Map populated at runtime via the `register_event_handler` decorator.
event_handler_map: dict[EventHandlerKey, Type[BaseEventHandler]] = {}

T = TypeVar("T", bound=BaseEventHandler)


def register_event_handler(
    event_handler_key: EventHandlerKey,
) -> Callable[[Type[T]], Type[T]]:
    """Decorator to register a `BaseEventHandler` subclass under a specified `EventHandlerKey`.

    :param event_handler_key: The key to register the `BaseEventHandler` subclass.
    :raises ValueError: If the provided `event_handler_key` is already registered.
    :return: A decorator that registers the `BaseBatch` subclass under the given `batch_key`.
    """

    def decorator(cls: Type[T]) -> Type[T]:
        if event_handler_key in event_handler_map:
            raise ValueError(
                f"An event handler with key '{event_handler_key}' is already registered!"
            )
        event_handler_map[event_handler_key] = cls
        return cls

    return decorator
