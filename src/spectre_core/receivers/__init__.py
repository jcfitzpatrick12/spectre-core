# SPDX-FileCopyrightText: © 2024-2025 Jimmy Fitzpatrick <jcfitzpatrick12@gmail.com>
# This file is part of SPECTRE
# SPDX-License-Identifier: GPL-3.0-or-later

"""A vendor-neutral interface for collecting data from SDRs."""

from .plugins._receiver_names import ReceiverName
from .plugins._rsp1a import RSP1A

# from .plugins._rspduo import RSPduo
# from .plugins._b200mini import B200mini
# from .plugins._test import Test

from ._receiver import Receiver, SpecName
from ._factory import get_receiver
from ._register import get_registered_receivers

__all__ = [
    "Test",
    "RSP1A",
    "RSPduo",
    "B200mini",
    "Receiver",
    "get_receiver",
    "get_registered_receivers",
    "SpecName",
    "ReceiverName",
]
