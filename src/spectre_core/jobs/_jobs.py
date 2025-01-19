# SPDX-FileCopyrightText: © 2024 Jimmy Fitzpatrick <jcfitzpatrick12@gmail.com>
# This file is part of SPECTRE
# SPDX-License-Identifier: GPL-3.0-or-later

from logging import getLogger
_LOGGER = getLogger(__name__)

from spectre_core.capture_configs import CaptureConfig
from spectre_core.logging import log_call
from spectre_core.receivers import get_receiver, ReceiverName
from spectre_core.post_processing import start_post_processor
from ._workers import as_worker, Worker


"""A job is a collection of one or more multiprocessing processes being executed by workers.

Each function in this module should create some workers to execute processes, and return the workers
managing them.
"""


@as_worker("capture")
@log_call
def capture(
    tag: str,
) -> None:
    """Start capturing data from an SDR in real time.

    :param tag: The capture config tag.
    """
    _LOGGER.info((f"Reading capture config with tag '{tag}'"))

    # load the receiver and mode from the capture config file
    capture_config = CaptureConfig(tag)

    _LOGGER.info((f"Starting capture with the receiver '{capture_config.receiver_name}' "
                  f"operating in mode '{capture_config.receiver_mode}' "
                  f"with tag '{tag}'"))

    name = ReceiverName( capture_config.receiver_name )
    receiver = get_receiver(name,
                            capture_config.receiver_mode)
    receiver.start_capture(tag)


@as_worker("post_processing")
@log_call
def post_process(
    tag: str,
) -> None:
    """Start post processing SDR data into spectrograms in real time.

    :param tag: The capture config tag.
    """
    _LOGGER.info(f"Starting post processor with tag '{tag}'")
    start_post_processor(tag)

    
@log_call
def session(
    tag: str,
) -> list[Worker]:
    """Start a session.
    
    When the function is called, two workers are started. One which captures the 
    data from the SDR, and one which post processes that data in real time into 
    spectrograms.

    :param tag: The capture config tag.
    :return: The workers managing the capture and postprocessing respectively.
    """
    post_process_worker = post_process(tag)
    capture_worker      = capture(tag)
    return [capture_worker, post_process_worker]

