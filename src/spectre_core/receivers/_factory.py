# SPDX-FileCopyrightText: © 2024-2025 Jimmy Fitzpatrick <jcfitzpatrick12@gmail.com>
# This file is part of SPECTRE
# SPDX-License-Identifier: GPL-3.0-or-later

import typing

import spectre_core.exceptions

from ._register import receivers
from ._base import Base


def get_receiver(receiver_name: str, mode: typing.Optional[str] = None) -> Base:
    """Get a registered receiver.

    :param receiver_name: The name of the receiver.
    :param mode: The initial operating mode for the receiver, defaults to None
    :raises ReceiverNotFoundError: If the receiver name is not registered.
    :return: An instance of the receiver class registered under `receiver_name`.
    """
    receiver_cls = receivers.get(receiver_name)
    if receiver_cls is None:
        valid_receivers = list(receivers.keys())
        raise spectre_core.exceptions.ReceiverNotFoundError(
            f"No class found for the receiver: {receiver_name}. "
            f"Please specify one of the following receivers {valid_receivers}"
        )
    return receiver_cls(receiver_name, mode=mode)
