# SPDX-FileCopyrightText: © 2024-2025 Jimmy Fitzpatrick <jcfitzpatrick12@gmail.com>
# This file is part of SPECTRE
# SPDX-License-Identifier: GPL-3.0-or-later

from datetime import datetime
from typing import TypeVar, Tuple
from base64 import b64encode
from functools import cached_property
from abc import ABC, abstractmethod
from dataclasses import dataclass
from os.path import splitext

from spectre_core._file_io import BaseFileHandler
from spectre_core.config import get_batches_dir_path, TimeFormat
from spectre_core.spectrograms import Spectrogram
from spectre_core.exceptions import deprecated


@deprecated(
    "The terminology (base file name) is inconsistent with the `_file_io` submodule. "
    f"Please use `parse_batch_file_name` instead."
)
def parse_batch_base_file_name(base_file_name: str) -> Tuple[str, str, str]:
    """Included for backwards compatability - please use `parse_batch_file_name` instead."""
    return parse_batch_file_name(base_file_name)


def parse_batch_file_name(file_name: str) -> Tuple[str, str, str]:
    """Parse the base file name of a batch file into a start time, tag and extension.

    :param file_name: The file name of the batch file, with optional extension.
    :return: The file name decomposed into its start time, tag and extension. If no extension is present,
    the final element of the tuple will be an empty string.
    """
    batch_name, extension = splitext(file_name)

    num_underscores = batch_name.count("_")
    if num_underscores != 1:
        raise ValueError(
            f"Expected exactly one underscore in the batch name '{batch_name}'. Found {num_underscores}"
        )

    # strip the dot from the extension
    extension = extension.lstrip(".")
    start_time, tag = batch_name.split("_", 1)
    return start_time, tag, extension


T = TypeVar("T")


class BatchFile(BaseFileHandler[T]):
    """Abstract base class for files belonging to a batch, identified by their file extension.

    Batch file names must conform to the following structure:

        `<start time>_<tag>.<extension>`

    The substring `<start time>_<tag>` is referred to as the batch name. Files with the same batch name
    belong to the same batch.
    """

    def __init__(
        self, batch_parent_dir_path: str, batch_name: str, extension: str
    ) -> None:
        """Initialise a `BatchFile` instance.

        :param batch_parent_dir_path: Parent directory of the batch.
        :param batch_name: Base file name, composed of the batch start time and tag.
        :param extension: File extension.
        """
        super().__init__(batch_parent_dir_path, batch_name, extension)
        self._start_time, self._tag = batch_name.split("_")

    @property
    def start_time(self) -> str:
        """The start time of the batch, formatted as a string up to seconds precision."""
        return self._start_time

    @cached_property
    def start_datetime(self) -> datetime:
        """The start time of the batch, parsed as a datetime up to seconds precision."""
        return datetime.strptime(self.start_time, TimeFormat.DATETIME)

    @property
    def tag(self) -> str:
        """The batch name tag."""
        return self._tag


@dataclass(frozen=True)
class _BatchExtension:
    """Supported extensions for a `BaseBatch`, inherited by all derived classes.

    :ivar PNG: Corresponds to the `.png` file extension.
    """

    PNG: str = "png"


class _PngFile(BatchFile[str]):
    """Stores an image visualising the data for the batch."""

    def __init__(self, batch_parent_dir_path: str, batch_name: str) -> None:
        """Initialise a `_PngFile` instance.

        :param batch_parent_dir_path: The parent directory for the batch.
        :param batch_name: The batch name.
        """
        super().__init__(batch_parent_dir_path, batch_name, _BatchExtension.PNG)

    def _read(self) -> str:
        """Reads the PNG file and returns it base64-encoded.

        :return: Base64-encoded string representation of the image.
        """
        with open(self.file_path, "rb") as f:
            encoded = b64encode(f.read())
            return encoded.decode("ascii")


