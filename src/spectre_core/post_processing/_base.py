# SPDX-FileCopyrightText: © 2024-2025 Jimmy Fitzpatrick <jcfitzpatrick12@gmail.com>
# This file is part of SPECTRE
# SPDX-License-Identifier: GPL-3.0-or-later

import logging
import typing
import abc

import pydantic
import watchdog.events

import spectre_core.spectrograms

_LOGGER = logging.getLogger(__name__)


class BaseEventHandlerModel(pydantic.BaseModel):
    time_range: float = pydantic.Field(
        0,
        ge=0,
        description="Spectrograms are stitched together until the time range has elapsed.",
    )
    origin: str = pydantic.Field(
        "Spectre", description="Corresponds to the FITS keyword ORIGIN."
    )
    telescope: str = pydantic.Field(
        "NOTSET", description="Corresponds to the FITS keyword TELESCOP."
    )
    instrument: str = pydantic.Field(
        "NOTSET", description="Corresponds to the FITS keyword INSTRUMEN."
    )
    object: str = pydantic.Field(
        "NOTSET", description="Corresponds to the FITS keyword OBJECT."
    )
    obs_lat: float = pydantic.Field(
        0.0, description="Corresponds to the FITS keyword OBS_LAT."
    )
    obs_alt: float = pydantic.Field(
        0.0, description="Corresponds to the FITS keyword OBS_ALT."
    )
    obs_lon: float = pydantic.Field(
        0.0, description="Corresponds to the FITS keyword OBS_LON."
    )

    class Config:
        validate_assignment = True


class BaseEventHandler(abc.ABC, watchdog.events.FileSystemEventHandler):
    """An abstract base class for event-driven file post-processing."""

    def __init__(
        self,
        tag: str,
        queued_file: typing.Optional[str] = None,
        cached_spectrogram: typing.Optional[
            spectre_core.spectrograms.Spectrogram
        ] = None,
        **params,
    ) -> None:
        self._tag = tag
        self.__time_range = typing.cast(float, params.pop("time_range"))
        self.__origin = typing.cast(str, params.pop("origin"))
        self.__instrument = typing.cast(str, params.pop("instrument"))
        self.__telescope = typing.cast(str, params.pop("telescope"))
        self.__object = typing.cast(str, params.pop("object"))
        self.__obs_alt = typing.cast(float, params.pop("obs_alt"))
        self.__obs_lat = typing.cast(float, params.pop("obs_lat"))
        self.__obs_lon = typing.cast(float, params.pop("obs_lon"))

        self.__queued_file = queued_file
        self.__cached_spectrogram = cached_spectrogram

    @abc.abstractmethod
    def process(self, absolute_file_path: str) -> None:
        """
        Process a batch file at the given file path.

        :param absolute_file_path: The absolute path to the batch file to be processed.
        """

    @property
    @abc.abstractmethod
    def _watch_extension(self) -> str: ...

    def on_created(self, event: watchdog.events.FileSystemEvent) -> None:
        """Process a newly created batch file, only once the next batch is created.

        Since we assume that the batches are non-overlapping in time, this guarantees
        we avoid post processing a file while it is being written to. Files are processed
        sequentially, in the order they are created.

        :param event: The file system event containing the file details.
        """
        # The `src_path`` attribute holds the absolute path of the freshly closed file
        absolute_file_path = event.src_path

        # Only process a file if:
        #
        # - It's extension matches the `watch_extension` as defined in the capture config.
        # - It's tag matches the current sessions tag.
        #
        # This is important for two reasons.
        #
        # In the case of one session, the capture worker may write to two batch files simultaneously
        # (e.g., raw data file + seperate metadata file). We want to process them together - but this method will get called
        # seperately for both file creation events. So, we filter by extension to account for this.
        #
        # Additionally in the case of multiple sessions, the capture workers will create batch files in the same directory concurrently.
        # This method is triggered for all file creation events, so we ensure the batch file tag matches the session tag and early return
        # otherwise. This way, each post processor worker picks up the right files to process.
        if not absolute_file_path.endswith(f"_{self._tag}.{self._watch_extension}"):
            return

        _LOGGER.info(f"Noticed {absolute_file_path}")
        # If there exists a queued file, try and process it
        if self.__queued_file is not None:
            try:
                self.process(self.__queued_file)
            except Exception:
                _LOGGER.error(
                    f"An error has occured while processing {self.__queued_file}",
                    exc_info=True,
                )
                # Flush any internally stored spectrogram on error to avoid lost data
                self.__flush_cache()
                # re-raise the exception to the main thread
                raise

        # Queue the current file for processing next
        _LOGGER.info(f"Queueing {absolute_file_path} for post processing")
        self.__queued_file = absolute_file_path

    def _cache_spectrogram(
        self, spectrogram: spectre_core.spectrograms.Spectrogram
    ) -> None:
        _LOGGER.info("Joining spectrogram")

        if self.__cached_spectrogram is None:
            self.__cached_spectrogram = spectrogram
        else:
            self.__cached_spectrogram = spectre_core.spectrograms.join_spectrograms(
                [self.__cached_spectrogram, spectrogram]
            )

        if self.__cached_spectrogram.time_range >= self.__time_range:
            self.__flush_cache()

    def __flush_cache(self) -> None:
        if self.__cached_spectrogram:
            _LOGGER.info(
                f"Flushing spectrogram to file with start time "
                f"'{self.__cached_spectrogram.format_start_time()}'"
            )
            self.__cached_spectrogram.save(
                self._tag,
                self.__origin,
                self.__instrument,
                self.__telescope,
                self.__object,
                self.__obs_alt,
                self.__obs_lat,
                self.__obs_lon,
            )
            _LOGGER.info("Flush successful, resetting spectrogram cache")
            self.__cached_spectrogram = None  # reset the cache
