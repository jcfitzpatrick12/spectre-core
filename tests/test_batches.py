# SPDX-FileCopyrightText: © 2024-2025 Jimmy Fitzpatrick <jcfitzpatrick12@gmail.com>
# This file is part of SPECTRE
# SPDX-License-Identifier: GPL-3.0-or-later

import pytest
from typing import Tuple

from spectre_core.batches._base import parse_batch_file_name


@pytest.mark.parametrize(
    "file_name, parsed_file_name",
    [
        (
            "2025-06-01T00:00:00_tag.ext",
            ("2025-06-01T00:00:00", "tag", "ext"),
        ),  # Happy path.
        (
            "2025-06-01T00:00:00_tag",
            ("2025-06-01T00:00:00", "tag", ""),
        ),  # No extension.
    ],
)
def test_parse_batch_file_name(
    file_name: str, parsed_file_name: Tuple[str, str, str]
) -> None:
    result = parse_batch_file_name(file_name)
    assert result == parsed_file_name


@pytest.mark.parametrize(
    "file_name",
    [
        "2025-06-01T00:00:00.ext",  # No tag
        "2025-06-01T00:00:00_bad_tag.ext",  # Multiple underscores.
    ],
)
def test_parse_batch_file_name_invalid_underscores(file_name: str) -> None:
    with pytest.raises(
        ValueError, match="Expected exactly one underscore in the batch name"
    ):
        parse_batch_file_name(file_name)
