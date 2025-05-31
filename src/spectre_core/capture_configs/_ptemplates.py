# SPDX-FileCopyrightText: © 2024-2025 Jimmy Fitzpatrick <jcfitzpatrick12@gmail.com>
# This file is part of SPECTRE
# SPDX-License-Identifier: GPL-3.0-or-later

from typing import Optional, TypeVar, Any, Generic, Callable
from textwrap import dedent
from copy import deepcopy

from ._pnames import PName
from ._pconstraints import BasePConstraint, EnforceSign, PowerOfTwo, Bound
from ._parameters import Parameter

# value type
VT = TypeVar("VT")


class PTemplate(Generic[VT]):
    """A template which constrains the value and type of a capture config parameter."""

    def __init__(
        self,
        name: PName,
        ptype: Callable[[Any], VT],
        default: Optional[VT] = None,
        nullable: bool = False,
        enforce_default: bool = False,
        help: Optional[str] = None,
        pconstraints: Optional[list[BasePConstraint]] = None,
    ) -> None:
        """Initialise an instance of `PTemplate`.

        :param name: The name of the parameter.
        :param ptype: The required type of the parameter value.
        :param default: The parameter value if not explicitly specified. Defaults to None.
        :param nullable: Whether the value of the parameter can be `None`. Defaults to False.
        :param enforce_default: Indicates whether the value must match the specified `default`. Defaults to False.
        :param help: A helpful description of what the parameter is and the value it stores. Defaults to None.
        :param pconstraints: Custom constraints to be applied to the value of the parameter. Defaults to None.
        """
        self._name = name
        self._ptype = ptype
        self._default = default
        self._nullable = nullable
        self._enforce_default = enforce_default
        self._help = (
            dedent(help).strip().replace("\n", " ")
            if help
            else "No help has been provided."
        )
        self._pconstraints: list[BasePConstraint] = pconstraints or []

    @property
    def name(self) -> PName:
        """The name of the parameter."""
        return self._name

    @property
    def ptype(self) -> Callable[[object], VT]:
        """The required type of the parameter. The value must be castable as this type."""
        return self._ptype

    @property
    def default(self) -> Optional[VT]:
        """The parameter value if not explictly specified."""
        return self._default

    @default.setter
    def default(self, value: VT) -> None:
        """Update the `default` of this parameter template.

        :param value: The new default value to set.
        """
        self._default = self._cast(value)

    @property
    def nullable(self) -> bool:
        """Whether the value of the parameter can be `None`."""
        return self._nullable

    @property
    def enforce_default(self) -> bool:
        """Indicates whether the value must match the specified `default`."""
        return self._enforce_default

    @enforce_default.setter
    def enforce_default(self, value: bool) -> None:
        """Update whether to `enforce_default` for this parameter template.

        :param value: Whether to enforce the default value.
        """
        self._enforce_default = value

    @property
    def help(self) -> str:
        """A helpful description of what the parameter is, and the value it stores."""
        return self._help

    def add_pconstraint(self, pconstraint: BasePConstraint) -> None:
        """Add a parameter constraint to this template.

        :param pconstraint: A `PConstraint` instance compatible with the `ptype`.
        """
        self._pconstraints.append(pconstraint)

    def _cast(self, value: Any) -> VT:
        """Cast the input value to the `ptype` for this parameter template.

        :param value: The value to be type casted.
        :raises ValueError: If there is any trouble casting `value` as the `ptype` for this parameter template.
        :return: The input value cast as `ptype` for this parameter template.
        """
        try:
            return self._ptype(value)
        except (TypeError, ValueError) as e:
            raise ValueError(
                f"Could not cast '{value}' to '{self._ptype.__name__}': {e}"
            )

    def _constrain(self, value: VT) -> VT:
        """Constrain the input value according to constraints of the template.

        :param value: The value to be constrained.
        :raises ValueError: If a custom `PConstraint` fails for the input value.
        :raises RuntimeError: If an unexpected error occurs during constraint validation.
        :return: The input value unchanged if it passes validation.
        """
        if self._enforce_default and value != self._default:
            raise ValueError(
                f"The default value of '{self._default}' "
                f"is required for the parameter '{self._name}'."
            )

        # apply existing pconstraints
        for constraint in self._pconstraints:
            try:
                constraint.constrain(value)
            except ValueError as e:
                raise ValueError(
                    f"PConstraint '{constraint.__class__.__name__}' failed for the parameter '{self._name}': {e}"
                )
            except Exception as e:
                raise RuntimeError(
                    f"An unexpected error occurred while applying the pconstraint '{constraint.__class__.__name__}' to "
                    f"'{self.name}': {e}"
                )
        return value

    def apply_template(self, value: Optional[Any]) -> Optional[VT]:
        """Cast a value and validate it according to this parameter template.

        :param value: The input value.
        :raises ValueError: If the value is `None`, no `default` is specified, and the parameter is not nullable.
        :return: The input value type cast and validated according to the parameter template.
        """
        if value is None:
            if self._default is not None:
                value = self._default
            elif not self._nullable:
                raise ValueError(
                    f"The parameter '{self._name}' is not nullable, "
                    f"but no value or default has been provided. "
                    f"Either provide a value, or provide a default."
                )
            else:
                return None

        return self._constrain(self._cast(value))

    def make_parameter(self, value: Optional[Any] = None) -> Parameter:
        """Create a `Parameter` compliant with this template.

        :param value: The provided value for the parameter. Defaults to None.
        :return: A `Parameter` object validated according to this template.
        """
        value = self.apply_template(value)
        return Parameter(self._name, value)

    def to_dict(self) -> dict[str, str]:
        """Convert this parameter template to a serialisable dictionary.

        :return: A dictionary representation of this parameter template with string formatted values.
        """
        d = {
            "name": self._name.value,
            "type": self._ptype.__name__,
            "default": self._default,
            "enforce_default": self._enforce_default,
            "help": self._help,
            "pconstraints": [f"{constraint}" for constraint in self._pconstraints],
        }
        return {k: f"{v}" for k, v in d.items()}


