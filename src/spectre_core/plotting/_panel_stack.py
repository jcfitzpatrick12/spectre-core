# SPDX-FileCopyrightText: © 2024 Jimmy Fitzpatrick <jcfitzpatrick12@gmail.com>
# This file is part of SPECTRE
# SPDX-License-Identifier: GPL-3.0-or-later

import numpy as np
import numpy.typing as npt
from typing import Optional, Tuple, cast
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.axes import Axes

from spectre_core.spectrograms import TimeType
from ._base import BasePanel, XAxisType
from ._format import PanelFormat
from ._panels import PanelName, SpectrogramPanel, TimeCutsPanel, FrequencyCutsPanel


def _is_cuts_panel(
    panel: BasePanel
) -> bool:
    """Check if a panel contains spectrogram cuts.

    :param panel: The panel to check.
    :return: True if the panel is a frequency or time cuts panel, otherwise False.
    """
    return panel.name in {PanelName.FREQUENCY_CUTS, PanelName.TIME_CUTS}


def _is_spectrogram_panel(
    panel: BasePanel
) -> bool:
    """Check if a panel is a spectrogram panel.

    :param panel: The panel to check.
    :return: True if the panel is a spectrogram panel, otherwise False.
    """
    return panel.name == PanelName.SPECTROGRAM


