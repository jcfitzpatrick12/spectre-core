# SPDX-FileCopyrightText: © 2024-2025 Jimmy Fitzpatrick <jcfitzpatrick12@gmail.com>
# This file is part of SPECTRE
# SPDX-License-Identifier: GPL-3.0-or-later

import pytest
from tempfile import TemporaryDirectory

from spectre_core.config import set_spectre_data_dir_path


@pytest.fixture
def spectre_data_dir_path():
    """Fixture to set up a temporary directory for Spectre filesystem data.

    Returns the name of the temporary directory.
    """
    with TemporaryDirectory() as temp_dir:
        set_spectre_data_dir_path(temp_dir)
        yield temp_dir
