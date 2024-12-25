# SPDX-FileCopyrightText: © 2024 Jimmy Fitzpatrick <jcfitzpatrick12@gmail.com>
# This file is part of SPECTRE
# SPDX-License-Identifier: GPL-3.0-or-later

"""
SPECTRE data paths.
"""

import os

_SPECTRE_DATA_DIR_PATH = os.environ.get("SPECTRE_DATA_DIR_PATH")
if _SPECTRE_DATA_DIR_PATH is None:
    raise ValueError("The environment variable SPECTRE_DATA_DIR_PATH has not been set")

_CHUNKS_DIR_PATH = os.environ.get("SPECTRE_CHUNKS_DIR_PATH", 
                                  os.path.join(_SPECTRE_DATA_DIR_PATH, 'chunks'))
os.makedirs(_CHUNKS_DIR_PATH, 
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
    return _SPECTRE_DATA_DIR_PATH


def _get_date_based_dir_path(base_dir: str, year: int = None, 
                             month: int = None, day: int = None
) -> str:
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


def get_chunks_dir_path(year: int = None, 
                        month: int = None, 
                        day: int = None
) -> str:
    return _get_date_based_dir_path(_CHUNKS_DIR_PATH, 
                                    year, 
                                    month, 
                                    day)


def get_logs_dir_path(year: int = None, 
                      month: int = None, 
                      day: int = None
) -> str:
    return _get_date_based_dir_path(_LOGS_DIR_PATH, 
                                    year, 
                                    month, 
                                    day)


def get_configs_dir_path(
) -> str:
    return _CONFIGS_DIR_PATH
