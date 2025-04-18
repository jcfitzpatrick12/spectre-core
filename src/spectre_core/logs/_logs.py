# SPDX-FileCopyrightText: © 2024 Jimmy Fitzpatrick <jcfitzpatrick12@gmail.com>
# This file is part of SPECTRE
# SPDX-License-Identifier: GPL-3.0-or-later

from logging import getLogger
_LOGGER = getLogger(__name__)

import os
from typing import Optional, Iterator, Tuple
from collections import OrderedDict
from datetime import datetime

from spectre_core._file_io import TextHandler
from spectre_core.config import get_logs_dir_path, TimeFormat
from ._process_types import ProcessType


def parse_log_base_file_name(
    base_file_name: str
) -> Tuple[str, str, str]:
    """Parse the base file name of a log into a start time, process ID and process type.
    """
    file_name, _ = os.path.splitext(base_file_name)
    log_start_time, pid, process_type = file_name.split("_")
    return log_start_time, pid, process_type


class Log(TextHandler):
    """Interface to read log files generated by `spectre`."""
    def __init__(
        self, 
        start_time: str, 
        pid: str, 
        process_type: ProcessType
    ) -> None:
        """Initialise a `Log` instance.

        :param start_time: The timestamp when the log file was created.
        :param pid: The ID of the process writing to the log file.
        :param process_type: Indicates the type of process, as defined by `ProcessType`.
        """
        self._start_time = start_time
        self._pid = pid
        self._process_type = process_type.value

        dt = datetime.strptime(start_time, TimeFormat.DATETIME)
        parent_path = get_logs_dir_path(dt.year, dt.month, dt.day)
        base_file_name = f"{start_time}_{pid}_{process_type.value}"

        super().__init__(parent_path, base_file_name, "log")
    

    @property
    def start_time(
        self
    ) -> str:
        """The system time when the log was created."""
        return self._start_time
    

    @property
    def pid(
        self
    ) -> str:
        """The ID of the process writing to the log file."""
        return self._pid
    

    @property
    def process_type(
        self
    ) -> str:
        """Indicates the type of process, as defined by `ProcessType`."""
        return self._process_type


class Logs:
    """Filter and read a collection of logs generated by `spectre`."""
    def __init__(
        self, 
        process_type: Optional[ProcessType] = None, 
        year: Optional[int] = None, 
        month: Optional[int] = None, 
        day: Optional[int] = None
    ) -> None:
        """Initialise a `Logs` instance.

        :param process_type: Filter by the process type. Defaults to None.
        :param year: Filter by the numeric year. Defaults to None.
        :param month: Filter by the numeric month. Defaults to None.
        :param day: Filter by the numeric day. Defaults to None.
        """
        self._process_type = process_type.value if process_type is not None else None
            
        self._log_map: dict[str, Log] = OrderedDict()
        self.set_date(year, month, day)


    @property
    def process_type(
        self
    ) -> Optional[str]:
        """Indicates the type of process, as defined by `ProcessType`."""
        return self._process_type
    

    @property
    def year(
        self
    ) -> Optional[int]:
        """Filter by the numeric year."""
        return self._year


    @property 
    def month(
        self
    ) -> Optional[int]:
        """Filter by the numeric month."""
        return self._month
    

    @property
    def day(
        self
    ) -> Optional[int]:
        """Filter by the numeric day."""
        return self._day


    @property
    def logs_dir_path(
        self
    ) -> str:
        """The shared ancestral path for all the log files. `Logs` recursively searches
        this directory to find all log files according to the date and process type."""
        return get_logs_dir_path(self.year, self.month, self.day)
        

    @property
    def log_list(
        self
    ) -> list[Log]:
        """A list of all log handlers representing files found within `logs_dir_path`."""
        return list(self._log_map.values())


    @property
    def num_logs(
        self
    ) -> int:
        """The number of log files found within `logs_dir_path`."""
        return len(self.log_list) 


    @property
    def file_names(
        self
    ) -> list[str]:
        """A list of all log file names found within `logs_dir_path`."""
        return list(self._log_map.keys())


    def set_date(
        self, 
        year: Optional[int],
        month: Optional[int],
        day: Optional[int]
    ) -> None:
        """Reset `logs_dir_path` according to the numeric date, and refresh the list
        of available log files.

        :param year: The numeric year.
        :param month: The numeric month of the year.
        :param day: The numeric day of the month.
        """
        self._year = year
        self._month = month
        self._day = day
        self.update()


    def update(
        self
    ) -> None:
        """Perform a fresh search of all files in `logs_dir_path` for log files
        according to the date and process type."""
        log_files = [f for (_, _, files) in os.walk(self.logs_dir_path) for f in files]

        for log_file in log_files:
            
            log_start_time, pid, process_type = parse_log_base_file_name(log_file)

            if self.process_type and process_type != self.process_type:
                continue

            self._log_map[log_file] = Log(log_start_time, pid, ProcessType(process_type))

        self._log_map = OrderedDict(sorted(self._log_map.items()))


    def __iter__(
        self
    ) -> Iterator[Log]:
        yield from self.log_list


    def get_from_file_name(
        self, 
        file_name: str
    ) -> Log:
        """Retrieve a `Log` instance based on the log file name.

        :param file_name: The name of the log file (with or without extension).
        :raises FileNotFoundError: If the log file name is not found.
        :return: The `Log` instance corresponding to the file name.
        """
        # auto strip the extension if present
        file_name, _ = os.path.splitext(file_name)
        try:
            return self._log_map[file_name]
        except KeyError:
            raise FileNotFoundError(f"Log handler for file name '{file_name}' not found in log map")


    def get_from_pid(
        self, 
        pid: str
    ) -> Log:
        """Retrieve a `Log` instance based on the process ID.

        :param pid: The process ID to search for.
        :raises FileNotFoundError: If a log file corresponding to the process ID is not found.
        :return: The `Log` instance corresponding to the process ID.
        """
        for log in self.log_list:
            if log.pid == pid:
                return log
        raise FileNotFoundError(f"Log handler for PID '{pid}' could not be identified")
