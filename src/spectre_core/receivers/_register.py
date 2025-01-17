# SPDX-FileCopyrightText: © 2024 Jimmy Fitzpatrick <jcfitzpatrick12@gmail.com>
# This file is part of SPECTRE
# SPDX-License-Identifier: GPL-3.0-or-later

from typing import TypeVar, Callable, Type

from .plugins._receiver_names import ReceiverName
from ._base import BaseReceiver

# map populated at runtime via the `register_receiver` decorator.
receivers: dict[ReceiverName, Type[BaseReceiver]] = {}

T = TypeVar('T', bound=BaseReceiver)
def register_receiver(
    receiver_name: ReceiverName,
) -> Callable[[Type[T]], Type[T]]:
    """Decorator to register a fully implemented `BaseReceiver` subclass under a specified `receiver_name`.

    :param receiver_name: The name of the receiver.
    :raises ValueError: If the provided `receiver_name` is already registered.
    :return: A decorator that registers the `BaseReceiver` subclass under the given `receiver_name`.
    """
    def decorator(
        cls: Type[T]
    ) -> Type[T]:
        if receiver_name in receivers:
            raise ValueError(f"The receiver '{receiver_name}' is already registered!")
        receivers[receiver_name] = cls
        return cls
    return decorator


def get_registered_receivers(
) -> list[str]:
    """List all registered receivers.

    :return: The string values of all registered `ReceiverName` enum keys.
    """
    return [k.value for k in receivers.keys()]




