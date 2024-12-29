# SPDX-FileCopyrightText: © 2024 Jimmy Fitzpatrick <jcfitzpatrick12@gmail.com>
# This file is part of SPECTRE
# SPDX-License-Identifier: GPL-3.0-or-later

from datetime import datetime
from typing import Optional

from spectre_core._file_io import BaseFileHandler
from spectre_core.config import get_chunks_dir_path, TimeFormats
from spectre_core.exceptions import ChunkFileNotFoundError

class ChunkFile(BaseFileHandler):
    def __init__(self, 
                 chunk_parent_path: str, 
                 chunk_name: str, 
                 extension: str, 
                 **kwargs):
        self._chunk_start_time, self._tag = chunk_name.split("_")
        self._chunk_start_datetime: Optional[datetime] = None
        super().__init__(chunk_parent_path, 
                         chunk_name, 
                         extension = extension, 
                         **kwargs)


    @property
    def chunk_start_time(self) -> str:
        return self._chunk_start_time
    

    @property
    def tag(self) -> str:
        return self._tag
    

    @property
    def chunk_start_datetime(self) -> datetime:
        if self._chunk_start_datetime is None:
            self._chunk_start_datetime = datetime.strptime(self.chunk_start_time, TimeFormats.DATETIME)
        return self._chunk_start_datetime
    


class BaseChunk:
    def __init__(self, 
                 chunk_start_time: str, 
                 tag: str):
        self._chunk_start_time: str = chunk_start_time
        self._tag: str = tag
        self._chunk_files: dict[str, ChunkFile] = {}
        self._chunk_start_datetime: Optional[datetime] = None
        self.chunk_parent_path: str = get_chunks_dir_path(year = self.chunk_start_datetime.year,
                                                          month = self.chunk_start_datetime.month,
                                                          day = self.chunk_start_datetime.day)
        self._chunk_name: str = f"{self.chunk_start_time}_{self.tag}"


    @property
    def chunk_start_time(self) -> str:
        return self._chunk_start_time


    @property
    def tag(self) -> str:
        return self._tag
      

    @property
    def chunk_start_datetime(self) -> datetime:
        if self._chunk_start_datetime is None:
            self._chunk_start_datetime = datetime.strptime(self.chunk_start_time, TimeFormats.DATETIME)
        return self._chunk_start_datetime


    @property
    def chunk_name(self) -> str:
        return f"{self._chunk_start_time}_{self._tag}"
    

    @property
    def extensions(self) -> list[str]:
        return list(self._chunk_files.keys())
    
    
    def add_file(self, chunk_file: ChunkFile) -> None:
        self._chunk_files[chunk_file.extension] = chunk_file
    

    def get_file(self, extension: str) -> ChunkFile:
        try:
            return self._chunk_files[extension]
        except KeyError:
            raise ChunkFileNotFoundError(f"No chunk file found with extension '{extension}'")


    def read_file(self, extension: str):
        chunk_file = self.get_file(extension)
        return chunk_file.read()


    def delete_file(self, extension: str, **kwargs):
        chunk_file = self.get_file(extension)
        try:
            chunk_file.delete(**kwargs)
        except FileNotFoundError as e:
            raise ChunkFileNotFoundError(str(e))


    def has_file(self, extension: str) -> bool:
        try:
            chunk_file = self.get_file(extension)
            return chunk_file.exists
        except ChunkFileNotFoundError:
            return False


