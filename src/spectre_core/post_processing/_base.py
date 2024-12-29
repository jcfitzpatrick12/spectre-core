# SPDX-FileCopyrightText: © 2024 Jimmy Fitzpatrick <jcfitzpatrick12@gmail.com>
# This file is part of SPECTRE
# SPDX-License-Identifier: GPL-3.0-or-later

from logging import getLogger
_LOGGER = getLogger(__name__)

from typing import Optional
from abc import ABC, abstractmethod
from scipy.signal import ShortTimeFFT, get_window

from watchdog.events import FileSystemEventHandler, FileCreatedEvent

from spectre_core.capture_configs import CaptureConfig, PNames
from spectre_core.chunks import BaseChunk, get_chunk_from_tag
from spectre_core.spectrograms import Spectrogram, join_spectrograms


def make_sft_instance(capture_config: CaptureConfig
) -> ShortTimeFFT:
    sample_rate   = capture_config.get_parameter_value(PNames.SAMPLE_RATE)
    window_hop    = capture_config.get_parameter_value(PNames.WINDOW_HOP)
    window_type   = capture_config.get_parameter_value(PNames.WINDOW_TYPE)
    window_size   = capture_config.get_parameter_value(PNames.WINDOW_SIZE)
    window = get_window(window_type, 
                        window_size)
    return ShortTimeFFT(window, 
                        window_hop,
                        sample_rate, 
                        fft_mode = "centered")


class BaseEventHandler(ABC, FileSystemEventHandler):
    def __init__(self, 
                 tag: str):
        self._tag = tag

        # the tag tells us 'what type' of data is stored in the files for each chunk
        self._Chunk: BaseChunk = get_chunk_from_tag(tag)
        # load the capture config corresponding to the tag
        self._capture_config   = CaptureConfig(tag)

        # post processing is triggered by files with this extension
        self._watch_extension = self._capture_config.get_parameter_value(PNames.WATCH_EXTENSION)

        # store the next file to be processed (specifically, the absolute file path of the file)
        self._queued_file: Optional[str] = None

        # store batched spectrograms as they are created into a cache
        # which is flushed periodically according to a user defined 
        # time range
        self._cached_spectrogram: Optional[Spectrogram] = None


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
                    self._flush_cache()
                    # re-raise the exception to the main thread
                    raise
            
            # Queue the current file for processing next
            _LOGGER.info(f"Queueing {absolute_file_path} for post processing")
            self._queued_file = absolute_file_path
    

    def _cache_spectrogram(self, 
                           spectrogram: Spectrogram) -> None:
        _LOGGER.info("Joining spectrogram")

        if self._cached_spectrogram is None:
            self._cached_spectrogram = spectrogram
        else:
            self._cached_spectrogram = join_spectrograms([self._cached_spectrogram, spectrogram])

        # if the time range is not specified
        time_range = self._capture_config.get_parameter_value(PNames.TIME_RANGE) or 0.0
  
        if self._cached_spectrogram.time_range >= time_range:
            self._flush_cache()
    

    def _flush_cache(self) -> None:
        if self._cached_spectrogram:
            _LOGGER.info(f"Flushing spectrogram to file with chunk start time "
                         f"'{self._cached_spectrogram.chunk_start_time}'")
            self._cached_spectrogram.save()
            _LOGGER.info("Flush successful, resetting spectrogram cache")
            self._cached_spectrogram = None # reset the cache