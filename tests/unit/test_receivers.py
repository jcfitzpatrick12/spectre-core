# SPDX-FileCopyrightText: © 2024-2025 Jimmy Fitzpatrick <jcfitzpatrick12@gmail.com>
# This file is part of SPECTRE
# SPDX-License-Identifier: GPL-3.0-or-later

import pytest
import os

import spectre_core.receivers
import spectre_core.exceptions
import spectre_core.config

ACTIVE_MODE = "cosine_wave"


@pytest.fixture
def custom_receiver() -> spectre_core.receivers.Base:
    return spectre_core.receivers.get_receiver(
        spectre_core.receivers.ReceiverName.CUSTOM
    )


@pytest.fixture()
def inactive_signal_generator() -> spectre_core.receivers.Base:
    return spectre_core.receivers.get_receiver(
        spectre_core.receivers.ReceiverName.SIGNAL_GENERATOR
    )


@pytest.fixture()
def signal_generator() -> spectre_core.receivers.Base:
    return spectre_core.receivers.get_receiver(
        spectre_core.receivers.ReceiverName.SIGNAL_GENERATOR, ACTIVE_MODE
    )


class TestReceiver:
    def test_no_active_mode(
        self, inactive_signal_generator: spectre_core.receivers.Base
    ) -> None:
        """Check that a receiver with no mode set, is inactive."""
        assert inactive_signal_generator.mode is None
        with pytest.raises(ValueError):
            inactive_signal_generator.active_mode

    def test_modes_consistent(
        self, signal_generator: spectre_core.receivers.Base
    ) -> None:
        """Check that the active mode is consistent with the mode."""
        assert signal_generator.active_mode == signal_generator.mode

    def test_active_mode(self, signal_generator: spectre_core.receivers.Base) -> None:
        """Check that a receiver with mode set, is active."""
        assert signal_generator.active_mode == ACTIVE_MODE

    def test_set_mode(
        self, inactive_signal_generator: spectre_core.receivers.Base
    ) -> None:
        """Check that a mode can be set and unset."""
        receiver = inactive_signal_generator
        receiver.mode = ACTIVE_MODE
        assert receiver.mode == ACTIVE_MODE
        receiver.mode = None
        assert receiver.mode is None

    def test_set_invalid_mode(
        self, custom_receiver: spectre_core.receivers.Base
    ) -> None:
        """Check that you cannot set an invalid mode."""
        with pytest.raises(spectre_core.exceptions.ModeNotFoundError):
            # Use an arbitrary invalid mode name
            custom_receiver.mode = "foobar"

    def test_name(self, signal_generator: spectre_core.receivers.Base) -> None:
        """Check that the receiver name is set correctly."""
        assert (
            signal_generator.name
            == spectre_core.receivers.ReceiverName.SIGNAL_GENERATOR
        )

    def test_check_modes(self, signal_generator: spectre_core.receivers.Base) -> None:
        """Check that the `modes` provides a correct list of available modes."""
        assert signal_generator.modes == ["cosine_wave", "constant_staircase"]

    def test_check_modes_empty(
        self, custom_receiver: spectre_core.receivers.Base
    ) -> None:
        """Check that an empty receiver has no operating modes."""
        assert len(custom_receiver.modes) == 0
        assert not custom_receiver.modes

    def test_config_io(
        self,
        signal_generator: spectre_core.receivers.Base,
        spectre_config_paths: spectre_core.config.Paths,
    ) -> None:
        """Check that we can read and write parameters from a config."""

        # Write a config to file, using defaults for most parameters except the sample rate.
        tag = "foobar"
        parameters = {"sample_rate": 256000}
        signal_generator.write_config(
            tag,
            parameters,
            configs_dir_path=spectre_config_paths.get_configs_dir_path(),
        )

        # Check a file got created at the expected path.
        expected_absolute_path = os.path.join(
            spectre_config_paths.get_configs_dir_path(), f"{tag}.json"
        )
        assert os.path.exists(expected_absolute_path)

        # Read it back and inspect the contents.
        config = signal_generator.read_config(
            tag, configs_dir_path=spectre_config_paths.get_configs_dir_path()
        )

        assert config.receiver_mode == "cosine_wave"
        assert config.receiver_name == "signal_generator"
        assert "sample_rate" in config.parameters
        assert config.parameters["sample_rate"] == 256000


class TestReceivers:
    @pytest.mark.parametrize(
        ("receiver_name"),
        [
            spectre_core.receivers.ReceiverName.RSP1A,
            spectre_core.receivers.ReceiverName.RSPDUO,
            spectre_core.receivers.ReceiverName.RSPDX,
            spectre_core.receivers.ReceiverName.USRP,
            spectre_core.receivers.ReceiverName.B200MINI,
            spectre_core.receivers.ReceiverName.HACKRF,
            spectre_core.receivers.ReceiverName.HACKRFONE,
            spectre_core.receivers.ReceiverName.RTLSDR,
        ],
    )
    def test_construction(self, receiver_name: str) -> None:
        """Check that each receiver can be constructed."""
        _ = spectre_core.receivers.get_receiver(receiver_name)

    @pytest.mark.parametrize(
        ("receiver_name"),
        [
            spectre_core.receivers.ReceiverName.RSP1A,
            spectre_core.receivers.ReceiverName.RSPDUO,
            spectre_core.receivers.ReceiverName.RSPDX,
            spectre_core.receivers.ReceiverName.USRP,
            spectre_core.receivers.ReceiverName.B200MINI,
            spectre_core.receivers.ReceiverName.HACKRF,
            spectre_core.receivers.ReceiverName.HACKRFONE,
            spectre_core.receivers.ReceiverName.RTLSDR,
        ],
    )
    def test_write_default_config(
        self, spectre_config_paths: spectre_core.config.Paths, receiver_name: str
    ) -> None:
        """Check that the default configs satisfy each model."""
        receiver = spectre_core.receivers.get_receiver(receiver_name)
        for mode in receiver.modes:
            receiver.mode = mode

            # Dynamically create the tag based on the receiver and mode.
            mode = mode.replace("_", "-")
            tag = f"{receiver_name}-{mode}"

            receiver.write_config(
                tag, {}, configs_dir_path=spectre_config_paths.get_configs_dir_path()
            )
            assert os.path.exists(
                spectre_core.receivers.get_config_file_path(
                    tag, spectre_config_paths.get_configs_dir_path()
                )
            )
