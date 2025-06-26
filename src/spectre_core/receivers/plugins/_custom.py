# SPDX-FileCopyrightText: © 2024-2025 Jimmy Fitzpatrick <jcfitzpatrick12@gmail.com>
# This file is part of SPECTRE
# SPDX-License-Identifier: GPL-3.0-or-later

from typing import Optional

from ._receiver_names import ReceiverName
from .._register import register_receiver
from .._receiver import Receiver


@register_receiver(ReceiverName.CUSTOM)
class CustomReceiver(Receiver):
    """A receiver which starts with no operating modes.

    Customise by adding modes using the `add_mode` method.
    """

    def __init__(self, name: ReceiverName, mode: Optional[str] = None) -> None:
        super().__init__(name, mode)
