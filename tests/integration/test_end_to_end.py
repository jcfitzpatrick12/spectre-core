# SPDX-FileCopyrightText: © 2024-2025 Jimmy Fitzpatrick <jcfitzpatrick12@gmail.com>
# This file is part of SPECTRE
# SPDX-License-Identifier: GPL-3.0-or-later

import typing
import pytest

import spectre_core.receivers
import spectre_core.config
import spectre_core.batches
import spectre_core.jobs


@pytest.fixture
def signal_generator() -> spectre_core.receivers.Base:
    """Get a signal generator, with mode not yet set."""
    return spectre_core.receivers.get_receiver(
        spectre_core.receivers.ReceiverName.SIGNAL_GENERATOR
    )


ATOL = 1e-4
DURATION = 6
BATCH_SIZE = 2
USE_DEFAULT_PARAMETERS: dict[str, typing.Any] = {}
COSINE_WAVE_MODE = "cosine_wave"
COSINE_WAVE_PARAMETERS = {
    "batch_size": BATCH_SIZE,
    "amplitude": 2.0,
    "frequency": 32000.0,
    "window_hop": 512,
    "window_size": 512,
    "window_type": "boxcar",
    "sample_rate": 128000,
}

CONSTANT_STAIRCASE_MODE = "constant_staircase"
CONSTANT_STAIRCASE_PARAMETERS = {
    "batch_size": BATCH_SIZE,
    "frequency_step": 128000.0,
    "max_samples_per_step": 5000,
    "min_samples_per_step": 4000,
    "sample_rate": 128000,
    "step_increment": 200,
    "window_hop": 512,
    "window_size": 512,
    "window_type": "boxcar",
}


class TestEndToEnd:
    """Test end-to-end execution of the program using the signal generator, comparing
    the results to analytically derived solutions."""

    @pytest.mark.parametrize(
        ("mode", "parameters"),
        [
            (COSINE_WAVE_MODE, USE_DEFAULT_PARAMETERS),
            (COSINE_WAVE_MODE, COSINE_WAVE_PARAMETERS),
            (CONSTANT_STAIRCASE_MODE, USE_DEFAULT_PARAMETERS),
            (CONSTANT_STAIRCASE_MODE, CONSTANT_STAIRCASE_PARAMETERS),
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
            tag,
            parameters,
            configs_dir_path=spectre_config_paths.get_configs_dir_path(),
        )

        # Read the config back from the filesystem.
        config = signal_generator.read_config(
            tag, configs_dir_path=spectre_config_paths.get_configs_dir_path()
        )

        # Record some spectrograms.
        spectre_core.receivers.record_spectrograms(
            config,
            DURATION,
            spectre_data_dir_path=spectre_config_paths.get_spectre_data_dir_path(),
        )

        # Check that we've found some spectrograms.
        found_spectrograms = False

        # Compare each spectrogram to the corresponding analytically derived solutions.
        for batch in spectre_core.batches.Batches(
            tag, signal_generator.batch_cls, spectre_config_paths.get_batches_dir_path()
        ):
            if batch.spectrogram_file.exists:

                spectrogram = batch.read_spectrogram()
                found_spectrograms = True

                result = signal_generator.validate_analytically(
                    spectrogram,
                    signal_generator.model_validate(config.parameters),
                    ATOL,
                )

                assert result["frequencies_validated"]
                assert result["times_validated"]

                # Permit at most one invalid spectrum (usually the first, due to window effects)
                assert 0 <= result["num_invalid_spectrums"] <= 1

        assert found_spectrograms
