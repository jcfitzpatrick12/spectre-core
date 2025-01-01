# SPDX-FileCopyrightText: © 2024 Jimmy Fitzpatrick <jcfitzpatrick12@gmail.com>
# This file is part of SPECTRE
# SPDX-License-Identifier: GPL-3.0-or-later

from datetime import datetime
from typing import Optional

from spectre_core._file_io import BaseFileHandler
from spectre_core.config import get_batches_dir_path, TimeFormats
from spectre_core.exceptions import BatchFileNotFoundError


class BatchFile(BaseFileHandler):
    """A specific file in a given batch, uniquely identified in the batch by the file extension."""
    def __init__(self, 
                 batch_parent_dir_path: str, 
                 batch_name: str, 
                 extension: str):
        super().__init__(batch_parent_dir_path, 
                         batch_name, 
                         extension)
        self._start_time, self._tag = batch_name.split("_")
        # computed if required
        self._start_datetime: Optional[datetime] = None
        
        
    @property
    def start_time(self) -> str:
        """The start time of the batch file, up to seconds precision."""
        return self._start_time


    @property
    def start_datetime(self) -> datetime:
        """The datetime of the batch file, up to seconds precision."""
        if self._start_datetime is None:
            self._start_datetime = datetime.strptime(self.start_time, TimeFormats.DATETIME)
        return self._start_datetime
    

    @property
    def tag(self) -> str:
        """The tag identifier for the batch file."""
        return self._tag
    


class BaseBatch:
    """A group of one or more files which share a common start time and a tag identifier.
    
    All files belonging to the same batch will share a batch name, and differ
    only in their file extension.
    """
    def __init__(self, 
                 start_time: str,
                 tag: str):
        self._start_time = start_time
        self._tag: str = tag
        self._batch_files: dict[str, BatchFile] = {}
        self._start_datetime = datetime.strptime(self.start_time, TimeFormats.DATETIME)
        self._parent_dir_path = get_batches_dir_path(year  = self.start_datetime.year,
                                                     month = self.start_datetime.month,
                                                     day   = self.start_datetime.day)


    @property
    def start_time(self) -> str:
        """The start time of the batch, up to seconds precision."""
        return self._start_time


    @property
    def tag(self) -> str:
        """The tag identifier of for the batch."""
        return self._tag
      

    @property
    def start_datetime(self) -> datetime:
        """The datetime of the batch file, up to seconds precision."""
        return self._start_datetime
    

    @property
    def parent_dir_path(self) -> str:
        """The parent directory for the batch."""
        return self._parent_dir_path


    @property
    def name(self) -> str:
        """The name of the batch."""
        return f"{self._start_time}_{self._tag}"
    
    
    @property
    def extensions(self) -> list[str]:
        """All defined file extensions for the batch."""
        return list(self._batch_files.keys())
    
    @property
    def batch_files(self) -> dict[str, BatchFile]:
        """Map each file extension in the batch to the corresponding batch file instance."""
        return self._batch_files
    
    
    def add_file(self, batch_file: BatchFile) -> None:
        """Add an instance of a batch file to the batch."""
        self._batch_files[batch_file.extension] = batch_file
    

    def get_file(self, extension: str) -> BatchFile:
        """Get a batch file instance from the batch, according to the file extension."""
        try:
            return self._batch_files[extension]
        except KeyError:
            raise BatchFileNotFoundError(f"No batch file found with extension '{extension}'")


    def read_file(self, extension: str):
        """Read a file from the batch, according to the file extension."""
        batch_file = self.get_file(extension)
        return batch_file.read()


    def delete_file(self, extension: str) -> None:
        """Delete a file from the batch, according to the file extension."""
        batch_file = self.get_file(extension)
        try:
            batch_file.delete()
        except FileNotFoundError as e:
            raise BatchFileNotFoundError(str(e))


    def has_file(self, extension: str) -> bool:
        """Return true if a file exists in the batch with the input file extension."""
        try:
            # only return true if both
            # -> the batch has the extension defined
            # -> the file with that extension exists in the batch parent directory
            batch_file = self.get_file(extension)
            return batch_file.exists
        except BatchFileNotFoundError:
            return False


