# SPDX-FileCopyrightText: © 2024 Jimmy Fitzpatrick <jcfitzpatrick12@gmail.com>
# This file is part of SPECTRE
# SPDX-License-Identifier: GPL-3.0-or-later

from typing import Optional, TypeVar, Any, Generic, Callable
from textwrap import dedent
from copy import deepcopy

from ._pnames import PNames
from ._pconstraints import PConstraint, PConstraints
from ._parameters import Parameter
    
VT = TypeVar('VT')

class PTemplate(Generic[VT]):
    """A parameter template. Constrains the value and type that a capture configuration parameter
    with a given name can take.
    """
    def __init__(self,
                 name: PNames,
                 ptype: Callable[[Any], VT],
                 default: Optional[VT] = None,
                 nullable: bool = False,
                 enforce_default: bool = False,
                 help: Optional[str] = None,
                 pconstraints: Optional[list[PConstraint]] = None):
        """Initialise an instance of `PTemplate`, and create a parameter template.

        Arguments:
            name -- The name of the parameter.
            ptype -- The required type of the parameter value.

        Keyword Arguments:
            default -- The parameter value if not explictly specified. (default: {None})
            nullable -- Whether the value of the parameter can be `None` (default: {False})
            enforce_default -- Whether we force that the value must be that specified by `default`. (default: {False})
            help -- A helpful description of what the parameter is, and the value it stores. (default: {None})
            pconstraints -- Custom constraints to be applied to the value of the parameter. (default: {None})
        """
        self._name = name
        self._ptype = ptype
        self._default = default
        self._nullable = nullable
        self._enforce_default = enforce_default
        self._help = dedent(help).strip().replace("\n", " ") if help else "No help has been provided."
        self._pconstraints: list[PConstraint] = pconstraints or []


    @property
    def name(self) -> PNames:
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
        """Update the `default` of this parameter template."""
        self._default = self._cast(value)


    @property
    def nullable(self) -> bool:
        """Whether the value of the parameter can be `None`."""
        return self._nullable
    

    @property
    def enforce_default(self) -> bool:
        """Whether we force that the value must be that specified by `default`."""
        return self._enforce_default
    

    @enforce_default.setter
    def enforce_default(self, value: bool) -> None:
        """Update whether we should `enforce_default` for this parameter template."""
        self._enforce_default = value
    

    @property
    def help(self) -> str:
        """A helpful description of what the parameter is, and the value it stores."""
        return self._help
    
    
    def add_pconstraint(self,
                        pconstraint: PConstraint) -> None:
        """Add a parameter constraint to this template.

        Arguments:
            pconstraint -- An instance of `PTemplate` compatable with the `ptype`.
        """
        self._pconstraints.append(pconstraint)


    def _cast(self, 
              value: Any) -> VT:
        """Cast the input value to the `ptype` for this parameter template.

        Arguments:
            value -- The value to be type casted.

        Raises:
            ValueError: If there is any trouble casting `value` as the `ptype` for this parameter template.

        Returns:
            The input value cast as `ptype` for this parameter template.
        """
        try:
            return self._ptype(value)
        except (TypeError, ValueError) as e:
            raise ValueError(f"Could not cast '{value}' to '{self._ptype.__name__}': {e}")


    def _constrain(self, 
                   value: VT) -> VT:
        """Constrain the input value according to constraints of the template.

        Arguments:
            value -- The value to be constrained.

        Raises:
            ValueError: If a custom `PConstraint` fails for the input value, and raises a `ValueError`.
            RuntimeError: If some other error occured at runtime while constraining the input value.

        Returns:
            The input value unchanged, if it passes validation according to parameter template constraints.
        """

        if self._enforce_default and value != self._default:
            raise ValueError(f"The default value of '{self._default}' "
                             f"is required for the parameter '{self._name}'.")

        # apply existing pconstraints
        for constraint in self._pconstraints:
            try:
                constraint.constrain(value)
            except ValueError as e:
                raise ValueError(f"PConstraint '{constraint.__class__.__name__}' failed for the parameter '{self._name}': {e}")
            except Exception as e:
                raise RuntimeError(f"An unexpected error occurred while applying the pconstraint '{constraint.__class__.__name__}' to "
                                    f"'{self.name}': {e}")
        return value


    def apply_template(self, 
                       value: Optional[Any]) -> Optional[VT]:
        """Cast a value and validate it according to this parameter template.

        Arguments:
            value -- The input value.

        Raises:
            ValueError: If value is `None`, no `default` is specified and the parameter is not allowed to be `None`.

        Returns:
            The input value type cast and validated according to the parameter template.
        """
        if value is None:
            if self._default is not None:
                value = self._default
            elif not self._nullable:
                raise ValueError(f"The parameter '{self._name}' is not nullable, "
                                 f"but no value or default has been provided. "
                                 f"Either provide a value, or provide a default.")
            else:
                return None
        
        return self._constrain( self._cast(value) )


    def make_parameter(self, 
                       value: Optional[Any] = None) -> Parameter:
        """
        Create a `Parameter` object based on this template and the provided value.
        
        If `value` is `None`, a default parameter will be c
        
        Args:
            value -- The provided value for the parameter.

        Returns:
            Parameter: A `Parameter` object, validated according to this template.
        """
        value = self.apply_template(value)
        return Parameter(self._name, value)


    def to_dict(self) -> dict[str, str]:
        """
        Convert this parameter template to a dictionary representation.

        Returns:
            A dictionary representation of this parameter template, 
            where all values are string-formatted for ease of serialisation.
        """
        d = {
            "name": self._name,
            "type": self._ptype,
            "default": self._default,
            "enforce_default": self._enforce_default,
            "help": self._help,
            "pconstraints": [f"{constraint}" for constraint in self._pconstraints]
        }
        return {k: f"{v}" for k,v in d.items()}
 

