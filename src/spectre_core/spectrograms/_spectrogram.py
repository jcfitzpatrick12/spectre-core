# SPDX-FileCopyrightText: © 2024 Jimmy Fitzpatrick <jcfitzpatrick12@gmail.com>
# This file is part of SPECTRE
# SPDX-License-Identifier: GPL-3.0-or-later

from typing import Optional, cast
from warnings import warn
from datetime import datetime
from dataclasses import dataclass
from enum import Enum
import os

import numpy as np
import numpy.typing as npt
from astropy.io import fits

from spectre_core.capture_configs import CaptureConfig, PName
from spectre_core.config import get_batches_dir_path, TimeFormat
from ._array_operations import (
    find_closest_index,
    normalise_peak_intensity,
    compute_resolution,
    compute_range,
    subtract_background,
)


class SpectrumUnit(Enum):
    """A defined unit for dynamic spectra values.
    
    :ivar AMPLITUDE: Formal definition TBC.
    :ivar POWER: Formal definition TBC.
    :ivar DIGITS: Formal definition TBC.
    """
    AMPLITUDE = "amplitude"
    POWER     = "power"
    DIGITS    = "digits"
    

@dataclass
class FrequencyCut:
    """A cut of a dynamic spectra, at a particular instant of time. Equivalently, some spectrum in 
    the spectrogram.
    
    :ivar time: The time of the frequency cut, either in relative time (if time is a float)
    or as a datetime.
    :ivar frequencies: The physical frequencies assigned to each spectral component, in Hz.
    :ivar cut: The spectrum values.
    :ivar spectrum_unit: The unit of each spectrum value.
    """
    time: float | datetime
    frequencies: npt.NDArray[np.float32]
    cut: npt.NDArray[np.float32]
    spectrum_unit: SpectrumUnit


@dataclass
class TimeCut:
    """A cut of a dynamic spectra, at some fixed frequency. Equivalently, a time series of
    some spectral component in the spectrogram.
    
    :ivar frequency: The physical frequency assigned to the spectral component, in Hz.
    :ivar times: The time for each time series value, either as a relative time (if 
    the elements are floats) or as a datetimes.
    :ivar cut: The time series values of the spectral component.
    :ivar spectrum_unit: The unit of each time series value.
    """
    frequency: float
    times: npt.NDArray[np.float32 | np.datetime64]
    cut: npt.NDArray[np.float32]
    spectrum_unit: SpectrumUnit


class TimeType(Enum):
    """The type of time we can assign to each spectrum in the dynamic spectra.
    
    :ivar RELATIVE: The elapsed time from the first spectrum, in seconds.
    :ivar DATETIMES: The datetime associated with each spectrum.
    """
    RELATIVE   = "relative"
    DATETIMES  = "datetimes"


