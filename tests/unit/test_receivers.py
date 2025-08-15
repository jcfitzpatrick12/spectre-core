# SPDX-FileCopyrightText: © 2024-2025 Jimmy Fitzpatrick <jcfitzpatrick12@gmail.com>
# This file is part of SPECTRE
# SPDX-License-Identifier: GPL-3.0-or-later

import pytest
import os
import json
from tempfile import TemporaryDirectory
from time import sleep
from typing import cast

from spectre_core.receivers import (
    get_receiver,
    Receiver,
    ReceiverName,
    SpecName,
    RSP1A,
    RSPduo,
    RSPdx,
)
from spectre_core.capture_configs import make_base_capture_template, Parameters, PName
from spectre_core.exceptions import ModeNotFoundError
from spectre_core.config import set_spectre_data_dir_path

_PLACEHOLDER_TAG = "foobar"
_SIGNAL_CAPTURE = "signal_capture"
_SAMPLE_RATE = 5  # Hz
_SAMPLE_RATE_LOWER_BOUND = 1  # Hz
_SAMPLE_RATE_UPPER_BOUND = 10  # Hz


@pytest.fixture
def spectre_data_dir_path():
    """Fixture to set up a temporary directory for SPECTRE data."""
    with TemporaryDirectory() as temp_dir:
        set_spectre_data_dir_path(temp_dir)
        yield temp_dir


@pytest.fixture()
def empty_receiver() -> Receiver:
    """Create an instance of `Receiver` with no operating modes."""
    return get_receiver(ReceiverName.CUSTOM)


def _signal_capture(tag: str, parameters: Parameters):
    """Simulate capture from an SDR."""
    sample_interval = 1 / cast(float, parameters.get_parameter_value(PName.SAMPLE_RATE))
    while True:
        print("Taking sample...")
        sleep(sample_interval)


@pytest.fixture()
def inactive_receiver() -> Receiver:
    """A simple receiver with one operating mode, and it's mode unset."""
    receiver = get_receiver(ReceiverName.CUSTOM)

    # Create a simple capture template, which allows us to configure the sleep.
    capture_template = make_base_capture_template(PName.SAMPLE_RATE)
    capture_template.set_default(PName.SAMPLE_RATE, 5)  # Hz

    # Set some bounds for the sample rate.
    receiver.add_spec(SpecName.SAMPLE_RATE_LOWER_BOUND, _SAMPLE_RATE_LOWER_BOUND)
    receiver.add_spec(SpecName.SAMPLE_RATE_UPPER_BOUND, _SAMPLE_RATE_UPPER_BOUND)

    # Add a single mode.
    receiver.add_mode(_SIGNAL_CAPTURE, _signal_capture, capture_template)

    return receiver


@pytest.fixture()
def receiver(inactive_receiver: Receiver) -> Receiver:
    """A simple receiver with one operating mode called `sleep`, and it's mode unset."""
    inactive_receiver.mode = _SIGNAL_CAPTURE
    return inactive_receiver


@pytest.fixture()
def inactive_rsp1a() -> RSP1A:
    """Return an instance of an RSP1A, with no mode set."""
    return get_receiver(ReceiverName.RSP1A)


@pytest.fixture()
def inactive_rspduo() -> RSPduo:
    """Return an instance of an RSPduo, with no mode set."""
    return get_receiver(ReceiverName.RSPDUO)


@pytest.fixture()
def inactive_rspdx() -> RSPdx:
    """Return an instance of an RSPdx, with no mode set."""
    return get_receiver(ReceiverName.RSPDX)


