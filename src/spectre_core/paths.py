# SPDX-FileCopyrightText: © 2024 Jimmy Fitzpatrick <jcfitzpatrick12@gmail.com>
# This file is part of SPECTRE
# SPDX-License-Identifier: GPL-3.0-or-later

import os
from importlib import import_module

SPECTRE_DATA_DIR_PATH = os.environ.get("SPECTRE_DATA_DIR_PATH")
if SPECTRE_DATA_DIR_PATH is None:
    raise ValueError("The environment variable SPECTRE_DATA_DIR_PATH has not been set")

_CHUNKS_DIR_PATH = os.environ.get("SPECTRE_CHUNKS_DIR_PATH", 
                                  os.path.join(SPECTRE_DATA_DIR_PATH, 'chunks'))
os.makedirs(_CHUNKS_DIR_PATH, 
            exist_ok=True)

_LOGS_DIR_PATH = os.environ.get("SPECTRE_LOGS_DIR_PATH",
                               os.path.join(SPECTRE_DATA_DIR_PATH, 'logs'))
os.makedirs(_LOGS_DIR_PATH, 
            exist_ok=True)

_CONFIGS_DIR_PATH = os.environ.get("SPECTRE_CONFIGS_DIR_PATH",
                                  os.path.join(SPECTRE_DATA_DIR_PATH, "configs"))
os.makedirs(_CONFIGS_DIR_PATH, 
            exist_ok=True)


def import_target_modules(caller_file: str, # __file__ in the calling context for the library
                          caller_name: str, # __name__ in the calling context for the library
                          target_module: str # the module we are looking to dynamically import
) -> None: 
    # fetch the directory path for the __init__.py in the library directory
    library_dir_path = os.path.dirname(caller_file)
    # list all subdirectories in the library directory
    subdirs = [x.name for x in os.scandir(library_dir_path) if x.is_dir() and (x.name != "__pycache__")]
    # for each subdirectory, try and import the target module
    for subdir in subdirs:
        full_module_name = f"{caller_name}.{subdir}.{target_module}"
        import_module(full_module_name)


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