# SPDX-FileCopyrightText: © 2024 Jimmy Fitzpatrick <jcfitzpatrick12@gmail.com>
# This file is part of SPECTRE
# SPDX-License-Identifier: GPL-3.0-or-later

import os
import logging
from datetime import datetime

from spectre_core.config import TimeFormats
from ._log_handlers import Log
from ._process_types import ProcessType


def configure_root_logger(
    process_type: ProcessType, 
    level: int = logging.INFO
) -> str:
    """Sets up the root logger to write log messages to a date-based log file.

    :param process_type: Indicates the type of process, as defined by `ProcessType`.
    :param level: The logging level, as defined in Python's `logging` module. Defaults to logging.INFO.
    :return: The file path of the created log file.
    """
    # create a `spectre` log handler instance, to represent the log file.
    # get the star time of the log
    system_datetime = datetime.now()
    start_time = system_datetime.strftime(TimeFormats.DATETIME)
    
    # extract the process identifier, and cast as a string
    pid = str( os.getpid() )
    
    # create a file handler representing the log file
    log = Log(start_time, 
              pid, 
              process_type)
    log.make_parent_dir_path()

    # configure the root logger level and remove any existing handlers.
    logger = logging.getLogger()
    logger.setLevel(level)
    for handler in logger.handlers:
        logger.removeHandler(handler)
        
    # Set up `logging` module specific file handler
    file_handler = logging.FileHandler(log.file_path)
    file_handler.setLevel(level)
    formatter = logging.Formatter("[%(asctime)s] [%(levelname)8s] --- %(message)s (%(name)s:%(lineno)s)")
    file_handler.setFormatter(formatter)
    # and add it to the root logger
    logger.addHandler(file_handler)

    return log.file_path