# SPDX-FileCopyrightText: © 2024-2025 Jimmy Fitzpatrick <jcfitzpatrick12@gmail.com>
# This file is part of SPECTRE
# SPDX-License-Identifier: GPL-3.0-or-later

import typing
import pytest
import tempfile

import spectre_core.receivers
import spectre_core.config
import spectre_core.batches
import spectre_core.post_processing
import spectre_core.spectrograms
import spectre_core.jobs


@pytest.fixture
def signal_generator() -> spectre_core.receivers.BaseReceiver:
    """Get a signal generator, with mode not yet set."""
    return spectre_core.receivers.get_receiver(
        spectre_core.receivers.ReceiverName.SIGNAL_GENERATOR
    )


TOTAL_RUNTIME = 10
ATOL = 1e-4

COSINE_WAVE_MODE = "cosine_wave"
COSINE_WAVE_PARAMETERS = {
    "amplitude": 2.0,
    "frequency": 32000.0,
    "window_hop": 512,
    "window_size": 512,
    "window_type": "boxcar",
    "batch_size": 2,
    "sample_rate": 128000,
}


class TestE2E:
    """Test end-to-end execution of the program using the signal generator, comparing
    the results to analytically derived solutions."""

    @pytest.mark.parametrize(
        ("mode", "parameters"),
        [
            (COSINE_WAVE_MODE, COSINE_WAVE_PARAMETERS),
        ],
    )
    def test_end_to_end(
        self,
        spectre_config_paths: spectre_core.config.Paths,
        signal_generator: spectre_core.receivers.SignalGenerator,
        mode: str,
        parameters: dict[str, typing.Any],
    ) -> None:
        # Set the mode of the receiver.
        signal_generator.mode = mode

        # Make a new config, with the tag dynamically created based on the receiver mode.
        tag = mode.replace("_", "-")
        signal_generator.write_config(
            tag, parameters, spectre_config_paths.get_configs_dir_path()
        )

        # Read the config back from the filesystem.
        config = signal_generator.read_config(
            tag, spectre_config_paths.get_configs_dir_path()
        )

        post_processing_worker = spectre_core.jobs.make_worker(
            "post_processing",
            signal_generator.activate_post_processing,
            (
                config,
                spectre_config_paths.get_batches_dir_path(),
            ),
            spectre_data_dir_path=spectre_config_paths.get_spectre_data_dir_path(),
        )

        flowgraph_worker = spectre_core.jobs.make_worker(
            "flowgraph",
            signal_generator.activate_flowgraph,
            (
                config,
                spectre_config_paths.get_batches_dir_path(),
            ),
            spectre_data_dir_path=spectre_config_paths.get_spectre_data_dir_path(),
        )
        spectre_core.jobs.start_job(
            [post_processing_worker, flowgraph_worker], TOTAL_RUNTIME
        )

        # Check that we've found some spectrums.
        found_spectrograms = False

        # Compare each spectrogram to the corresponding analytically derived solutions.
        for batch in spectre_core.batches.Batches(
            tag, signal_generator.batch, spectre_config_paths.get_batches_dir_path()
        ):
            if batch.spectrogram_file.exists:

                spectrogram = batch.read_spectrogram()
                found_spectrograms = True

                result = signal_generator.validate_analytically(
                    spectrogram, config, ATOL
                )

                assert result["frequencies_validated"]
                assert result["times_validated"]

                # Permit at most one invalid spectrum (usually the first, due to window effects)
                assert 0 <= result["num_invalid_spectrums"] <= 1

        assert found_spectrograms
