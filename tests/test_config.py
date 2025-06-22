# SPDX-FileCopyrightText: © 2024-2025 Jimmy Fitzpatrick <jcfitzpatrick12@gmail.com>
# This file is part of SPECTRE
# SPDX-License-Identifier: GPL-3.0-or-later

import pytest
import os
from spectre_core.config import (
    get_batches_dir_path,
    get_logs_dir_path,
    get_configs_dir_path,
)


@pytest.fixture(autouse=True)
def patch_spectre_data_dir_path():
    """Patch the environment which defines the shared ancestral path of all log, batch and config files."""
    pytest.MonkeyPatch().setenv(
        "SPECTRE_DATA_DIR_PATH", os.path.join("/tmp", ".spectre-data")
    )


@pytest.mark.parametrize(
    ["year", "month", "day", "expected_dir_path"],
    [
        (None, None, None, os.path.join("/tmp", ".spectre-data", "batches")),
        (2025, None, None, os.path.join("/tmp", ".spectre-data", "batches", "2025")),
        (2025, 2, None, os.path.join("/tmp", ".spectre-data", "batches", "2025", "02")),
        (
            2025,
            2,
            13,
            os.path.join("/tmp", ".spectre-data", "batches", "2025", "02", "13"),
        ),
    ],
)
def test_get_batches_dir_path(
    year: int,
    month: int,
    day: int,
    expected_dir_path: str,
) -> None:
    """Check that the batches directory paths are created as expected."""
    result = get_batches_dir_path(year, month, day)
    assert result == expected_dir_path


@pytest.mark.parametrize(
    ["year", "month", "day", "expected_dir_path"],
    [
        (None, None, None, os.path.join("/tmp", ".spectre-data", "logs")),
        (2025, None, None, os.path.join("/tmp", ".spectre-data", "logs", "2025")),
        (2025, 2, None, os.path.join("/tmp", ".spectre-data", "logs", "2025", "02")),
        (
            2025,
            2,
            13,
            os.path.join("/tmp", ".spectre-data", "logs", "2025", "02", "13"),
        ),
    ],
)
def test_get_logs_dir_path(
    year: int,
    month: int,
    day: int,
    expected_dir_path: str,
) -> None:
    """Check that the logs directory paths are created as expected."""
    result = get_logs_dir_path(year, month, day)
    assert result == expected_dir_path


def test_get_configs_dir_path():
    """Check that the configs directory path is created as expected."""
    assert get_configs_dir_path() == os.path.join("/tmp", ".spectre-data", "configs")
