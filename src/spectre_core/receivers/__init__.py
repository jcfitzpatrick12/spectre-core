# SPDX-FileCopyrightText: © 2024-2025 Jimmy Fitzpatrick <jcfitzpatrick12@gmail.com>
# This file is part of SPECTRE
# SPDX-License-Identifier: GPL-3.0-or-later

"""A vendor-neutral interface for capturing data from SDRs."""

from .plugins._receiver_names import ReceiverName
from .plugins._signal_generator import SignalGenerator
from .plugins._rsp1a import RSP1A
from .plugins._rspduo import RSPduo
from .plugins._b200mini import B200mini

from ._receiver import Receiver, ReceiverComponents
from ._specs import SpecName, Specs
from ._factory import get_receiver
from ._register import get_registered_receivers

__all__ = [
    "Receiver",
    "ReceiverComponents",
    "Specs",
    "SpecName",
    "ReceiverName",
    "SignalGenerator",
    "RSP1A",
    "RSPduo",
    "B200mini",
    "Custom",
    "get_receiver",
    "get_registered_receivers",
]