class BaseBatch(ABC):
    """
    An abstract base class representing a group of data files over a common time interval.

    All files in a batch share a base file name and differ only by their extension.
    Subclasses of `BaseBatch` define the expected data for each file extension and
    provide an API for accessing their contents using `BatchFile` subclasses.

    Subclasses should expose `BatchFile` instances directly as attributes, which
    simplifies static typing. Additionally, they should call `add_file` in the constructor
    to formally register each `BatchFile`.
    """

    def __init__(self, start_time: str, tag: str) -> None:
        """Initialise a `BaseBatch` instance.

        :param start_time: Start time of the batch as a string with seconds precision.
        :param tag: The batch name tag.
        """
        self._start_time = start_time
        self._tag: str = tag
        self._start_datetime = datetime.strptime(self.start_time, TimeFormat.DATETIME)
        self._parent_dir_path = get_batches_dir_path(
            year=self.start_datetime.year,
            month=self.start_datetime.month,
            day=self.start_datetime.day,
        )

        # internal register of batch files
        self._batch_files: dict[str, BatchFile] = {}

        # Add the files shared by all derived classes
        self._png_file = _PngFile(self.parent_dir_path, self.name)
        self.add_file(self._png_file)

    @property
    @abstractmethod
    def spectrogram_file(self) -> BatchFile:
        """The batch file which contains spectrogram data."""

    @property
    def start_time(self) -> str:
        """The start time of the batch, formatted as a string up to seconds precision."""
        return self._start_time

    @property
    def start_datetime(self) -> datetime:
        """The start time of the batch, parsed as a datetime up to seconds precision."""
        return self._start_datetime

    @property
    def tag(self) -> str:
        """The batch name tag."""
        return self._tag

    @property
    def parent_dir_path(self) -> str:
        """The parent directory for the batch."""
        return self._parent_dir_path

    @property
    def name(self) -> str:
        """Return the base file name shared by all files in the batch,
        composed of the start time and the batch tag."""
        return f"{self._start_time}_{self._tag}"

    @property
    def extensions(self) -> list[str]:
        """All defined file extensions for the batch."""
        return list(self._batch_files.keys())

    @property
    def batch_files(self) -> dict[str, BatchFile]:
        """Map each file extension in the batch to the corresponding batch file instance.

        Use `add_file` to add a file to the batch.
        """
        return self._batch_files

    @property
    def png_file(self) -> _PngFile:
        """The batch file corresponding to the `.png` extension."""
        return self._png_file

    def add_file(self, batch_file: BatchFile) -> None:
        """Add an instance of a batch file to the batch.

        :param batch_file: The `BatchFile` instance to add to the batch.
        :raises ValueError: If the `BatchFile` instance does not have a defined file extension.
        """
        if batch_file.extension is None:
            raise ValueError(
                f"The `BatchFile` must have a defined file extension. "
                f"Received '{batch_file.extension}."
            )
        self._batch_files[batch_file.extension] = batch_file

    def get_file(self, extension: str) -> BatchFile:
        """Get a batch file instance from the batch, according to the file extension.

        :param extension: The file extension of the batch file.
        :raises NotImplementedError: If the extension is undefined for the batch.
        :return: The batch file instance registered under the input file extension.
        """
        try:
            return self._batch_files[extension]
        except KeyError:
            raise NotImplementedError(
                f"A batch file with extension '{extension}' is not implemented for this batch."
            )

    def delete_file(self, extension: str) -> None:
        """Delete a file from the batch, according to the file extension.

        :param extension: The file extension of the batch file.
        :raises FileNotFoundError: If the batch file does not exist in the file system.
        """
        batch_file = self.get_file(extension)
        batch_file.delete()

    def has_file(self, extension: str) -> bool:
        """Determine the existance of a batch file in the file system.

        :param extension: The file extension of the batch file.
        :return: True if the batch file exists in the file system, False otherwise.
        """
        try:
            batch_file = self.get_file(extension)
            return batch_file.exists
        except FileNotFoundError:
            return False

    def read_spectrogram(self) -> Spectrogram:
        """Read and return the spectrogram data stored in the batch.

        :return: The spectrogram stored by the batch `spectrogram_file`.
        """
        return self.spectrogram_file.read()
