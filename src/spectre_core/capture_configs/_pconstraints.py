# SPDX-FileCopyrightText: © 2024 Jimmy Fitzpatrick <jcfitzpatrick12@gmail.com>
# This file is part of SPECTRE
# SPDX-License-Identifier: GPL-3.0-or-later

from dataclasses import dataclass
from abc import ABC, abstractmethod
from typing import TypeVar, Optional, Any, Generic

VT = TypeVar('VT')

class BasePConstraint(ABC, Generic[VT]):
    """An abstract base class for an arbitary parameter constraint.
    
    Derived classes must:
    - Implement the `constraint` method, which defines how the value of a parameter 
    is to be constrainted.
    """
    @abstractmethod
    def constrain(self, value: VT) -> None:
        """Apply a constraint to the input parameter. Implementations must raise a `ValueError` for
        if the input value fails the constraint.

        :param value: The value to be constrained.
        """
        

    def __format__(self, format_spec: str = "") -> str:
        attrs = ", ".join(f"{key}={value!r}" for key, value in vars(self).items())
        return f"{self.__class__.__name__}({attrs})"


class Bound(BasePConstraint[float | int]):
    """Bound a numeric parameter value to a some specified interval."""
    def __init__(self,
                 lower_bound: Optional[float | int] = None,
                 upper_bound: Optional[float | int] = None,
                 strict_lower: bool = False,
                 strict_upper: bool = False):
        """Create an instance of `Bound`.

        :param lower_bound: The value must be greater than `lower_bound`. Inclusive if `strict_lower` is False. Defaults to None.
        :param upper_bound: The value must be less than `upper_bound`. Inclusive if `strict_upper` is False. Defaults to None.
        :param strict_lower: If true, the value must be strictly greater than `lower_bound`. Defaults to False.
        :param strict_upper: If true, the value must be strictly less than `upper_bound`. Defaults to False.
        """
        self._lower_bound = lower_bound
        self._upper_bound = upper_bound
        self._strict_lower = strict_lower
        self._strict_upper = strict_upper

    def constrain(self, value: float | int) -> None:
        """Bound the parameter value to a specified interval.

        :param value: The value to be constrained.
        :raises ValueError: If the value is outside the specified interval.
        """
        if self._lower_bound is not None:
            if self._strict_lower and value <= self._lower_bound:
                raise ValueError(f"Value must be strictly greater than {self._lower_bound}. "
                                 f"Got {value}.")
            if not self._strict_lower and value < self._lower_bound:
                raise ValueError(f"Value must be greater than or equal to {self._lower_bound}. "
                                 f"Got {value}.")

        if self._upper_bound is not None:
            if self._strict_upper and value >= self._upper_bound:
                raise ValueError(f"Value must be strictly less than {self._upper_bound}. "
                                 f"Got {value}.")
            if not self._strict_upper and value > self._upper_bound:
                raise ValueError(f"Value must be less than or equal to {self._upper_bound}. "
                                 f"Got {value}.")


class OneOf(BasePConstraint[Any]):
    """Constrain a parameter value to be one of a pre-defined list of options."""

    def __init__(self, options: Optional[list[Any]] = None) -> None:
        """Initialise an instance of `OneOf`.

        :param options: Input values are required to be one of `options`. If no options are provided,
        it is assumed to be an empty list. Defaults to None.
        """
        self._options = options or []


    def constrain(self, value: Any) -> None:
        """Constrain the input value to be one of a list of pre-defined options.

        :param value: The value to be constrained.
        :raises ValueError: If the input value is not one of the pre-defined options.
        """
        if value not in self._options:
            raise ValueError(f"Value must be one of {self._options}. Got {value}.")
        

class _PowerOfTwo(BasePConstraint[int]):
    """Constrain a numeric parameter value to be a power of two."""
    def constrain(self, value: int) -> None:
        """Constrain the input value to be a power of two.

        :param value: The input value to be constrained.
        :raises ValueError: If the input value is not exactly some power of two.
        """
        if value <= 0 or (value & (value - 1)) != 0:
            raise ValueError(f"Value must be a power of two. Got {value}.")


@dataclass(frozen=True)
class PConstraint:
    """Ready-made `PConstraint` subclass instances for frequent use-cases."""
    power_of_two           = _PowerOfTwo()
    enforce_positive       = Bound(lower_bound=0, strict_lower=True)
    enforce_negative       = Bound(upper_bound=0, strict_upper=True)
    enforce_non_negative   = Bound(lower_bound=0, strict_lower=False)
    enforce_non_positive   = Bound(upper_bound=0, strict_upper=False)