# ------------------------------------------------------------------------------------------ #
# `_base_ptemplates` holds all shared base parameter templates. They are 'base' templates,
# in the sense that they should be configured according to specific use-cases. For example,
# `default` values should be set, and `pconstraints` added according to specific SDR specs.
# ------------------------------------------------------------------------------------------ #

_base_ptemplates: dict[PName, PTemplate] = {
    PName.CENTER_FREQUENCY: PTemplate(
        PName.CENTER_FREQUENCY,
        float,
        help="The center frequency of the SDR in Hz. This value determines the midpoint of the frequency range being processed.",
        pconstraints=[EnforceSign.positive],
    ),
    PName.MIN_FREQUENCY: PTemplate(
        PName.MIN_FREQUENCY,
        float,
        help="The minimum center frequency, in Hz, for the frequency sweep.",
        pconstraints=[EnforceSign.positive],
    ),
    PName.MAX_FREQUENCY: PTemplate(
        PName.MAX_FREQUENCY,
        float,
        help="The maximum center frequency, in Hz, for the frequency sweep.",
        pconstraints=[EnforceSign.positive],
    ),
    PName.FREQUENCY_STEP: PTemplate(
        PName.FREQUENCY_STEP,
        float,
        help="The amount, in Hz, by which the center frequency is incremented for each step in the frequency sweep.",
        pconstraints=[EnforceSign.positive],
    ),
    PName.BANDWIDTH: PTemplate(
        PName.BANDWIDTH,
        float,
        help="The frequency range in Hz the signal will occupy without significant attenutation.",
        pconstraints=[EnforceSign.positive],
    ),
    PName.SAMPLE_RATE: PTemplate(
        PName.SAMPLE_RATE,
        int,
        help="The number of samples per second in Hz.",
        pconstraints=[EnforceSign.positive],
    ),
    PName.IF_GAIN: PTemplate(
        PName.IF_GAIN,
        float,
        help="The intermediate frequency gain, in dB. Negative value indicates attenuation.",
        pconstraints=[EnforceSign.negative],
    ),
    PName.RF_GAIN: PTemplate(
        PName.RF_GAIN,
        float,
        help="The radio frequency gain, in dB. Negative value indicates attenuation.",
        pconstraints=[EnforceSign.non_positive],
    ),
    PName.GAIN: PTemplate(
        PName.GAIN,
        float,
        help="The gain value for the SDR, in dB",
    ),
    PName.MASTER_CLOCK_RATE: PTemplate(
        PName.MASTER_CLOCK_RATE,
        int,
        help="The primary reference clock for the SDR, specified in Hz.",
    ),
    PName.WIRE_FORMAT: PTemplate(
        PName.WIRE_FORMAT,
        str,
        help="Controls the form of the data over the bus/network.",
    ),
    PName.EVENT_HANDLER_KEY: PTemplate(
        PName.EVENT_HANDLER_KEY,
        str,
        help="Identifies which post-processing functions to invokeon newly created files.",
    ),
    PName.BATCH_KEY: PTemplate(
        PName.BATCH_KEY,
        str,
        help="Identifies the type of data is stored in each batch.",
    ),
    PName.WINDOW_SIZE: PTemplate(
        PName.WINDOW_SIZE,
        int,
        help="The size of the window, in samples, when performing the Short Time FFT.",
        pconstraints=[
            EnforceSign.positive,
            PowerOfTwo(),
        ],
    ),
    PName.WINDOW_HOP: PTemplate(
        PName.WINDOW_HOP,
        int,
        help="How much the window is shifted, in samples, when performing the Short Time FFT.",
        pconstraints=[EnforceSign.positive],
    ),
    PName.WINDOW_TYPE: PTemplate(
        PName.WINDOW_TYPE,
        str,
        help="The type of window applied when performing the Short Time FFT.",
    ),
    PName.WATCH_EXTENSION: PTemplate(
        PName.WATCH_EXTENSION,
        str,
        help="Post-processing is triggered by newly created files with this extension. Extensions are specified without the '.' character.",
    ),
    PName.TIME_RESOLUTION: PTemplate(
        PName.TIME_RESOLUTION,
        float,
        nullable=True,
        help="Batched spectrograms are smoothed by averaging up to the time resolution, specified in seconds.",
        pconstraints=[EnforceSign.non_negative],
    ),
    PName.FREQUENCY_RESOLUTION: PTemplate(
        PName.FREQUENCY_RESOLUTION,
        float,
        nullable=True,
        help="Batched spectrograms are smoothed by averaging up to the frequency resolution, specified in Hz.",
        pconstraints=[EnforceSign.non_negative],
    ),
    PName.TIME_RANGE: PTemplate(
        PName.TIME_RANGE,
        float,
        nullable=True,
        help="Batched spectrograms are stitched together until the time range, in seconds, is surpassed.",
        pconstraints=[EnforceSign.non_negative],
    ),
    PName.BATCH_SIZE: PTemplate(
        PName.BATCH_SIZE,
        int,
        help="SDR data is collected in batches of this size, specified in seconds.",
        pconstraints=[EnforceSign.positive],
    ),
    PName.SAMPLES_PER_STEP: PTemplate(
        PName.SAMPLES_PER_STEP,
        int,
        help="The number of samples taken at each center frequency in the sweep. This may vary slightly from what is specified due to the nature of GNU Radio runtime.",
        pconstraints=[EnforceSign.positive],
    ),
    PName.ORIGIN: PTemplate(
        PName.ORIGIN,
        str,
        nullable=True,
        help="Corresponds to the FITS keyword ORIGIN.",
    ),
    PName.TELESCOPE: PTemplate(
        PName.TELESCOPE,
        str,
        nullable=True,
        help="Corresponds to the FITS keyword TELESCOP.",
    ),
    PName.INSTRUMENT: PTemplate(
        PName.INSTRUMENT,
        str,
        nullable=True,
        help="Corresponds to the FITS keyword INSTRUME.",
    ),
    PName.OBJECT: PTemplate(
        PName.OBJECT,
        str,
        nullable=True,
        help="Corresponds to the FITS keyword OBJECT.",
    ),
    PName.OBS_LAT: PTemplate(
        PName.OBS_LAT,
        float,
        nullable=True,
        help="Corresponds to the FITS keyword OBS_LAT.",
    ),
    PName.OBS_LON: PTemplate(
        PName.OBS_LON,
        float,
        nullable=True,
        help="Corresponds to the FITS keyword OBS_LONG.",
    ),
    PName.OBS_ALT: PTemplate(
        PName.OBS_ALT,
        float,
        nullable=True,
        help="Corresponds to the FITS keyword OBS_ALT.",
    ),
    PName.AMPLITUDE: PTemplate(
        PName.AMPLITUDE,
        float,
        help="The amplitude of the signal.",
    ),
    PName.FREQUENCY: PTemplate(
        PName.FREQUENCY,
        float,
        help="The frequency of the signal, in Hz.",
    ),
    PName.MIN_SAMPLES_PER_STEP: PTemplate(
        PName.MIN_SAMPLES_PER_STEP,
        int,
        help="The number of samples in the shortest step of the staircase.",
        pconstraints=[EnforceSign.positive],
    ),
    PName.MAX_SAMPLES_PER_STEP: PTemplate(
        PName.MAX_SAMPLES_PER_STEP,
        int,
        help="The number of samples in the longest step of the staircase.",
        pconstraints=[EnforceSign.positive],
    ),
    PName.STEP_INCREMENT: PTemplate(
        PName.STEP_INCREMENT,
        int,
        help="The length by which each step in the staircase is incremented.",
        pconstraints=[
            EnforceSign.positive,
        ],
    ),
}


def get_base_ptemplate(
    pname: PName,
) -> PTemplate:
    """Get a pre-defined base parameter template, to be configured according to the specific use case.

    :param pname: The parameter name for the template.
    :raises KeyError: If there is no base parameter template corresponding to the input name.
    :return: A deep copy of the corresponding base parameter template, if it exists.
    """
    if pname not in _base_ptemplates:
        raise KeyError(
            f"No ptemplate found for the parameter name '{pname}'. "
            f"Expected one of {list(_base_ptemplates.keys())}"
        )
    # A deep copy is required as each receiver instance may mutate the original instance
    # according to its particular use case. Copying preserves the original instance,
    # enabling reuse.
    return deepcopy(_base_ptemplates[pname])
