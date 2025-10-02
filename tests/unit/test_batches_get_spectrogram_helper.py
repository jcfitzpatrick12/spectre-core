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


def test_filter_batches_by_start_time(batches):
    """Test filtering batches by start time."""
    batch1 = MagicMock(spec=BaseBatch)
    batch2 = MagicMock(spec=BaseBatch)
    batches._batch_map = {
        "2025-01-01T10:00:00": batch1,
        "2025-01-01T10:20:00": batch2,
    }
    filtered = batches.filter_batches_by_start_time(
        datetime(2025, 1, 1, 9, 50), datetime(2025, 1, 1, 10, 15)
    )
    assert batch1 in filtered
    assert batch2 not in filtered


def test_filter_batches_by_existence(batches):
    """Test filtering batches by existence of spectrogram files."""
    batch1 = MagicMock(spec=BaseBatch)
    batch1.spectrogram_file.exists = True
    batch2 = MagicMock(spec=BaseBatch)
    batch2.spectrogram_file.exists = False
    filtered = batches.filter_batches_by_existence([batch1, batch2])
    assert batch1 in filtered
    assert batch2 not in filtered


def test_load_spectrograms_from_batches(batches):
    """Test loading spectrograms from batches."""
    batch = MagicMock(spec=BaseBatch)
    spec = create_real_spectrogram(datetime.now())
    batch.read_spectrogram.return_value = spec
    loaded = batches.load_spectrograms_from_batches([batch])
    assert loaded == [spec]


def test_apply_time_chop_to_spectrograms(batches):
    """Test applying time chop to spectrograms."""
    spec = create_real_spectrogram(datetime(2025, 1, 1, 10, 0))
    with patch(
        "spectre_core.batches._batches.time_chop", side_effect=lambda s, st, et: s
    ) as mock_time_chop:
        chopped = batches.apply_time_chop_to_spectrograms(
            [spec], datetime(2025, 1, 1, 10, 0), datetime(2025, 1, 1, 10, 10)
        )
        assert chopped == [spec]
        assert mock_time_chop.called
