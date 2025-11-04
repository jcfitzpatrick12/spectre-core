# SPDX-FileCopyrightText: © 2024-2025 Jimmy Fitzpatrick <jcfitzpatrick12@gmail.com>
# This file is part of SPECTRE
# SPDX-License-Identifier: GPL-3.0-or-later

"""A vendor-neutral interface for capturing data from SDRs."""

from ._register import register_receiver, get_registered_receivers
from ._flowgraph import BaseFlowgraph
from ._factory import get_receiver
from ._config import Config, read_config, write_config
from ._base import BaseReceiver
from .plugins._signal_generator import SignalGenerator
from .plugins._receiver_names import ReceiverName

__all__ = [
    "register_receiver",
    "get_registered_receivers",
    "BaseFlowgraph",
    "get_receiver",
    "Config",
    "read_config",
    "write_config",
    "BaseReceiver",
    "SignalGenerator",
    "ReceiverName",
]
