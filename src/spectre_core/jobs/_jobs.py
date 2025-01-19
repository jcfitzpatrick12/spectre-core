# SPDX-FileCopyrightText: © 2024 Jimmy Fitzpatrick <jcfitzpatrick12@gmail.com>
# This file is part of SPECTRE
# SPDX-License-Identifier: GPL-3.0-or-later

from logging import getLogger
_LOGGER = getLogger(__name__)

from spectre_core.capture_configs import CaptureConfig
from spectre_core.receivers import get_receiver, ReceiverName
from spectre_core.post_processing import start_post_processor
from ._worker import as_worker


@as_worker("capture")
def capture(
    tag: str,
) -> None:
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
def post_process(
    tag: str,
) -> None:
    _LOGGER.info(f"Starting post processor with tag '{tag}'")
    start_post_processor(tag)
