# SPDX-FileCopyrightText: © 2024-2025 Jimmy Fitzpatrick <jcfitzpatrick12@gmail.com>
# This file is part of SPECTRE
# SPDX-License-Identifier: GPL-3.0-or-later

from dataclasses import dataclass
from typing import Optional
from functools import partial

from ._receiver_names import ReceiverName
from ._sdrplay_receiver import (
    SDRplayReceiver,
    make_capture_template_fixed_center_frequency,
    make_capture_template_swept_center_frequency,
    make_pvalidator_fixed_center_frequency,
    make_pvalidator_swept_center_frequency,
)
from ._rsp1a_gr import swept_center_frequency, fixed_center_frequency
from ._receiver_names import ReceiverName
from ._gr import capture
from .._register import register_receiver


@dataclass(frozen=True)
class _Mode:
    """An operating mode for the `RSP1A` receiver."""

    FIXED_CENTER_FREQUENCY = "fixed_center_frequency"
    SWEPT_CENTER_FREQUENCY = "swept_center_frequency"


@register_receiver(ReceiverName.RSP1A)
class RSP1A(SDRplayReceiver):
    """Receiver implementation for the SDRPlay RSP1A (https://www.sdrplay.com/rsp1a/)"""

    def __init__(self, name: ReceiverName, mode: Optional[str] = None) -> None:
        """Initialise an instance of an `RSP1A`."""
        super().__init__(name, mode)

        self.add_mode(
            _Mode.FIXED_CENTER_FREQUENCY,
            partial(capture, top_block_cls=fixed_center_frequency),
            make_capture_template_fixed_center_frequency(self),
            make_pvalidator_fixed_center_frequency(self),
        )
        self.add_mode(
            _Mode.SWEPT_CENTER_FREQUENCY,
            partial(
                capture, top_block_cls=swept_center_frequency, max_noutput_items=1024
            ),
            make_capture_template_swept_center_frequency(self),
            make_pvalidator_swept_center_frequency(self),
        )

    def get_rf_gains(self, center_frequency: float) -> list[int]:
        if center_frequency <= 60e6:
            return [0, -6, -12, -18, -37, -42, -61]
        elif center_frequency <= 420e6:
            return [0, -6, -12, -18, -20, -26, -32, -38, -57, -62]
        elif center_frequency <= 1e9:
            return [0, -7, -13, -19, -20, -27, -33, -39, -45, -64]
        elif center_frequency <= 2e9:
            return [0, -6, -12, -20, -26, -32, -38, -43, -62]
        else:
            return []
