# SPDX-FileCopyrightText: © 2024-2025 Jimmy Fitzpatrick <jcfitzpatrick12@gmail.com>
# This file is part of SPECTRE
# SPDX-License-Identifier: GPL-3.0-or-later

from typing import Any
import pytest
from tempfile import TemporaryDirectory

from spectre_core.capture_configs import make_parameters, CaptureConfig
from spectre_core.batches import Batches, IQStreamBatch
from spectre_core.receivers import ReceiverName, Receiver, get_receiver
from spectre_core.post_processing import start_post_processor
from spectre_core.spectrograms import validate_analytically
from spectre_core.jobs import make_worker, start_job


@pytest.fixture
def signal_generator() -> Receiver:
    """Get a signal generator, with mode not yet set."""
    return get_receiver(ReceiverName.SIGNAL_GENERATOR)


TOTAL_RUNTIME = 10
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

CONSTANT_STAIRCASE_MODE = "constant_staircase"
CONSTANT_STAIRCASE_PARAMETERS = {
    "batch_key": "iq_stream",
    "batch_size": 3,
    "event_handler_key": "swept_center_frequency",
    "frequency_step": 128000.0,
    "max_samples_per_step": 5000,
    "min_samples_per_step": 4000,
    "sample_rate": 128000,
    "step_increment": 200,
    "watch_extension": "bin",
    "window_hop": 512,
    "window_size": 512,
    "window_type": "boxcar",
    "time_range": None,
    "time_resolution": None,
    "frequency_resolution": None,
}


class TestE2E:
    """Test end-to-end execution of the program using the signal generator, comparing
    the results to analytically derived solutions."""

    @pytest.mark.parametrize(
        ("mode", "parameters"),
        [
            (COSINE_WAVE_MODE, COSINE_WAVE_PARAMETERS),
            (CONSTANT_STAIRCASE_MODE, CONSTANT_STAIRCASE_PARAMETERS),
        ],
    )
    def test_end_to_end(
        self,
        spectre_data_dir_path: str,
        signal_generator: Receiver,
        mode: str,
        parameters: dict[str, Any],
    ) -> None:
        # Set the mode of the receiver.
        signal_generator.mode = mode

        # Create a capture config, with the tag dynamically created based on the mode.
        # Underscores are replaced by hyphens, since they are used as a seperator
        # in the capture config name and are not allowed.
        tag = mode.replace("_", "-")
        signal_generator.save_parameters(tag, make_parameters(parameters), force=True)

        # Use the signal generator to produce some spectrograms.
        post_processing_worker = make_worker(
            "post_processing_worker",
            start_post_processor,
            (tag,),
            spectre_data_dir_path=spectre_data_dir_path,
        )
        capture_worker = make_worker(
            "capture_worker",
            signal_generator.start_capture,
            (tag,),
            spectre_data_dir_path=spectre_data_dir_path,
        )
        start_job([post_processing_worker, capture_worker], TOTAL_RUNTIME)

        # Compare each spectrogram to the corresponding analytically derived solutions.
        for batch in Batches(tag, IQStreamBatch):
            if batch.spectrogram_file.exists:
                spectrogram = batch.read_spectrogram()

                capture_config = CaptureConfig(tag)
                test_results = validate_analytically(spectrogram, capture_config, ATOL)

                assert test_results.frequencies_validated
                assert test_results.times_validated

                # Permit at most one invalid spectrum (usually the first, due to window effects)
                assert 0 <= test_results.num_invalid_spectrums <= 1
