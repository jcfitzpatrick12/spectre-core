# SPDX-FileCopyrightText: © 2024 Jimmy Fitzpatrick <jcfitzpatrick12@gmail.com>
# This file is part of SPECTRE
# SPDX-License-Identifier: GPL-3.0-or-later

from typing import Literal, overload, Type, TypeVar

from spectre_core.exceptions import BatchNotFoundError
from ._base import BaseBatch
from ._register import batch_map
from .plugins._batch_keys import BatchKey
from .plugins._callisto import CallistoBatch
from .plugins._iq_stream import IQStreamBatch


@overload
def get_batch_cls(
    batch_key: Literal[BatchKey.CALLISTO],
) -> Type[CallistoBatch]:
    ...


@overload
def get_batch_cls(
    batch_key: Literal[BatchKey.IQ_STREAM],
) -> Type[IQStreamBatch]:
    ...


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
        raise BatchNotFoundError(f"No batch found for the batch key: {batch_key}. "
                                 f"Valid batch keys are: {valid_batch_keys}")
    return batch_cls