# ------------------------------------------------------------------------------------------ #
# `_base_ptemplates` holds all shared base parameter templates. They are 'base' templates, 
# in the sense that they should be configured according to specific use-cases. For example, 
# `default` values should be set, and `pconstraints` added according to specific SDR specs.
# ------------------------------------------------------------------------------------------ # 

_base_ptemplates: dict[PNames, PTemplate] = {
    PNames.CENTER_FREQUENCY:       PTemplate(PNames.CENTER_FREQUENCY,       
                                             float, 
                                             help = """
                                                    The center frequency of the SDR in Hz.
                                                    This value determines the midpoint of the frequency range
                                                    being processed.
                                                    """,
                                             pconstraints=[
                                                 PConstraints.enforce_positive
                                                 ]),
    PNames.MIN_FREQUENCY:          PTemplate(PNames.MIN_FREQUENCY,          
                                             float, 
                                             help = """
                                                    The minimum center frequency, in Hz, for the frequency sweep.
                                                    """,
                                             pconstraints=[
                                                 PConstraints.enforce_positive
                                                 ]),
    PNames.MAX_FREQUENCY:          PTemplate(PNames.MAX_FREQUENCY,          
                                             float, 
                                             help = """
                                                    The maximum center frequency, in Hz, for the frequency sweep.
                                                    """,
                                             pconstraints=[
                                                 PConstraints.enforce_positive
                                                 ]),
    PNames.FREQUENCY_STEP:         PTemplate(PNames.FREQUENCY_STEP,         
                                             float, 
                                             help = """
                                                    The amount, in Hz, by which the center frequency is incremented
                                                    for each step in the frequency sweep. 
                                                    """,
                                             pconstraints=[
                                                 PConstraints.enforce_positive
                                                 ]),
    PNames.BANDWIDTH:              PTemplate(PNames.BANDWIDTH,              
                                             float, 
                                             help = """
                                                    The frequency range in Hz the signal will occupy without
                                                    significant attenutation.
                                                    """,
                                             pconstraints=[
                                                 PConstraints.enforce_positive
                                                 ]),
    PNames.SAMPLE_RATE:            PTemplate(PNames.SAMPLE_RATE,            
                                             int,   
                                             help = """
                                                    The number of samples per second in Hz.
                                                    """,
                                             pconstraints=[
                                                 PConstraints.enforce_positive
                                                 ]),
    PNames.IF_GAIN:                PTemplate(PNames.IF_GAIN,                
                                             float, 
                                             help = """
                                                    The intermediate frequency gain, in dB.
                                                    Negative value indicates attenuation.
                                                    """,
                                             pconstraints=[
                                                 PConstraints.enforce_negative
                                                 ]),
    PNames.RF_GAIN:                PTemplate(PNames.RF_GAIN,                
                                             float, 
                                             help = """
                                                    The radio frequency gain, in dB.
                                                    Negative value indicates attenuation.
                                                    """,
                                             pconstraints=[
                                                 PConstraints.enforce_non_positive
                                                 ]),
    PNames.EVENT_HANDLER_KEY:      PTemplate(PNames.EVENT_HANDLER_KEY,      
                                             str,
                                             help = """
                                                    Identifies which post-processing functions to invoke
                                                    on newly created files.
                                                    """),
    PNames.BATCH_KEY:              PTemplate(PNames.BATCH_KEY,              
                                             str,
                                             help = """
                                                    Identifies the type of data is stored in each batch.
                                                    """,
                                             ),
    PNames.WINDOW_SIZE:            PTemplate(PNames.WINDOW_SIZE,            
                                             int,  
                                             help = """
                                                    The size of the window, in samples, when performing the
                                                    Short Time FFT.
                                                    """,
                                             pconstraints=[
                                                 PConstraints.enforce_positive, 
                                                 PConstraints.power_of_two
                                                 ]),
    PNames.WINDOW_HOP:             PTemplate(PNames.WINDOW_HOP,             
                                             int,   
                                             help = """
                                                    How much the window is shifted, in samples, 
                                                    when performing the Short Time FFT.
                                                    """,
                                             pconstraints=[
                                                 PConstraints.enforce_positive
                                                 ]),
    PNames.WINDOW_TYPE:            PTemplate(PNames.WINDOW_TYPE,            
                                             str,
                                             help = """
                                                    The type of window applied when performing the Short
                                                    Time FFT.
                                                    """,
                                             ),
    PNames.WATCH_EXTENSION:        PTemplate(PNames.WATCH_EXTENSION,        
                                             str,
                                             help = """
                                                    Post-processing is triggered by newly created files with this extension.
                                                    Extensions are specified without the '.' character.
                                                    """,
                                             ),
    PNames.TIME_RESOLUTION:        PTemplate(PNames.TIME_RESOLUTION,        
                                             float, 
                                             nullable=True,
                                             help = """
                                                    Batched spectrograms are smoothed by averaging up to the time resolution,
                                                    specified in seconds.
                                                    """,
                                             pconstraints=[
                                                 PConstraints.enforce_non_negative
                                                 ]),
    PNames.FREQUENCY_RESOLUTION:   PTemplate(PNames.FREQUENCY_RESOLUTION,   
                                             float, 
                                             nullable=True,
                                             help = """
                                                    Batched spectrograms are smoothed by averaging up to the frequency resolution,
                                                    specified in Hz.
                                                    """,
                                             pconstraints=[
                                                 PConstraints.enforce_non_negative
                                                 ]),
    PNames.TIME_RANGE:             PTemplate(PNames.TIME_RANGE,             
                                             float, 
                                             nullable=True,
                                             help = """
                                                    Batched spectrograms are stitched together until
                                                    the time range, in seconds, is surpassed.
                                                    """,
                                             pconstraints=[
                                                 PConstraints.enforce_non_negative
                                                 ]),
    PNames.BATCH_SIZE:             PTemplate(PNames.BATCH_SIZE,             
                                             int,   
                                             help = """
                                                    SDR data is collected in batches of this size, specified
                                                    in seconds.
                                                    """,
                                             pconstraints=[
                                                 PConstraints.enforce_positive
                                                 ]),
    PNames.SAMPLES_PER_STEP:       PTemplate(PNames.SAMPLES_PER_STEP,       
                                             int,   
                                             help = """
                                                    The number of samples taken at each center frequency in the sweep.
                                                    This may vary slightly from what is specified due to the nature of
                                                    GNU Radio runtime.
                                                    """,
                                             pconstraints=[
                                                 PConstraints.enforce_positive
                                                 ]),
    PNames.ORIGIN:                 PTemplate(PNames.ORIGIN,
                                             str,
                                             nullable=True,
                                             help="""
                                                  Corresponds to the FITS keyword ORIGIN.
                                                  """),
    PNames.TELESCOPE:              PTemplate(PNames.TELESCOPE,
                                             str,
                                             nullable=True,
                                             help="""
                                                  Corresponds to the FITS keyword TELESCOP.
                                                  """),
    PNames.INSTRUMENT:             PTemplate(PNames.INSTRUMENT,
                                             str,
                                             nullable=True,
                                             help="""
                                                  Corresponds to the FITS keyword INSTRUME.
                                                  """),
    PNames.OBJECT:                 PTemplate(PNames.OBJECT,
                                             str,
                                             nullable=True,
                                             help="""
                                                  Corresponds to the FITS keyword OBJECT.
                                                  """),
    PNames.OBS_LAT:                PTemplate(PNames.OBS_LAT,
                                             float,
                                             nullable=True,
                                             help="""
                                                  Corresponds to the FITS keyword OBS_LAT.
                                                  """),
    PNames.OBS_LON:                PTemplate(PNames.OBS_LON,
                                             float,
                                             nullable=True,
                                             help="""
                                                  Corresponds to the FITS keyword OBS_LONG.
                                                  """),
    PNames.OBS_ALT:                PTemplate(PNames.OBS_ALT,
                                             float,
                                             nullable=True,
                                             help="""
                                                  Corresponds to the FITS keyword OBS_ALT.
                                                  """),
    PNames.AMPLITUDE:              PTemplate(PNames.AMPLITUDE,
                                             float,
                                             help="""
                                                  The amplitude of the signal.
                                                  """),
    PNames.FREQUENCY:              PTemplate(PNames.FREQUENCY,
                                             float,
                                             help="""
                                                  The frequency of the signal, in Hz.
                                                  """),
    PNames.MIN_SAMPLES_PER_STEP:   PTemplate(PNames.MIN_SAMPLES_PER_STEP,
                                             int,
                                             help="""
                                                  The number of samples in the shortest step of the staircase.
                                                  """,
                                             pconstraints=[
                                                 PConstraints.enforce_positive
                                                 ]),
    PNames.MAX_SAMPLES_PER_STEP:   PTemplate(PNames.MAX_SAMPLES_PER_STEP,
                                             int,
                                             help="""
                                                  The number of samples in the longest step of the staircase.
                                                  """,
                                            pconstraints=[
                                                  PConstraints.enforce_positive
                                                  ]),
    PNames.STEP_INCREMENT:         PTemplate(PNames.STEP_INCREMENT,
                                             int,
                                             help="""
                                                  The length by which each step in the staircase is incremented.
                                                  """,
                                             pconstraints=[
                                                  PConstraints.enforce_positive,
                                              ])
                                    
                                           
}


def get_base_ptemplate(
    pname: PNames,
) -> PTemplate:
    """Get a pre-defined base parameter template, to be configured according to the specific use case.

    Arguments:
        parameter_name -- The parameter name for the template.

    Raises:
        KeyError: If there is no base parameter template corresponding to the input name.

    Returns:
        A deep copy of the corresponding base parameter template, if it exists.
    """
    if pname not in _base_ptemplates:
        raise KeyError(f"No ptemplate found for the parameter name '{pname}'. "
                       f"Expected one of {list(_base_ptemplates.keys())}")
    # A deep copy is required as each receiver instance may mutate the original instance
    # according to its particular use case. Copying preserves the original instance,
    # enabling reuse.
    return deepcopy( _base_ptemplates[pname] )