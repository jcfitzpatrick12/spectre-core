# SPDX-FileCopyrightText: © 2024-2025 Jimmy Fitzpatrick <jcfitzpatrick12@gmail.com>
# This file is part of SPECTRE
# SPDX-License-Identifier: GPL-3.0-or-later

from dataclasses import dataclass
from typing import Optional
from functools import partial

from spectre_core.capture_configs import (
    CaptureTemplate,
    get_base_ptemplate,
    PName,
    OneOf,
)

from ._receiver_names import ReceiverName
from ._rspduo_gr import fixed_center_frequency, swept_center_frequency, Port
from ._receiver_names import ReceiverName
from ._gr import capture
from ._sdrplay_receiver import (
    SDRplayReceiver,
    make_capture_template_fixed_center_frequency,
    make_capture_template_swept_center_frequency,
    make_pvalidator_fixed_center_frequency,
    make_pvalidator_swept_center_frequency,
)

from .._register import register_receiver


def _make_capture_template_fixed_center_frequency(
    receiver: SDRplayReceiver,
) -> CaptureTemplate:
    """Add some RSPduo specific parameters to the general SDRplay fixed center frequency capture template."""
    capture_template = make_capture_template_fixed_center_frequency(receiver)
    capture_template.add_ptemplate(get_base_ptemplate(PName.ANTENNA_PORT))

    capture_template.set_defaults((PName.ANTENNA_PORT, Port.TUNER_1))

    capture_template.add_pconstraint(
        PName.ANTENNA_PORT, [OneOf([Port.TUNER_1, Port.TUNER_2])]
    )
    return capture_template


def _make_capture_template_swept_center_frequency(
    receiver: SDRplayReceiver,
) -> CaptureTemplate:
    """Add some RSPduo specific parameters to the general SDRplay swept center frequency capture template."""
    capture_template = make_capture_template_swept_center_frequency(receiver)
    capture_template.add_ptemplate(get_base_ptemplate(PName.ANTENNA_PORT))

    capture_template.set_defaults((PName.ANTENNA_PORT, Port.TUNER_1))

    capture_template.add_pconstraint(
        PName.ANTENNA_PORT, [OneOf([Port.TUNER_1, Port.TUNER_2])]
    )
    return capture_template


@dataclass
class _Mode:
    """An operating mode for the `RSPduo` receiver."""

    FIXED_CENTER_FREQUENCY = f"fixed_center_frequency"
    SWEPT_CENTER_FREQUENCY = f"swept_center_frequency"


@register_receiver(ReceiverName.RSPDUO)
class RSPduo(SDRplayReceiver):
    """Receiver implementation for the SDRPlay RSPduo (https://www.sdrplay.com/rspduo/)"""

    def __init__(self, name: ReceiverName, mode: Optional[str] = None) -> None:
        """Initialise an instance of an `RSPduo`."""
        super().__init__(name, mode)

        self.add_mode(
            _Mode.FIXED_CENTER_FREQUENCY,
            partial(capture, top_block_cls=fixed_center_frequency),
            _make_capture_template_fixed_center_frequency(self),
            make_pvalidator_fixed_center_frequency(self),
        )

        self.add_mode(
            _Mode.SWEPT_CENTER_FREQUENCY,
            partial(
                capture, top_block_cls=swept_center_frequency, max_noutput_items=1024
            ),
            _make_capture_template_swept_center_frequency(self),
            make_pvalidator_swept_center_frequency(self),
        )

    def get_rf_gains(self, center_frequency: float) -> list[int]:
        # Assuming high z is not enabled.
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