class TestReceiver:
    def test_no_active_mode(self, inactive_receiver: Receiver) -> None:
        """Check that a receiver with no mode set, is inactive."""
        assert inactive_receiver.mode is None
        with pytest.raises(ValueError):
            inactive_receiver.active_mode

    def test_active_mode(self, receiver: Receiver) -> None:
        """Check that a receiver with mode set, is active."""
        # Check that the active mode is consistent with the mode
        assert receiver.active_mode == receiver.mode
        # Check that the active mode is the mode we added to the custom receiver
        assert receiver.active_mode == _SIGNAL_CAPTURE

    def test_name(self, receiver: Receiver) -> None:
        """Check that the receiver name is set correctly."""
        assert receiver.name == ReceiverName.CUSTOM

    def test_set_invalid_mode(self, empty_receiver: Receiver) -> None:
        """Check that you cannot set an invalid mode."""
        with pytest.raises(ModeNotFoundError):
            # Use an arbitrary invalid mode name
            empty_receiver.mode = "foobarbaz"

    def test_set_valid_mode(self, inactive_receiver: Receiver) -> None:
        """Check that you can set a mode."""
        assert inactive_receiver.mode is None
        inactive_receiver.mode = _SIGNAL_CAPTURE
        assert inactive_receiver.mode == _SIGNAL_CAPTURE

    def test_check_modes(self, receiver: Receiver) -> None:
        """Check that the `modes` provides a correct list of available modes."""
        assert receiver.modes == [_SIGNAL_CAPTURE]

    def test_check_modes_empty(self, empty_receiver: Receiver) -> None:
        """Check that an empty receiver has no operating modes."""
        assert len(empty_receiver.modes) == 0
        assert not empty_receiver.modes

    def test_no_specs(self, empty_receiver: Receiver) -> None:
        with pytest.raises(KeyError):
            # Choose any `SpecName` arbitrarily (the empty receiver doesn't have any at all, so all should raise an error)
            empty_receiver.get_spec(SpecName.MASTER_CLOCK_RATE_UPPER_BOUND)

    def test_save_parameters(
        self, spectre_data_dir_path: str, receiver: Receiver
    ) -> None:
        """Check that valid parameters may be written to a capture config, and the contents are as expected."""

        # Define a tag for the capture config, and some valid parameters to save within it.
        tag = "tmp-tag"
        parameters = Parameters()
        parameters.add_parameter(PName.SAMPLE_RATE, _SAMPLE_RATE)

        receiver.save_parameters(tag, parameters)

        # Check the newly created file exists in the file system.
        expected_abs_file_path = os.path.join(
            spectre_data_dir_path, "configs", f"{tag}.json"
        )
        assert os.path.exists(expected_abs_file_path)

        # Read it, and check the contents are as expected.
        with open(expected_abs_file_path, "rb") as f:
            actual_contents = json.load(f)
            expected_contents = {
                "receiver_mode": "signal_capture",
                "receiver_name": "custom",
                "parameters": {"sample_rate": 5},
            }
            assert actual_contents == expected_contents

    def test_load_parameters(
        self, spectre_data_dir_path: str, receiver: Receiver
    ) -> None:
        """Check that a capture config can be loaded from file, and the contents are as expected."""
        # Define a tag for the capture config, and some valid parameters to save within it.
        tag = "tmp-tag"
        parameters = Parameters()
        parameters.add_parameter(PName.SAMPLE_RATE, _SAMPLE_RATE)

        # Save some parameters, and immediately read them back and check for consistency.
        receiver.save_parameters(tag, parameters)
        parameters = receiver.load_parameters(tag)
        assert parameters.name_list == [PName.SAMPLE_RATE]
        assert parameters.get_parameter_value(PName.SAMPLE_RATE) == _SAMPLE_RATE

    def test_add_spec(self, empty_receiver: Receiver) -> None:
        """Check that we can add a hardware specification, and it updates the instance accordingly."""
        spec_name = SpecName.SAMPLE_RATE_LOWER_BOUND
        spec_value = 1
        empty_receiver.add_spec(spec_name, spec_value)
        assert empty_receiver.specs == {spec_name: spec_value}
        assert empty_receiver.get_spec(spec_name) == spec_value


class TestSDRPlay:
    def test_rsp1a_modes(self, inactive_rsp1a: RSP1A) -> None:
        """Check that the modes are as expected."""
        assert inactive_rsp1a.modes == [
            "fixed_center_frequency",
            "swept_center_frequency",
        ]

    def test_rsp1a_default_parameters(
        self, spectre_data_dir_path: str, inactive_rsp1a: RSP1A
    ) -> None:
        """Check that the default parameters for an RSP1A in each mode pass validation."""
        rsp1a = inactive_rsp1a

        rsp1a.mode = "fixed_center_frequency"
        rsp1a.save_parameters(_PLACEHOLDER_TAG, Parameters(), force=True)

        rsp1a.mode = "swept_center_frequency"
        rsp1a.save_parameters(_PLACEHOLDER_TAG, Parameters(), force=True)

    def test_rspduo_modes(self, inactive_rspduo: RSPduo) -> None:
        """Check that the modes are as expected."""
        assert inactive_rspduo.modes == [
            "fixed_center_frequency",
            "swept_center_frequency",
        ]

    def test_rspduo_default_parameters(
        self, spectre_data_dir_path: str, inactive_rspduo: RSPduo
    ) -> None:
        """ "Check that the default parameters for an RSPduo in each mode pass validation."""
        rspduo = inactive_rspduo

        rspduo.mode = "fixed_center_frequency"
        rspduo.save_parameters(_PLACEHOLDER_TAG, Parameters(), force=True)

        rspduo.mode = "swept_center_frequency"
        rspduo.save_parameters(_PLACEHOLDER_TAG, Parameters(), force=True)

    def test_rspdx_modes(self, inactive_rspdx: RSPduo) -> None:
        """Check that the modes are as expected."""
        assert inactive_rspdx.modes == [
            "fixed_center_frequency",
            "swept_center_frequency",
        ]

    def test_rspdx_default_parameters(
        self, spectre_data_dir_path: str, inactive_rspdx: RSPdx
    ) -> None:
        """ "Check that the default parameters for an RSPdx in each mode pass validation."""
        rspdx = inactive_rspdx

        rspdx.mode = "fixed_center_frequency"
        rspdx.save_parameters(_PLACEHOLDER_TAG, Parameters(), force=True)

        rspdx.mode = "swept_center_frequency"
        rspdx.save_parameters(_PLACEHOLDER_TAG, Parameters(), force=True)
