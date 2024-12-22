# SPDX-FileCopyrightText: © 2024 Jimmy Fitzpatrick <jcfitzpatrick12@gmail.com>
# This file is part of SPECTRE
# SPDX-License-Identifier: GPL-3.0-or-later

from typing import Any
import json

from spectre_core.file_handlers.base import BaseFileHandler

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
    

    # def __getitem__(self, 
    #                 key: str) -> Any:
    #     return self.dict[key]
    

    # def get(self, 
    #         *args, 
    #         **kwargs) -> Any:
    #     return self.dict.get(*args, 
    #                          **kwargs)
    
    
    # def update(self, 
    #            *args, 
    #            **kwargs) -> None:
    #     self.dict.update(*args, **kwargs)

    
    # def items(self):
    #     return self.dict.items()
    
    
    # def keys(self):
    #     return self.dict.keys()
    
    
    # def values(self):
    #     return self.dict.values()