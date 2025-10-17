# SPDX-FileCopyrightText: © 2024-2025 Jimmy Fitzpatrick <jcfitzpatrick12@gmail.com>
# This file is part of SPECTRE
# SPDX-License-Identifier: GPL-3.0-or-later

from dataclasses import dataclass
from functools import partial
from typing import Callable, Optional

from spectre_core.capture_configs import (
    CaptureTemplate,
    CaptureMode,
    Parameters,
    PName,
    validate_window,
    get_base_capture_template,
    get_base_ptemplate,
)

from ._receiver_names import ReceiverName
from ._gr import capture
from ._rtlsdr_gr import fixed_center_frequency
from .._receiver import Receiver
from .._register import register_receiver


def _make_pvalidator_fixed_center_frequency(
    receiver: Receiver,
) -> Callable[[Parameters], None]:
    def pvalidator(parameters: Parameters) -> None:
        validate_window(parameters)

    return pvalidator


def _make_capture_template_fixed_center_frequency(
    receiver: Receiver,
) -> CaptureTemplate:

    capture_template = get_base_capture_template(CaptureMode.FIXED_CENTER_FREQUENCY)
    capture_template.add_ptemplate(get_base_ptemplate(PName.RF_GAIN))

    capture_template.set_defaults(
        (PName.BATCH_SIZE, 3.0),
        (PName.CENTER_FREQUENCY, 95800000),
        (PName.SAMPLE_RATE, 1.536e6),
        (PName.WINDOW_HOP, 1024),
        (PName.WINDOW_SIZE, 2048),
        (PName.WINDOW_TYPE, "blackman"),
        (PName.RF_GAIN, 30),
    )

    return capture_template


@dataclass(frozen=True)
class _Mode:
    """An operating mode for the `HackRF One` receiver."""

    FIXED_CENTER_FREQUENCY = "fixed_center_frequency"


@register_receiver(ReceiverName.RTLSDR)
class RTLSDR(Receiver):
    """Receiver implementation for the RTL-SDR (https://www.rtl-sdr.com/about-rtl-sdr/)"""

    def __init__(self, name: ReceiverName, mode: Optional[str] = None) -> None:
        super().__init__(name, mode)

        # TODO: Implement more safeguards according to hardware constraints. See https://github.com/jcfitzpatrick12/spectre/issues/186
        self.add_mode(
            _Mode.FIXED_CENTER_FREQUENCY,
            partial(capture, top_block_cls=fixed_center_frequency),
            _make_capture_template_fixed_center_frequency(self),
            _make_pvalidator_fixed_center_frequency(self),
        )
