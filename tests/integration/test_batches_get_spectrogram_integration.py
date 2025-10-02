# SPDX-FileCopyrightText: © 2024-2025 Jimmy Fitzpatrick <jcfitzpatrick12@gmail.com>
# This file is part of SPECTRE
# SPDX-License-Identifier: GPL-3.0-or-later

# SPDX-FileCopyrightText: © 2024-2025 Jimmy Fitzpatrick <jcfitzpatrick12@gmail.com>
# This file is part of SPECTRE
# SPDX-License-Identifier: GPL-3.0-or-later

from typing import Any
import pytest
from tempfile import TemporaryDirectory
from datetime import datetime, timedelta

from spectre_core.capture_configs import make_parameters
from spectre_core.spectrograms import Spectrogram, SpectrumUnit
from spectre_core.batches import Batches, IQStreamBatch
from spectre_core.receivers import ReceiverName, Receiver, get_receiver
from spectre_core.post_processing import start_post_processor
from spectre_core.jobs import make_worker, start_job
from spectre_core.config import set_spectre_data_dir_path


@pytest.fixture
def signal_generator() -> Receiver:
    """Get a signal generator, with mode not yet set."""
    return get_receiver(ReceiverName.SIGNAL_GENERATOR)


@pytest.fixture
def spectre_data_dir_path():
    """Fixture to set up a temporary directory for Spectre filesystem data."""
    with TemporaryDirectory() as temp_dir:
        set_spectre_data_dir_path(temp_dir)
        yield temp_dir


TOTAL_RUNTIME = 5
ATOL = 1e-5

COSINE_WAVE_MODE = "cosine_wave"
COSINE_WAVE_PARAMETERS = {
    "amplitude": 2.0,
    "event_handler_key": "fixed_center_frequency",
    "frequency": 32000.0,
    "watch_extension": "bin",
    "window_hop": 512,
    "window_size": 512,
    "window_type": "boxcar",
    "sample_rate": 128000,
    "frequency_resolution": None,
    "time_range": None,
    "time_resolution": None,
}


def _run_and_query(
    receiver: Receiver,
    tag: str,
    data_dir: str,
    total_runtime: int,
) -> Spectrogram:
    """Helper to spin up capture + post-processing and return the spectrogram."""
    post_proc = make_worker(
        "post_processing_worker",
        start_post_processor,
        (tag,),
        spectre_data_dir_path=data_dir,
    )
    capture = make_worker(
        "capture_worker",
        receiver.start_capture,
        (tag,),
        spectre_data_dir_path=data_dir,
    )
    start_job([post_proc, capture], total_runtime)

    batches = Batches(tag, IQStreamBatch)
    times = [datetime.fromisoformat(t) for t in batches.start_times]
    start = min(times) - timedelta(seconds=1)
    end = max(times) + timedelta(seconds=5)
    return batches.get_spectrogram(start, end)


class TestBatchesGetSpectrogramIntegration:
    @pytest.mark.parametrize(
        ("mode", "parameters"),
        [(COSINE_WAVE_MODE, COSINE_WAVE_PARAMETERS)],
    )
    def test_valid_time_range_returns_spectrogram(
        self,
        spectre_data_dir_path: str,
        signal_generator: Receiver,
        mode: str,
        parameters: dict[str, Any],
    ) -> None:
        """Test that a valid time range returns a spectrogram."""

        signal_generator.mode = mode
        tag = mode.replace("_", "-")
        signal_generator.save_parameters(tag, make_parameters(parameters), force=True)

        spectrogram = _run_and_query(
            receiver=signal_generator,
            tag=tag,
            data_dir=spectre_data_dir_path,
            total_runtime=TOTAL_RUNTIME,
        )

        assert spectrogram is not None
        assert isinstance(spectrogram, Spectrogram)
        assert spectrogram.tag == tag
        assert spectrogram.spectrum_unit == SpectrumUnit.AMPLITUDE
        assert spectrogram.dynamic_spectra.ndim == 2
        assert spectrogram.times.min() >= 0


    @pytest.mark.parametrize(
        ("mode", "parameters"),
        [(COSINE_WAVE_MODE, COSINE_WAVE_PARAMETERS)],
    )
    def test_invalid_time_range_raises_file_not_found(
        self,
        spectre_data_dir_path: str,
        signal_generator: Receiver,
        mode: str,
        parameters: dict[str, Any],
    ) -> None:
        """Test that querying a time range with no data raises FileNotFoundError."""

        signal_generator.mode = mode
        tag = mode.replace("_", "-")
        signal_generator.save_parameters(tag, make_parameters(parameters), force=True)
        _ = _run_and_query(
            receiver=signal_generator,
            tag=tag,
            data_dir=spectre_data_dir_path,
            total_runtime=TOTAL_RUNTIME,
        )

        batches = Batches(tag, IQStreamBatch)
        start_range = datetime(3000, 1, 1)
        end_range   = datetime(3000, 1, 2)
        with pytest.raises(FileNotFoundError):
            _ = batches.get_spectrogram(start_range, end_range)