# SPDX-FileCopyrightText: © 2024-2025 Jimmy Fitzpatrick <jcfitzpatrick12@gmail.com>
# This file is part of SPECTRE
# SPDX-License-Identifier: GPL-3.0-or-later

from datetime import datetime
from dataclasses import dataclass
from typing import Optional

import numpy as np
import numpy.typing as npt
from astropy.io import fits
from astropy.io.fits.hdu.image import PrimaryHDU
from astropy.io.fits.hdu.table import BinTableHDU
from astropy.io.fits.hdu.hdulist import HDUList

from spectre_core.exceptions import InvalidSweepMetadataError
from spectre_core.config import TimeFormat
from spectre_core.spectrograms import Spectrogram, SpectrumUnit
from ._batch_keys import BatchKey
from .._base import BaseBatch, BatchFile
from .._register import register_batch


@dataclass(frozen=True)
class _BatchExtension:
    """Supported extensions for a `IQStreamBatch`.

    :ivar FITS: Corresponds to the `.fits` file extension.
    :ivar BIN: Corresponds to the `.bin` file extension.
    :ivar HDR: Corresponds to the `.hdr` file extension.
    """

    FITS: str = "fits"
    BIN: str = "bin"
    HDR: str = "hdr"


class _BinFile(BatchFile[npt.NDArray[np.complex64]]):
    """Stores complex IQ samples in the binary format, as produced by the `gr-spectre`
    OOT module block `batched_file_sink`.
    """

    def __init__(self, batch_parent_dir_path: str, batch_name: str) -> None:
        """Initialise a `_BinFile` instance.

        :param batch_parent_dir_path: The parent directory for the batch.
        :param batch_name: The batch name.
        """
        super().__init__(batch_parent_dir_path, batch_name, _BatchExtension.BIN)

    def _read(self) -> npt.NDArray[np.complex64]:
        """Reads the binary file and returns the stored complex IQ samples.

        :return: The raw 32-bit floats in the binary file, interpreted as 64-bit complex IQ samples.
        """
        with open(self.file_path, "rb") as fh:
            return np.fromfile(fh, dtype=np.complex64)


@dataclass
class IQMetadata:
    """Represents metadata for IQ samples produced by the `gr-spectre` OOT module block `batched_file_sink`.

    :ivar millisecond_correction: The millisecond component of the batch start time.
    :ivar center_frequencies: Center frequencies for each IQ sample, if the stream was frequency tagged.
    None otherwise.
    :ivar num_samples: Number of samples collected at each center frequency, if the stream was frequency
    tagged. None otherwise.
    """

    millisecond_correction: int
    center_frequencies: Optional[npt.NDArray[np.float32]] = None
    num_samples: Optional[npt.NDArray[np.int32]] = None

    def is_frequency_tagged(self) -> bool:
        """Check if the IQ metadata contains frequency tagging information.

        :return: True if frequency tagging information is present; False otherwise.
        """
        return (self.center_frequencies is not None) and (self.num_samples is not None)


class _HdrFile(BatchFile[IQMetadata]):
    """Stores IQ sample metadata produced by the `gr-spectre` OOT module block `batched_file_sink`, used
    to help parse the corresponding `.bin` file.

    File Structure:
        - If frequency tagged:
            (`<millisecond_correction>`, `<freq_0>`, `<num_samples_0>`, `<freq_1>`, `<num_samples_1>`, ...)
            All values are stored as 32-bit floats.
            - The first value is the millisecond component for the batch start time.
            - Subsequent tuples (`<freq_n>`, `<num_samples_n>`) indicate that `<num_samples_n>` samples were collected at `<freq_n>`.
        - If not frequency tagged:
            (`<millisecond_correction>`)
            Only the millisecond correction is present, with no frequency information.

    This format enables mapping IQ samples in the binary file to their corresponding center frequencies, if applicable.
    """

    def __init__(self, parent_dir_path: str, base_file_name: str) -> None:
        """Initialise a `_HdrFile` instance.

        :param parent_dir_path: The parent directory for the batch.
        :param base_file_name: The batch name.
        """
        super().__init__(parent_dir_path, base_file_name, _BatchExtension.HDR)

    def _read(self) -> IQMetadata:
        """Parses the binary contents of the `.hdr` file to extract IQ sample metadata.

        :return: An instance of `IQMetadata` containing the parsed metadata, including the millisecond correction
        and, if applicable, frequency tagging details.
        """
        hdr_contents = self._extract_raw_contents()
        millisecond_correction = self._get_millisecond_correction(hdr_contents)
        if hdr_contents.size == 1:
            return IQMetadata(millisecond_correction)
        else:
            center_frequencies = self._get_center_frequencies(hdr_contents)
            num_samples = self._get_num_samples(hdr_contents)
            self._validate_frequencies_and_samples(center_frequencies, num_samples)
            return IQMetadata(millisecond_correction, center_frequencies, num_samples)

    def _extract_raw_contents(self) -> npt.NDArray[np.float32]:
        """Reads the raw contents of the `.hdr` file."""
        with open(self.file_path, "rb") as fh:
            # the `batched_file_sink` block in the `gr-spectre` GNU Radio OOT module stores
            # the integral millisecond component as a 32-bit float.
            return np.fromfile(fh, dtype=np.float32)

    def _get_millisecond_correction(self, hdr_contents: npt.NDArray[np.float32]) -> int:
        """Extracts and validates the millisecond component of the batch start time.

        The value is stored as a 32-bit float but interpreted as an integer.
        """
        millisecond_correction = float(hdr_contents[0])

        if not millisecond_correction.is_integer():
            raise TypeError(
                f"Expected integer value for millisecond correction, but got {millisecond_correction}"
            )

        return int(millisecond_correction)

    def _get_center_frequencies(
        self, hdr_contents: npt.NDArray[np.float32]
    ) -> npt.NDArray[np.float32]:
        """Extracts the center frequencies from the `.hdr` file contents.

        Center frequencies are stored at every second entry, starting from the first index.
        """
        return hdr_contents[1::2]

    def _get_num_samples(
        self, hdr_contents: npt.NDArray[np.float32]
    ) -> npt.NDArray[np.int32]:
        """Extracts the number of samples per frequency from the `.hdr` file contents.

        The values are stored as 32-bit floats but are interpreted as integers.
        Sample counts are located at every second entry, starting from the second index.
        """
        num_samples_as_float = hdr_contents[2::2]
        if not all(num_samples_as_float == num_samples_as_float.astype(int)):
            raise InvalidSweepMetadataError(
                "Number of samples per frequency is expected to describe an integer"
            )
        return num_samples_as_float.astype(np.int32)

    def _validate_frequencies_and_samples(
        self,
        center_frequencies: npt.NDArray[np.float32],
        num_samples: npt.NDArray[np.int32],
    ) -> None:
        """Ensures that each center frequency has a corresponding sample count."""
        if len(center_frequencies) != len(num_samples):
            raise InvalidSweepMetadataError(
                "Center frequencies and number of samples arrays are not the same length"
            )


