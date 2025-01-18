# SPDX-FileCopyrightText: © 2024 Jimmy Fitzpatrick <jcfitzpatrick12@gmail.com>
# This file is part of SPECTRE
# SPDX-License-Identifier: GPL-3.0-or-later

"""An intuitive API for plotting spectrogram data."""

from ._format import PanelFormat
from ._panels import SpectrogramPanel, FrequencyCutsPanel, TimeCutsPanel, IntegralOverFrequencyPanel
from ._panel_stack import PanelStack

__all__ = [
    "PanelFormat", "PanelStack", "SpectrogramPanel", "FrequencyCutsPanel", "TimeCutsPanel", "IntegralOverFrequencyPanel"
]