# SPDX-FileCopyrightText: © 2024 Jimmy Fitzpatrick <jcfitzpatrick12@gmail.com>
# This file is part of SPECTRE
# SPDX-License-Identifier: GPL-3.0-or-later

import os
from abc import ABC, abstractmethod
from typing import Any, Optional
from warnings import warn

class BaseFileHandler(ABC):
    def __init__(self, 
                 parent_path: str, 
                 base_file_name: str, 
                 extension: Optional[str] = None):
        self._parent_path = parent_path
        self._base_file_name = base_file_name
        self._extension = extension

        
    @abstractmethod
    def read(self) -> Any:
        pass
 

    @property
    def parent_path(self) -> str:
        return self._parent_path
    

    @property
    def base_file_name(self) -> str:
        return self._base_file_name
    

    @property
    def extension(self) -> Optional[str]:
        return self._extension
    

    @property
    def file_name(self) -> str:
        return self._base_file_name if (self._extension is None) else f"{self._base_file_name}.{self._extension}"
    

    @property
    def file_path(self) -> str:
        return os.path.join(self._parent_path, self.file_name)
    
    
    @property
    def exists(self) -> bool:
        return os.path.exists(self.file_path) 


    def make_parent_path(self) -> None:
        os.makedirs(self.parent_path, exist_ok=True) 
    

    def delete(self,
               ignore_if_missing: bool = False) -> None:
        if not self.exists and not ignore_if_missing:
            raise FileNotFoundError(f"{self.file_name} does not exist, and so cannot be deleted")
        else:
            os.remove(self.file_path)
    

    def cat(self) -> None:
        print(self.read())