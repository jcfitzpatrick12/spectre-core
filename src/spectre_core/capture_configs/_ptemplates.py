# SPDX-FileCopyrightText: © 2024 Jimmy Fitzpatrick <jcfitzpatrick12@gmail.com>
# This file is part of SPECTRE
# SPDX-License-Identifier: GPL-3.0-or-later

from typing import Optional, TypeVar, Any
from copy import deepcopy
from textwrap import dedent
from dataclasses import dataclass

from ._pconstraints import PConstraint, PConstraints
from ._parameters import Parameter

T = TypeVar('T')

class PTemplate:
    """A parameter template. 
    
    Constrain the value and type that a parameter can take.
    """
    def __init__(self,
                 name: str,
                 ptype: T,
                 default: Optional[T] = None,
                 nullable: bool = False,
                 enforce_default: Optional[bool] = False,
                 help: Optional[str] = None,
                 pconstraints: Optional[list[PConstraint]] = None):
        if not callable(ptype):
            raise TypeError("ptype must be callable.")

        self._name = name
        self._ptype = ptype
        self._default = default
        self._nullable = nullable
        self._enforce_default = enforce_default
        self._help = dedent(help).strip().replace("\n", " ") if help else "No help has been provided."
        self._pconstraints: list[PConstraint] = pconstraints or []


    @property
    def name(self) -> str:
        """The name of the parameter."""
        return self._name
    

    @property
    def ptype(self) -> T:
        """The parameter type."""
        return self._ptype
    

    @property
    def default(self) -> Optional[T]:
        """The value of the parameter, if the value is unspecified."""
        return self._default
    

    @default.setter
    def default(self, value: T) -> None:
        """Update the default of a ptemplate"""
        self._default = value


    @property
    def nullable(self) -> bool:
        """Whether the value of the parameter is allowed to be of None type."""
        return self._nullable
    

    @property
    def enforce_default(self) -> bool:
        """Whether the provided default value is enforced."""
        return self._enforce_default
    

    @enforce_default.setter
    def enforce_default(self, value: bool) -> None:
        """Set whether the provided default value is enforced."""
        self._enforce_default = value
    

    @property
    def help(self) -> str:
        """A description of what the parameter is, and the value it stores."""
        return self._help
    
    
    def add_pconstraint(self,
                        pconstraint: PConstraint) -> None:
        self._pconstraints.append(pconstraint)


    def _cast(self, 
              value: Any) -> T:
        """Cast the input value to the ptype of this template"""
        try:
            return self._ptype(value)
        except (TypeError, ValueError) as e:
            raise ValueError(f"Could not cast '{value}' to '{self._ptype.__name__}': {e}")


    def _constrain(self, 
                   value: T) -> T:
        """Constrain the input value according to constraints of the template."""

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
                       value: Optional[Any]) -> T:
        """Cast the value and constrain it according to this ptemplate."""
        if value is None:
            if self._default is not None:
                value = self._default
            elif not self._nullable:
                raise ValueError(f"The parameter '{self._name}' is not nullable, "
                                 f"but no value or default has been provided. "
                                 f"Either provide a value, or provide a default.")
            else:
                return None
        
        value = self._cast(value)
        value = self._constrain(value)
        return value


    def make_parameter(self, 
                       value: Optional[Any] = None) -> Parameter:
        value = self.apply_template(value)
        return Parameter(self._name, value)


    def to_dict(self) -> dict:
        """Convert the template to a dictionary representation."""
        return {
            "name": self._name,
            "type": str(self._ptype),
            "default": self._default,
            "enforce_default": self._enforce_default,
            "help": self._help,
            "constraints": [f"{constraint}" for constraint in self._pconstraints]
        }
    

@dataclass(frozen=True)
class PNames:
    """A centralised store of default parameter template names"""
    CENTER_FREQUENCY        : str = "center_frequency"
    MIN_FREQUENCY           : str = "min_frequency"
    MAX_FREQUENCY           : str = "max_frequency"
    FREQUENCY_STEP          : str = "frequency_step"
    FREQUENCY               : str = "frequency"
    BANDWIDTH               : str = "bandwidth"
    SAMPLE_RATE             : str = "sample_rate"
    IF_GAIN                 : str = "if_gain"
    RF_GAIN                 : str = "rf_gain"
    AMPLITUDE               : str = "amplitude"
    FREQUENCY               : str = "frequency"
    TIME_RESOLUTION         : str = "time_resolution"
    FREQUENCY_RESOLUTION    : str = "frequency_resolution"
    TIME_RANGE              : str = "time_range"
    BATCH_SIZE              : str = "batch_size"
    WINDOW_TYPE             : str = "window_type"
    WINDOW_HOP              : str = "window_hop"
    WINDOW_SIZE             : str = "window_size"
    EVENT_HANDLER_KEY       : str = "event_handler_key"
    WATCH_EXTENSION         : str = "watch_extension"
    CHUNK_KEY               : str = "chunk_key"
    SAMPLES_PER_STEP        : str = "samples_per_step"
    MIN_SAMPLES_PER_STEP    : str = "min_samples_per_step"
    MAX_SAMPLES_PER_STEP    : str = "max_samples_per_step"
    STEP_INCREMENT          : str = "step_increment"
    ORIGIN                  : str = "origin"
    TELESCOPE               : str = "telescope"
    INSTRUMENT              : str = "instrument"
    OBJECT                  : str = "object"
    OBS_LAT                 : str = "obs_lat"
    OBS_LON                 : str = "obs_lon"
    OBS_ALT                 : str = "obs_alt"

#
# All stored base ptemplates
#
_base_ptemplates = {
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
    PNames.CHUNK_KEY:              PTemplate(PNames.CHUNK_KEY,              
                                             str,
                                             help = """
                                                    Identifies the type of data is stored in each chunk.
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

T = TypeVar('T')
def get_base_ptemplate(
    parameter_name: str,
) -> PTemplate:
    """Create a fresh deep copy of a pre-defined ptemplate"""
    if parameter_name not in _base_ptemplates:
        raise KeyError(f"No ptemplate found for the parameter name '{parameter_name}'. "
                       f"Expected one of {list(_base_ptemplates.keys())}")
    return deepcopy( _base_ptemplates[parameter_name] )