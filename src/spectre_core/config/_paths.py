# SPDX-FileCopyrightText: © 2024 Jimmy Fitzpatrick <jcfitzpatrick12@gmail.com>
# This file is part of SPECTRE
# SPDX-License-Identifier: GPL-3.0-or-later

"""
File system path definitions.

By default, `spectre` uses the required environment variable `os.environ.get("SPECTRE_DATA_DIR_PATH)`
and creates three directories inside it:  

- `batches` -- to hold the batched data files.
- `logs` -- to log files generated at runtime.
- `configs` -- to hold the capture configuration files.

Each of these three directories can be customised using the optional environment variables

- `SPECTRE_BATCHES_DIR_PATH`
- `SPECTRE_LOGS_DIR_PATH`
- `SPECTRE_CONFIGS_DIR_PATH`

respectively.
"""

import os
from typing import Optional


_SPECTRE_DATA_DIR_PATH = os.environ.get("SPECTRE_DATA_DIR_PATH")
if _SPECTRE_DATA_DIR_PATH is None:
    raise ValueError("The environment variable SPECTRE_DATA_DIR_PATH has not been set")

_BATCHES_DIR_PATH = os.environ.get("SPECTRE_BATCHES_DIR_PATH", 
                                   os.path.join(_SPECTRE_DATA_DIR_PATH, 'batches'))
os.makedirs(_BATCHES_DIR_PATH, 
            exist_ok=True)

_LOGS_DIR_PATH = os.environ.get("SPECTRE_LOGS_DIR_PATH",
                               os.path.join(_SPECTRE_DATA_DIR_PATH, 'logs'))
os.makedirs(_LOGS_DIR_PATH, 
            exist_ok=True)

_CONFIGS_DIR_PATH = os.environ.get("SPECTRE_CONFIGS_DIR_PATH",
                                  os.path.join(_SPECTRE_DATA_DIR_PATH, "configs"))
os.makedirs(_CONFIGS_DIR_PATH, 
            exist_ok=True)


def get_spectre_data_dir_path(
) -> str:
    """The default ancestral path for all `spectre` file system data.

    Returns:
        The value stored by the `SPECTRE_DATA_DIR_PATH` environment variable.
    """
    return _SPECTRE_DATA_DIR_PATH


def _get_date_based_dir_path(
    base_dir: str, year: int = None, 
    month: int = None, day: int = None
) -> str:
    """Append a date-based directory onto the base directory.

    Arguments:
        base_dir -- The base directory to have the date directory appended to.

    Keyword Arguments:
        year -- Numeric year. (default: {None})
        month -- Numeric month. (default: {None})
        day -- Numeric day. (default: {None})

    Raises:
        ValueError: If a day is specified without the year or month.
        ValueError: If a month is specified with the year.

    Returns:
        If no date information is specified, returns `base_dir` unchanged.
        If the year is specified, returns `base_dir` / `year`.
        If the year and month is specified, returns `base_dir` / `year` / `month`
        If all of year month and day are specified, returns: `base_dir` / `year` / `month` / `day`
    """
    if day and not (year and month):
        raise ValueError("A day requires both a month and a year")
    if month and not year:
        raise ValueError("A month requires a year")
    
    date_dir_components = []
    if year:
        date_dir_components.append(f"{year:04}")
    if month:
        date_dir_components.append(f"{month:02}")
    if day:
        date_dir_components.append(f"{day:02}")
    
    return os.path.join(base_dir, *date_dir_components)


def get_batches_dir_path(
    year: Optional[int] = None, 
    month: Optional[int] = None, 
    day: Optional[int] = None
) -> str:
    """The directory in the file system containing the batched data files. Optionally, append
    a date based directory to the end of the path.

    Keyword Arguments:
        year -- The numeric year. (default: {None})
        month -- The numeric month. (default: {None})
        day -- The numeric day. (default: {None})

    Returns:
        If defined, the value stored by the `SPECTRE_BATCHES_DIR_PATH` environment variable.
        Otherwise, defaults to `SPECTRE_DATA_DIR_PATH` / `batches`.
    """
    return _get_date_based_dir_path(_BATCHES_DIR_PATH, 
                                    year, 
                                    month, 
                                    day)


def get_logs_dir_path(
    year: Optional[int] = None, 
    month: Optional[int] = None, 
    day: Optional[int] = None
) -> str:
    """The directory in the file system containing the log files generated at runtime. Optionally, append
    a date based directory to the end of the path.

    Keyword Arguments:
        year -- The numeric year. (default: {None})
        month -- The numeric month. (default: {None})
        day -- The numeric day. (default: {None})

    Returns:
        If defined, the value stored by the `SPECTRE_LOGS_DIR_PATH` environment variable.
        Otherwise, defaults to `SPECTRE_DATA_DIR_PATH` / `logs`.
    """
    return _get_date_based_dir_path(_LOGS_DIR_PATH, 
                                    year, 
                                    month, 
                                    day)


def get_configs_dir_path(
) -> str:
    """The directory in the file system containing the capture configuration files.

    Returns:
        If defined, the value stored by the `SPECTRE_CONFIGS_DIR_PATH` environment variable.
        Otherwise, defaults to `SPECTRE_DATA_DIR_PATH` / `configs`.
    """
    return _CONFIGS_DIR_PATH
