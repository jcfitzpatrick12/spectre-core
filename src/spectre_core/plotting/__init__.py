# SPDX-FileCopyrightText: © 2024-2025 Jimmy Fitzpatrick <jcfitzpatrick12@gmail.com>
# This file is part of SPECTRE
# SPDX-License-Identifier: GPL-3.0-or-later

"""An intuitive API for plotting spectrogram data."""

from ._format import PanelFormat
from ._panel_names import PanelName
from ._base import BasePanel, BaseTimeSeriesPanel, XAxisType
from ._panels import (
    SpectrogramPanel,
    FrequencyCutsPanel,
    TimeCutsPanel,
    IntegralOverFrequencyPanel,
)
from ._panel_stack import PanelStack

__all__ = [
    "BaseTimeSeriesPanel",
    "PanelName",
    "XAxisType",
    "BasePanel",
    "PanelFormat",
    "PanelStack",
    "SpectrogramPanel",
    "FrequencyCutsPanel",
    "TimeCutsPanel",
    "IntegralOverFrequencyPanel",
]
