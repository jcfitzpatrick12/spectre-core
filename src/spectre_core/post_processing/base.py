# SPDX-FileCopyrightText: © 2024 Jimmy Fitzpatrick <jcfitzpatrick12@gmail.com>
# This file is part of SPECTRE
# SPDX-License-Identifier: GPL-3.0-or-later

from logging import getLogger
_LOGGER = getLogger(__name__)

from queue import Queue
from typing import Optional
from abc import ABC, abstractmethod
from math import floor

from watchdog.events import (
    FileSystemEventHandler, 
    FileCreatedEvent, 
)

from spectre_core.chunks.factory import get_chunk_from_tag
from spectre_core.file_handlers.configs import CaptureConfig
from spectre_core.spectrograms.spectrogram import Spectrogram
from spectre_core.spectrograms.transform import join_spectrograms
from spectre_core.spectrograms.transform import (
    time_average, 
    frequency_average
)


class BaseEventHandler(ABC, FileSystemEventHandler):
    def __init__(self, 
                 tag: str):
        self._tag = tag

        self._Chunk = get_chunk_from_tag(tag)

        self._capture_config = CaptureConfig(tag)

        self._watch_extension = self._capture_config.get("watch_extension")
        if self._watch_extension is None:
            raise KeyError("The watch extension has not been specified in the capture config")

        # attribute to store the next file to be processed 
        # (specifically, the absolute file path of the file)
        self._queued_file: Optional[str] = None

        # spectrogram cache stores spectrograms in memory
        # such that they can be periodically written to files
        # according to the joining time.
        self._spectrogram: Optional[Spectrogram] = None
        


    @abstractmethod
    def process(self, 
                absolute_file_path: str) -> None:
        """Process the file stored at the input absolute file path.
        
        To be implemented by derived classes.
        """


    def on_created(self, 
                   event: FileCreatedEvent):
        """Process a newly created batch file, only once the next batch is created.
        
        Since we assume that the batches are non-overlapping in time, this guarantees
        we avoid post processing a file while it is being written to. Files are processed
        sequentially, in the order they are created.
        """

        # the 'src_path' attribute holds the absolute path of the newly created file
        absolute_file_path = event.src_path
        
        # only 'notice' a file if it ends with the appropriate extension
        # as defined in the capture config
        if absolute_file_path.endswith(self._watch_extension):
            _LOGGER.info(f"Noticed {absolute_file_path}")
            
            # If there exists a queued file, try and process it
            if self._queued_file is not None:
                try:
                    self.process(self._queued_file)
                except Exception:
                    _LOGGER.error(f"An error has occured while processing {self._queued_file}",
                                  exc_info=True)
                     # flush any internally stored spectrogram on error to avoid lost data
                    self._flush_spectrogram()
                    # re-raise the exception to the main thread
                    raise
            
            # Queue the current file for processing next
            _LOGGER.info(f"Queueing {absolute_file_path} for post processing")
            self._queued_file = absolute_file_path


    def _average_in_time(self, 
                         spectrogram: Spectrogram) -> Spectrogram:
        _LOGGER.info("Averaging spectrogram in time")
        requested_time_resolution = self._capture_config['time_resolution'] # [s]
        if requested_time_resolution is None:
            raise KeyError(f"Time resolution has not been specified in the capture config")
        average_over = floor(requested_time_resolution/spectrogram.time_resolution) if requested_time_resolution > spectrogram.time_resolution else 1
        return time_average(spectrogram, average_over)
    
    
    def _average_in_frequency(self, 
                              spectrogram: Spectrogram) -> Spectrogram:
        _LOGGER.info("Averaging spectrogram in frequency")
        frequency_resolution = self._capture_config['frequency_resolution'] # [Hz]
        if frequency_resolution is None:
            raise KeyError(f"Frequency resolution has not been specified in the capture config")
        average_over = floor(frequency_resolution/spectrogram.frequency_resolution) if frequency_resolution > spectrogram.frequency_resolution else 1
        return frequency_average(spectrogram, average_over)
    

    def _join_spectrogram(self, 
                          spectrogram: Spectrogram) -> None:
        _LOGGER.info("Joining spectrogram")
        if self._spectrogram is None:
            self._spectrogram = spectrogram
        else:
            self._spectrogram = join_spectrograms([self._spectrogram, spectrogram])

        if self._spectrogram.time_range >= self._capture_config['joining_time']:
            self._flush_spectrogram()
    

    def _flush_spectrogram(self) -> None:
        if self._spectrogram:
            _LOGGER.info(f"Flushing spectrogram to file with chunk start time {self._spectrogram.chunk_start_time}")
            self._spectrogram.save()
            _LOGGER.info("Flush successful, resetting spectrogram cache")
            self._spectrogram = None # reset the cache