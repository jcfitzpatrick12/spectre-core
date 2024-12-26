# SPDX-FileCopyrightText: © 2024 Jimmy Fitzpatrick <jcfitzpatrick12@gmail.com>
# This file is part of SPECTRE
# SPDX-License-Identifier: GPL-3.0-or-later

from typing import Tuple
from dataclasses import dataclass

import numpy as np

from spectre_core.exceptions import InvalidSweepMetadataError
from spectre_core.capture_configs import CaptureModes
from ._fixed_center_frequency import BinChunk, FitsChunk
from .._register import register_chunk
from .._base import BaseChunk, ChunkFile


@dataclass
class SweepMetadata:
    """Wrapper for metadata required to assign center frequencies to each IQ sample in the chunk.
    
    center_frequencies is an ordered list containing all the center frequencies that the IQ samples
    were collected at. Typically, these will be ordered in "steps", where each step corresponds to
    IQ samples collected at a constant center frequency:

    (freq_0, freq_1, ..., freq_M, freq_0, freq_1, ..., freq_M, ...), freq_0 < freq_1 < ... < freq_M

    The n'th element of the num_samples list, tells us how many samples were collected at the n'th
    element of center_frequencies:
chunks.library.fixed_center_frequency.chunk import (
    BinChunk, FitsChunk
)
    Number of samples: (num_samples_at_freq_0, num_samples_at_freq_1, ...)

    Both these lists together allow us to map for each IQ sample, the center frequency it was collected at.
    """
    center_frequencies: np.ndarray
    num_samples: np.ndarray


@register_chunk(CaptureModes.SWEPT_CENTER_FREQUENCY)
class _Chunk(BaseChunk):
    def __init__(self, chunk_start_time, tag):
        super().__init__(chunk_start_time, tag)

        self.add_file(BinChunk(self.chunk_parent_path, self.chunk_name))
        self.add_file(FitsChunk(self.chunk_parent_path, self.chunk_name))
        self.add_file(HdrChunk(self.chunk_parent_path, self.chunk_name))

    
class HdrChunk(ChunkFile):
    def __init__(self, chunk_parent_path: str, chunk_name: str):
        super().__init__(chunk_parent_path, chunk_name, "hdr")

    def read(self) -> Tuple[int, SweepMetadata]:
        hdr_contents = self._read_file_contents()
        millisecond_correction = self._get_millisecond_correction(hdr_contents)
        center_frequencies = self._get_center_frequencies(hdr_contents)
        num_samples = self._get_num_samples(hdr_contents)
        self._validate_frequencies_and_samples(center_frequencies, 
                                               num_samples)
        return millisecond_correction, SweepMetadata(center_frequencies, num_samples)
        

    def _read_file_contents(self) -> np.ndarray:
        with open(self.file_path, "rb") as fh:
            return np.fromfile(fh, dtype=np.float32)


    def _get_millisecond_correction(self, hdr_contents: np.ndarray) -> int:
        ''' Millisecond correction is an integral quantity, but stored in the detached header as a 32-bit float.'''
        millisecond_correction_as_float = float(hdr_contents[0])

        if not millisecond_correction_as_float.is_integer():
            raise TypeError(f"Expected integer value for millisecond correction, but got {millisecond_correction_as_float}")
        
        return int(millisecond_correction_as_float)


    def _get_center_frequencies(self, hdr_contents: np.ndarray) -> np.ndarray:
        ''' 
        Detached header contents are stored in (center_freq_i, num_samples_at_center_freq_i) pairs
        Return only a list of center frequencies, by skipping over file contents in twos.
        '''
        return hdr_contents[1::2]


    def _get_num_samples(self, hdr_contents: np.ndarray) -> np.ndarray:
        ''' 
        Detached header contents are stored in (center_freq_i, num_samples_at_center_freq_i) pairs
        Return only the number of samples at each center frequency, by skipping over file contents in twos.
        Number of samples is an integral quantity, but stored in the detached header as a 32-bit float.
        Types are checked before return.
        '''
        num_samples_as_float = hdr_contents[2::2]
        if not all(num_samples_as_float == num_samples_as_float.astype(int)):
            raise InvalidSweepMetadataError("Number of samples per frequency is expected to describe an integer")
        return num_samples_as_float.astype(int)


    def _validate_frequencies_and_samples(self, center_frequencies: np.ndarray, num_samples: np.ndarray) -> None:
        """Validates that the center frequencies and the number of samples arrays have the same length."""
        if len(center_frequencies) != len(num_samples):
            raise InvalidSweepMetadataError("Center frequencies and number of samples arrays are not the same length")
