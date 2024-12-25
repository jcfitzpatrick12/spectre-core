# SPDX-FileCopyrightText: © 2024 Jimmy Fitzpatrick <jcfitzpatrick12@gmail.com>
# This file is part of SPECTRE
# SPDX-License-Identifier: GPL-3.0-or-later


from logging import getLogger
_LOGGER = getLogger(__name__)

import os
import logging
from dataclasses import dataclass
from typing import Optional
import warnings
from collections import OrderedDict
from datetime import datetime

from spectre_core._file_io import TextHandler
from spectre_core.config import get_logs_dir_path, TimeFormats

PROCESS_TYPES = [
    "user", 
    "worker"
]

def _validate_process_type(process_type: str
) -> None:
    if process_type not in PROCESS_TYPES:
        raise ValueError(f"Invalid process type: {process_type}. Expected one of {PROCESS_TYPES}")


class LogHandler(TextHandler):
    def __init__(self, 
                 datetime_stamp: str, 
                 pid: str, 
                 process_type: str):
        self._datetime_stamp = datetime_stamp
        self._pid = pid
        _validate_process_type(process_type)
        self._process_type = process_type

        dt = datetime.strptime(datetime_stamp, TimeFormats.DATETIME)
        parent_path = get_logs_dir_path(dt.year, dt.month, dt.day)
        base_file_name = f"{datetime_stamp}_{pid}_{process_type}"

        super().__init__(parent_path, base_file_name, extension = "log")
    

    @property
    def datetime_stamp(self) -> str:
        return self._datetime_stamp
    

    @property
    def pid(self) -> str:
        return self._pid
    

    @property
    def process_type(self) -> str:
        return self._process_type


class LogHandlers:
    def __init__(self, 
                 process_type: Optional[str] = None, 
                 year: Optional[int] = None, 
                 month: Optional[int] = None, 
                 day: Optional[int] = None):
        self._log_handler_map: dict[str, LogHandler] = OrderedDict()
        self._process_type = process_type
        self.set_date(year, month, day)


    @property
    def process_type(self) -> str:
        return self._process_type
    

    @property
    def year(self) -> Optional[int]:
        return self._year


    @property 
    def month(self) -> Optional[int]:
        return self._month
    

    @property
    def day(self) -> Optional[int]:
        return self._day


    @property
    def logs_dir_path(self) -> str:
        return get_logs_dir_path(self.year, self.month, self.day)


    @property 
    def log_handler_map(self) -> dict[str, LogHandler]:
        if not self._log_handler_map: # check for empty dictionary
            self._update_log_handler_map()
        return self._log_handler_map
        

    @property
    def log_handler_list(self) -> list[LogHandler]:
        return list(self.log_handler_map.values())


    @property
    def num_logs(self) -> int:
        return len(self.log_handler_list) 


    @property
    def file_names(self) -> list[str]:
        return list(self.log_handler_map.keys())


    def set_date(self, 
                 year: Optional[int],
                 month: Optional[int],
                 day: Optional[int]) -> None:
        self._year = year
        self._month = month
        self._day = day
        self._update_log_handler_map()


    def _update_log_handler_map(self) -> None:
        log_files = [f for (_, _, files) in os.walk(self.logs_dir_path) for f in files]

        if not log_files:
            warning_message = "No logs found, setting log map to an empty dictionary"
            _LOGGER.warning(warning_message)
            warnings.warn(warning_message)
            return

        for log_file in log_files:
            file_name, _ = os.path.splitext(log_file)
            log_start_time, pid, process_type = file_name.split("_")

            if self.process_type and process_type != self.process_type:
                continue

            self._log_handler_map[file_name] = LogHandler(log_start_time, pid, process_type)

        self._log_handler_map = OrderedDict(sorted(self._log_handler_map.items()))


    def update(self) -> None:
        """Public alias for setting log handler map"""
        self._update_log_handler_map()


    def __iter__(self):
        yield from self.log_handler_list


    def get_from_file_name(self, 
                           file_name: str) -> LogHandler:
        # auto strip the extension if present
        file_name, _ = os.path.splitext(file_name)
        try:
            return self.log_handler_map[file_name]
        except KeyError:
            raise FileNotFoundError(f"Log handler for file name '{file_name}' not found in log map")


    def get_from_pid(self, 
                     pid: str) -> LogHandler:
        for log_handler in self.log_handler_list:
            if log_handler.pid == pid:
                return log_handler
        raise FileNotFoundError(f"Log handler for PID '{pid}' not found in log map")