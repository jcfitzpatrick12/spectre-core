# SPDX-FileCopyrightText: © 2024-2025 Jimmy Fitzpatrick <jcfitzpatrick12@gmail.com>
# This file is part of SPECTRE
# SPDX-License-Identifier: GPL-3.0-or-later

from datetime import datetime
import numpy as np
import pytest
from unittest.mock import MagicMock, patch
from spectre_core.batches._batches import Batches, BaseBatch, Spectrogram


@pytest.fixture
def batches():
    """Fixture to create a Batches instance with a mock Batch class."""
    mock_batch_cls = MagicMock(spec=BaseBatch)
    return Batches(tag="test", batch_cls=mock_batch_cls)


def create_real_spectrogram(start_time):
    """Helper fucntion to create a real Spectorgram object."""
    times = np.linspace(0, 600, 11)
    frequencies = np.array([100, 200])
    dynamic_spectra = np.random.rand(len(frequencies), len(times))
    return Spectrogram(
        dynamic_spectra=dynamic_spectra,
        times=times,
        frequencies=frequencies,
        tag="test",
        spectrum_unit="power",
        start_datetime=start_time,
    )


def test_get_spectrogram_returns_joined(batches):
    """Test that get_spectrogram correctly joins overlapping batches."""
    start1 = datetime(2025, 1, 1, 10, 0)
    start2 = datetime(2025, 1, 1, 10, 20)
    batch1 = MagicMock(spec=BaseBatch)
    batch2 = MagicMock(spec=BaseBatch)

    # batch1 spectrogram file exists and returns spectrogram covering 10:00 to 10:10
    batch1.spectrogram_file.exists.return_value = True
    batch1.read_spectrogram.return_value = create_real_spectrogram(start1)

    # batch2 spectrogram file exists and returns spectrogram covering 10:20 to 10:30
    batch2.spectrogram_file.exists.return_value = True
    batch2.read_spectrogram.return_value = create_real_spectrogram(start2)

    batches._batch_map = {
        "2025-01-01T10:00:00": batch1,
        "2025-01-01T10:20:00": batch2,
    }

    with patch(
        "spectre_core.batches._batches.join_spectrograms",
        side_effect=lambda specs: specs[0],
    ) as mock_join, patch(
        "spectre_core.batches._batches.time_chop",
        side_effect=lambda spec, start, end: spec,
    ) as mock_time_chop:
        result = batches.get_spectrogram(
            start_datetime=datetime(2025, 1, 1, 10, 0),
            end_datetime=datetime(2025, 1, 1, 10, 30),
        )

        assert mock_time_chop.call_count == 2
        mock_join.assert_called_once()
        assert result == batch1.read_spectrogram()


def test_get_spectrogram_skips_batches_without_files(batches):
    """Test that get_spectrogram skips batches without spectrogram files."""
    batch = MagicMock(spec=BaseBatch)
    batch.spectrogram_file.exists.return_value = False
    batches._batch_map = {"2025-01-01T10:00:00": batch}

    with pytest.raises(FileNotFoundError):
        batches.get_spectrogram(datetime(2025, 1, 1), datetime(2025, 1, 1, 2))


def test_get_spectrogram_raises_file_not_found(batches):
    """Test that get_spectrogram raises FileNotFoundError when no batches exists."""
    batches._batch_map = {}

    with pytest.raises(FileNotFoundError):
        batches.get_spectrogram(datetime(2025, 1, 1), datetime(2025, 1, 1, 2))


@pytest.mark.parametrize(
    "start1, start2, query_start, query_end, expected_calls",
    [
        # Partial overlap with both batches
        (
            datetime(2025, 1, 1, 9, 50),
            datetime(2025, 1, 1, 10, 10),
            datetime(2025, 1, 1, 10, 0),
            datetime(2025, 1, 1, 10, 20),
            2,
        ),
        # No overlap with any batch
        (
            datetime(2025, 1, 1, 8, 0),
            datetime(2025, 1, 1, 9, 0),
            datetime(2025, 1, 1, 10, 0),
            datetime(2025, 1, 11, 0),
            0,
        ),
        # Single batch overlap
        (
            datetime(2025, 1, 1, 10, 0),
            datetime(2025, 1, 1, 10, 10),
            datetime(2025, 1, 1, 10, 5),
            datetime(2025, 1, 1, 10, 15),
            1,
        ),
        # Complete overlap with one batch
    ],
)
def test_get_spectrogram_various_overlaps(
    batches, start1, start2, query_start, query_end, expected_calls
):
    """Test various overlap scenarios for get_spectrogram."""
    batch1 = MagicMock(spec=BaseBatch)
    batch2 = MagicMock(spec=BaseBatch)

    batch1.spectrogram_file.exists.return_value = True
    batch1.read_spectrogram.return_value = create_real_spectrogram(start1)

    batch2.spectrogram_file.exists.return_value = True
    batch2.read_spectrogram.return_value = create_real_spectrogram(start2)

    batches._batch_map = {
        "2025-01-01T10:00:00": batch1,
        "2025-01-01T10:20:00": batch2,
    }

    with patch(
        "spectre_core.batches._batches.join_spectrograms",
        side_effect=lambda specs: specs[0],
    ) as mock_join, patch(
        "spectre_core.batches._batches.time_chop",
        side_effect=lambda spec, start, end: spec,
    ) as mock_time_chop:
        if expected_calls == 0:
            with pytest.raises(FileNotFoundError):
                batches.get_spectrogram(query_start, query_end)
        else:
            result = batches.get_spectrogram(query_start, query_end)
            assert mock_time_chop.call_count == expected_calls
            mock_join.assert_called_once()
            assert result is not None
