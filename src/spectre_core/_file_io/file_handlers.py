# SPDX-FileCopyrightText: © 2024 Jimmy Fitzpatrick <jcfitzpatrick12@gmail.com>
# This file is part of SPECTRE
# SPDX-License-Identifier: GPL-3.0-or-later

import os
import json
from abc import ABC, abstractmethod
from typing import Any, Optional, TypeVar, Generic

T = TypeVar('T')

class BaseFileHandler(ABC, Generic[T]):
    """
    Base class for handling file operations.

    When subclassing, specify the return type of `_read` 
    using `Generic[T]`. 

    Example:
    .. code-block:: python

        from typing import Any, Generic

        class JsonHandler(BaseFileHandler[dict[str, Any]]):
            def _read(self) -> dict[str, Any]:
                # Implementation here
                ...
    """
    def __init__(
        self, 
        parent_dir_path: str, 
        base_file_name: str, 
        extension: Optional[str] = None
    ) -> None:
        """Initialise a `BaseFileHandler` instance.

        :param parent_dir_path: The directory path where the file is located (absolute or relative).
        :param base_file_name: The name of the file without its extension.
        :param extension: The file extension (without the dot), defaults to None
        """
        self._data_cache: Optional[T] = None
        
        self._parent_dir_path = parent_dir_path
        self._base_file_name  = base_file_name
        
        if extension == "":
            extension = None
        self._extension = extension

     
    @abstractmethod
    def _read(
        self
    ) -> T:
        """The grunt work to return the file contents.

        :return: The file contents.
        """
     
    
    @property
    def parent_dir_path(
        self
    ) -> str:
        """Return the parent directory path for the file."""
        return self._parent_dir_path
    

    @property
    def base_file_name(
        self
    ) -> str:
        """Return the file name, stripped of the file extension."""
        return self._base_file_name
    

    @property
    def extension(
        self
    ) -> Optional[str]:
        """Return the file path suffix, excluding the dot."""
        return self._extension
    

    @property
    def file_name(
        self
    ) -> str:
        """Generate the file name based on the base name and extension.

        :return: The file name with the extension (including the dot), or the base name if no extension is set.
        """
        return self._base_file_name if (self._extension is None) else f"{self._base_file_name}.{self._extension}"
    

    @property
    def file_path(
        self
    ) -> str:
        """The absolute or relative file path as defined by the parent directory path,
        base file name and extension."""
        return os.path.join(self._parent_dir_path, self.file_name)
    
    
    @property
    def exists(
        self
    ) -> bool:
        """Check if the file exists in the filesystem."""
        return os.path.exists(self.file_path) 


    def read(
        self,
        cache: bool = True
    ) -> T:
        """Read the file contents.
        
        :param cache: If False, bypasses the cache and reads the file directly on each `read` call, defaults to True
        :return: The file contents.
        """
        # if the user has specified to ignore the cache, simply read the file.
        if not cache:
            return self._read()
        
        # otherwise make use of the cache
        if self._data_cache is None:
            self._data_cache = self._read()
        return self._data_cache
    
    
    def make_parent_dir_path(
        self
    ) -> None:
        """Make the parent directory path of the file. No error is raised if the target 
        directory already exists.
        """
        os.makedirs(self.parent_dir_path, exist_ok=True) 
    

    def delete(
        self,
        ignore_if_missing: bool = False
    ) -> None:
        """Delete the file from the filesystem.

        :param ignore_if_missing: If True, skips deletion if the file does not exist, defaults to False
        :raises FileNotFoundError: If the file is missing and `ignore_if_missing` is False.
        """
        if not self.exists and not ignore_if_missing:
            raise FileNotFoundError(f"{self.file_name} does not exist, and so cannot be deleted")
        else:
            os.remove(self.file_path)
    

    def cat(
        self
    ) -> None:
        """Display the file contents on the standard output."""
        print(self.read())


class JsonHandler(BaseFileHandler[dict[str, Any]]):
    """File handler for JSON formatted files.
    
    We assume that the files are of the form
    {
        "foo": <JSON compatable structure>
        ... and so on.
    }

    """
    def __init__(
        self, 
        parent_dir_path: str, 
        base_file_name: str,
        extension: str = "json"
    ) -> None:
        super().__init__(parent_dir_path, 
                         base_file_name, 
                         extension)
    
    
    def _read(
        self
    ) -> dict[str, Any]:
        with open(self.file_path, 'r') as f:
            return json.load(f)
        
        
    def save(
        self, 
        d: dict[str, Any], 
        force: bool = False
    ) -> None:
        """Save the input dictionary to file in the JSON file format.

        :param d: The dictionary to save.
        :param force: If True, overwrites the file if it already exists, defaults to False
        :raises FileExistsError: If the file exists and `force` is False.
        """
        self.make_parent_dir_path()

        if self.exists:
            if force:
                pass
            else:
                raise FileExistsError((f"{self.file_name} already exists, write has been abandoned. "
                                       f"You can override this functionality with `force`"))

        with open(self.file_path, 'w') as file:
                json.dump(d, file, indent=4)

    

class TextHandler(BaseFileHandler[str]):
    """File handler for text formatted files."""
    def __init__(
        self, 
        parent_dir_path: str,
        base_file_name: str, 
        extension: str = "txt"
    ) -> None:
        super().__init__(parent_dir_path,
                         base_file_name,
                         extension)
    
    
    def _read(
        self
    ) -> str:
        with open(self.file_path, 'r') as f:
            return f.read()