# SPDX-FileCopyrightText: © 2024 Jimmy Fitzpatrick <jcfitzpatrick12@gmail.com>
# This file is part of SPECTRE
# SPDX-License-Identifier: GPL-3.0-or-later

from abc import ABC, abstractmethod
from typing import Optional, Literal
from enum import Enum

import numpy.typing as npt
import numpy as np
import matplotlib.dates as mdates
from matplotlib.axes import Axes
from matplotlib.figure import Figure

from spectre_core.spectrograms import Spectrogram, TimeType
from ._format import PanelFormat
from ._panel_names import PanelName


class XAxisType(Enum):
    """The x-axis type for a panel.
    
    Axes are shared in a stack between panels with common `XAxisType`.
    
    :ivar TIME: The xaxis has units of time.
    :ivar FREQUENCY: The xaxis has units of frequency.
    """
    TIME      = "time"
    FREQUENCY = "frequency"


class BasePanel(ABC):
    """Abstract base class for a panel used to visualise spectrogram data.

    `BasePanel` instances are designed to be part of a `PanelStack`, where multiple
    panels contribute to a composite plot. Subclasses must implement methods to define
    how the panel is drawn and annotated, and specify its x-axis type.
    """
    def __init__(
        self, 
        name: PanelName,
        spectrogram: Spectrogram
    ) -> None:
        """Initialize an instance of `BasePanel`.

        :param name: The name of the panel.
        :param spectrogram: The spectrogram being visualised.
        """
        self._name = name
        self._spectrogram = spectrogram

        # internal attributes set by `PanelStack` during stacking.
        self._panel_format: Optional[PanelFormat] = None
        self._time_type   : Optional[TimeType]    = None
        self._ax          : Optional[Axes]        = None
        self._fig         : Optional[Figure]      = None
        self._identifier  : Optional[str]         = None


    @abstractmethod
    def draw(
        self
    ) -> None:
        """Modify the `ax` attribute to draw the panel contents."""


    @abstractmethod
    def annotate_xaxis(
        self
    ) -> None:
        """Modify the `ax` attribute to annotate the x-axis of the panel."""


    @abstractmethod
    def annotate_yaxis(
        self
    ) -> None:
        """Modify the `ax` attribute to annotate the y-axis of the panel."""


    @property
    @abstractmethod
    def xaxis_type(
        self
    ) -> XAxisType:
     """Specify the x-axis type for the panel."""


    @property
    def spectrogram(
        self
    ) -> Spectrogram:
        """The spectrogram being visualised on this panel."""
        return self._spectrogram
    

    @property
    def tag(
        self
    ) -> str:
        """The tag of the spectrogram being visualised."""
        return self._spectrogram.tag
    

    @property
    def time_type(
        self
    ) -> TimeType:
        """The time type of the spectrogram.

        :raises ValueError: If the `time_type` has not been set.
        """
        if self._time_type is None:
            raise ValueError(f"`time_type` for the panel '{self.name}' must be set.")
        return self._time_type
    

    @time_type.setter
    def time_type(
        self, 
        value: TimeType
    ) -> None:
        """Set the `TimeType` for the spectrogram.

        This controls how time is represented and annotated on the panel.

        :param value: The `TimeType` to assign to the spectrogram.
        """
        self._time_type = value
    

    @property
    def name(
        self
    ) -> PanelName:
        """The name of the panel."""
        return self._name
    
    
    @property
    def panel_format(
        self
    ) -> PanelFormat:
        """Retrieve the panel format, which controls the style of the panel.

        :raises ValueError: If the `panel_format` has not been set.
        """
        if self._panel_format is None:
            raise ValueError(f"`panel_format` for the panel '{self.name}' must be set.")
        return self._panel_format


    @panel_format.setter
    def panel_format(
        self, 
        value: PanelFormat
    ) -> None:
        """Set the panel format to control the style of the panel.
        
        :param value: The `PanelFormat` to assign to the panel.
        """
        self._panel_format = value


    @property
    def ax(
        self
    ) -> Axes:
        """The `Axes` object bound to this panel.

        :raises AttributeError: If the `Axes` object has not been set.
        """
        if self._ax is None:
            raise AttributeError(f"`ax` must be set for the panel `{self.name}`")
        return self._ax
    

    @ax.setter
    def ax(
        self, 
        value: Axes
    ) -> None:
        """Assign a Matplotlib `Axes` object to this panel.

        This `Axes` will be used for drawing and annotations.

        :param value: The Matplotlib `Axes` to assign to the panel.
        """
        self._ax = value


    @property
    def fig(
        self
    ) -> Figure:
        """
        The `Figure` object bound to this panel.

        :raises AttributeError: If the `Figure` object has not been set.
        """
        if self._fig is None:
            raise AttributeError(f"`fig` must be set for the panel `{self.name}`")
        return self._fig
    

    @fig.setter
    def fig(
        self, 
        value: Figure
    ) -> None:
        """
        Assign a Matplotlib `Figure` object to this panel.

        This `Figure` is shared across all panels in the `PanelStack`.

        :param value: The Matplotlib `Figure` to assign to the panel.
        """
        self._fig = value
    
    
    @property
    def identifier(
        self
    ) -> Optional[str]:
        """Optional identifier for the panel.

        This identifier can be used to distinguish panels or aid in superimposing 
        panels in a stack.
        """
        return self._identifier
    
    
    @identifier.setter
    def identifier(
        self, 
        value: str
    ) -> None:
        """Set the optional identifier for the panel.
        
        This can be used to distinguish panels or aid in superimposing panels.
        """
        self._identifier = value
    

    def hide_xaxis_labels(
        self
    ) -> None:
        """Hide the x-axis labels for this panel."""
        self.ax.tick_params(axis='x', labelbottom=False)


    def hide_yaxis_labels(
        self
    ) -> None:
        """Hide the y-axis labels for this panel."""
        self.ax.tick_params(axis='y', labelbottom=False)
    

class BaseTimeSeriesPanel(BasePanel):
    """
    Abstract subclass of `BasePanel` designed for visualising time series data.

    Subclasses must implement any remaining abstract methods from `BasePanel`.
    """   
    @property
    def xaxis_type(
        self
    ) -> Literal[XAxisType.TIME]:
        return XAxisType.TIME
    
    
    @property
    def times(
        self
    ) -> npt.NDArray[np.float32 | np.datetime64]:
        """The times assigned to each spectrum according to the `TimeType`."""
        return self.spectrogram.times if self.time_type == TimeType.RELATIVE else self.spectrogram.datetimes
    

    def annotate_xaxis(
        self
    ) -> None:
        """Annotate the x-axis according to the specified `TimeType`."""
        if self.time_type == TimeType.RELATIVE:
            self.ax.set_xlabel('Time [s]')
        else:
            self.ax.set_xlabel('Time [UTC]')
            self.ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))



class BaseSpectrumPanel(BasePanel):
    """An abstract subclass of `BasePanel` tailored for visualising spectrum data.
    
    Subclasses must implement any remaining abstract methods as described by `BasePanel`.
    """   
    @property
    def xaxis_type(
        self
    ) -> Literal[XAxisType.FREQUENCY]:
        return XAxisType.FREQUENCY
    
    
    @property
    def frequencies(
        self
    ) -> npt.NDArray[np.float32]:
        """The physical frequencies assigned to each spectral component."""
        return self._spectrogram.frequencies


    def annotate_xaxis(
        self
    ) -> None:
        """Annotate the x-axis assuming frequency in units of Hz."""
        self.ax.set_xlabel('Frequency [Hz]')