class _FitsFile(BatchFile[Spectrogram]):
    """Stores spectrogram data in the FITS file format, as generated by `spectre` from a stream of IQ samples."""

    def __init__(self, parent_dir_path: str, base_file_name: str) -> None:
        """Initialise a `_FitsFile` instance.

        :param parent_dir_path: The parent directory for the batch.
        :param base_file_name: The batch name.
        """
        super().__init__(parent_dir_path, base_file_name, _BatchExtension.FITS)

    def _read(self) -> Spectrogram:
        """Read the FITS file and create a spectrogram.

        :return: A `Spectrogram` instance containing the parsed FITS file data.
        """
        with fits.open(self.file_path, mode="readonly") as hdulist:
            primary_hdu = self._get_primary_hdu(hdulist)
            dynamic_spectra = self._get_dynamic_spectra(primary_hdu)
            bunit = self._get_bunit(primary_hdu)
            spectrogram_start_datetime = self._get_spectrogram_start_datetime(
                primary_hdu
            )
            bintable_hdu = self._get_bintable_hdu(hdulist)
            times = self._get_times(bintable_hdu)
            frequencies = self._get_frequencies(bintable_hdu)

        # bunit is interpreted as a SpectrumUnit.
        spectrum_unit = SpectrumUnit(bunit)
        return Spectrogram(
            dynamic_spectra,
            times,
            frequencies,
            self.tag,
            spectrum_unit,
            spectrogram_start_datetime,
        )

    def _get_primary_hdu(self, hdulist: HDUList) -> PrimaryHDU:
        return hdulist["PRIMARY"]

    def _get_bintable_hdu(self, hdulist: HDUList) -> BinTableHDU:
        return hdulist[1]

    def _get_bunit(self, primary_hdu: PrimaryHDU) -> str:
        """Get the units corresponding to the elements of the dynamic spectra."""
        return primary_hdu.header["BUNIT"]

    def _get_dynamic_spectra(self, primary_hdu: PrimaryHDU) -> npt.NDArray[np.float32]:
        return primary_hdu.data

    def _get_spectrogram_start_datetime(self, primary_hdu: PrimaryHDU) -> datetime:
        """Get the start time of the spectrogram, up to the full precision available."""
        date_obs = primary_hdu.header["DATE-OBS"]
        time_obs = primary_hdu.header["TIME-OBS"]
        return datetime.strptime(f"{date_obs}T{time_obs}", TimeFormat.PRECISE_DATETIME)

    def _get_times(self, bintable_hdu: BinTableHDU) -> npt.NDArray[np.float32]:
        """Extracts the elapsed times for each spectrum in seconds, with the first spectrum set to t=0
        by convention.
        """
        return bintable_hdu.data["TIME"][0]  # already in seconds

    def _get_frequencies(self, bintable_hdu: BinTableHDU) -> npt.NDArray[np.float32]:
        """Extracts the frequencies for each spectral component."""
        frequencies_MHz = bintable_hdu.data["FREQUENCY"][0]
        return frequencies_MHz * 1e6  # convert to Hz


@register_batch(BatchKey.IQ_STREAM)
class IQStreamBatch(BaseBatch):
    """A batch of data derived from a stream of IQ samples from some receiver.

    Supports the following extensions:
    - `.fits` (via the `spectrogram_file` attribute)
    - `.bin` (via the `bin_file` attribute)
    - `.hdr` (via the `hdr_file` attribute)
    """

    def __init__(self, start_time: str, tag: str) -> None:
        """Initialise a `IQStreamBatch` instance.

        :param start_time: The start time of the batch.
        :param tag: The batch name tag.
        """
        super().__init__(start_time, tag)
        self._fits_file = _FitsFile(self.parent_dir_path, self.name)
        self._bin_file = _BinFile(self.parent_dir_path, self.name)
        self._hdr_file = _HdrFile(self.parent_dir_path, self.name)

        # add files formally to the batch
        self.add_file(self.spectrogram_file)
        self.add_file(self.bin_file)
        self.add_file(self.hdr_file)

    @property
    def spectrogram_file(self) -> _FitsFile:
        """The batch file corresponding to the `.fits` extension."""
        return self._fits_file

    @property
    def bin_file(self) -> _BinFile:
        """The batch file corresponding to the `.bin` extension."""
        return self._bin_file

    @property
    def hdr_file(self) -> _HdrFile:
        """The batch file corresponding to the `.hdr` extension."""
        return self._hdr_file