class Spectrogram:
    """Standardised wrapper for spectrogram data, providing a consistent
    interface for storing, accessing, and manipulating spectrogram data, 
    along with associated metadata.
    """
    def __init__(
        self, 
        dynamic_spectra: npt.NDArray[np.float32],
        times          : npt.NDArray[np.float32], 
        frequencies    : npt.NDArray[np.float32], 
        tag            : str,
        spectrum_unit  : SpectrumUnit,
        start_datetime : Optional[datetime | np.datetime64] = None
    ) -> None:
        """Initialise a Spectrogram instance.

        :param dynamic_spectra: A 2D array of spectrogram data.
        :param times: A 1D array representing the elapsed time of each spectrum, in seconds, relative to the first
        in the spectrogram.
        :param frequencies: A 1D array representing the physical frequencies assigned to each spectral component, in Hz.
        :param tag: A string identifier for the spectrogram.
        :param spectrum_unit: The unit of the dynamic_spectra values.
        :param start_datetime: The datetime corresponding to the first spectrum, defaults to None.
        :raises ValueError: If times does not start at 0 or array shapes are inconsistent.
        """
        
        self._dynamic_spectra = dynamic_spectra

        if times[0] != 0:
            raise ValueError(f"The first spectrum must correspond to t=0")
        self._times = times
        
        self._frequencies = frequencies
        self._tag = tag
        self._spectrum_unit = spectrum_unit
        self._start_datetime = np.datetime64(start_datetime)
        
        # by default, the background is evaluated over the whole spectrogram
        self._start_background_index = 0 
        self._end_background_index   = self.num_times 
        # the background interval can be set after instantiation
        self._start_background: Optional[str]   = None 
        self._end_background  : Optional[str]   = None
        
        # finally check that the spectrogram arrays are matching in shape
        self._check_shapes()


    @property
    def dynamic_spectra(
        self
    ) -> npt.NDArray[np.float32]:
        """The dynamic spectra array.
        
        Returns the 2D array of spectrogram data with shape (num_frequencies, num_times), 
        where values are in the units specified by `spectrum_unit`.
        """
        return self._dynamic_spectra
    

    @property
    def times(
        self
    ) -> npt.NDArray[np.float32]:
        """A 1D array representing the elapsed time of each spectrum, in seconds, relative to the first
        in the spectrogram."""
        return self._times
    
    
    @property
    def num_times(
        self
    ) -> int:
        """The size of the times array. Equivalent to the number of spectrums in the spectrogram."""
        return len(self._times)
    

    @property
    def time_resolution(
        self
    ) -> float:
        """The time resolution of the dynamic spectra.

        Represents the spacing between consecutive time values in the times array, 
        calculated as the median difference between adjacent elements.
        """
        return compute_resolution(self._times)
    

    @property
    def time_range(
        self
    ) -> float:
        """The time range of the dynamic spectra.

        Represents the difference between the first and last time values 
        in the times array.
        """
        return compute_range(self._times)
    

    @property
    def frequencies(
        self
    ) -> npt.NDArray[np.float32]:
        """A 1D array representing the physical frequencies assigned to each spectral component, in Hz."""
        return self._frequencies


    @property
    def num_frequencies(
        self
    ) -> int:
        """The number of spectral components in the spectrogram.

        Equivalent to the size of the frequencies array.
        """
        return len(self._frequencies)
    
    
    @property
    def frequency_resolution(
        self
    ) -> float:
        """The frequency resolution of the dynamic spectra.

        Represents the spacing between consecutive frequency values in the frequencies array, 
        calculated as the median difference between adjacent elements.
        """
        return compute_resolution(self._frequencies)
    

    @property
    def frequency_range(
        self
    ) -> float:
        """The frequency range covered by the dynamic spectra.

        Represents the difference between the minimum and maximum frequency 
        values in the frequencies array.
        """
        return compute_range(self._frequencies)
    

    @property
    def tag(
        self
    ) -> str:
        """The tag identifier for the spectrogram"""
        return self._tag
    

    @property
    def start_datetime_is_set(
        self
    ) -> bool:
        """Indicates whether the start datetime for the spectrogram has been set."""
        return (self._start_datetime is not None)
    
    
    @property
    def start_datetime(
        self
    ) -> np.datetime64:
        """The datetime assigned to the first spectrum in `dynamic_spectra`.

        :raises AttributeError: If the start_datetime has not been set.
        """
        if self._start_datetime is None:
            raise AttributeError(f"A start time has not been set.")
        return self._start_datetime
    
    
    @property
    def datetimes(
        self
    ) -> npt.NDArray[np.datetime64]:
        """The datetimes associated with each spectrum in `dynamic_spectra`.

        Returns a list of datetime objects, calculated by adding the elapsed 
        times in the times array to the start_datetime.
        """
        return self.start_datetime + (1e6*self._times).astype('timedelta64[us]')
    

    @property
    def spectrum_unit(
        self
    ) -> SpectrumUnit:
        """The units associated with the `dynamic_spectra` array."""
        return self._spectrum_unit
    

    @property
    def start_background(
        self
    ) -> Optional[str]:
        """The start of the background interval.

        Returns a string-formatted datetime up to seconds precision, or None 
        if the background interval has not been set.
        """
        return self._start_background
    

    @property
    def end_background(
        self
    ) -> Optional[str]:
        """The end of the background interval.

        Returns a string-formatted datetime up to seconds precision, or None 
        if the background interval has not been set.
        """
        return self._end_background
    

    def compute_background_spectrum(
        self
    ) -> npt.NDArray[np.float32]:
        """Compute the background spectrum by averaging the dynamic spectra in time.

        By default, the entire dynamic spectra is averaged. Use set_background to 
        specify a custom background interval.

        :return: A 1D array representing the time-averaged dynamic spectra over the 
        specified background interval.
        """
        return np.nanmean(self._dynamic_spectra[:, self._start_background_index:self._end_background_index+1], 
                                                   axis=-1)
    

    def compute_dynamic_spectra_dBb(
        self
    ) -> npt.NDArray[np.float32]:
        """Compute the dynamic spectra in units of decibels above the background spectrum.

        The computation applies logarithmic scaling based on the `spectrum_unit`. 

        :raises NotImplementedError: If the spectrum_unit is unrecognised.
        :return: A 2D array with the same shape as `dynamic_spectra`, representing 
        the values in decibels above the background.
        """
        # Create a 'background' spectrogram where each spectrum is identically the background spectrum
        background_spectrum = self.compute_background_spectrum()
        background_spectra = background_spectrum[:, np.newaxis]
        # Suppress divide by zero and invalid value warnings for this block of code
        with np.errstate(divide='ignore', invalid='ignore'):
            if self._spectrum_unit == SpectrumUnit.AMPLITUDE or self._spectrum_unit == SpectrumUnit.DIGITS:
                dynamic_spectra_dBb = 10 * np.log10(self._dynamic_spectra / background_spectra)
            elif self._spectrum_unit == SpectrumUnit.POWER:
                dynamic_spectra_dBb = 20 * np.log10(self._dynamic_spectra / background_spectra)
            else:
                raise NotImplementedError(f"{self._spectrum_unit} is unrecognised; decibel conversion is uncertain!")
        return dynamic_spectra_dBb.astype(np.float32)
    
    
    def format_start_time(
        self
    ) -> str:
        """Format the datetime assigned to the first spectrum in the dynamic spectra.

        :return: A string representation of the `start_datetime`, up to seconds precision.
        """
        dt = self.start_datetime.astype(datetime)
        return datetime.strftime(dt, TimeFormat.DATETIME)
    
    
    def set_background(
        self, 
        start_background: str, 
        end_background: str
    ) -> None:
        """Set the background interval for computing the background spectrum, and doing
        background subtractions.

        :param start_background: The start time of the background interval, formatted as 
        a string in the format `TimeFormat.DATETIME` (up to seconds precision).
        :param end_background: The end time of the background interval, formatted as 
        a string in the format `TimeFormat.DATETIME` (up to seconds precision).
        """
        self._start_background = start_background
        self._end_background   = end_background
        self._update_background_indices_from_interval(self._start_background, 
                                                      self._end_background)
    
    
    
    def _update_background_indices_from_interval(
        self,
        start_background: str,
        end_background: str
    ) -> None:
        start_background_datetime = np.datetime64( datetime.strptime(start_background, TimeFormat.DATETIME) )
        end_background_datetime   = np.datetime64( datetime.strptime(end_background,   TimeFormat.DATETIME) )
        self._start_background_index = find_closest_index(start_background_datetime, 
                                                          self.datetimes, 
                                                          enforce_strict_bounds=True)
        self._end_background_index   = find_closest_index(end_background_datetime, 
                                                          self.datetimes, 
                                                          enforce_strict_bounds=True)


    def _check_shapes(
        self
    ) -> None:
        """Check that the data array shapes are consistent with one another."""
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
        

    def save(
        self
    ) -> None:
        """Write the spectrogram and its associated metadata to a batch file in the FITS format."""
        _save_spectrogram(self)
    

    def integrate_over_frequency(
        self, 
        correct_background: bool = False, 
        peak_normalise: bool = False
    ) -> npt.NDArray[np.float32]:
        """Numerically integrate the spectrogram over the frequency axis.

        :param correct_background: Indicates whether to subtract the background after
        computing the integral, defaults to False
        :param peak_normalise: Indicates whether to normalise the integral such that
        the peak value is equal to unity, defaults to False
        :return: A 1D array containing each spectrum numerically integrated over the 
        frequency axis.
        """
        # numerically integrate over frequency
        I = np.trapz(self._dynamic_spectra, self._frequencies, axis=0)

        if correct_background:
            I = subtract_background(I, 
                                    self._start_background_index, 
                                    self._end_background_index)
        if peak_normalise:
            I = normalise_peak_intensity(I)
        return I


    def get_frequency_cut(
        self, 
        at_time: float | str,
        dBb: bool = False,
        peak_normalise: bool = False
    ) -> FrequencyCut:
        """Retrieve a cut of the dynamic spectra at a specific time.

        If `at_time` does not match exactly with a time in `times`, the closest match 
        is selected. The cut represents one of the spectrums in the spectrogram.

        :param at_time: The requested time for the cut. If a string, it is parsed 
        as a datetime. If a float, it is treated as elapsed time since the first spectrum.
        :param dBb: If True, returns the cut in decibels above the background, 
        defaults to False.
        :param peak_normalise: If True, normalises the cut such that its peak value 
        is equal to 1. Ignored if dBb is True, defaults to False.
        :raises ValueError: If at_time is not a recognised type.
        :return: A FrequencyCut object containing the spectral values and associated metadata.
        """

        if isinstance(at_time, str):
            _at_datetime = np.datetime64( datetime.strptime(at_time, TimeFormat.DATETIME) )
            index_of_cut = find_closest_index(_at_datetime, 
                                              self.datetimes,  
                                              enforce_strict_bounds = True)
            time_of_cut = self.datetimes[index_of_cut]  

        elif isinstance(at_time, float):
            _at_time = np.float32(at_time)
            index_of_cut = find_closest_index(_at_time, 
                                              self._times, 
                                              enforce_strict_bounds = True)
            time_of_cut = self.times[index_of_cut]
        
        else:
            raise ValueError(f"'at_time' type '{type(at_time)}' is unsupported.")
        
        if dBb:
            ds = self.compute_dynamic_spectra_dBb()
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
                            self._spectrum_unit)

        
    def get_time_cut(
        self,
        at_frequency: float,
        dBb: bool = False,
        peak_normalise = False, 
        correct_background = False, 
        return_time_type: TimeType = TimeType.RELATIVE
    ) -> TimeCut:
        """Retrieve a cut of the dynamic spectra at a specific frequency.

        If `at_frequency` does not exactly match a frequency in `frequencies`, the 
        closest match is selected. The cut represents the time series of some spectral
        component.

        :param at_frequency: The requested frequency for the cut, in Hz.
        :param dBb: If True, returns the cut in decibels above the background. 
        Defaults to False.
        :param peak_normalise: If True, normalises the cut so its peak value is 1. 
        Ignored if dBb is True. Defaults to False.
        :param correct_background: If True, subtracts the background from the cut. 
        Ignored if dBb is True. Defaults to False.
        :param return_time_type: Specifies the type of time values in the cut 
        (TimeType.RELATIVE or TimeType.DATETIMES). Defaults to TimeType.RELATIVE.
        :raises ValueError: If return_time_type is not recognised.
        :return: A TimeCut object containing the temporal values and associated metadata.
        """
        _at_frequency = np.float32(at_frequency)
        index_of_cut = find_closest_index(_at_frequency, 
                                          self._frequencies, 
                                          enforce_strict_bounds = True)
        frequency_of_cut = float( self.frequencies[index_of_cut] )

        # dependent on the requested cut type, we return the dynamic spectra in the preferred units
        if dBb:
            ds = self.compute_dynamic_spectra_dBb()
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

        if return_time_type == TimeType.DATETIMES:
            return TimeCut(frequency_of_cut,
                           self.datetimes,
                           cut,
                           self.spectrum_unit)
        elif return_time_type == TimeType.RELATIVE:
            return TimeCut(frequency_of_cut, 
                           self.times, 
                           cut,
                           self.spectrum_unit)
        else:
            raise ValueError(f"Invalid return_time_type. Got {return_time_type}, "
                             f"expected one of 'datetimes' or 'seconds'")

    

