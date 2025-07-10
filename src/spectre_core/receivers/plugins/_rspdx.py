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
from ._rspdx_gr import fixed_center_frequency, swept_center_frequency, Port
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
    """Add some RSPdx specific parameters to the general SDRplay fixed center frequency capture template."""
    capture_template = make_capture_template_fixed_center_frequency(receiver)
    capture_template.add_ptemplate(get_base_ptemplate(PName.ANTENNA_PORT))

    capture_template.set_defaults((PName.ANTENNA_PORT, Port.ANT_A))

    capture_template.add_pconstraint(
        PName.ANTENNA_PORT, [OneOf([Port.ANT_A, Port.ANT_B])]
    )
    return capture_template


def _make_capture_template_swept_center_frequency(
    receiver: SDRplayReceiver,
) -> CaptureTemplate:
    """Add some RSPdx specific parameters to the general SDRplay swept center frequency capture template."""
    capture_template = make_capture_template_swept_center_frequency(receiver)
    capture_template.add_ptemplate(get_base_ptemplate(PName.ANTENNA_PORT))

    capture_template.set_defaults((PName.ANTENNA_PORT, Port.ANT_A))

    capture_template.add_pconstraint(
        PName.ANTENNA_PORT, [OneOf([Port.ANT_A, Port.ANT_B])]
    )
    return capture_template


@dataclass
class _Mode:
    """An operating mode for the `RSPdx` receiver."""

    FIXED_CENTER_FREQUENCY = f"fixed_center_frequency"
    SWEPT_CENTER_FREQUENCY = f"swept_center_frequency"


@register_receiver(ReceiverName.RSPDX)
class RSPdx(SDRplayReceiver):
    """Receiver implementation for the SDRPlay RSPdx (https://www.sdrplay.com/rspdx/)"""

    def __init__(self, name: ReceiverName, mode: Optional[str] = None) -> None:
        """Initialise an instance of an `RSPdx`."""
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
        # Assume HDR mode is false.
        # Some nasty black formatting, but we move.
        if center_frequency <= 12e6:
            return [
                0,
                -3,
                -6,
                -9,
                -12,
                -15,
                -24,
                -27,
                -30,
                -33,
                -36,
                -39,
                -42,
                -45,
                -48,
                -51,
                -54,
                -57,
                -60,
            ]
        elif center_frequency <= 50e6:
            return [
                0,
                -3,
                -6,
                -9,
                -12,
                -15,
                -18,
                -24,
                -27,
                -30,
                -33,
                -36,
                -39,
                -42,
                -45,
                -48,
                -51,
                -54,
                -57,
                -60,
            ]
        elif center_frequency <= 60e6:
            return [
                0,
                -3,
                -6,
                -9,
                -12,
                -20,
                -23,
                -26,
                -29,
                -32,
                -35,
                -38,
                -44,
                -47,
                -50,
                -53,
                -56,
                -59,
                -62,
                -65,
                -68,
                -71,
                -74,
                -77,
                -80,
            ]
        elif center_frequency <= 250e6:
            return [
                0,
                -3,
                -6,
                -9,
                -12,
                -15,
                -24,
                -27,
                -30,
                -33,
                -36,
                -39,
                -42,
                -45,
                -48,
                -51,
                -54,
                -57,
                -60,
                -63,
                -66,
                -69,
                -72,
                -75,
                -78,
                -81,
                -84,
            ]
        elif center_frequency <= 420e6:
            return [
                0,
                -3,
                -6,
                -9,
                -12,
                -15,
                -18,
                -24,
                -27,
                -30,
                -33,
                -36,
                -39,
                -42,
                -45,
                -48,
                -51,
                -54,
                -57,
                -60,
                -63,
                -66,
                -69,
                -72,
                -75,
                -78,
                -81,
                -84,
            ]
        elif center_frequency <= 1000e6:
            return [
                0,
                -7,
                -10,
                -13,
                -16,
                -19,
                -22,
                -25,
                -31,
                -34,
                -37,
                -40,
                -43,
                -46,
                -49,
                -52,
                -55,
                -58,
                -61,
                -64,
                -67,
            ]
        elif center_frequency <= 2000e6:
            return [
                0,
                -5,
                -8,
                -11,
                -14,
                -17,
                -20,
                -32,
                -35,
                -38,
                -41,
                -44,
                -47,
                -50,
                -53,
                -56,
                -59,
                -62,
                -65,
            ]
        else:
            return []
