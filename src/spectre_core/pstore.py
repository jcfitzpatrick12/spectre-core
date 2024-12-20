# SPDX-FileCopyrightText: © 2024 Jimmy Fitzpatrick <jcfitzpatrick12@gmail.com>
# This file is part of SPECTRE
# SPDX-License-Identifier: GPL-3.0-or-later

from typing import Optional, Any, TypeVar 
from dataclasses import dataclass

from spectre_core.parameters import PTemplate, PConstraint
from spectre_core import pconstraints


# ------------------------- # 
# Parameter store
# ------------------------- # 


#
#  Frequently used specification names.
#
@dataclass(frozen=True)
class SpecNames:
    """A centralised store of spec names"""
    FREQUENCY_LOWER_BOUND    = "frequency_lower_bound"
    FREQUENCY_UPPER_BOUND    = "frequency_upper_bound"
    SAMPLE_RATE_LOWER_BOUND  = "sample_rate_lower_bound"
    SAMPLE_RATE_UPPER_BOUND  = "sample_rate_upper_bound"
    BANDWIDTH_LOWER_BOUND    = "bandwidth_lower_bound"
    BANDWIDTH_UPPER_BOUND    = "bandwidth_upper_bound"
    DEFINED_BANDWIDTHS       = "defined_bandwidths"
    IF_GAIN_UPPER_BOUND      = "if_gain_upper_bound"
    RF_GAIN_UPPER_BOUND      = "rf_gain_upper_bound"
    API_LATENCY              = "api_latency"


#
#  Frequently used parameter names.
#
@dataclass(frozen=True)
class PNames:
    """A centralised store of frequently used parameter template names"""
    CENTER_FREQUENCY         = "center_frequency"
    MIN_FREQUENCY            = "min_frequency"
    MAX_FREQUENCY            = "max_frequency"
    FREQUENCY_STEP           = "frequency_step"
    FREQUENCY                = "frequency"
    BANDWIDTH                = "bandwidth"
    SAMPLE_RATE              = "sample_rate"
    IF_GAIN                  = "if_gain"
    RF_GAIN                  = "rf_gain"
    AMPLITUDE                = "amplitude"
    TIME_RESOLUTION          = "time_resolution"
    FREQUENCY_RESOLUTION     = "frequency_resolution"
    TIME_RANGE               = "time_range"
    BATCH_SIZE               = "batch_size"
    WINDOW_TYPE              = "window_type"
    WINDOW_HOP               = "window_hop"
    WINDOW_SIZE              = "window_size"
    EVENT_HANDLER_KEY        = "event_handler_key"
    WATCH_EXTENSION          = "watch_extension"
    CHUNK_KEY                = "chunk_key"
    SAMPLES_PER_STEP         = "samples_per_step"
    MIN_SAMPLES_PER_STEP     = "min_samples_per_step"
    MAX_SAMPLES_PER_STEP     = "max_samples_per_step"
    FREQUENCY_STEP           = "frequency_step"
    STEP_INCREMENT           = "step_increment"
    ORIGIN                   = "origin"
    TELESCOPE                = "telescope"
    INSTRUMENT               = "instrument"
    OBJECT                   = "object"
    OBSERVATION_LATITUDE     = "observation_latitude"
    OBSERVATION_LONGITUDE    = "observation_longitude"
    OBSERVATION_ALTITUDE     = "observation_altitude"


