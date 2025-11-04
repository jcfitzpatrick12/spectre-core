# SPDX-FileCopyrightText: © 2024-2025 Jimmy Fitzpatrick <jcfitzpatrick12@gmail.com>
# This file is part of SPECTRE
# SPDX-License-Identifier: GPL-3.0-or-later

"""Basic file io for common file formats."""

from .files import BaseFile, FileFormat, read_file

__all__ = ["BaseFile", "FileFormat", "read_file"]
