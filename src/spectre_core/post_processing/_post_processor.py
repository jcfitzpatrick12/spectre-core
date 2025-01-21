# SPDX-FileCopyrightText: © 2024 Jimmy Fitzpatrick <jcfitzpatrick12@gmail.com>
# This file is part of SPECTRE
# SPDX-License-Identifier: GPL-3.0-or-later

from logging import getLogger
_LOGGER = getLogger(__name__)

from watchdog.observers import Observer
from watchdog.events import FileCreatedEvent

from ._factory import get_event_handler
from spectre_core.config import get_batches_dir_path


def start_post_processor(
    tag: str
) -> None:
    """Start a thread to process newly created files in the `batches` directory.

    :param tag: The tag of the capture config used for data capture.
    """
    post_processor = Observer()
    event_handler = get_event_handler(tag)
    post_processor.schedule(event_handler, 
                            get_batches_dir_path(), 
                            recursive=True,
                            event_filter=[ FileCreatedEvent ])
    
    try:
        _LOGGER.info("Starting the post processing thread...") 
        post_processor.start()
        post_processor.join()
    except KeyboardInterrupt:
        _LOGGER.warning(("Keyboard interrupt detected. Signalling "
                         "the post processing thread to stop"))
        post_processor.stop()
        _LOGGER.warning(("Post processing thread has been successfully stopped"))

