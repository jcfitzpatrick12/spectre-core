# SPDX-FileCopyrightText: © 2024-2025 Jimmy Fitzpatrick <jcfitzpatrick12@gmail.com>
# This file is part of SPECTRE
# SPDX-License-Identifier: GPL-3.0-or-later

from typing import Literal, overload, Type, cast

from spectre_core.exceptions import BatchNotFoundError
from spectre_core.capture_configs import CaptureConfig, PName
from ._base import BaseBatch
from ._register import batch_map
from .plugins._batch_keys import BatchKey
from .plugins._callisto import CallistoBatch
from .plugins._iq_stream import IQStreamBatch


@overload
def get_batch_cls(
    batch_key: Literal[BatchKey.CALLISTO],
) -> Type[CallistoBatch]: ...


@overload
def get_batch_cls(
    batch_key: Literal[BatchKey.IQ_STREAM],
) -> Type[IQStreamBatch]: ...


@overload
def get_batch_cls(batch_key: BatchKey) -> Type[BaseBatch]: ...


def get_batch_cls(
    batch_key: BatchKey,
) -> Type[BaseBatch]:
    """Get a registered `BaseBatch` subclass.

    :param batch_key: The key used to register the `BaseBatch` subclass.
    :raises BatchNotFoundError: If an invalid `batch_key` is provided.
    :return: The `BaseBatch` subclass corresponding to the input key.
    """
    batch_cls = batch_map.get(batch_key)
    if batch_cls is None:
        valid_batch_keys = list(batch_map.keys())
        raise BatchNotFoundError(
            f"No batch found for the batch key: {batch_key}. "
            f"Valid batch keys are: {valid_batch_keys}"
        )
    return batch_cls


def get_batch_cls_from_tag(tag: str) -> Type[BaseBatch]:
    # if the tag is reserved (i.e., corresponds to third-party spectrogram data)
    # directly fetch the right class.
    if "callisto" in tag:
        return get_batch_cls(BatchKey.CALLISTO)

    # otherwise, assume that the tag has an associated capture config,
    else:
        capture_config = CaptureConfig(tag)
        if PName.BATCH_KEY not in capture_config.parameters.name_list:
            raise ValueError(
                f"Could not infer batch class from the tag 'tag'. "
                f"A parameter with name `{PName.BATCH_KEY.value}` "
                f"does not exist."
            )

        batch_key = BatchKey(
            cast(str, capture_config.get_parameter_value(PName.BATCH_KEY))
        )
        return get_batch_cls(batch_key)
