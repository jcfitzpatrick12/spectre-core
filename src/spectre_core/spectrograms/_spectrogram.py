# SPDX-FileCopyrightText: © 2024 Jimmy Fitzpatrick <jcfitzpatrick12@gmail.com>
# This file is part of SPECTRE
# SPDX-License-Identifier: GPL-3.0-or-later

from typing import Optional
from warnings import warn
from datetime import datetime, timedelta
from dataclasses import dataclass
import os

import numpy as np
from astropy.io import fits

from spectre_core.capture_configs import CaptureConfig, PNames
from spectre_core.config import get_batches_dir_path, TimeFormats
from ._array_operations import (
    find_closest_index,
    normalise_peak_intensity,
    compute_resolution,
    compute_range,
    subtract_background,
)


@dataclass
class FrequencyCut:
    """A container to hold a cut of a dynamic spectra at a particular instant of time."""
    time: float | datetime
    frequencies: np.ndarray
    cut: np.ndarray
    spectrum_type: str


@dataclass
class TimeCut:
    """A container to hold a cut of a dynamic spectra at a particular frequency."""
    frequency: float
    times: np.ndarray
    cut: np.ndarray
    spectrum_type: str


@dataclass(frozen=True)
class TimeTypes:
    """Container to hold the different types of time we can assign to each spectrum in the dynamic spectra.
    
    'SECONDS' is equivalent to 'seconds elapsed since the first spectrum'.
    'DATETIMES' is equivalent to 'the datetime associated with each spectrum'.
    """
    SECONDS  : str = "seconds"
    DATETIMES: str = "datetimes"
    

@dataclass(frozen=True)
class SpectrumTypes:
    """A container for defined units of dynamic spectra."""
    AMPLITUDE: str = "amplitude"
    POWER    : str = "power"
    DIGITS   : str = "digits"


