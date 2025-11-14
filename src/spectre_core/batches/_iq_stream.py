# SPDX-FileCopyrightText: © 2024-2025 Jimmy Fitzpatrick <jcfitzpatrick12@gmail.com>
# This file is part of SPECTRE
# SPDX-License-Identifier: GPL-3.0-or-later

import datetime
import dataclasses
import typing

import numpy as np
import numpy.typing as npt
import astropy.io

import spectre_core.exceptions
import spectre_core.config
import spectre_core.spectrograms

from ._base import Base, BatchFile


@dataclasses.dataclass(frozen=True)
class IQStreamBatchExtension:
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

    def read(self) -> npt.NDArray[np.complex64]:
        """Reads the binary file and returns the stored complex IQ samples.

        :return: The raw 32-bit floats are interpreted as 64-bit complex IQ samples.
        """
        return np.fromfile(self.file_path, dtype=np.complex64)


@dataclasses.dataclass
class IQMetadata:
    """Stores metadata produced by the `gr-spectre` OOT module block `batched_file_sink`.

    :ivar millisecond_correction: The millisecond component of the batch start time.
    :ivar center_frequencies: Center frequencies for each IQ sample, if the stream was frequency tagged.
    None otherwise.
    :ivar num_samples: Number of samples collected at each center frequency, if the stream was frequency
    tagged. None otherwise.
    """

    millisecond_correction: int
    center_frequencies: typing.Optional[npt.NDArray[np.float32]] = None
    num_samples: typing.Optional[npt.NDArray[np.int32]] = None

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

    def read(self) -> IQMetadata:
        """Parses the binary contents of the `.hdr` file to extract IQ sample metadata.

        :return: An instance of `IQMetadata` containing the parsed metadata, including the millisecond correction
        and, if applicable, frequency tag details.
        """
        hdr_contents = np.fromfile(self.file_path, dtype=np.float32)

        millisecond_correction_f = float(hdr_contents[0])
        if not millisecond_correction_f.is_integer():
            raise TypeError(
                f"Expected integer value for millisecond correction, but got {millisecond_correction_f}"
            )
        millisecond_correction = int(millisecond_correction_f)

        if hdr_contents.size == 1:
            return IQMetadata(millisecond_correction)
        else:
            # Center frequencies are stored at every second entry, starting from the first index.
            center_frequencies = hdr_contents[1::2]

            # Sample counts are located at every second entry, starting from the second index.
            # The values are stored as 32-bit floats but are interpreted as integers.
            num_samples_f = hdr_contents[2::2]
            if not all(num_samples_f == num_samples_f.astype(int)):
                raise spectre_core.exceptions.InvalidSweepMetadataError(
                    "Number of samples per frequency is expected to describe an integer"
                )
            num_samples = num_samples_f.astype(np.int32)

            if len(center_frequencies) != len(num_samples):
                raise spectre_core.exceptions.InvalidSweepMetadataError(
                    "Center frequencies and number of samples arrays are not the same length"
                )

            return IQMetadata(millisecond_correction, center_frequencies, num_samples)


class _FitsFile(BatchFile[spectre_core.spectrograms.Spectrogram]):
    """Stores spectrogram data in the FITS file format, as generated by Spectre from a stream of IQ samples."""

    def read(self) -> spectre_core.spectrograms.Spectrogram:
        """Read the FITS file and create a spectrogram.

        :return: A `Spectrogram` containing the parsed FITS file data.
        """
        with astropy.io.fits.open(self.file_path, mode="readonly") as hdulist:
            primary_hdu = hdulist["PRIMARY"]
            dynamic_spectra = primary_hdu.data
            bunit = primary_hdu.header["BUNIT"]

            date_obs = primary_hdu.header["DATE-OBS"]
            time_obs = primary_hdu.header["TIME-OBS"]
            spectrogram_start_datetime = datetime.datetime.strptime(
                f"{date_obs}T{time_obs}",
                spectre_core.config.TimeFormat.PRECISE_DATETIME,
            )

            bintable_hdu = hdulist[1]
            times = bintable_hdu.data["TIME"][0]
            frequencies = bintable_hdu.data["FREQUENCY"][0] * 1e6  # Convert to Hz

        # bunit is interpreted as a SpectrumUnit.
        spectrum_unit = spectre_core.spectrograms.SpectrumUnit(bunit)
        return spectre_core.spectrograms.Spectrogram(
            dynamic_spectra,
            times,
            frequencies,
            spectrum_unit,
            spectrogram_start_datetime,
        )


class IQStreamBatch(Base):

    def __init__(self, batches_dir_path: str, start_time: str, tag: str) -> None:
        """A batch of data derived from a stream of IQ samples from some receiver.

        Supports the following extensions:
        - `.fits`
        - `.bin`
        - `.hdr`


        :param start_time: The start time of the batch.
        :param tag: The batch name tag.
        """
        super().__init__(batches_dir_path, start_time, tag)

        self.add_file(_FitsFile, IQStreamBatchExtension.FITS)
        self.add_file(_BinFile, IQStreamBatchExtension.BIN)
        self.add_file(_HdrFile, IQStreamBatchExtension.HDR)

    @property
    def fits_file(self) -> _FitsFile:
        """The batch file corresponding to the `.fits` extension."""
        return typing.cast(_FitsFile, self.get_file(IQStreamBatchExtension.FITS))

    @property
    def bin_file(self) -> _BinFile:
        """The batch file corresponding to the `.bin` extension."""
        return typing.cast(_BinFile, self.get_file(IQStreamBatchExtension.BIN))

    @property
    def hdr_file(self) -> _HdrFile:
        """The batch file corresponding to the `.hdr` extension."""
        return typing.cast(_HdrFile, self.get_file(IQStreamBatchExtension.HDR))

    @property
    def spectrogram_file(self) -> _FitsFile:
        return self.fits_file
