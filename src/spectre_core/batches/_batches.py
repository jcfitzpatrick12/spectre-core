# SPDX-FileCopyrightText: © 2024-2025 Jimmy Fitzpatrick <jcfitzpatrick12@gmail.com>
# This file is part of SPECTRE
# SPDX-License-Identifier: GPL-3.0-or-later

import os
from typing import Optional, TypeVar, Type, Generic, Iterator
from collections import OrderedDict
from datetime import datetime

from spectre_core.config import TimeFormat
from spectre_core.spectrograms import Spectrogram, time_chop, join_spectrograms
from spectre_core.config import get_batches_dir_path
from spectre_core.exceptions import BatchNotFoundError
from ._base import BaseBatch, parse_batch_file_name

T = TypeVar("T", bound=BaseBatch)


class Batches(Generic[T]):
    """Managed collection of `Batch` instances for a given tag. Provides a simple
    interface for read operations on batched data files."""

    def __init__(
        self,
        tag: str,
        batch_cls: Type[T],
        year: Optional[int] = None,
        month: Optional[int] = None,
        day: Optional[int] = None,
    ) -> None:
        """Initialise a `Batches` instance.

        :param tag: The batch name tag.
        :param batch_cls: The `Batch` class used to read data files tagged by `tag`.
        :param year: Filter batch files under a numeric year. Defaults to None.
        :param month: Filter batch files under a numeric month. Defaults to None.
        :param day: Filter batch files under a numeric day. Defaults to None.
        """
        self._tag = tag
        self._batch_cls = batch_cls
        self._batch_map: dict[str, T] = OrderedDict()
        self.set_date(year, month, day)

    @property
    def tag(self) -> str:
        """The batch name tag."""
        return self._tag

    @property
    def batch_cls(self) -> Type[T]:
        """The `Batch` class used to read the batched files."""
        return self._batch_cls

    @property
    def year(self) -> Optional[int]:
        """The numeric year, to filter batch files."""
        return self._year

    @property
    def month(self) -> Optional[int]:
        """The numeric month of the year, to filter batch files."""
        return self._month

    @property
    def day(self) -> Optional[int]:
        """The numeric day of the year, to filter batch files."""
        return self._day

    @property
    def batches_dir_path(self) -> str:
        """The shared ancestral path for all the batches. `Batches` recursively searches
        this directory to find all batches whose batch name contains `tag`."""
        return get_batches_dir_path(self.year, self.month, self.day)

    @property
    def batch_list(self) -> list[T]:
        """A list of all batches found within `batches_dir_path`."""
        return list(self._batch_map.values())

    @property
    def start_times(self) -> list[str]:
        """The start times of each batch found within `batches_dir_path`."""
        return list(self._batch_map.keys())

    @property
    def num_batches(self) -> int:
        """The total number of batches found within `batches_dir_path`."""
        return len(self.batch_list)

    def set_date(
        self, year: Optional[int], month: Optional[int], day: Optional[int]
    ) -> None:
        """Reset `batches_dir_path` according to the numeric date, and refresh the list
        of available batches.

        :param year: Filter by the numeric year.
        :param month: Filter by the numeric month of the year.
        :param day: Filter by the numeric day of the month.
        """
        self._year = year
        self._month = month
        self._day = day
        self.update()

    def update(self) -> None:
        """Perform a fresh search all files in `batches_dir_path` for batches
        with `tag` in the batch name."""
        # reset cache
        self._batch_map = OrderedDict()

        # get a list of all batch file names in the batches directory path
        batch_file_names = [
            f for (_, _, files) in os.walk(self.batches_dir_path) for f in files
        ]
        for batch_file_name in batch_file_names:
            start_time, tag, _ = parse_batch_file_name(batch_file_name)
            if tag == self._tag:
                self._batch_map[start_time] = self.batch_cls(start_time, tag)

        self._batch_map = OrderedDict(sorted(self._batch_map.items()))

    def __iter__(self) -> Iterator[T]:
        """Iterate over the stored batch instances."""
        yield from self.batch_list

    def __len__(self):
        return self.num_batches

    def _get_from_start_time(self, start_time: str) -> T:
        """Find and return the `Batch` instance based on the string formatted start time."""
        try:
            return self._batch_map[start_time]
        except KeyError:
            raise BatchNotFoundError(
                f"Batch with start time {start_time} could not be found within {self.batches_dir_path}"
            )

    def _get_from_index(self, index: int) -> T:
        """Find and return the `Batch` instance based on its numeric index.

        Batches are ordered sequentially in time, so index `0` corresponds to the oldest
        `Batch` with respect to the start time.
        """
        if self.num_batches == 0:
            raise BatchNotFoundError("No batches are available")
        elif index > self.num_batches:
            raise IndexError(
                f"Index '{index}' is greater than the number of batches '{self.num_batches}'"
            )
        return self.batch_list[index]

    def __getitem__(self, subscript: str | int) -> T:
        """Get a `Batch` instanced based on either the start time or chronological index.

        :param subscript: If the subscript is a string, interpreted as a formatted start time.
        If the subscript is an integer, it is interpreted as a chronological index.
        :return: The corresponding `BaseBatch` subclass.
        """
        if isinstance(subscript, str):
            return self._get_from_start_time(subscript)
        elif isinstance(subscript, int):
            return self._get_from_index(subscript)

    def get_spectrogram(
        self, start_datetime: datetime, end_datetime: datetime
    ) -> Spectrogram:
        """
        Retrieve a spectrogram spanning the specified time range.

        :param start_datetime: The start time of the range (inclusive).
        :param end_datetime: The end time of the range (inclusive).
        :raises FileNotFoundError: If no spectrogram data is available within the specified time range.
        :return: A spectrogram created by stitching together data from all matching batches.
        """
        filtered_batches = self.filter_batches_by_start_time(
            start_datetime, end_datetime
        )
        existing_batches = self.filter_batches_by_existence(filtered_batches)
        spectrograms = self.load_spectrograms_from_batches(existing_batches)
        chopped_spectrograms = self.apply_time_chop_to_spectrograms(
            spectrograms, start_datetime, end_datetime
        )
    
        if not chopped_spectrograms:
            raise FileNotFoundError(
                f"No spectrogram data found for the time range {start_datetime} to {end_datetime}."
            )
        return join_spectrograms(chopped_spectrograms)

    def filter_batches_by_start_time(
        self, start_datetime: datetime, end_datetime: datetime
    ) -> list[T]:
        """Filter the available batches to only those that fall within the specified
        time range.

        :param start_datetime: The start time of the range (inclusive).
        :param end_datetime: The end time of the range (inclusive).
        :return: A list of `Batch` instances that fall within the specified time range.
        """
        filtered_batches = []
        batch_datetimes = [
            datetime.strptime(t, TimeFormat.DATETIME) for t in self.start_times
        ]
        for idx, batch in enumerate(self):
            this_start = batch_datetimes[idx]
            next_start = (
                batch_datetimes[idx + 1]
                if idx + 1 < len(batch_datetimes)
                else datetime.max
            )

            if start_datetime <= next_start and this_start <= end_datetime:
                filtered_batches.append(batch)

        return filtered_batches

    def filter_batches_by_existence(self, batches: list[T]) -> list[T]:
        """Filter the available batches to only those that have existing spectrogram files.

        :param batches: A list of `Batch` instances to filter.
        :return: A list of `Batch` instances that have existing spectrogram files.
        """
        return [batch for batch in batches if batch.spectrogram_file.exists]

    def load_spectrograms_from_batches(self, batches: list[T]) -> list[Spectrogram]:
        """Load spectrograms from the provided list of batches assuming their spectrogram files exist.

        :param batches: A list of `Batch` instances to load spectrograms from.
        :return: A list of `Spectrogram` instances loaded from the provided batches.
        """
        return [batch.read_spectrogram() for batch in batches]

    def apply_time_chop_to_spectrograms(
        self,
        spectrograms: list[Spectrogram],
        start_datetime: datetime,
        end_datetime: datetime,
    ) -> list[Spectrogram]:
        """Apply time chopping to a list of spectrograms based on the specified time range.

        :param spectrograms: A list of `Spectrogram` instances to apply time chopping to.
        :param start_datetime: The start time of the range (inclusive).
        :param end_datetime: The end time of the range (inclusive).
        :return: A list of `Spectrogram` instances after applying time chopping.
        """
        
        chopped = []
        for spectrogram in spectrograms:
            lower_bound = spectrogram.datetimes[0]
            upper_bound = spectrogram.datetimes[-1]
            if start_datetime <= upper_bound and lower_bound <= end_datetime:
                chopped.append(time_chop(spectrogram, start_datetime, end_datetime))
        return chopped
