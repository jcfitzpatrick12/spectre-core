# SPDX-FileCopyrightText: © 2024-2025 Jimmy Fitzpatrick <jcfitzpatrick12@gmail.com>
# This file is part of SPECTRE
# SPDX-License-Identifier: GPL-3.0-or-later

"""A vendor-neutral interface for recording signals and spectrograms from SDRs."""

from ._register import register_receiver, get_registered_receivers
from ._factory import get_receiver
from ._config import Config, read_config, write_config
from ._base import Base
from ._names import ReceiverName
from ._signal_generator import SignalGenerator
from ._record import record_signal, record_spectrograms

__all__ = [
    "register_receiver",
    "get_registered_receivers",
    "get_receiver",
    "ReceiverName",
    "Config",
    "read_config",
    "write_config",
    "Base",
    "SignalGenerator",
    "ReceiverName",
    "record_signal",
    "record_spectrograms",
]
