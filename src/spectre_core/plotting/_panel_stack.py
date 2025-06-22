# SPDX-FileCopyrightText: © 2024-2025 Jimmy Fitzpatrick <jcfitzpatrick12@gmail.com>
# This file is part of SPECTRE
# SPDX-License-Identifier: GPL-3.0-or-later

import os
import numpy as np
from typing import Optional, Tuple, cast
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.axes import Axes
from matplotlib import use
from datetime import datetime

from spectre_core.spectrograms import TimeType
from spectre_core.config import TimeFormat, get_batches_dir_path
from ._base import BasePanel, XAxisType
from ._format import PanelFormat
from ._panels import PanelName, SpectrogramPanel, TimeCutsPanel, FrequencyCutsPanel


def _is_cuts_panel(panel: BasePanel) -> bool:
    """Check if a panel contains spectrogram cuts.

    :param panel: The panel to check.
    :return: True if the panel is a frequency or time cuts panel, otherwise False.
    """
    return panel.name in {PanelName.FREQUENCY_CUTS, PanelName.TIME_CUTS}


def _is_spectrogram_panel(panel: BasePanel) -> bool:
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
        figsize: Tuple[int, int] = (15, 8),
        non_interactive: bool = False,
    ) -> None:
        """Initialize an instance of `PanelStack`.

        :param panel_format: Formatting applied across all panels in the stack. Defaults to `PanelFormat()`.
        :param time_type: The type of time assigned to spectrograms, defaults to `TimeType.RELATIVE`.
        :param figsize: The size of the `matplotlib` figure as (width, height). Defaults to (15, 8).
        """
        self._panel_format = panel_format
        self._time_type = time_type
        self._figsize = figsize

        if non_interactive:
            # Use a non-interactive matplotlib backend, which can only write files.
            use("agg")

        self._panels: list[BasePanel] = []
        self._superimposed_panels: list[BasePanel] = []

        self._fig: Optional[Figure] = None
        self._axs: Optional[np.ndarray] = None

    def _sort_by_xaxis_type(self, panels: list[BasePanel]) -> list[BasePanel]:
        return list(sorted(panels, key=lambda panel: panel.xaxis_type.value))

    @property
    def panels(self) -> list[BasePanel]:
        """Get the panels in the stack, sorted by their `XAxisType`."""
        return self._sort_by_xaxis_type(self._panels)

    @property
    def superimposed_panels(self) -> list[BasePanel]:
        """Get the superimposed panels in the stack, sorted by their `XAxisType"""
        return self._sort_by_xaxis_type(self._superimposed_panels)

    @property
    def num_panels(self) -> int:
        """Get the number of panels in the stack."""
        return len(self._panels)

    @property
    def num_superimposed_panels(self) -> int:
        """Get the number of superimposed panels in the stack."""
        return len(self._superimposed_panels)

    @property
    def time_type(self) -> TimeType:
        """The imposed time type on all time series panels in the stack.

        :raises ValueError: If the `time_type` has not been set.
        """
        return self._time_type

    @time_type.setter
    def time_type(self, value: TimeType) -> None:
        """Set the `TimeType` for all time series panels in the stack.

        This controls how time is represented and annotated on the panel.

        :param value: The `TimeType` to impose on all time series panels in the stack.
        """
        self._time_type = value

    def _get_fig(self) -> Figure:
        """Get the shared `matplotlib` figure for the panel stack.

        :raises ValueError: If the axes have not been initialized.
        """
        if self._fig is None:
            raise ValueError(
                f"An unexpected error has occured, `fig` must be set for the panel stack."
            )
        return self._fig

    def _get_axes(self) -> np.ndarray:
        """Get the `matplotlib` axes in the stack.

        :return: An array of `matplotlib.axes.Axes`, one for each panel in the stack.
        :raises ValueError: If the axes have not been initialized.
        """
        if self._axs is None:
            raise ValueError(
                f"An unexpected error has occured, `axs` must be set for the panel stack."
            )
        return np.atleast_1d(self._axs)

    def _validate_time_type(self, panel: BasePanel) -> None:
        """Check that the time type of the input panel, is consistent with the time type of the stack."""
        if panel.get_time_type() != self._time_type:
            raise ValueError(
                f"Cannot add a panel with inconsistent time type. "
                f"Expected {self._time_type.value}, but got {panel.get_time_type().value}"
            )

    def add_panel(
        self,
        panel: BasePanel,
        identifier: Optional[str] = None,
        panel_format: Optional[PanelFormat] = None,
    ) -> None:
        """Add a panel to the stack.

        Overrides the time type of the panel, to the time type of the stack.

        :param panel: An instance of a `BasePanel` subclass to be added to the stack.
        :param identifier: An optional string to link the panel with others for superimposing.
        """
        panel.set_panel_format(panel_format or self._panel_format)
        panel.set_time_type(self._time_type)
        if identifier:
            panel.set_identifier(identifier)

        self._panels.append(panel)

    def superimpose_panel(
        self,
        panel: BasePanel,
        identifier: Optional[str] = None,
        panel_format: Optional[PanelFormat] = None,
    ) -> None:
        """Superimpose a panel onto an existing panel in the stack.

        Overrides the time type of the panel, to the time type of the stack.

        :param panel: The panel to superimpose.
        :param identifier: An optional identifier to link panels during superimposing, defaults to None
        """
        if identifier:
            panel.set_identifier(identifier)
        panel.set_panel_format(panel_format or self._panel_format)
        panel.set_time_type(self._time_type)

        self._superimposed_panels.append(panel)

    def _init_plot_style(self) -> None:
        """Initialize the global plot style for the stack.

        This method sets `matplotlib` styles and font sizes based on the `panel_format`.
        """
        plt.style.use(self._panel_format.style)

        plt.rc("font", size=self._panel_format.small_size)

        plt.rc(
            "axes",
            titlesize=self._panel_format.medium_size,
            labelsize=self._panel_format.medium_size,
        )

        plt.rc("xtick", labelsize=self._panel_format.small_size)
        plt.rc("ytick", labelsize=self._panel_format.small_size)

        plt.rc("legend", fontsize=self._panel_format.small_size)
        plt.rc("figure", titlesize=self._panel_format.large_size)

    def _create_figure_and_axes(self) -> None:
        """Create the `matplotlib` figure and axes for the panel stack.

        This initializes a figure with a specified number of vertically stacked axes.
        """
        self._fig, self._axs = plt.subplots(
            self.num_panels, 1, figsize=self._figsize, layout="constrained"
        )

    def _assign_axes(self) -> None:
        """Assign each axes in the figure to some panel in the stack.

        Axes are shared between panels with common `XAxisType`.
        """
        shared_axes: dict[XAxisType, Axes] = {}
        for i, panel in enumerate(self.panels):
            ax = self._get_axes()[i]
            panel.set_ax(ax)
            panel.set_fig(self._fig)
            if panel.xaxis_type in shared_axes:
                panel.sharex(shared_axes[panel.xaxis_type])
            else:
                shared_axes[panel.xaxis_type] = ax

    def _overlay_cuts(self, cuts_panel: BasePanel) -> None:
        """Overlay cuts onto corresponding spectrogram panels.

        For a given cuts panel, locate any spectrogram panels in the stack with a matching tag
        and add the appropriate frequency or time cuts overlay.

        :param cuts_panel: A panel containing frequency or time cuts.
        """
        for panel in self.panels:
            if _is_spectrogram_panel(panel) and panel.tag == cuts_panel.tag:
                panel = cast(SpectrogramPanel, panel)
                if cuts_panel.name == PanelName.FREQUENCY_CUTS:
                    panel.overlay_frequency_cuts(cast(FrequencyCutsPanel, cuts_panel))
                elif cuts_panel.name == PanelName.TIME_CUTS:
                    panel.overlay_time_cuts(cast(TimeCutsPanel, cuts_panel))

    def _overlay_superimposed_panels(self) -> None:
        """Superimpose panels onto matching panels in the stack.

        For each superimposed panel, find a matching panel in the stack with the same name
        and identifier. Share the axes and figure, then draw the superimposed panel. If the
        panel contains cuts, overlay those cuts onto the corresponding spectrogram panels.
        """
        for super_panel in self._superimposed_panels:
            for panel in self._panels:
                if panel.name == super_panel.name and (
                    panel.get_identifier() == super_panel.get_identifier()
                ):
                    super_panel.share_axes(panel)
                    super_panel.draw()
                    if _is_cuts_panel(super_panel):
                        self._overlay_cuts(super_panel)

    def _make_figure(self) -> None:
        """Make the panel stack figure."""
        if self.num_panels < 1:
            raise ValueError(f"There must be at least one panel in the stack.")

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

    def show(self) -> None:
        """Display the panel stack figure."""
        self._make_figure()
        self._get_fig().show()
        self._get_fig().clear()
        plt.close(self._fig)

    def save(
        self,
    ) -> str:
        """Save the panel stack figure as a batch file under the tag of the first
        panel in the stack. The file format is `png`.

        :return: The file path of the newly created batch file containing the figure.
        """
        self._make_figure()
        first_panel = self._panels[0]

        start_dt = cast(
            datetime, first_panel.spectrogram.start_datetime.astype(datetime)
        )
        batch_name = (
            f"{start_dt.strftime(TimeFormat.DATETIME)}_{first_panel.spectrogram.tag}"
        )
        batch_file_path = os.path.join(
            get_batches_dir_path(start_dt.year, start_dt.month, start_dt.day),
            f"{batch_name}.png",
        )
        # If the parent directory does not exist, create it.
        os.makedirs(os.path.dirname(batch_file_path), exist_ok=True)
        self._get_fig().savefig(batch_file_path)
        self._get_fig().clear()
        plt.close(self._fig)
        return batch_file_path
