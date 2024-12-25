# SPDX-FileCopyrightText: © 2024 Jimmy Fitzpatrick <jcfitzpatrick12@gmail.com>
# This file is part of SPECTRE
# SPDX-License-Identifier: GPL-3.0-or-later

import os
import logging
from datetime import datetime

from spectre_core.config import TimeFormats
from ._log_handlers import LogHandler

def configure_root_logger(process_type: str, 
                          level: int = logging.INFO
) -> LogHandler:
    system_datetime = datetime.now()
    datetime_stamp = system_datetime.strftime(TimeFormats.DATETIME)
    pid = os.getpid()
    log_handler = LogHandler(datetime_stamp, pid, process_type)
    log_handler.make_parent_path()

    # configure the root logger
    logger = logging.getLogger()
    logger.setLevel(level)
    # Remove any existing handlers to avoid duplicate logs
    for handler in logger.handlers:
        logger.removeHandler(handler)
    # Set up file handler with specific filename
    file_handler = logging.FileHandler(log_handler.file_path)
    file_handler.setLevel(level)
    formatter = logging.Formatter("[%(asctime)s] [%(levelname)8s] --- %(message)s (%(name)s:%(lineno)s)")
    file_handler.setFormatter(formatter)
    # and add it to the root logger
    logger.addHandler(file_handler)

    return log_handler