# SPDX-FileCopyrightText: © 2024 Jimmy Fitzpatrick <jcfitzpatrick12@gmail.com>
# This file is part of SPECTRE
# SPDX-License-Identifier: GPL-3.0-or-later

import numpy as np
from typing import Optional, Tuple
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.axes import Axes

from spectre_core.spectrograms import TimeTypes
from ._base import BasePanel
from ._format import PanelFormat, DEFAULT_FORMAT
from ._panels import PanelNames


def _is_cuts_panel(panel: BasePanel) -> bool:
    return (panel.name == PanelNames.FREQUENCY_CUTS or panel.name == PanelNames.TIME_CUTS)


def _is_spectrogram_panel(panel: BasePanel) -> bool:
    return (panel.name == PanelNames.SPECTROGRAM)


class PanelStack:
    def __init__(self, 
                 panel_format: PanelFormat = DEFAULT_FORMAT,
                 time_type: str = TimeTypes.SECONDS,
                 figsize: Tuple[int, int] = (10, 10)):
        self._panel_format = panel_format
        self._time_type = time_type
        self._figsize = figsize

        self._panels: list[BasePanel] = []
        self._superimposed_panels: list[BasePanel] = []
        self._fig: Optional[Figure] = None
        self._axs: Optional[np.ndarray[Axes]] = None


    @property
    def time_type(self) -> str:
        return self._time_type


    @property
    def panels(self) -> list[BasePanel]:
        return sorted(self._panels, key=lambda panel: panel.x_axis_type)


    @property
    def fig(self) -> Optional[Figure]:
        return self._fig


    @property
    def axs(self) -> Optional[np.ndarray[Axes]]:
        return np.atleast_1d(self._axs)


    @property
    def num_panels(self) -> int:
        return len(self._panels)


    def add_panel(self, 
                  panel: BasePanel,
                  identifier: Optional[str] = None) -> None:
        panel.panel_format = self._panel_format
        panel.time_type    = self._time_type
        if identifier: 
            panel.identifier = identifier
        self._panels.append(panel)


    def superimpose_panel(self, 
                          panel: BasePanel,
                          identifier: Optional[str] = None) -> None:
        if identifier:
            panel.identifier = identifier
        panel.panel_format = self._panel_format
        self._superimposed_panels.append(panel)


    def _init_plot_style(self) -> None:
        plt.style.use(self._panel_format.style)

        plt.rc('font'  , size=self._panel_format.small_size)
        plt.rc('axes'  , titlesize=self._panel_format.medium_size, 
                         labelsize=self._panel_format.medium_size)
        plt.rc('xtick' , labelsize=self._panel_format.small_size)
        plt.rc('ytick' , labelsize=self._panel_format.small_size)
        plt.rc('legend', fontsize=self._panel_format.small_size)
        plt.rc('figure', titlesize=self._panel_format.large_size)


    def _create_figure_and_axes(self) -> None:
        self._fig, self._axs = plt.subplots(self.num_panels, 
                                            1, 
                                            figsize=self._figsize, 
                                            layout="constrained")


    def _assign_axes(self) -> None:
        shared_axes = {}
        for i, panel in enumerate(self.panels):
            panel.ax = self.axs[i]
            panel.fig = self._fig
            if panel.x_axis_type in shared_axes:
                panel.ax.sharex(shared_axes[panel.x_axis_type])
            else:
                shared_axes[panel.x_axis_type] = panel.ax


    def _overlay_cuts(self, cuts_panel: BasePanel) -> None:
        """Given a cuts panel, finds any corresponding spectrogram panels and adds the appropriate overlay"""
        for panel in self.panels:
            is_corresponding_panel = _is_spectrogram_panel(panel) and (panel.tag == cuts_panel.tag)
            if is_corresponding_panel:
                panel.overlay_cuts(cuts_panel)


    def _overlay_superimposed_panels(self) -> None:
        for super_panel in self._superimposed_panels:
            for panel in self._panels:
                if panel.name == super_panel.name and (panel.identifier == super_panel.identifier):
                    super_panel.ax, super_panel.fig = panel.ax, self._fig
                    super_panel.draw()
                    if _is_cuts_panel(super_panel):
                        self._overlay_cuts(super_panel)


    def show(self) -> None:
        self._init_plot_style()
        self._create_figure_and_axes()
        self._assign_axes()
        last_panel_per_axis = {panel.x_axis_type: panel for panel in self.panels}
        for panel in self.panels:
            panel.draw()
            panel.annotate_y_axis()
            if panel == last_panel_per_axis[panel.x_axis_type]:
                panel.annotate_x_axis()
            else:
                panel.hide_x_axis_labels()
            if _is_cuts_panel(panel):
                self._overlay_cuts(panel)
        self._overlay_superimposed_panels()
        plt.show()
