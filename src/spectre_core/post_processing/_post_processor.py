# SPDX-FileCopyrightText: © 2024 Jimmy Fitzpatrick <jcfitzpatrick12@gmail.com>
# This file is part of SPECTRE
# SPDX-License-Identifier: GPL-3.0-or-later

from logging import getLogger
_LOGGER = getLogger(__name__)

from watchdog.observers import Observer
from watchdog.events import FileCreatedEvent

from ._factory import get_event_handler_from_tag
from spectre_core.config import get_chunks_dir_path

class PostProcessor:
    def __init__(self, 
                 tag: str):
        
        self._observer = Observer()

        EventHandler = get_event_handler_from_tag(tag)
        self._event_handler = EventHandler(tag)


    def start(self):
        """Start an observer to process newly created files in the chunks directory"""
        self._observer.schedule(self._event_handler, 
                                get_chunks_dir_path(), 
                                recursive=True,
                                event_filter=[FileCreatedEvent])
        
        try:
            _LOGGER.info("Starting the post processing thread...") 
            self._observer.start()
            self._observer.join()
        except KeyboardInterrupt:
            _LOGGER.warning(("Keyboard interrupt detected. Signalling "
                             "the post processing thread to stop"))
            self._observer.stop()
            _LOGGER.warning(("Post processing thread has been successfully stopped"))

