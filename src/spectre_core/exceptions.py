# SPDX-FileCopyrightText: © 2024-2025 Jimmy Fitzpatrick <jcfitzpatrick12@gmail.com>
# This file is part of SPECTRE
# SPDX-License-Identifier: GPL-3.0-or-later

"""
`spectre` custom exceptions.
"""

import warnings
from functools import wraps
from typing import TypeVar, Callable, Any, cast

F = TypeVar("F", bound=Callable[..., Any])


def deprecated(message: str) -> Callable[[F], F]:
    """A decorator to mark functions as deprecated.

    :param message: Warning message explaining what to use instead
    """

    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            warnings.warn(
                f"{func.__name__} is deprecated. {message}",
                category=DeprecationWarning,
                stacklevel=2,
            )
            return func(*args, **kwargs)

        return cast(F, wrapper)

    return decorator


class BatchNotFoundError(KeyError): ...


class ModeNotFoundError(KeyError): ...


class EventHandlerNotFoundError(KeyError): ...


class ReceiverNotFoundError(KeyError): ...


class InvalidTagError(ValueError): ...


class InvalidSweepMetadataError(ValueError): ...
