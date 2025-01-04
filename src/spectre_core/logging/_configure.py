# SPDX-FileCopyrightText: © 2024 Jimmy Fitzpatrick <jcfitzpatrick12@gmail.com>
# This file is part of SPECTRE
# SPDX-License-Identifier: GPL-3.0-or-later

import os
import logging
from datetime import datetime
from typing import Literal

from spectre_core.config import TimeFormats
from ._log_handlers import LogHandler
from ._process_types import ProcessTypes


def configure_root_logger(
    process_type: Literal[ProcessTypes.USER, ProcessTypes.WORKER], 
    level: int = logging.INFO
) -> str:
    """Sets up the root logger to write log messages to a date-based log file.

    Arguments:
        process_type: Indicates whether the process is user-initiated or created internally 
                      by `spectre`. Accepts values from `ProcessTypes`.
    
    Keyword Arguments:
        level: The logging level, as defined in Python's `logging` module (default: logging.INFO).
    
    Returns:
        str: The file path of the created log file.
    """

    # create a `spectre` log handler instance, to represent the log file.
    # get the star time of the log
    system_datetime = datetime.now()
    start_time = system_datetime.strftime(TimeFormats.DATETIME)
    
    # extract the process identifier, and cast as a string
    pid = str( os.getpid() )
    
    log_handler = LogHandler(start_time, 
                             pid, 
                             process_type.value)
    log_handler.make_parent_dir_path()

    # configure the root logger level and remove any existing handlers.
    logger = logging.getLogger()
    logger.setLevel(level)
    for handler in logger.handlers:
        logger.removeHandler(handler)
        
    # Set up `logging` module specific file handler
    file_handler = logging.FileHandler(log_handler.file_path)
    file_handler.setLevel(level)
    formatter = logging.Formatter("[%(asctime)s] [%(levelname)8s] --- %(message)s (%(name)s:%(lineno)s)")
    file_handler.setFormatter(formatter)
    # and add it to the root logger
    logger.addHandler(file_handler)

    return log_handler.file_path