#
# Frequently used ptemplates
#
_ptemplates = {
    PNames.CENTER_FREQUENCY:       PTemplate(PNames.CENTER_FREQUENCY,       
                                             float, 
                                             help = """
                                                    The center frequency of the SDR in Hz. 
                                                    This value determines the midpoint of the frequency range 
                                                    being processed.
                                                    """,
                                             pconstraints=[pconstraints.enforce_positive]),
    PNames.MIN_FREQUENCY:          PTemplate(PNames.MIN_FREQUENCY,          
                                             float, 
                                             help = """
                                                    The minimum center frequency, in Hz, for the frequency sweep. 
                                                    """,
                                             pconstraints=[pconstraints.enforce_positive]),
    PNames.MAX_FREQUENCY:          PTemplate(PNames.MAX_FREQUENCY,          
                                             float, 
                                             help = """
                                                    The maximum center frequency, in Hz, for the frequency sweep. 
                                                    """,
                                             pconstraints=[pconstraints.enforce_positive]),
    PNames.FREQUENCY_STEP:         PTemplate(PNames.FREQUENCY_STEP,         
                                             float, 
                                             help = """
                                                    The amount, in Hz, by which the center frequency is incremented
                                                    for each step in the frequency sweep. 
                                                    """,
                                             pconstraints=[pconstraints.enforce_positive]),
    PNames.BANDWIDTH:              PTemplate(PNames.BANDWIDTH,              
                                             float, 
                                             help = """
                                                    The frequency range in Hz the signal will occupy without
                                                    significant attenutation.
                                                    """,
                                             pconstraints=[pconstraints.enforce_positive]),
    PNames.SAMPLE_RATE:            PTemplate(PNames.SAMPLE_RATE,            
                                             int,   
                                             help = """
                                                    The number of samples per second in Hz.
                                                    """,
                                             pconstraints=[pconstraints.enforce_positive]),
    PNames.IF_GAIN:                PTemplate(PNames.IF_GAIN,                
                                             float, 
                                             help = """
                                                    The intermediate frequency gain, in dB. 
                                                    Negative value indicates attenuation.
                                                    """,
                                             pconstraints=[pconstraints.enforce_negative]),
    PNames.RF_GAIN:                PTemplate(PNames.RF_GAIN,                
                                             float, 
                                             help = """
                                                    The radio frequency gain, in dB. 
                                                    Negative value indicates attenuation.
                                                    """,
                                             pconstraints=[pconstraints.enforce_non_positive]),
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
                                             pconstraints=[pconstraints.enforce_positive, pconstraints.enforce_power_of_two]),
    PNames.WINDOW_HOP:             PTemplate(PNames.WINDOW_HOP,             
                                             int,   
                                             help = """
                                                    How much the window is shifted, in samples, 
                                                    when performing the Short Time FFT.
                                                    """,
                                             pconstraints=[pconstraints.enforce_positive]),
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
                                                    Post-processing is triggered by files created with this extension.
                                                    Extensions are specified without the '.' character.
                                                    """,
                                             ),
    PNames.TIME_RESOLUTION:        PTemplate(PNames.TIME_RESOLUTION,        
                                             float, 
                                             help = """
                                                    Batched spectrograms are smoothed by averaging up to the time resolution, 
                                                    specified in seconds.
                                                    """,
                                             pconstraints=[pconstraints.enforce_non_negative]),
    PNames.FREQUENCY_RESOLUTION:   PTemplate(PNames.FREQUENCY_RESOLUTION,   
                                             float, 
                                             help = """
                                                    Batched spectrograms are smoothed by averaging up to the frequency resolution, 
                                                    specified in Hz.
                                                    """,
                                             pconstraints=[pconstraints.enforce_non_negative]),
    PNames.TIME_RANGE:             PTemplate(PNames.TIME_RANGE,             
                                             float, 
                                             help = """
                                                    Batched spectrograms are stitched together until 
                                                    the time range, in seconds, is surpassed.
                                                    """,
                                             pconstraints=[pconstraints.enforce_non_negative]),
    PNames.BATCH_SIZE:             PTemplate(PNames.BATCH_SIZE,             
                                             int,   
                                             help = """
                                                    SDR data is collected in batches of this size, specified 
                                                    in seconds.
                                                    """,
                                             pconstraints=[pconstraints.enforce_positive]),
    PNames.SAMPLES_PER_STEP:       PTemplate(PNames.SAMPLES_PER_STEP,       
                                             int,   
                                             help = """
                                                    The amount of samples taken at each center frequency in the sweep. 
                                                    This may vary slightly from what is specified due to the nature of 
                                                    GNU Radio runtime.
                                                    """,
                                             pconstraints=[pconstraints.enforce_positive]),
    PNames.ORIGIN:                 PTemplate(PNames.ORIGIN,
                                             str,
                                             default="NOTSET",
                                             help="""
                                                  Corresponds to the FITS keyword ORIGIN.
                                                  """),
    PNames.TELESCOPE:              PTemplate(PNames.TELESCOPE,
                                             str,
                                             default="NOTSET",
                                             help="""
                                                  Corresponds to the FITS keyword TELESCOP.
                                                  """),
    PNames.INSTRUMENT:             PTemplate(PNames.INSTRUMENT,
                                             str,
                                             default="NOTSET",
                                             help="""
                                                  Corresponds to the FITS keyword INSTRUME.
                                                  """),
    PNames.OBJECT:                 PTemplate(PNames.OBJECT,
                                             str,
                                             default="NOTSET",
                                             help="""
                                                  Corresponds to the FITS keyword OBJECT.
                                                  """),
    PNames.OBSERVATION_LATITUDE:   PTemplate(PNames.OBSERVATION_LATITUDE,
                                             float,
                                             default=0.0,
                                             help="""
                                                  Corresponds to the FITS keyword OBS_LAT.
                                                  """),
    PNames.OBSERVATION_LONGITUDE:  PTemplate(PNames.OBSERVATION_LONGITUDE,
                                             float,
                                             default=0.0,
                                             help="""
                                                  Corresponds to the FITS keyword OBS_LONG.
                                                  """),
    PNames.OBSERVATION_ALTITUDE:   PTemplate(PNames.OBSERVATION_ALTITUDE,
                                             float,
                                             default=0.0,
                                             help="""
                                                  Corresponds to the FITS keyword OBS_ALT.
                                                  """)
                                           
}

#
# Public getter for frequently used ptemplates.
#

T = TypeVar('T')
def get_ptemplate(name: str, 
                  default: Optional[T],
                  enforce_default: bool = False,
                  pconstraints: Optional[list[PConstraint]] = None
) -> PTemplate:
    """Create a fresh copy of one of the default PTemplates
    
    Notably, pconstraints are stacked with those which already exist.
    """
    if name not in _ptemplates:
        raise KeyError(f"No default PTemplate found for parameter name '{name}'.")

    # Retrieve the shared PTemplate instance
    ptemplate = _ptemplates[name]
    
    # Clone it with the updated default and enforce_default values
    return ptemplate.clone(default=default,
                           enforce_default=enforce_default,
                           pconstraints=pconstraints)

