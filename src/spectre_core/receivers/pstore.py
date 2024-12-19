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
    FREQ_STEP                = "freq_step"
    STEP_INCREMENT           = "step_increment"



#
# Frequently used ptemplates
#
_ptemplates = {
    PNames.CENTER_FREQUENCY:       PTemplate(PNames.CENTER_FREQUENCY,       
                                             float, 
                                             help = """
                                                    
                                                    """,
                                             add_pconstraints=[pconstraints.enforce_positive]),
    PNames.MIN_FREQUENCY:          PTemplate(PNames.MIN_FREQUENCY,          
                                             float, 
                                             help = """

                                                    """,
                                             add_pconstraints=[pconstraints.enforce_positive]),
    PNames.MAX_FREQUENCY:          PTemplate(PNames.MAX_FREQUENCY,          
                                             float, 
                                             help = """

                                                    """,
                                             add_pconstraints=[pconstraints.enforce_positive]),
    PNames.FREQUENCY_STEP:         PTemplate(PNames.FREQUENCY_STEP,         
                                             float, 
                                             help = """

                                                    """,
                                             add_pconstraints=[pconstraints.enforce_positive]),
    PNames.BANDWIDTH:              PTemplate(PNames.BANDWIDTH,              
                                             float, 
                                             help = """

                                                    """,
                                             add_pconstraints=[pconstraints.enforce_positive]),
    PNames.SAMPLE_RATE:            PTemplate(PNames.SAMPLE_RATE,            
                                             int,   
                                             help = """

                                                    """,
                                             add_pconstraints=[pconstraints.enforce_positive]),
    PNames.IF_GAIN:                PTemplate(PNames.IF_GAIN,                
                                             float, 
                                             help = """

                                                    """,
                                             add_pconstraints=[pconstraints.enforce_negative]),
    PNames.RF_GAIN:                PTemplate(PNames.RF_GAIN,                
                                             float, 
                                             help = """

                                                    """,
                                             add_pconstraints=[pconstraints.enforce_non_positive]),
    PNames.EVENT_HANDLER_KEY:      PTemplate(PNames.EVENT_HANDLER_KEY,      
                                             str,
                                             help = """

                                                    """),
    PNames.CHUNK_KEY:              PTemplate(PNames.CHUNK_KEY,              
                                             str,
                                             help = """

                                                    """,
                                             ),
    PNames.WINDOW_SIZE:            PTemplate(PNames.WINDOW_SIZE,            
                                             int,   
                                             help = """

                                                    """,
                                             add_pconstraints=[pconstraints.enforce_positive, pconstraints.enforce_power_of_two]),
    PNames.WINDOW_HOP:             PTemplate(PNames.WINDOW_HOP,             
                                             int,   
                                             help = """

                                                    """,
                                             add_pconstraints=[pconstraints.enforce_positive]),
    PNames.WINDOW_TYPE:            PTemplate(PNames.WINDOW_TYPE,            
                                             str,
                                             help = """

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

                                                    """,
                                             add_pconstraints=[pconstraints.enforce_non_negative]),
    PNames.FREQUENCY_RESOLUTION:   PTemplate(PNames.FREQUENCY_RESOLUTION,   
                                             float, 
                                             help = """

                                                    """,
                                             add_pconstraints=[pconstraints.enforce_non_negative]),
    PNames.TIME_RANGE:             PTemplate(PNames.TIME_RANGE,             
                                             float, 
                                             help = """

                                                    """,
                                             add_pconstraints=[pconstraints.enforce_non_negative]),
    PNames.BATCH_SIZE:             PTemplate(PNames.BATCH_SIZE,             
                                             int,   
                                             help = """

                                                    """,
                                             add_pconstraints=[pconstraints.enforce_positive]),
    PNames.SAMPLES_PER_STEP:       PTemplate(PNames.SAMPLES_PER_STEP,       
                                             int,   
                                             help = """

                                                    """,
                                             add_pconstraints=[pconstraints.enforce_positive]),
}

#
# Public getter for frequently used ptemplates.
#

T = TypeVar('T')
def get_ptemplate(name: str, 
                  default: Optional[T],
                  enforce_default: bool = False,
                  add_pconstraints: Optional[list[PConstraint]] = None
) -> PTemplate:
    """Create a fresh copy of one of the default PTemplates"""
    if name not in _ptemplates:
        raise KeyError(f"No default PTemplate found for parameter name '{name}'.")

    # Retrieve the shared PTemplate instance
    ptemplate = _ptemplates[name]
    
    # Clone it with the updated default and enforce_default values
    return ptemplate.clone(default=default,
                           enforce_default=enforce_default,
                           add_pconstraints=add_pconstraints)

