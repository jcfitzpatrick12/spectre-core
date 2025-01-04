# SPDX-FileCopyrightText: © 2024 Jimmy Fitzpatrick <jcfitzpatrick12@gmail.com>
# This file is part of SPECTRE
# SPDX-License-Identifier: GPL-3.0-or-later

from abc import ABC, abstractmethod
from typing import Optional, Iterator, Tuple
from enum import Enum

import numpy.typing as npt
import numpy as np
from matplotlib import cm
import matplotlib.dates as mdates
from matplotlib.axes import Axes
from matplotlib.figure import Figure

from spectre_core.spectrograms import Spectrogram, TimeTypes
from ._format import PanelFormat
from ._panel_names import PanelNames


class XAxisTypes(Enum):
    """Defined x-axis types for a stack of panels.
    
    Axes are shared between panels with common `XAxisTypes`.
    """
    TIME      = "time"
    FREQUENCY = "frequency"


class BasePanel(ABC):
    """
    Abstract base class for a panel used to visualise spectrogram data.
    `BasePanel` instances are managed as part of a `PanelStack` to make
    the final plot.

    Subclasses must implement the following methods:
    - The `draw` method, which tells `PanelStack` what to draw onto the panel.
    - The `annotate_xaxis` method, which tells `PanelStack` how the x-axis should be annotated.
    - The `annotate_yaxis` method, which tells `PanelStack` how the y-axis should be annotated.
    - The `xaxis_type` property, which enables axes sharing between panels in a a `PanelStack`.
    """
    def __init__(self, 
                 name: PanelNames,
                 spectrogram: Spectrogram):
        """Initialise an instance of `BasePanel`.

        :param name: The name of the panel.
        :param spectrogram: The spectrogram being visualised.
        """
        self._name = name
        self._spectrogram = spectrogram

        # attributes set by `PanelStack` during stacking.
        self._panel_format: Optional[PanelFormat] = None
        self._time_type   : Optional[TimeTypes]   = None
        self._ax          : Optional[Axes]        = None
        self._fig         : Optional[Figure]      = None
        self._identifier  : Optional[str]         = None


    @abstractmethod
    def draw(self) -> None:
        """Modify the public `ax` attribute to draw onto the matplotlib `Axes` for the panel."""


    @abstractmethod
    def annotate_xaxis(self) -> None:
        """Modify the public `ax` attribute and annotate the x-axis for the panel."""


    @abstractmethod
    def annotate_yaxis(self) -> None:
        """Modify the public `ax` attribute and annotate the y-axis for the panel."""

    @property
    @abstractmethod
    def xaxis_type(self) -> XAxisTypes:
        """Define the x-axis type for the panel. Enables panels to share axes in a `PanelStack`."""


    @property
    def spectrogram(self) -> Spectrogram:
        """The spectrogram being visualised on this panel."""
        return self._spectrogram
    

    @property
    def tag(self) -> str:
        """The tag of the spectrogram being visualised."""
        return self._spectrogram.tag
    

    @property
    def time_type(self) -> TimeTypes:
        """The time type of the spectrogram."""
        return self._time_type
    

    @time_type.setter
    def time_type(self, value: TimeTypes) -> None:
        """Specify the `TimeType` for the spectrogram to control how time is represented and annotated on the panel."""
        self._time_type = value
    

    @property
    def name(self) -> PanelNames:
        """The name of the panel."""
        return self._name
    
    
    @property
    def panel_format(self) -> PanelFormat:
        """Retrieve formatting parameters, such as font sizes and line colours, used to style the panel."""
        return self._panel_format


    @panel_format.setter
    def panel_format(self, value: PanelFormat) -> None:
        """Set the panel format."""
        self._panel_format = value


    @property
    def ax(self) -> Optional[Axes]:
        """The `Axes` object bound to this panel."""
        if self._ax is None:
            raise AttributeError(f"`ax` must be set for the panel `{self.name}`")
        return self._ax
    

    @ax.setter
    def ax(self, value: Axes) -> None:
        """Assign a Matplotlib `Axes` object to this panel, which will be used for drawing and annotations."""
        self._ax = value


    @property
    def fig(self) -> Figure:
        """The `Figure` object bound to this panel."""
        if self._fig is None:
            raise AttributeError(f"`fig` must be set for the panel `{self.name}`")
        return self._fig
    

    @fig.setter
    def fig(self, value: Figure) -> None:
        """Assign a Matplotlib `Figure` object to this panel, shared across all panels in the `PanelStack`."""
        self._fig = value
    
    
    @property
    def identifier(self) -> Optional[str]:
        """Optional extra identifier for the panel to aid in superimposing."""
        return self._identifier
    
    
    @identifier.setter
    def identifier(self, value: str) -> None:
        """An optional identifier for the panel, used for superimposing other panels."""
        self._identifier = value
        
        
    def bind_to_colors(self, 
                       values: npt.NDArray[np.float32], 
                       cmap: str = "winter") -> Iterator[Tuple[np.float32, npt.NDArray[np.float32]]]: 
        """
        Assign RGBA colours to values using a colormap.

        Values are linearly mapped to a subset of the unit interval before being 
        converted to RGBA colours using the specified colormap. 

        :param values: Array of values to be coloured.
        :param cmap: Name of the Matplotlib colormap, defaults to "winter".
        :return: Iterator of tuples pairing each value with an RGBA colour.
        """
        colormap = cm.get_cmap(cmap)
        rgbas = colormap(np.linspace(0.1, 0.9, len(values)))
        return zip(values, rgbas)
    

    def hide_xaxis_labels(self) -> None:
        """Hide the x-axis labels for this panel to reduce visual clutter in the plot."""
        self.ax.tick_params(axis='x', labelbottom=False)


    def hide_yaxis_labels(self) -> None:
        """Hide the y-axis labels for this panel to reduce visual clutter in the plot."""
        self.ax.tick_params(axis='y', labelbottom=False)
    

class BaseTimeSeriesPanel(BasePanel):
    """An abstract subclass of `BasePanel` designed specifically for visualising time series data.

    
    Subclasses must implement any remaining abstract methods as described by `BasePanel`.
    """    
    @property
    def xaxis_type(self) -> XAxisTypes.TIME:
        return XAxisTypes.TIME
    
    
    @property
    def times(self):
        """The times assigned to each spectrum according to the `TimeType`."""
        return self.spectrogram.times if self.time_type == TimeTypes.RELATIVE else self.spectrogram.datetimes
    

    def annotate_xaxis(self):
        """Annotate the x-axis according to the specified `TimeType`."""
        if self.time_type == TimeTypes.RELATIVE:
            self.ax.set_xlabel('Time [s]')
        else:
            self.ax.set_xlabel('Time [UTC]')
            self.ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))



class BaseSpectrumPanel(BasePanel):
    """An abstract subclass of `BasePanel` tailored for visualising spectral data.
    
    Subclasses must implement any remaining abstract methods as described by `BasePanel`.
    """   
    @property
    def xaxis_type(self) -> XAxisTypes.FREQUENCY:
        return XAxisTypes.FREQUENCY
    
    
    @property
    def frequencies(self):
        """The physical frequencies assigned to each spectral component."""
        return self._spectrogram.frequencies


    def annotate_xaxis(self):
        """Annotate the x-axis with a label representing frequency in hertz."""
        self.ax.set_xlabel('Frequency [Hz]')