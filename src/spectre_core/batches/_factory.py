# SPDX-FileCopyrightText: © 2024 Jimmy Fitzpatrick <jcfitzpatrick12@gmail.com>
# This file is part of SPECTRE
# SPDX-License-Identifier: GPL-3.0-or-later

from spectre_core.capture_configs import CaptureConfig, PNames
from spectre_core.exceptions import BatchNotFoundError
from ._register import batch_map
from ._base import BaseBatch


def _get_batch_cls(batch_key: str) -> BaseBatch:
    Batch = batch_map.get(batch_key)
    if Batch is None:
        valid_batch_keys = list(batch_map.keys())
        raise BatchNotFoundError(f"No batch found for the batch key: {batch_key}. Valid batch keys are: {valid_batch_keys}")
    return Batch


def get_batch_cls_from_tag(tag: str) -> BaseBatch:
    # if we are dealing with a callisto batch, the batch key is equal to the tag
    if "callisto" in tag:
        batch_key = "callisto"
    # otherwise, we fetch the batch key from the capture config
    else:
        capture_config= CaptureConfig(tag)
        batch_key = capture_config.get_parameter_value(PNames.BATCH_KEY)
    return _get_batch_cls(batch_key)
