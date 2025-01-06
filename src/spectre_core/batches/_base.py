# SPDX-FileCopyrightText: © 2024 Jimmy Fitzpatrick <jcfitzpatrick12@gmail.com>
# This file is part of SPECTRE
# SPDX-License-Identifier: GPL-3.0-or-later

from datetime import datetime
from typing import Optional, TypeVar
from abc import ABC, abstractmethod

from spectre_core._file_io import BaseFileHandler
from spectre_core.config import get_batches_dir_path, TimeFormat
from spectre_core.spectrograms import Spectrogram


T = TypeVar('T')

class BatchFile(BaseFileHandler[T]):
    """Abstract base class for files belonging to a batch, identified by their file extension.

    Batch file names must conform to the following structure:

        `<start time>_<tag>.<extension>`

    Here, `<start time>_<tag>` is referred to as the batch name. Files with the same batch name 
    belong to the same batch. Subclass this as needed based on `BaseFileHandler` requirements.
    """
    

    def __init__(self, 
                 batch_parent_dir_path: str, 
                 batch_name: str, 
                 extension: str) -> None:
        """Initialise a `BatchFile` instance.

        :param batch_parent_dir_path: Parent directory of the batch.
        :param batch_name: Base file name, composed of the batch start time and tag.
        :param extension: File extension.
        """
        # no cache, as batch files should always be static in content when reading
        super().__init__(batch_parent_dir_path, 
                         batch_name, 
                         extension,
                         no_cache=False)
        self._start_time, self._tag = batch_name.split("_")
        # the start datetime is lazily computed, if it is required.
        self._start_datetime: Optional[datetime] = None
   
   
    @property
    def start_time(self) -> str:
        """The start time of the batch, formatted as a string up to seconds precision."""
        return self._start_time


    @property
    def start_datetime(self) -> datetime:
        """The start time of the batch, parsed as a datetime up to seconds precision."""
        # the start datetime is lazily computed, if it is required.
        if self._start_datetime is None:
            self._start_datetime = datetime.strptime(self.start_time, TimeFormat.DATETIME)
        return self._start_datetime
    

    @property
    def tag(self) -> str:
        """The batch name tag."""
        return self._tag
         
 
class BaseBatch(ABC):
    """Abstract base class representing a group of data files for a common time interval.

    All files in a batch share a base file name and differ only by their extension. 
    `BaseBatch` subclasses define the expected data for each file extension and provide 
    an API for accessing their contents using `BatchFile` subclasses.

    Derived classes must:
    - Implement the `spectrogram_file` abstract property, as all batches in SPECTRE 
    must include a `BatchFile` subclass containing spectrogram data.
    - Expose `BatchFile` instances directly as attributes.
    """
    def __init__(self, 
                 start_time: str,
                 tag: str) -> None:
        """Initialise a `BaseBatch` instance.

        :param start_time: Start time of the batch as a string with seconds precision.
        :param tag: The batch name tag.
        """
        self._start_time = start_time
        self._tag: str = tag
        self._start_datetime = datetime.strptime(self.start_time, TimeFormat.DATETIME)
        self._parent_dir_path = get_batches_dir_path(year  = self.start_datetime.year,
                                                     month = self.start_datetime.month,
                                                     day   = self.start_datetime.day)
            
    
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
        composed of the start time and tag identifier."""
        return f"{self._start_time}_{self._tag}"
    

    def read_spectrogram(self) -> Spectrogram:
        """Read and return the spectrogram data stored in the batch.

        :return: The spectrogram stored by the batch `spectrogram_file`.
        """
        return self.spectrogram_file.read()