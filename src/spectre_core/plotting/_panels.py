# SPDX-FileCopyrightText: © 2024 Jimmy Fitzpatrick <jcfitzpatrick12@gmail.com>
# This file is part of SPECTRE
# SPDX-License-Identifier: GPL-3.0-or-later

from typing import Optional
from datetime import datetime
from dataclasses import dataclass
from warnings import warn

from matplotlib.colors import LogNorm
import numpy as np

from spectre_core.spectrograms import Spectrogram, FrequencyCut, TimeCut
from ._base import BasePanel, BaseSpectrumPanel, BaseTimeSeriesPanel


@dataclass(frozen=True)
class PanelNames:
    SPECTROGRAM            : str = "spectrogram"
    FREQUENCY_CUTS         : str = "frequency_cuts"
    TIME_CUTS              : str = "time_cuts"
    INTEGRAL_OVER_FREQUENCY: str = "integral_over_frequency"


class _FrequencyCutsPanel(BaseSpectrumPanel):
    def __init__(self, 
                 spectrogram: Spectrogram, 
                 *times: list[float | str],
                 dBb: bool = False,
                 peak_normalise: bool = False):
        super().__init__(PanelNames.FREQUENCY_CUTS,
                         spectrogram)
        self._times = times
        self._dBb = dBb
        self._peak_normalise = peak_normalise
        # map each time cut to the corresponding FrequencyCut dataclass
        self._frequency_cuts: Optional[dict[float | datetime, FrequencyCut]] = {}


    @property
    def frequency_cuts(self) -> dict[float | str, FrequencyCut]:
        if not self._frequency_cuts:
            for time in self._times:
                frequency_cut = self._spectrogram.get_frequency_cut(time,
                                                                    dBb = self._dBb,
                                                                    peak_normalise = self._peak_normalise)
                self._frequency_cuts[frequency_cut.time] = frequency_cut
        return self._frequency_cuts


    @property
    def times(self) -> list[float | datetime]:
        return list(self.frequency_cuts.keys())
    

    def draw(self):
        for time, color in self.bind_to_colors():
            frequency_cut = self.frequency_cuts[time]
            self.ax.step(self.frequencies*1e-6, # convert to MHz
                         frequency_cut.cut, 
                         where='mid', 
                         color = color)
    

    def annotate_y_axis(self) -> None:
        if self._dBb:
            self.ax.set_ylabel('dBb')
        elif self._peak_normalise:
            return # no y-axis label
        else:
            self.ax.set_ylabel(f'{self._spectrogram.spectrum_type.capitalize()}')

    
    def bind_to_colors(self):
        return super().bind_to_colors(self.times, cmap = self.panel_format.cuts_cmap)
    

class _IntegralOverFrequencyPanel(BaseTimeSeriesPanel):
    def __init__(self, 
                 spectrogram: Spectrogram, 
                 peak_normalise: bool = False,
                 background_subtract: bool = False):
        super().__init__(PanelNames.INTEGRAL_OVER_FREQUENCY,
                         spectrogram)
        self._peak_normalise = peak_normalise
        self._background_subtract = background_subtract


    def draw(self):
        I = self._spectrogram.integrate_over_frequency(correct_background = self._background_subtract,
                                                       peak_normalise = self._peak_normalise)
        self.ax.step(self.times, I, where="mid", color = self.panel_format.integral_color)
 

    def annotate_y_axis(self):
        # no y-axis label
        return 