class Spectrogram:
    """A convenient, standardised wrapper for spectrogram data."""
    def __init__(self, 
                 dynamic_spectra: np.ndarray,
                 times: np.ndarray, 
                 frequencies: np.ndarray, 
                 tag: str,
                 start_datetime: Optional[datetime] = None, 
                 spectrum_type: Optional[str] = None): 
        
        # dynamic spectra
        self._dynamic_spectra = dynamic_spectra
        self._dynamic_spectra_dBb: Optional[np.ndarray] = None # cache

        # assigned times and frequencies
        if times[0] != 0:
            raise ValueError(f"The first spectrum must correspond to t=0")
        
        self._times = times
        self._frequencies = frequencies

        # general metadata
        self._tag = tag
        self._spectrum_type = spectrum_type
        
        # datetime information 
        self._start_datetime = start_datetime
        self._datetimes: Optional[list[datetime]] = None # cache
        
        # background metadata     
        self._background_spectrum: Optional[np.ndarray] = None # cache
        self._start_background_index = 0 
        self._end_background_index   = self.num_times 
        # background interval can be set after instanitation.
        self._start_background = None
        self._end_background   = None
        
        # finally check that the spectrogram arrays are matching in shape
        self._check_shapes()


    @property
    def dynamic_spectra(self) -> np.ndarray:
        """The dynamic spectra."""
        return self._dynamic_spectra
    

    @property
    def times(self) -> np.ndarray:
        """The physical time assigned to each spectrum.
        
        Equivalent to the 'seconds elapsed since the first spectrum'. So, by convention, the
        first spectrum is at t=0.
        """
        return self._times
    
    
    @property
    def num_times(self) -> int:
        """The size of the times array. Equivalent to the number of spectrums in the spectrogram."""
        return len(self._times)
    

    @property
    def time_resolution(self) -> float:
        """The time resolution of the dynamic spectra."""
        return compute_resolution(self._times)
    

    @property
    def time_range(self) -> float:
        """The time range of the dynamic spectra."""
        return compute_range(self._times)
    

    @property
    def frequencies(self) -> np.ndarray:
        """The physical frequency assigned to each spectral component."""
        return self._frequencies


    @property
    def num_frequencies(self) -> int:
        """The number of spectral components."""
        return len(self._frequencies)
    
    
    @property
    def frequency_resolution(self) -> float:
        """The frequency resolution of the dynamic spectra."""
        return compute_resolution(self._frequencies)
    

    @property
    def frequency_range(self) -> float:
        """The frequency range covered by the dynamic spectra."""
        return compute_range(self._frequencies)
    

    @property
    def tag(self) -> str:
        """The tag identifier corresponding to the dynamic spectra."""
        return self._tag
    

    @property
    def start_datetime_is_set(self) -> bool:
        """Returns true if the start datetime for the spectrogram has been set."""
        return (self._start_datetime is not None)
    
    
    @property
    def start_datetime(self) -> datetime:
        """The datetime assigned to the first spectrum in the dynamic spectra."""
        if self._start_datetime is None:
            raise AttributeError(f"A start time has not been set.")
        return self._start_datetime
    
    
    def format_start_time(self,
                          precise: bool = False) -> str:
        """The datetime assigned to the first spectrum in the dynamic spectra, formatted as a string."""
        if precise:
            return datetime.strftime(self.start_datetime, TimeFormats.PRECISE_DATETIME)
        return datetime.strftime(self.start_datetime, TimeFormats.DATETIME)
    
    
    @property
    def datetimes(self) -> list[datetime]:
        """The datetimes associated with each spectrum in the dynamic spectra."""
        if self._datetimes is None:
            self._datetimes = [self.start_datetime + timedelta( seconds=(float(t)) ) for t in self._times]
        return self._datetimes
    

    @property
    def spectrum_type(self) -> Optional[str]:
        """The units of the dynamic spectra."""
        return self._spectrum_type
    

    @property
    def start_background(self) -> Optional[str]:
        """The start of the background interval, as a datetime string up to seconds precision."""
        return self._start_background
    

    @property
    def end_background(self) -> Optional[str]:
        """The end of the background interval, as a datetime string up to seconds precision."""
        return self._end_background
    
    
    @property
    def background_spectrum(self) -> np.ndarray:
        """The background spectrum, computed by averaging the dynamic spectra according to the specified background interval.
        
        By default, the entire dynamic spectra is averaged over.
        """
        if self._background_spectrum is None:
            self._background_spectrum = np.nanmean(self._dynamic_spectra[:, self._start_background_index:self._end_background_index+1], 
                                                   axis=-1)
        return self._background_spectrum
    

    @property
    def dynamic_spectra_dBb(self) -> np.ndarray:
        """The dynamic spectra in units of decibels above the background spectrum."""
        if self._dynamic_spectra_dBb is None:
            # Create an artificial spectrogram where each spectrum is identically the background spectrum
            background_spectra = self.background_spectrum[:, np.newaxis]
            # Suppress divide by zero and invalid value warnings for this block of code
            with np.errstate(divide='ignore'):
                # Depending on the spectrum type, compute the dBb values differently
                if self._spectrum_type == SpectrumTypes.AMPLITUDE or self._spectrum_type == SpectrumTypes.DIGITS:
                    self._dynamic_spectra_dBb = 10 * np.log10(self._dynamic_spectra / background_spectra)
                elif self._spectrum_type == SpectrumTypes.POWER:
                    self._dynamic_spectra_dBb = 20 * np.log10(self._dynamic_spectra / background_spectra)
                else:
                    raise NotImplementedError(f"{self.spectrum_type} unrecognised, uncertain decibel conversion!")
        return self._dynamic_spectra_dBb  
    
    
    def set_background(self, 
                       start_background: str, 
                       end_background: str) -> None:
        """Public setter for start and end of the background"""
        self._dynamic_spectra_dBb = None # reset cache
        self._background_spectrum = None # reset cache
        self._start_background = start_background
        self._end_background = end_background
        self._update_background_indices_from_interval()
    
    
    
    def _update_background_indices_from_interval(self) -> None:
        start_background = datetime.strptime(self._start_background, TimeFormats.DATETIME)
        end_background   = datetime.strptime(self._end_background, TimeFormats.DATETIME)
        self._start_background_index = find_closest_index(start_background, 
                                                          self.datetimes, 
                                                          enforce_strict_bounds=True)
        self._end_background_index   = find_closest_index(end_background, 
                                                          self.datetimes, 
                                                          enforce_strict_bounds=True)


    def _check_shapes(self) -> None:
        num_spectrogram_dims = np.ndim(self._dynamic_spectra)
        # Check if 'dynamic_spectra' is a 2D array
        if num_spectrogram_dims != 2:
            raise ValueError(f"Expected dynamic spectrogram to be a 2D array, but got {num_spectrogram_dims}D array")
        dynamic_spectra_shape = self.dynamic_spectra.shape
        # Check if the dimensions of 'dynamic_spectra' are consistent with the time and frequency arrays
        if dynamic_spectra_shape[0] != self.num_frequencies:
            raise ValueError(f"Mismatch in number of frequency bins: Expected {self.num_frequencies}, but got {dynamic_spectra_shape[0]}")
        
        if dynamic_spectra_shape[1] != self.num_times:
            raise ValueError(f"Mismatch in number of time bins: Expected {self.num_times}, but got {dynamic_spectra_shape[1]}")
        

    def save(self) -> None:
        """Save the spectrogram as a fits file."""
        _save_spectrogram(self)
    

    def integrate_over_frequency(self, 
                                 correct_background: bool = False, 
                                 peak_normalise: bool = False) -> np.ndarray[np.float32]:
        """Return the dynamic spectra, numerically integrated over frequency."""
        # integrate over frequency
        I = np.trapz(self._dynamic_spectra, self._frequencies, axis=0)

        if correct_background:
            I = subtract_background(I, 
                                    self._start_background_index, 
                                    self._end_background_index)
        if peak_normalise:
            I = normalise_peak_intensity(I)
        return I


    def get_frequency_cut(self, 
                          at_time: float | str,
                          dBb: bool = False,
                          peak_normalise: bool = False) -> FrequencyCut:
        """Get a cut of the dynamic spectra at a particular instant of time.

        It is important to note that the 'at_time' as specified at input may not correspond exactly
        to one of the times assigned to each spectrogram. 
        """

        if isinstance(at_time, str):
            at_time = datetime.strptime(at_time, TimeFormats.DATETIME)
            index_of_cut = find_closest_index(at_time, 
                                              self.datetimes, 
                                              enforce_strict_bounds = True)
            time_of_cut = self.datetimes[index_of_cut]  

        elif isinstance(at_time, (float, int)):
            index_of_cut = find_closest_index(at_time, 
                                              self._times, 
                                              enforce_strict_bounds = True)
            time_of_cut = self.times[index_of_cut]
        
        else:
            raise ValueError(f"Type of at_time is unsupported: {type(at_time)}")
        
        if dBb:
            ds = self.dynamic_spectra_dBb
        else:
            ds = self._dynamic_spectra
        
        cut = ds[:, index_of_cut].copy() # make a copy so to preserve the spectrum on transformations of the cut

        if dBb:
            if peak_normalise:
                warn("Ignoring frequency cut normalisation, since dBb units have been specified")
        else:
            if peak_normalise:
                cut = normalise_peak_intensity(cut)
        
        return FrequencyCut(time_of_cut, 
                            self._frequencies, 
                            cut, 
                            self._spectrum_type)

        
    def get_time_cut(self,
                     at_frequency: float,
                     dBb: bool = False,
                     peak_normalise = False, 
                     correct_background = False, 
                     return_time_type: str = TimeTypes.SECONDS) -> TimeCut:
        """Get a cut of the dynamic spectra at a particular frequency.

        It is important to note that the 'at_frequency' as specified at input may not correspond exactly
        to one of the times assigned to each spectrogram. 
        """
        index_of_cut = find_closest_index(at_frequency, 
                                          self._frequencies, 
                                          enforce_strict_bounds = True)
        frequency_of_cut = self.frequencies[index_of_cut]

        if return_time_type == TimeTypes.DATETIMES:
            times = self.datetimes
        elif return_time_type == TimeTypes.SECONDS:
            times = self.times
        else:
            raise ValueError(f"Invalid return_time_type. Got {return_time_type}, expected one of 'datetimes' or 'seconds'")

        # dependent on the requested cut type, we return the dynamic spectra in the preferred units
        if dBb:
            ds = self.dynamic_spectra_dBb
        else:
            ds = self.dynamic_spectra
        
        cut = ds[index_of_cut,:].copy() # make a copy so to preserve the spectrum on transformations of the cut

        # Warn if dBb is used with background correction or peak normalisation
        if dBb:
            if correct_background or peak_normalise:
                warn("Ignoring time cut normalisation, since dBb units have been specified")
        else:
            # Apply background correction if required
            if correct_background:
                cut = subtract_background(cut, 
                                          self._start_background_index,
                                          self._end_background_index)
            
            # Apply peak normalisation if required
            if peak_normalise:
                cut = normalise_peak_intensity(cut)

        return TimeCut(frequency_of_cut, 
                         times, 
                         cut,
                         self.spectrum_type)
    

