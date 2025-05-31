# SPDX-FileCopyrightText: © 2024-2025 Jimmy Fitzpatrick <jcfitzpatrick12@gmail.com>
# This file is part of SPECTRE
# SPDX-License-Identifier: GPL-3.0-or-later

from typing import Type, Callable, TypeVar

from ._base import BaseBatch
from .plugins._batch_keys import BatchKey

# Map populated at runtime via the `register_batch` decorator.
batch_map: dict[BatchKey, Type[BaseBatch]] = {}

T = TypeVar("T", bound=BaseBatch)


def register_batch(batch_key: BatchKey) -> Callable[[Type[T]], Type[T]]:
    """Decorator to register a `BaseBatch` subclass under a specified `BatchKey`.

    :param batch_key: The key to register the `BaseBatch` subclass under.
    :raises ValueError: If the provided `batch_key` is already registered.
    :return: A decorator that registers the `BaseBatch` subclass under the given `batch_key`.
    """

    def decorator(cls: Type[T]) -> Type[T]:
        if batch_key in batch_map:
            raise ValueError(f"A batch with key '{batch_key}' is already registered!")
        batch_map[batch_key] = cls
        return cls

    return decorator
