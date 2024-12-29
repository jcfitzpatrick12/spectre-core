# SPDX-FileCopyrightText: © 2024 Jimmy Fitzpatrick <jcfitzpatrick12@gmail.com>
# This file is part of SPECTRE
# SPDX-License-Identifier: GPL-3.0-or-later

import os
import json
from abc import ABC, abstractmethod
from typing import Any, Optional


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


class JsonHandler(BaseFileHandler):
    def __init__(self, 
                 parent_path: str, 
                 base_file_name: str,
                 extension: str = "json",
                 **kwargs):
        
        self._dict = None # cache
        super().__init__(parent_path, 
                         base_file_name, 
                         extension,
                         **kwargs)
    
    
    def read(self) -> dict[str, Any]:
        with open(self.file_path, 'r') as f:
            return json.load(f)
        

    def save(self, 
             d: dict, 
             force: bool = False) -> None:
        self.make_parent_path()

        if self.exists:
            if force:
                pass
            else:
                raise RuntimeError((f"{self.file_name} already exists, write has been abandoned. "
                                    f"You can override this functionality with `force`"))

        with open(self.file_path, 'w') as file:
                json.dump(d, file, indent=4)


    @property
    def dict(self) -> dict[str, Any]:
        if self._dict is None:
            self._dict = self.read()
        return self._dict
    

class TextHandler(BaseFileHandler):
    def __init__(self, 
                 parent_path: str,
                 base_file_name: str, 
                 extension: str = "txt",
                 **kwargs):
        super().__init__(parent_path,
                         base_file_name,
                         extension, 
                         **kwargs)
    

    def read(self) -> dict:
        with open(self.file_path, 'r') as f:
            return f.read()