def _seconds_of_day(dt: datetime) -> float:
    start_of_day = datetime(dt.year, dt.month, dt.day)
    return (dt - start_of_day).total_seconds()


# Function to create a FITS file with the specified structure
def _save_spectrogram(spectrogram: Spectrogram) -> None:
    
    # making the write path
    batch_parent_path = get_batches_dir_path(year  = spectrogram.start_datetime.year,
                                             month = spectrogram.start_datetime.month,
                                             day   = spectrogram.start_datetime.day)
    # file name formatted as a batch file
    file_name = f"{spectrogram.format_start_time()}_{spectrogram.tag}.fits"
    write_path = os.path.join(batch_parent_path, 
                                file_name)
    
    # get optional metadata from the capture config
    capture_config = CaptureConfig(spectrogram.tag)
    ORIGIN    = capture_config.get_parameter_value(PNames.ORIGIN)
    INSTRUME  = capture_config.get_parameter_value(PNames.INSTRUMENT)
    TELESCOP  = capture_config.get_parameter_value(PNames.TELESCOPE)
    OBJECT    = capture_config.get_parameter_value(PNames.OBJECT)
    OBS_ALT   = capture_config.get_parameter_value(PNames.OBS_ALT)
    OBS_LAT   = capture_config.get_parameter_value(PNames.OBS_LAT)
    OBS_LON   = capture_config.get_parameter_value(PNames.OBS_LON)
    
    # Primary HDU with data
    primary_data = spectrogram.dynamic_spectra.astype(dtype=np.float32) 
    primary_hdu = fits.PrimaryHDU(primary_data)

    primary_hdu.header.set('SIMPLE', True, 'file does conform to FITS standard')
    primary_hdu.header.set('BITPIX', -32, 'number of bits per data pixel')
    primary_hdu.header.set('NAXIS', 2, 'number of data axes')
    primary_hdu.header.set('NAXIS1', spectrogram.dynamic_spectra.shape[1], 'length of data axis 1')
    primary_hdu.header.set('NAXIS2', spectrogram.dynamic_spectra.shape[0], 'length of data axis 2')
    primary_hdu.header.set('EXTEND', True, 'FITS dataset may contain extensions')

    # Add comments
    comments = [
        "FITS (Flexible Image Transport System) format defined in Astronomy and",
        "Astrophysics Supplement Series v44/p363, v44/p371, v73/p359, v73/p365.",
        "Contact the NASA Science Office of Standards and Technology for the",
        "FITS Definition document #100 and other FITS information."
    ]
    
    # The comments section remains unchanged since add_comment is the correct approach
    for comment in comments:
        primary_hdu.header.add_comment(comment)

    start_datetime = spectrogram.datetimes[0]
    start_date = start_datetime.strftime("%Y-%m-%d")
    start_time = start_datetime.strftime("%H:%M:%S.%f")

    end_datetime = spectrogram.datetimes[-1]
    end_date = end_datetime.strftime("%Y-%m-%d")
    end_time = end_datetime.strftime("%H:%M:%S.%f")

    primary_hdu.header.set('DATE', start_date, 'time of observation')
    primary_hdu.header.set('CONTENT', f'{start_date} dynamic spectrogram', 'title of image')
    primary_hdu.header.set('ORIGIN', f'{ORIGIN}')
    primary_hdu.header.set('TELESCOP', f'{TELESCOP}', 'type of instrument')
    primary_hdu.header.set('INSTRUME', f'{INSTRUME}') 
    primary_hdu.header.set('OBJECT', f'{OBJECT}', 'object description')

    primary_hdu.header.set('DATE-OBS', f'{start_date}', 'date observation starts')
    primary_hdu.header.set('TIME-OBS', f'{start_time}', 'time observation starts')
    primary_hdu.header.set('DATE-END', f'{end_date}', 'date observation ends')
    primary_hdu.header.set('TIME-END', f'{end_time}', 'time observation ends')

    primary_hdu.header.set('BZERO', 0, 'scaling offset')
    primary_hdu.header.set('BSCALE', 1, 'scaling factor')
    primary_hdu.header.set('BUNIT', f"{spectrogram.spectrum_type}", 'z-axis title') 

    primary_hdu.header.set('DATAMIN', np.nanmin(spectrogram.dynamic_spectra), 'minimum element in image')
    primary_hdu.header.set('DATAMAX', np.nanmax(spectrogram.dynamic_spectra), 'maximum element in image')

    primary_hdu.header.set('CRVAL1', f'{_seconds_of_day(start_datetime)}', 'value on axis 1 at reference pixel [sec of day]')
    primary_hdu.header.set('CRPIX1', 0, 'reference pixel of axis 1')
    primary_hdu.header.set('CTYPE1', 'TIME [UT]', 'title of axis 1')
    primary_hdu.header.set('CDELT1', spectrogram.time_resolution, 'step between first and second element in x-axis')

    primary_hdu.header.set('CRVAL2', 0, 'value on axis 2 at reference pixel')
    primary_hdu.header.set('CRPIX2', 0, 'reference pixel of axis 2')
    primary_hdu.header.set('CTYPE2', 'Frequency [Hz]', 'title of axis 2')
    primary_hdu.header.set('CDELT2', spectrogram.frequency_resolution, 'step between first and second element in axis')

    primary_hdu.header.set('OBS_LAT', f'{OBS_LAT}', 'observatory latitude in degree')
    primary_hdu.header.set('OBS_LAC', 'N', 'observatory latitude code {N,S}')
    primary_hdu.header.set('OBS_LON', f'{OBS_LON}', 'observatory longitude in degree')
    primary_hdu.header.set('OBS_LOC', 'W', 'observatory longitude code {E,W}')
    primary_hdu.header.set('OBS_ALT', f'{OBS_ALT}', 'observatory altitude in meter asl')


    # Wrap arrays in an additional dimension to mimic the e-CALLISTO storage
    times_wrapped = np.array([spectrogram.times.astype(np.float32)])
    # To mimic e-Callisto storage, convert frequencies to MHz
    frequencies_MHz = spectrogram.frequencies * 1e-6
    frequencies_wrapped = np.array([frequencies_MHz.astype(np.float32)])
    
    # Binary Table HDU (extension)
    col1 = fits.Column(name='TIME', format='PD', array=times_wrapped)
    col2 = fits.Column(name='FREQUENCY', format='PD', array=frequencies_wrapped)
    cols = fits.ColDefs([col1, col2])

    bin_table_hdu = fits.BinTableHDU.from_columns(cols)

    bin_table_hdu.header.set('PCOUNT', 0, 'size of special data area')
    bin_table_hdu.header.set('GCOUNT', 1, 'one data group (required keyword)')
    bin_table_hdu.header.set('TFIELDS', 2, 'number of fields in each row')
    bin_table_hdu.header.set('TTYPE1', 'TIME', 'label for field 1')
    bin_table_hdu.header.set('TFORM1', 'D', 'data format of field: 8-byte DOUBLE')
    bin_table_hdu.header.set('TTYPE2', 'FREQUENCY', 'label for field 2')
    bin_table_hdu.header.set('TFORM2', 'D', 'data format of field: 8-byte DOUBLE')
    bin_table_hdu.header.set('TSCAL1', 1, '')
    bin_table_hdu.header.set('TZERO1', 0, '')
    bin_table_hdu.header.set('TSCAL2', 1, '')
    bin_table_hdu.header.set('TZERO2', 0, '')

    # Create HDU list and write to file
    hdul = fits.HDUList([primary_hdu, bin_table_hdu])
    hdul.writeto(write_path, overwrite=True)
