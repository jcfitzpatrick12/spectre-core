# SPDX-FileCopyrightText: © 2024 Jimmy Fitzpatrick <jcfitzpatrick12@gmail.com>
# This file is part of SPECTRE
# SPDX-License-Identifier: GPL-3.0-or-later

from logging import getLogger
_LOGGER = getLogger(__name__)

from typing import Optional, cast
from abc import ABC, abstractmethod
from scipy.signal import ShortTimeFFT, get_window

from watchdog.events import FileSystemEventHandler, FileSystemEvent

from spectre_core.capture_configs import CaptureConfig, PName
from spectre_core.spectrograms import Spectrogram, join_spectrograms


def make_sft_instance(
    capture_config: CaptureConfig
) -> ShortTimeFFT:
    """Extract window parameters from the input capture config and create an instance
    of `ShortTimeFFT` from `scipy.signal`.

    :param capture_config: The capture config storing the parameters.
    :return: An instance of `ShortTimeFFT` consistent with the window parameters 
    in the capture config.
    """
    window_type   = cast(str, capture_config.get_parameter_value(PName.WINDOW_TYPE))
    sample_rate   = cast(int, capture_config.get_parameter_value(PName.SAMPLE_RATE))
    window_hop    = cast(int, capture_config.get_parameter_value(PName.WINDOW_HOP))
    window_size   = cast(int, capture_config.get_parameter_value(PName.WINDOW_SIZE))
    window = get_window(window_type, 
                        window_size)
    return ShortTimeFFT(window, 
                        window_hop,
                        sample_rate, 
                        fft_mode = "centered")


class BaseEventHandler(ABC, FileSystemEventHandler):
    """An abstract base class for event-driven file post-processing."""
    def __init__(
        self, 
        tag: str
    ) -> None:
        """Initialise a `BaseEventHandler` instance.

        :param tag: The tag of the capture config used to capture the data.
        """
        self._tag = tag

        # load the capture config corresponding to the input tag
        self._capture_config = CaptureConfig(tag)
        
        # store the next file to be processed (specifically, the absolute file path of the file)
        self._queued_file: Optional[str] = None

        # optionally store batched spectrograms as they are created into a cache
        # this can be flushed periodically to file as required.
        self._cached_spectrogram: Optional[Spectrogram] = None


    @abstractmethod
    def process(
        self, 
        absolute_file_path: str
    ) -> None:
        """
        Process a batch file at the given file path.

        :param absolute_file_path: The absolute path to the batch file to be processed.
        """


    def on_created(
        self, 
        event: FileSystemEvent
    ) -> None:
        """Process a newly created batch file, only once the next batch is created.
        
        Since we assume that the batches are non-overlapping in time, this guarantees
        we avoid post processing a file while it is being written to. Files are processed
        sequentially, in the order they are created.

        :param event: The file system event containing the file details.
        """
        # the `src_path`` attribute holds the absolute path of the freshly closed file
        absolute_file_path = event.src_path
        
        # only 'notice' a file if it ends with the appropriate extension as defined in the capture config
        watch_extension = cast(str, self._capture_config.get_parameter_value(PName.WATCH_EXTENSION))
        
        if absolute_file_path.endswith( watch_extension ):
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


    def _cache_spectrogram(
        self, 
        spectrogram: Spectrogram
    ) -> None:
        """Cache the input spectrogram by storing it in the `_cached_spectrogram` attribute.
        
        If the time range of the cached spectrogram exceeds that as specified in the capture config
        `PName.TIME_RANGE` parameter, the spectrogram in the cache is flushed to file. If `PName.TIME_RANGE`
        is nulled, the cache is flushed immediately.

        :param spectrogram: The spectrogram to store in the cache.
        """
        _LOGGER.info("Joining spectrogram")

        if self._cached_spectrogram is None:
            self._cached_spectrogram = spectrogram
        else:
            self._cached_spectrogram = join_spectrograms([self._cached_spectrogram, spectrogram])
  
        time_range = self._capture_config.get_parameter_value(PName.TIME_RANGE) or 0.0
        if self._cached_spectrogram.time_range >= cast(float, time_range):
            self._flush_cache()
    

    def _flush_cache(
        self
    ) -> None:
        """Flush the cached spectrogram to file."""
        if self._cached_spectrogram:
            _LOGGER.info(f"Flushing spectrogram to file with start time "
                         f"'{self._cached_spectrogram.format_start_time()}'")
            self._cached_spectrogram.save()
            _LOGGER.info("Flush successful, resetting spectrogram cache")
            self._cached_spectrogram = None # reset the cache