class PanelStack:
    """Visualise spectrogram data in a stack of panels."""
    def __init__(
        self, 
        panel_format: PanelFormat = PanelFormat(),
        time_type: TimeType = TimeType.RELATIVE,
        figsize: Tuple[int, int] = (10, 10)
    ) -> None:
        """Initialize an instance of `PanelStack`.

        :param panel_format: Formatting applied across all panels in the stack. Defaults to `PanelFormat()`.
        :param time_type: The type of time assigned to spectrograms, defaults to `TimeType.RELATIVE`.
        :param figsize: The size of the `matplotlib` figure as (width, height). Defaults to (10, 10).
        """
        self._panel_format = panel_format
        self._time_type = time_type
        self._figsize = figsize

        self._panels             : list[BasePanel] = []
        self._superimposed_panels: list[BasePanel] = []
        
        self._fig: Optional[Figure] = None
        self._axs: Optional[np.ndarray] = None


    @property
    def time_type(
        self
    ) -> TimeType:
        """The type of time we assign to the spectrograms"""
        return self._time_type


    @property
    def panels(
        self
    ) -> list[BasePanel]:
        """Get the panels in the stack, sorted by their `XAxisType`."""
        return list(sorted(self._panels, key=lambda panel: panel.xaxis_type.value))


    @property
    def fig(
        self
    ) -> Figure:
        """Get the shared `matplotlib` figure for the panel stack.

        :raises ValueError: If the axes have not been initialized.
        """
        if self._fig is None:
            raise ValueError(f"An unexpected error has occured, `fig` must be set for the panel stack.")
        return self._fig


    @property
    def axs(
        self
    ) -> np.ndarray:
        """Get the `matplotlib` axes in the stack.

        :return: An array of `matplotlib.axes.Axes`, one for each panel in the stack.
        :raises ValueError: If the axes have not been initialized.
        """
        if self._axs is None:
            raise ValueError(f"An unexpected error has occured, `axs` must be set for the panel stack.")
        return np.atleast_1d(self._axs)


    @property
    def num_panels(
        self
    ) -> int:
        """Get the number of panels in the stack."""
        return len(self._panels)


    def add_panel(
        self, 
        panel: BasePanel,
        identifier: Optional[str] = None
    ) -> None:
        """Add a panel to the stack.

        :param panel: An instance of a `BasePanel` subclass to be added to the stack.
        :param identifier: An optional string to link the panel with others for superimposing.
        """
        panel.panel_format = self._panel_format
        panel.time_type    = self._time_type
        if identifier: 
            panel.identifier = identifier
        self._panels.append(panel)


    def superimpose_panel(
        self, 
        panel: BasePanel,
        identifier: Optional[str] = None
    ) -> None:
        """Superimpose a panel onto an existing panel in the stack.

        :param panel: The panel to superimpose.
        :param identifier: An optional identifier to link panels during superimposing, defaults to None
        """
        if identifier:
            panel.identifier = identifier
        panel.panel_format = self._panel_format
        self._superimposed_panels.append(panel)


    def _init_plot_style(
        self
    ) -> None:
        """Initialize the global plot style for the stack.

        This method sets `matplotlib` styles and font sizes based on the `panel_format`.
        """
        plt.style.use(self._panel_format.style)
        
        plt.rc('font', size=self._panel_format.small_size)
        
        plt.rc('axes', titlesize=self._panel_format.medium_size, 
                       labelsize=self._panel_format.medium_size)
        
        plt.rc('xtick', labelsize=self._panel_format.small_size)
        plt.rc('ytick', labelsize=self._panel_format.small_size)
        
        plt.rc('legend', fontsize=self._panel_format.small_size)
        plt.rc('figure', titlesize=self._panel_format.large_size)


    def _create_figure_and_axes(
        self
    ) -> None:
        """Create the `matplotlib` figure and axes for the panel stack.

        This initializes a figure with a specified number of vertically stacked axes.
        """
        self._fig, self._axs = plt.subplots(self.num_panels, 
                                            1, 
                                            figsize=self._figsize, 
                                            layout="constrained")


    def _assign_axes(
        self
    ) -> None:
        """Assign each axes in the figure to some panel in the stack.
        
        Axes are shared between panels with common `xaxis_type`.
        """
        shared_axes: dict[XAxisType, Axes] = {}
        for i, panel in enumerate(self.panels):
            panel.ax = self.axs[i]
            panel.fig = self._fig
            if panel.xaxis_type in shared_axes:
                panel.ax.sharex( shared_axes[panel.xaxis_type] )
            else:
                shared_axes[panel.xaxis_type] = panel.ax


    def _overlay_cuts(
        self, 
        cuts_panel: BasePanel
    ) -> None:
        """Overlay cuts onto corresponding spectrogram panels.

        For a given cuts panel, locate any spectrogram panels in the stack with a matching tag
        and add the appropriate frequency or time cuts overlay.

        :param cuts_panel: A panel containing frequency or time cuts.
        """
        for panel in self.panels:
            if _is_spectrogram_panel(panel) and panel.tag == cuts_panel.tag:
                panel = cast(SpectrogramPanel, panel)
                if cuts_panel.name == PanelName.FREQUENCY_CUTS:
                    panel.overlay_frequency_cuts( cast(FrequencyCutsPanel, cuts_panel) )
                elif cuts_panel.name == PanelName.TIME_CUTS:
                    panel.overlay_time_cuts( cast(TimeCutsPanel, cuts_panel) )


    def _overlay_superimposed_panels(
        self
    ) -> None:
        """Superimpose panels onto matching panels in the stack.

        For each superimposed panel, find a matching panel in the stack with the same name 
        and identifier. Share the axes and figure, then draw the superimposed panel. If the 
        panel contains cuts, overlay those cuts onto the corresponding spectrogram panels.
        """
        for super_panel in self._superimposed_panels:
            for panel in self._panels:
                if panel.name == super_panel.name and (panel.identifier == super_panel.identifier):
                    super_panel.ax, super_panel.fig = panel.ax, self._fig
                    super_panel.draw()
                    if _is_cuts_panel(super_panel):
                        self._overlay_cuts(super_panel)


    def show(
        self
    ) -> None:
        """Display the panel stack figure."""
        self._init_plot_style()
        self._create_figure_and_axes()
        self._assign_axes()
        
        last_panel_per_axis = {panel.xaxis_type: panel for panel in self.panels}
        
        for panel in self.panels:
            panel.draw()
            panel.annotate_yaxis()
            
            if panel == last_panel_per_axis[panel.xaxis_type]:
                panel.annotate_xaxis()
            else:
                panel.hide_xaxis_labels()
                
            if _is_cuts_panel(panel):
                self._overlay_cuts(panel)
                
        self._overlay_superimposed_panels()
        plt.show()
