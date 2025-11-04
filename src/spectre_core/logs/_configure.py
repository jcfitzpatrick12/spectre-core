# SPDX-FileCopyrightText: © 2024-2025 Jimmy Fitzpatrick <jcfitzpatrick12@gmail.com>
# This file is part of SPECTRE
# SPDX-License-Identifier: GPL-3.0-or-later

import os
import logging
import datetime
import typing

import spectre_core.config
from ._process_types import ProcessType


def configure_root_logger(
    process_type: ProcessType,
    level: int = logging.INFO,
    logs_dir_path: typing.Optional[str] = None,
) -> str:
    # Get the root logger, set its level and remove any existing handlers.
    logger = logging.getLogger()
    logger.setLevel(level)
    for handler in logger.handlers:
        logger.removeHandler(handler)

    # Get the current system time and current process ID.
    system_datetime = datetime.datetime.now()
    start_time = system_datetime.strftime(spectre_core.config.TimeFormat.DATETIME)
    pid = str(os.getpid())

    # Make the file path.
    if logs_dir_path is None:
        logs_dir_path = spectre_core.config.paths.get_logs_dir_path(
            system_datetime.year, system_datetime.month, system_datetime.day
        )
    if not os.path.exists(logs_dir_path):
        os.makedirs(logs_dir_path)
    file_path = os.path.join(
        logs_dir_path, f"{start_time}_{pid}_{process_type.value}.log"
    )

    # Add the file handler to the root logger.
    file_handler = logging.FileHandler(file_path)
    file_handler.setLevel(level)
    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)8s] --- %(message)s (%(name)s:%(lineno)s)"
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return file_path


def get_root_logger_state() -> tuple[bool, int]:
    """Get the state of the root logger.

    :return: Whether the root logger has any handlers, and the level of the root logger.
    """
    root_logger = logging.getLogger()
    if root_logger.handlers:
        return True, root_logger.level
    return False, logging.NOTSET
