# SPDX-FileCopyrightText: © 2024 Jimmy Fitzpatrick <jcfitzpatrick12@gmail.com>
# This file is part of SPECTRE
# SPDX-License-Identifier: GPL-3.0-or-later

from datetime import datetime, timedelta
from typing import Tuple
import numpy as np

from astropy.io import fits
from astropy.io.fits.hdu.image import PrimaryHDU
from astropy.io.fits.hdu.table import BinTableHDU
from astropy.io.fits.hdu.hdulist import HDUList

from spectre_core.config import TimeFormats
from spectre_core.spectrograms import Spectrogram
from spectre_core.capture_configs import CaptureModes
from .._register import register_batch
from .._base import BaseBatch, BatchFile


@register_batch(CaptureModes.FIXED_CENTER_FREQUENCY)
class _Batch(BaseBatch):
    def __init__(self,
                 start_time: str,
                 tag: str):
        super().__init__(start_time, tag) 
        self.add_file( BinFile(self.parent_dir_path, self.name) )
        self.add_file( HdrFile(self.parent_dir_path, self.name) )
        self.add_file( FitsFile(self.parent_dir_path, self.name))


class BinFile(BatchFile):
    def __init__(self, 
                 parent_dir_path: str, 
                 base_file_name: str):
        super().__init__(parent_dir_path, base_file_name, "bin")

    def read(self) -> np.ndarray:
        with open(self.file_path, "rb") as fh:
            return np.fromfile(fh, dtype=np.complex64)


  
class HdrFile(BatchFile):
    def __init__(self, 
                 parent_dir_path: str, 
                 base_file_name: str):
        super().__init__(parent_dir_path, base_file_name, "hdr")


    def read(self) -> int:
        hdr_contents = self._extract_contents()
        return self._get_millisecond_correction(hdr_contents)


    def _extract_contents(self) -> np.ndarray:
        with open(self.file_path, "rb") as fh:
            return np.fromfile(fh, dtype=np.float32)


    def _get_millisecond_correction(self, hdr_contents: np.ndarray) -> int:
        if len(hdr_contents) != 1:
            raise ValueError(f"Expected exactly one integer in the header, but received header contents: {hdr_contents}")
        
        millisecond_correction_as_float = float(hdr_contents[0])

        if not millisecond_correction_as_float.is_integer():
            raise TypeError(f"Expected integer value for millisecond correction, but got {millisecond_correction_as_float}")
        
        return int(millisecond_correction_as_float)
        

class FitsFile(BatchFile):
    def __init__(self, 
                 parent_dir_path: str, 
                 base_file_name: str):
        super().__init__(parent_dir_path, base_file_name, "fits")


    @property
    def datetimes(self) -> np.ndarray:
        with fits.open(self.file_path, mode='readonly') as hdulist:
            bintable_data = hdulist[1].data
            times = bintable_data['TIME'][0]
            return [self.start_datetime + timedelta(seconds=t) for t in times]
        

    def read(self) -> Spectrogram:
        with fits.open(self.file_path, mode='readonly') as hdulist:
            primary_hdu                = self._get_primary_hdu(hdulist)
            dynamic_spectra            = self._get_dynamic_spectra(primary_hdu)
            spectrum_type              = self._get_spectrum_type(primary_hdu)
            spectrogram_start_datetime = self._get_spectrogram_start_datetime(primary_hdu)
            bintable_hdu               = self._get_bintable_hdu(hdulist)
            times, frequencies         = self._get_time_and_frequency(bintable_hdu)

        return Spectrogram(dynamic_spectra, 
                           times, 
                           frequencies, 
                           self.tag,
                           spectrogram_start_datetime,
                           spectrum_type)


    def _get_primary_hdu(self, hdulist: HDUList) -> PrimaryHDU:
        return hdulist['PRIMARY']


    def _get_dynamic_spectra(self, primary_hdu: PrimaryHDU) -> np.ndarray:
        return primary_hdu.data


    def _get_spectrum_type(self, primary_hdu: PrimaryHDU) -> str:
        return primary_hdu.header['BUNIT']


    def _get_spectrogram_start_datetime(self, primary_hdu: PrimaryHDU) -> datetime:
        date_obs = primary_hdu.header['DATE-OBS']
        time_obs = primary_hdu.header['TIME-OBS']
        return datetime.strptime(f"{date_obs}T{time_obs}", TimeFormats.PRECISE_DATETIME)


    def _get_bintable_hdu(self, hdulist: HDUList) -> BinTableHDU:
        return hdulist[1]


    def _get_time_and_frequency(self, bintable_hdu: BinTableHDU) -> Tuple[np.ndarray, np.ndarray]:
        data = bintable_hdu.data
        times = data['TIME'][0]
        frequencies_MHz = data['FREQUENCY'][0]
        frequencies = frequencies_MHz * 1e6 # convert to Hz
        return times, frequencies

