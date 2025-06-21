# SPDX-FileCopyrightText: © 2024-2025 Jimmy Fitzpatrick <jcfitzpatrick12@gmail.com>
# This file is part of SPECTRE
# SPDX-License-Identifier: GPL-3.0-or-later

"""An intuitive API for plotting spectrogram data."""

from ._format import PanelFormat
from ._base import BasePanel, XAxisType
from ._panels import (
    SpectrogramPanel,
    FrequencyCutsPanel,
    TimeCutsPanel,
    IntegralOverFrequencyPanel,
)
from ._panel_stack import PanelStack

__all__ = [
    "XAxisType",
    "BasePanel",
    "PanelFormat",
    "PanelStack",
    "SpectrogramPanel",
    "FrequencyCutsPanel",
    "TimeCutsPanel",
    "IntegralOverFrequencyPanel",
]
