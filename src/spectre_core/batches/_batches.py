# SPDX-FileCopyrightText: © 2024 Jimmy Fitzpatrick <jcfitzpatrick12@gmail.com>
# This file is part of SPECTRE
# SPDX-License-Identifier: GPL-3.0-or-later

from logging import getLogger
_LOGGER = getLogger(__name__)

import os
from typing import Optional
from collections import OrderedDict
import warnings
from datetime import datetime

from spectre_core.spectrograms import Spectrogram, time_chop, join_spectrograms
from spectre_core.config import get_batches_dir_path, TimeFormats
from spectre_core.exceptions import (
    SpectrogramNotFoundError,
    BatchNotFoundError
)
from ._base import BaseBatch
from ._factory import get_batch_cls_from_tag

class Batches:
    """A collection of batches for a given day of the year."""
    def __init__(self, 
                 tag: str,
                 year: Optional[int] = None, 
                 month: Optional[int] = None, 
                 day: Optional[int] = None):
        self._tag = tag
        self._Batch = get_batch_cls_from_tag(tag)
        self._batch_map: dict[str, BaseBatch] = OrderedDict()
        self.set_date(year, month, day)


    @property
    def tag(self) -> str:
        """Tag identifier for each batch."""
        return self._tag


    @property
    def year(self) -> int:
        """The numeric year."""
        return self._year


    @property 
    def month(self) -> int:
        """The numeric month of the year."""
        return self._month
    

    @property
    def day(self) -> int:
        """The numeric day of the year."""
        return self._day
    

    @property
    def batches_dir_path(self) -> str:
        """The parent directory for all the batches."""
        return get_batches_dir_path(self.year, self.month, self.day)
    

    @property
    def batch_list(self) -> list[BaseBatch]:
        """A list of all the batch instances."""
        return  list(self._batch_map.values())
    

    @property
    def start_times(self) -> list[str]:
        """The start times of each batch."""
        return list(self._batch_map.keys())


    @property
    def num_batches(self) -> int:
        """The number of batches in the batch parent directory."""
        return len(self.batch_list)


    def set_date(self, 
                 year: Optional[int],
                 month: Optional[int],
                 day: Optional[int]) -> None:
        """Update the parent directory for the batches according to the numeric date."""
        self._year = year
        self._month = month
        self._day = day
        self._update_batch_map()


    def _update_batch_map(self) -> None:
        # reset cache
        self._batch_map = OrderedDict() 
        
        # get a list of all batch file names in the batches directory path
        batch_file_names = [f for (_, _, files) in os.walk(self.batches_dir_path) for f in files]
        for batch_file_name in batch_file_names:
            # strip the extension
            batch_name, _ = os.path.splitext(batch_file_name)
            start_time, tag = batch_name.split("_", 1)
            if tag == self._tag:
                self._batch_map[start_time] = self._Batch(start_time, tag)
        
        self._batch_map = OrderedDict(sorted(self._batch_map.items()))


    def update(self) -> None:
        """Public alias for setting batch map"""
        self._update_batch_map()
    

    def __iter__(self):
        """Iterate over the stored batch instances."""
        yield from self.batch_list


    def _get_from_start_time(self, 
                             start_time: str) -> BaseBatch:
        """Get the batch according to the input start time."""
        try:
            return self._batch_map[start_time]
        except KeyError:
            raise BatchNotFoundError(f"Batch with start time {start_time} could not be found within {self.batches_dir_path}")


    def _get_from_index(self, 
                        index: int) -> BaseBatch:
        """Get the batch according to its index, where the batches are ordered in time."""
        num_batches = len(self.batch_list)
        if num_batches == 0:
            raise BatchNotFoundError("No batches are available")
        index = index % num_batches  # Use modulo to make the index wrap around. Allows the user to iterate over all the batches via index cyclically.
        return self.batch_list[index]


    def __getitem__(self, subscript: str | int):
        if isinstance(subscript, str):
            return self._get_from_start_time(subscript)
        elif isinstance(subscript, int):
            return self._get_from_index(subscript)
    

    def num_batch_files(self, 
                        extension: str) -> int:
        """Get the number of existing batch files with the given extension."""
        return sum(1 for batch_file in self if batch_file.has_file(extension))


    def get_spectrogram_from_range(self, 
                                   start_time: str, 
                                   end_time: str) -> Spectrogram:
        """Return a spectrogram over the input time range."""
        # Convert input strings to datetime objects
        start_datetime = datetime.strptime(start_time, TimeFormats.DATETIME)
        end_datetime   = datetime.strptime(end_time, TimeFormats.DATETIME)

        if start_datetime.day != end_datetime.day:
            warning_message = "Joining spectrograms across multiple days"
            _LOGGER.warning(warning_message)
            warnings.warn(warning_message, RuntimeWarning)

        spectrograms = []
        num_fits_batch_files = self.num_batch_files("fits")

        for i, batch in enumerate(self):
            # skip batches without fits files
            if not batch.has_file("fits"):
                continue
            
            # rather than reading all files to evaluate the actual upper bound to their time range (slow)
            # place an upper bound by using the start datetime for the next batch
            # this assumes that the batches are non-overlapping (reasonable assumption)
            lower_bound = batch.start_datetime
            if i < num_fits_batch_files:
                next_batch = self[i + 1]
                upper_bound = next_batch.start_datetime
            # if there is no "next batch" then we do have to read the file
            else:
                fits_batch = batch.get_file("fits")
                upper_bound = fits_batch.datetimes[-1]

            # if the batch overlaps with the input time range, then read the fits file
            if start_datetime <= upper_bound and lower_bound <= end_datetime:
                spectrogram = batch.read_file("fits")
                spectrogram = time_chop(spectrogram, start_time, end_time)
                # if we have a non-empty spectrogram, append it to the list of spectrograms
                if spectrogram:
                    spectrograms.append(spectrogram)

        if spectrograms:
            return join_spectrograms(spectrograms)
        else:
            raise SpectrogramNotFoundError("No spectrogram data found for the given time range")
