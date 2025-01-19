# SPDX-FileCopyrightText: © 2024 Jimmy Fitzpatrick <jcfitzpatrick12@gmail.com>
# This file is part of SPECTRE
# SPDX-License-Identifier: GPL-3.0-or-later

import os
import logging
from typing import Tuple
from datetime import datetime

from spectre_core.config import TimeFormat
from ._logs import Log
from ._process_types import ProcessType


def configure_root_logger(
    process_type: ProcessType, 
    level: int = logging.INFO
) -> str:
    """Configures the root logger to write logs to a file named based on 
    the process type, process ID, and the current system time.

    :param process_type: Indicates the type of process, as defined by `ProcessType`.
    :param level: The logging level, as defined in Python's `logging` module. Defaults to `logging.INFO`.
    :return: The file path of the created log file.
    """
    # create a `spectre` log handler instance, to represent the log file.
    # get the star time of the log
    system_datetime = datetime.now()
    start_time = system_datetime.strftime(TimeFormat.DATETIME)
    
    # extract the process identifier, and cast as a string
    pid = str( os.getpid() )
    
    # create a file handler representing the log file
    log = Log(start_time, 
              pid, 
              process_type)
    log.make_parent_dir_path()

    # get the root logger and set its level.
    logger = logging.getLogger()
    logger.setLevel(level)
    
    # remove existing handlers
    for handler in logger.handlers:
        logger.removeHandler(handler)
        
    # Set up a file handler and add it to the root logger
    file_handler = logging.FileHandler(log.file_path)
    file_handler.setLevel(level)
    formatter = logging.Formatter("[%(asctime)s] [%(levelname)8s] --- %(message)s (%(name)s:%(lineno)s)")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return log.file_path


def get_root_logger_state(
) -> Tuple[bool, int]:
    """Get the state of the root logger.

    :return: Whether the root logger has any handlers, and the level of the root logger.
    """
    root_logger = logging.getLogger()
    if root_logger.handlers:
        return True, root_logger.level
    return False, logging.NOTSET