# SPDX-FileCopyrightText: © 2024 Jimmy Fitzpatrick <jcfitzpatrick12@gmail.com>
# This file is part of SPECTRE
# SPDX-License-Identifier: GPL-3.0-or-later

from typing import Optional

from spectre_core.exceptions import ReceiverNotFoundError
from ._register import receivers
from ._base import BaseReceiver

# used to fetch an instance of the receiver class
def get_receiver(receiver_name: str, mode: Optional[str] = None) -> BaseReceiver:
    Receiver = receivers.get(receiver_name)
    if Receiver is None:
        valid_receivers = list(receivers.keys())
        raise ReceiverNotFoundError(f"No class found for the receiver: {receiver_name}. "
                                    f"Please specify one of the following receivers {valid_receivers}")
    return Receiver(receiver_name, 
                    mode = mode)