def _seconds_of_day(
    dt: datetime
) -> float:
    start_of_day = datetime(dt.year, dt.month, dt.day)
    return (dt - start_of_day).total_seconds()


# Function to create a FITS file with the specified structure
def _save_spectrogram(
    spectrogram: Spectrogram
) -> None:
    """Save the input spectrogram and associated metadata to a fits file. Some metadata
    will be fetched from the corresponding capture config.
    
    :param spectrogram: The spectrogram containing the data to be saved.
    """
    dt = spectrogram.start_datetime.astype(datetime)
    # making the write path
    batch_parent_path = get_batches_dir_path(year  = dt.year,
                                             month = dt.month,
                                             day   = dt.day)
    # file name formatted as a batch file
    file_name = f"{spectrogram.format_start_time()}_{spectrogram.tag}.fits"
    write_path = os.path.join(batch_parent_path, 
                                file_name)
    
    # get optional metadata from the capture config
    capture_config = CaptureConfig(spectrogram.tag)
    ORIGIN    = cast(str,   capture_config.get_parameter_value(PName.ORIGIN))
    INSTRUME  = cast(str,   capture_config.get_parameter_value(PName.INSTRUMENT))
    TELESCOP  = cast(str,   capture_config.get_parameter_value(PName.TELESCOPE))
    OBJECT    = cast(str,   capture_config.get_parameter_value(PName.OBJECT))
    OBS_ALT   = cast(float, capture_config.get_parameter_value(PName.OBS_ALT))
    OBS_LAT   = cast(float, capture_config.get_parameter_value(PName.OBS_LAT))
    OBS_LON   = cast(float, capture_config.get_parameter_value(PName.OBS_LON))
    
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

    start_datetime = cast(datetime, spectrogram.datetimes[0].astype(datetime))
    start_date     = start_datetime.strftime("%Y-%m-%d")
    start_time     = start_datetime.strftime("%H:%M:%S.%f")

    end_datetime   = cast(datetime, spectrogram.datetimes[-1].astype(datetime))
    end_date       = end_datetime.strftime("%Y-%m-%d")
    end_time       = end_datetime.strftime("%H:%M:%S.%f")

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
    primary_hdu.header.set('BUNIT', f"{spectrogram.spectrum_unit.value}", 'z-axis title') 

    primary_hdu.header.set('DATAMIN', np.nanmin(spectrogram.dynamic_spectra), 'minimum element in image')
    primary_hdu.header.set('DATAMAX', np.nanmax(spectrogram.dynamic_spectra), 'maximum element in image')

    primary_hdu.header.set('CRVAL1', f'{_seconds_of_day( start_datetime)}', 'value on axis 1 at reference pixel [sec of day]')
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