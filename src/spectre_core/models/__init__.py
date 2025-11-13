# SPDX-FileCopyrightText: © 2024-2025 Jimmy Fitzpatrick <jcfitzpatrick12@gmail.com>
# This file is part of SPECTRE
# SPDX-License-Identifier: GPL-3.0-or-later


"""Templatise configurable parameters."""

from ._signal_generator import (
    SignalGeneratorCosineWaveModel,
    SignalGeneratorConstantStaircaseModel,
)
from ._rsp1a import RSP1AFixedCenterFrequency, RSP1ASweptCenterFrequency
from ._rspduo import RSPduoFixedCenterFrequency, RSPduoSweptCenterFrequency
from ._rspdx import RSPdxFixedCenterFrequency, RSPdxSweptCenterFrequency
from ._usrp import USRPFixedCenterFrequency, USRPSweptCenterFrequency
from ._b200mini import B200miniFixedCenterFrequency, B200miniSweptCenterFrequency
from ._hackrf import HackRFFixedCenterFrequency
from ._hackrfone import HackRFOneFixedCenterFrequency
from ._rtlsdr import RTLSDRFixedCenterFrequency

__all__ = [
    "SignalGeneratorCosineWaveModel",
    "SignalGeneratorConstantStaircaseModel",
    "RSP1AFixedCenterFrequency",
    "RSP1ASweptCenterFrequency",
    "RSPduoFixedCenterFrequency",
    "RSPduoSweptCenterFrequency",
    "RSPdxFixedCenterFrequency",
    "RSPdxSweptCenterFrequency",
    "USRPFixedCenterFrequency",
    "USRPSweptCenterFrequency",
    "B200miniFixedCenterFrequency",
    "B200miniSweptCenterFrequency",
    "HackRFFixedCenterFrequency",
    "HackRFOneFixedCenterFrequency",
    "RTLSDRFixedCenterFrequency",
]
