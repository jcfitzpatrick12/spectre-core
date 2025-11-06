# SPDX-FileCopyrightText: © 2024-2025 Jimmy Fitzpatrick <jcfitzpatrick12@gmail.com>
# This file is part of SPECTRE
# SPDX-License-Identifier: GPL-3.0-or-later

import dataclasses


@dataclasses.dataclass(frozen=True)
class ReceiverName:
    """The name of a supported receiver.

    :ivar SIGNAL_GENERATOR: A synthetic signal generator.
    """

    SIGNAL_GENERATOR = "signal_generator"
