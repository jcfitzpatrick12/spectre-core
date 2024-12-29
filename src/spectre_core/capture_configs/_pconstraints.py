# SPDX-FileCopyrightText: © 2024 Jimmy Fitzpatrick <jcfitzpatrick12@gmail.com>
# This file is part of SPECTRE
# SPDX-License-Identifier: GPL-3.0-or-later

from dataclasses import dataclass
from abc import ABC, abstractmethod
from typing import TypeVar, Optional, Any
from numbers import Number

T = TypeVar('T')

class PConstraint(ABC):
    """Abstract base class for parameter constraints."""

    @abstractmethod
    def constrain(self, value: T) -> None:
        """Apply a constraint to the input parameter."""
        pass

    def __format__(self, format_spec: str = "") -> str:
        attrs = ", ".join(f"{key}={value!r}" for key, value in vars(self).items())
        return f"{self.__class__.__name__}({attrs})"

class Bound(PConstraint):
    """Constrain a parameter value to a specific range."""

    def __init__(self,
                 lower_bound: Optional[Number] = None,
                 upper_bound: Optional[Number] = None,
                 strict_lower: bool = False,
                 strict_upper: bool = False):
        self._lower_bound = lower_bound
        self._upper_bound = upper_bound
        self._strict_lower = strict_lower
        self._strict_upper = strict_upper

    def constrain(self, value: Number) -> None:
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


class OneOf(PConstraint):
    """Constrain a parameter to one of a set of defined options."""

    def __init__(self, options: list[Any] = None):
        self._options = options


    def constrain(self, value: Any) -> None:
        if value not in self._options:
            raise ValueError(f"Value must be one of {self._options}. Got {value}.")
        

class _PowerOfTwo(PConstraint):
    """Constrain a parameter value to be a power of two."""

    def constrain(self, value: Number) -> None:
        if value <= 0 or (value & (value - 1)) != 0:
            raise ValueError(f"Value must be a power of two. Got {value}.")


@dataclass(frozen=True)
class PConstraints:
    """Ready-made pconstraint instances for frequent use-cases."""
    power_of_two           = _PowerOfTwo()
    enforce_positive       = Bound(lower_bound=0, strict_lower=True)
    enforce_negative       = Bound(upper_bound=0, strict_upper=True)
    enforce_non_negative   = Bound(lower_bound=0, strict_lower=False)
    enforce_non_positive   = Bound(upper_bound=0, strict_upper=False)
