# SPDX-FileCopyrightText: © 2024-2025 Jimmy Fitzpatrick <jcfitzpatrick12@gmail.com>
# This file is part of SPECTRE
# SPDX-License-Identifier: GPL-3.0-or-later

import dataclasses
import os
import typing
import json

import spectre_core.io
import spectre_core.config

_reserved = ["callisto"]


def _validate_tag(tag: str) -> None:
    if "_" in tag:
        raise ValueError("An underscore is not allowed in a capture config tag.")
    for s in _reserved:
        if s in tag:
            raise ValueError(
                f"'{tag}' is an invalid tag, the substring '{s}' is reserved, "
            )


def _validate_keys(content: dict[str, str]) -> None:
    required_keys = {
        _CaptureConfigKey.RECEIVER_NAME,
        _CaptureConfigKey.RECEIVER_MODE,
        _CaptureConfigKey.PARAMETERS,
    }
    missing_keys = required_keys - content.keys()
    if missing_keys:
        raise ValueError(f"Missing required keys in config content: {missing_keys}")


@dataclasses.dataclass(frozen=True)
class _CaptureConfigKey:
    """Defined JSON keys for configs.

    :ivar RECEIVER_NAME: The name of the receiver.
    :ivar RECEIVER_MODE: The operating mode for the receiver.
    :ivar PARAMETERS: User-configured parameters.
    """

    RECEIVER_NAME = "receiver_name"
    RECEIVER_MODE = "receiver_mode"
    PARAMETERS = "parameters"


class Config:
    def __init__(self, tag: str, content: dict[str, typing.Any]) -> None:
        _validate_keys(content)
        _validate_tag(tag)
        self._tag = tag
        self._content = content

    @property
    def tag(self) -> str:
        """A unique identifier."""
        return self._tag

    @property
    def receiver_name(self) -> str:
        """The name of the receiver."""
        return self._content[_CaptureConfigKey.RECEIVER_NAME]

    @property
    def receiver_mode(self) -> str:
        """The operating mode for the receiver."""
        return self._content[_CaptureConfigKey.RECEIVER_MODE]

    @property
    def parameters(self) -> dict[str, typing.Any]:
        """User-configurable parameters."""
        return self._content[_CaptureConfigKey.PARAMETERS]


def read_config(tag: str, configs_dir_path: typing.Optional[str] = None) -> Config:
    configs_dir_path = configs_dir_path or spectre_core.config.paths.get_logs_dir_path()
    file_path = os.path.join(configs_dir_path, f"{tag}.json")
    return Config(
        tag, spectre_core.io.read_file(file_path, spectre_core.io.FileFormat.JSON)
    )


def write_config(
    tag: str,
    receiver_name: str,
    receiver_mode: str,
    parameters: dict[str, typing.Any],
    configs_dir_path: typing.Optional[str] = None,
) -> None:
    configs_dir_path = (
        configs_dir_path or spectre_core.config.paths.get_configs_dir_path()
    )
    content = {
        _CaptureConfigKey.RECEIVER_NAME: receiver_name,
        _CaptureConfigKey.RECEIVER_MODE: receiver_mode,
        _CaptureConfigKey.PARAMETERS: parameters,
    }
    file_path = os.path.join(configs_dir_path, f"{tag}.json")
    with open(file_path, "w") as f:
        json.dump(content, f, indent=4)