class _TimeCutsPanel(BaseTimeSeriesPanel):
    def __init__(self, 
                 spectrogram: Spectrogram, 
                 *frequencies: list[float],
                 dBb: bool = False,
                 peak_normalise: bool = False,
                 background_subtract: bool = False):
        super().__init__(PanelNames.TIME_CUTS, 
                         spectrogram)
        self._frequencies = frequencies
        self._dBb = dBb
        self._peak_normalise = peak_normalise
        self._background_subtract = background_subtract
        # map each cut frequency to the corresponding TimeCut dataclass
        self._time_cuts: Optional[dict[float, TimeCut]] = {} 
    

    @property
    def time_cuts(self) -> dict[float, TimeCut]:
        if not self._time_cuts:
            for frequency in self._frequencies:
                time_cut =  self._spectrogram.get_time_cut(frequency,
                                                           dBb = self._dBb,
                                                           peak_normalise = self._peak_normalise,
                                                           correct_background = self._background_subtract,
                                                           return_time_type=self._time_type)
                self._time_cuts[time_cut.frequency] = time_cut
        return self._time_cuts
    

    @property
    def frequencies(self) -> list[float]:
        return list(self.time_cuts.keys())


    def draw(self):
        for frequency, color in self.bind_to_colors():
            time_cut = self.time_cuts[frequency]
            self.ax.step(self.times, 
                         time_cut.cut, 
                         where='mid', 
                         color = color)
    

    def annotate_y_axis(self) -> None:
        if self._dBb:
            self.ax.set_ylabel('dBb')
        elif self._peak_normalise:
            return # no y-axis label
        else:
            self.ax.set_ylabel(f'{self._spectrogram.spectrum_type.capitalize()}')

    
    def bind_to_colors(self):
        return super().bind_to_colors(self.frequencies, cmap = self.panel_format.cuts_cmap)
    

class _SpectrogramPanel(BaseTimeSeriesPanel):
    def __init__(self, 
                 spectrogram: Spectrogram, 
                 log_norm: bool = False,
                 dBb: bool = False,
                 vmin: float | None = -1,
                 vmax: float | None = 2):
        super().__init__(PanelNames.SPECTROGRAM,
                         spectrogram)
        self._log_norm = log_norm
        self._dBb = dBb
        self._vmin = vmin
        self._vmax = vmax


    def draw(self):
        dynamic_spectra = self._spectrogram.dynamic_spectra_as_dBb if self._dBb else self._spectrogram.dynamic_spectra

        norm = LogNorm(vmin=np.nanmin(dynamic_spectra[dynamic_spectra > 0]), 
                       vmax=np.nanmax(dynamic_spectra)) if self._log_norm else None
        

        if self._log_norm and (self._vmin or self._vmax):
            warn("vmin/vmax will be ignored while using log_norm.")
            self._vmin = None 
            self._vmax = None
        
        # Plot the spectrogram with kwargs
        pcm = self.ax.pcolormesh(self.times, 
                            self._spectrogram.frequencies * 1e-6, 
                            dynamic_spectra,
                            vmin=self._vmin, 
                            vmax=self._vmax,
                            norm=norm, 
                            cmap=self.panel_format.spectrogram_cmap)
        
        # Add colorbar if dBb is used
        if self._dBb:
            cbar = self.fig.colorbar(pcm, 
                                      ax=self.ax, 
                                      ticks=np.linspace(self._vmin, self._vmax, 6, dtype=int))
            cbar.set_label('dBb')


    def annotate_y_axis(self) -> None:
        self.ax.set_ylabel('Frequency [MHz]')
        return
    
    
    def overlay_cuts(self, cuts_panel: BasePanel) -> None:
        if cuts_panel.name == PanelNames.TIME_CUTS:
            self._overlay_time_cuts(cuts_panel)
        elif cuts_panel.name == PanelNames.FREQUENCY_CUTS:
            self._overlay_frequency_cuts(cuts_panel)


    def _overlay_time_cuts(self, time_cuts_panel: _TimeCutsPanel) -> None:
        for frequency, color in time_cuts_panel.bind_to_colors():
            self.ax.axhline(frequency*1e-6, # convert to MHz
                            color = color,
                            linewidth=self.panel_format.line_width
                            )
            
            
    def _overlay_frequency_cuts(self, frequency_cuts_panel: _FrequencyCutsPanel) -> None:
        for time, color in frequency_cuts_panel.bind_to_colors():
            self.ax.axvline(time,
                            color = color,
                            linewidth=self.panel_format.line_width
                            )


@dataclass(frozen=True)
class Panels:
    TimeCuts                    = _TimeCutsPanel
    FrequencyCuts               = _FrequencyCutsPanel
    Spectrogram                 = _SpectrogramPanel
    IntegralOverFrequency       = _IntegralOverFrequencyPanel