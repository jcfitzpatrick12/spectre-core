# SPDX-FileCopyrightText: © 2024 Jimmy Fitzpatrick <jcfitzpatrick12@gmail.com>
# This file is part of SPECTRE
# SPDX-License-Identifier: GPL-3.0-or-later

from typing import Optional, overload, Literal, TypeVar

from spectre_core.exceptions import ReceiverNotFoundError
from ._register import receivers
from ._base import BaseReceiver
from .plugins._receiver_names import ReceiverName
from .plugins._rsp1a import RSP1A
from .plugins._rspduo import RSPduo
from .plugins._test import Test
from .plugins._b200mini import B200mini


@overload
def get_receiver(
    receiver_name: Literal[ReceiverName.RSP1A],
    mode: Optional[str] = None
) -> RSP1A:
    ...
    
    
@overload
def get_receiver(
    receiver_name: Literal[ReceiverName.RSPDUO],
    mode: Optional[str] = None
) -> RSPduo:
    ...
    
    
@overload
def get_receiver(
    receiver_name: Literal[ReceiverName.TEST],
    mode: Optional[str] = None
) -> Test:
    ...


@overload
def get_receiver(
    receiver_name: Literal[ReceiverName.B200MINI],
    mode: Optional[str] = None
) -> B200mini:
    ...


@overload
def get_receiver(
    receiver_name: ReceiverName,
    mode: Optional[str] = None
) -> BaseReceiver:
    ...


def get_receiver(
    receiver_name: ReceiverName, 
    mode: Optional[str] = None
) -> BaseReceiver:
    """Get a registered receiver.

    :param receiver_name: The name of the receiver.
    :param mode: The initial operating mode for the receiver, defaults to None
    :raises ReceiverNotFoundError: If the receiver name is not registered.
    :return: An instance of the receiver class registered under `receiver_name`.
    """
    receiver_cls = receivers.get(receiver_name)
    if receiver_cls is None:
        valid_receivers = list(receivers.keys())
        raise ReceiverNotFoundError(f"No class found for the receiver: {receiver_name}. "
                                    f"Please specify one of the following receivers {valid_receivers}")
    return receiver_cls(receiver_name, 
                        mode = mode)
