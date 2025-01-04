# SPDX-FileCopyrightText: © 2024 Jimmy Fitzpatrick <jcfitzpatrick12@gmail.com>
# This file is part of SPECTRE
# SPDX-License-Identifier: GPL-3.0-or-later

from typing import Literal, overload, Type

from spectre_core.exceptions import BatchNotFoundError
from ._base import BaseBatch
from ._register import batch_map
from .plugins._batch_keys import BatchKeys
from .plugins._callisto import CallistoBatch
from .plugins._iq_stream import IQStreamBatch


@overload
def get_batch_cls(
    batch_key: Literal[BatchKeys.CALLISTO],
) -> Type[CallistoBatch]:
    ...


@overload
def get_batch_cls(
    batch_key: Literal[BatchKeys.IQ_STREAM],
) -> Type[IQStreamBatch]:
    ...


def get_batch_cls(
    batch_key: Literal[BatchKeys.CALLISTO, BatchKeys.IQ_STREAM]
) -> Type[BaseBatch]:
    """Get a `Batch` plugin class.

    :param batch_key: The key used to register the `Batch` class.
    :raises BatchNotFoundError: If an undefined `batch_key` is provided.
    :return: The `Batch` corresponding to the input key.
    """
    Batch = batch_map.get(batch_key)
    if Batch is None:
        valid_batch_keys = list(batch_map.keys())
        raise BatchNotFoundError(f"No batch found for the batch key: {batch_key}. "
                                 f"Valid batch keys are: {valid_batch_keys}")
    return Batch
