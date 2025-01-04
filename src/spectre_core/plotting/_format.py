# SPDX-FileCopyrightText: © 2024 Jimmy Fitzpatrick <jcfitzpatrick12@gmail.com>
# This file is part of SPECTRE
# SPDX-License-Identifier: GPL-3.0-or-later

from dataclasses import dataclass

@dataclass
class PanelFormat:
    """Specifies formatting options for a panel, including font sizes, line styles, 
    colour maps, and general visual settings.

    These formatting values can be applied consistently across all panels within a `PanelStack`,
    but are optional.

    :param small_size: Font size for small text elements, defaults to 18.
    :param medium_size: Font size for medium text elements, defaults to 21.
    :param large_size: Font size for large text elements, defaults to 24.
    :param line_width: Thickness of lines in the plot, defaults to 3.
    :param line_color: Colour used for line elements, defaults to "lime".
    :param line_cmap: Colormap applied to line-based visual elements, defaults to "winter".
    :param style: Matplotlib style applied to the panel, defaults to "dark_background".
    """
    small_size      : int = 18
    medium_size     : int = 21
    large_size      : int = 24
    line_width      : int = 3
    line_color      : str = "lime"
    line_cmap       : str = "winter"
    style           : str = "dark_background"
    spectrogram_cmap: str = "gnuplot2"
