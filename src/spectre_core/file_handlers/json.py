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