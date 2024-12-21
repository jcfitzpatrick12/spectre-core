# SPDX-FileCopyrightText: © 2024 Jimmy Fitzpatrick <jcfitzpatrick12@gmail.com>
# This file is part of SPECTRE
# SPDX-License-Identifier: GPL-3.0-or-later

from copy import deepcopy
from typing import TypeVar 
from dataclasses import dataclass

from spectre_core.parameters import PTemplate
from spectre_core import pconstraints
from spectre_core.capture_config import CaptureTemplate


# ------------------------------------------ # 
# A store for shared parameters and templates
# ------------------------------------------ # 

#
# Shared parameter names
#
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
    COSINE_AMPLITUDE        : str = "cosine_amplitude"
    COSINE_FREQUENCY        : str = "cosine_frequency"
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
# A protected map to default PTemplate instances
#

_base_ptemplates = {
    PNames.CENTER_FREQUENCY:       PTemplate(PNames.CENTER_FREQUENCY,       
                                             float, 
                                             default=None,
                                             help = """
                                                    The center frequency of the SDR in Hz. 
                                                    This value determines the midpoint of the frequency range 
                                                    being processed.
                                                    """,
                                             pconstraints=[
                                                 pconstraints.enforce_positive
                                                 ]),
    PNames.MIN_FREQUENCY:          PTemplate(PNames.MIN_FREQUENCY,          
                                             float, 
                                             default=None,
                                             help = """
                                                    The minimum center frequency, in Hz, for the frequency sweep. 
                                                    """,
                                             pconstraints=[
                                                 pconstraints.enforce_positive
                                                 ]),
    PNames.MAX_FREQUENCY:          PTemplate(PNames.MAX_FREQUENCY,          
                                             float, 
                                             default=None,
                                             help = """
                                                    The maximum center frequency, in Hz, for the frequency sweep. 
                                                    """,
                                             pconstraints=[
                                                 pconstraints.enforce_positive
                                                 ]),
    PNames.FREQUENCY_STEP:         PTemplate(PNames.FREQUENCY_STEP,         
                                             float, 
                                             default=None,
                                             help = """
                                                    The amount, in Hz, by which the center frequency is incremented
                                                    for each step in the frequency sweep. 
                                                    """,
                                             pconstraints=[
                                                 pconstraints.enforce_positive
                                                 ]),
    PNames.BANDWIDTH:              PTemplate(PNames.BANDWIDTH,              
                                             float, 
                                             default=None,
                                             help = """
                                                    The frequency range in Hz the signal will occupy without
                                                    significant attenutation.
                                                    """,
                                             pconstraints=[
                                                 pconstraints.enforce_positive
                                                 ]),
    PNames.SAMPLE_RATE:            PTemplate(PNames.SAMPLE_RATE,            
                                             int,   
                                             default=None,
                                             help = """
                                                    The number of samples per second in Hz.
                                                    """,
                                             pconstraints=[
                                                 pconstraints.enforce_positive
                                                 ]),
    PNames.IF_GAIN:                PTemplate(PNames.IF_GAIN,                
                                             float, 
                                             default=None,
                                             help = """
                                                    The intermediate frequency gain, in dB. 
                                                    Negative value indicates attenuation.
                                                    """,
                                             pconstraints=[
                                                 pconstraints.enforce_negative
                                                 ]),
    PNames.RF_GAIN:                PTemplate(PNames.RF_GAIN,                
                                             float, 
                                             default=None,
                                             help = """
                                                    The radio frequency gain, in dB. 
                                                    Negative value indicates attenuation.
                                                    """,
                                             pconstraints=[
                                                 pconstraints.enforce_non_positive
                                                 ]),
    PNames.EVENT_HANDLER_KEY:      PTemplate(PNames.EVENT_HANDLER_KEY,      
                                             str,
                                             default=None,
                                             help = """
                                                    Identifies which post-processing functions to invoke
                                                    on newly created files.
                                                    """),
    PNames.CHUNK_KEY:              PTemplate(PNames.CHUNK_KEY,              
                                             str,
                                             default=None,
                                             help = """
                                                    Identifies the type of data is stored in each chunk.
                                                    """,
                                             ),
    PNames.WINDOW_SIZE:            PTemplate(PNames.WINDOW_SIZE,            
                                             int,  
                                             default=None,
                                             help = """
                                                    The size of the window, in samples, when performing the 
                                                    Short Time FFT.
                                                    """,
                                             pconstraints=[
                                                 pconstraints.enforce_positive, 
                                                 pconstraints.enforce_power_of_two
                                                 ]),
    PNames.WINDOW_HOP:             PTemplate(PNames.WINDOW_HOP,             
                                             int,   
                                             default=None,
                                             help = """
                                                    How much the window is shifted, in samples, 
                                                    when performing the Short Time FFT.
                                                    """,
                                             pconstraints=[
                                                 pconstraints.enforce_positive
                                                 ]),
    PNames.WINDOW_TYPE:            PTemplate(PNames.WINDOW_TYPE,            
                                             str,
                                             default=None,
                                             help = """
                                                    The type of window applied when performing the Short 
                                                    Time FFT.
                                                    """,
                                             ),
    PNames.WATCH_EXTENSION:        PTemplate(PNames.WATCH_EXTENSION,        
                                             str,
                                             default=None,
                                             help = """
                                                    Post-processing is triggered by newly created files with this extension.
                                                    Extensions are specified without the '.' character.
                                                    """,
                                             ),
    PNames.TIME_RESOLUTION:        PTemplate(PNames.TIME_RESOLUTION,        
                                             float, 
                                             default=None,
                                             help = """
                                                    Batched spectrograms are smoothed by averaging up to the time resolution, 
                                                    specified in seconds.
                                                    """,
                                             pconstraints=[
                                                 pconstraints.enforce_non_negative
                                                 ]),
    PNames.FREQUENCY_RESOLUTION:   PTemplate(PNames.FREQUENCY_RESOLUTION,   
                                             float, 
                                             default=None,
                                             help = """
                                                    Batched spectrograms are smoothed by averaging up to the frequency resolution, 
                                                    specified in Hz.
                                                    """,
                                             pconstraints=[
                                                 pconstraints.enforce_non_negative
                                                 ]),
    PNames.TIME_RANGE:             PTemplate(PNames.TIME_RANGE,             
                                             float, 
                                             default=None,
                                             help = """
                                                    Batched spectrograms are stitched together until 
                                                    the time range, in seconds, is surpassed.
                                                    """,
                                             pconstraints=[
                                                 pconstraints.enforce_non_negative
                                                 ]),
    PNames.BATCH_SIZE:             PTemplate(PNames.BATCH_SIZE,             
                                             int,   
                                             default=None,
                                             help = """
                                                    SDR data is collected in batches of this size, specified 
                                                    in seconds.
                                                    """,
                                             pconstraints=[
                                                 pconstraints.enforce_positive
                                                 ]),
    PNames.SAMPLES_PER_STEP:       PTemplate(PNames.SAMPLES_PER_STEP,       
                                             int,   
                                             default=None,
                                             help = """
                                                    The number of samples taken at each center frequency in the sweep. 
                                                    This may vary slightly from what is specified due to the nature of 
                                                    GNU Radio runtime.
                                                    """,
                                             pconstraints=[
                                                 pconstraints.enforce_positive
                                                 ]),
    PNames.ORIGIN:                 PTemplate(PNames.ORIGIN,
                                             str,
                                             default=None,
                                             help="""
                                                  Corresponds to the FITS keyword ORIGIN.
                                                  """),
    PNames.TELESCOPE:              PTemplate(PNames.TELESCOPE,
                                             str,
                                             default=None,
                                             help="""
                                                  Corresponds to the FITS keyword TELESCOP.
                                                  """),
    PNames.INSTRUMENT:             PTemplate(PNames.INSTRUMENT,
                                             str,
                                             default=None,
                                             help="""
                                                  Corresponds to the FITS keyword INSTRUME.
                                                  """),
    PNames.OBJECT:                 PTemplate(PNames.OBJECT,
                                             str,
                                             default=None,
                                             help="""
                                                  Corresponds to the FITS keyword OBJECT.
                                                  """),
    PNames.OBS_LAT:                PTemplate(PNames.OBS_LAT,
                                             float,
                                             default=None,
                                             help="""
                                                  Corresponds to the FITS keyword OBS_LAT.
                                                  """),
    PNames.OBS_LON:                PTemplate(PNames.OBS_LON,
                                             float,
                                             default=None,
                                             help="""
                                                  Corresponds to the FITS keyword OBS_LONG.
                                                  """),
    PNames.OBS_ALT:                PTemplate(PNames.OBS_ALT,
                                             float,
                                             default=None,
                                             help="""
                                                  Corresponds to the FITS keyword OBS_ALT.
                                                  """),
    PNames.COSINE_AMPLITUDE:        PTemplate(PNames.COSINE_AMPLITUDE,
                                              float,
                                              default=None,
                                              help="""
                                                   The amplitude of the cosine signal source.
                                                   """),
    PNames.COSINE_FREQUENCY:        PTemplate(PNames.COSINE_FREQUENCY,
                                              float,
                                              default=None,
                                              help="""
                                                   The frequency, in Hz, of the cosine signal source.
                                                   """),
    PNames.MIN_SAMPLES_PER_STEP:    PTemplate(PNames.MIN_SAMPLES_PER_STEP,
                                              int,
                                              default=None,
                                              help="""
                                                   The number of samples in the shortest step of the staircase.
                                                   """,
                                              pconstraints=[
                                                  pconstraints.enforce_positive
                                                  ]),
    PNames.MAX_SAMPLES_PER_STEP:    PTemplate(PNames.MAX_SAMPLES_PER_STEP,
                                              int,
                                              default=None,
                                              help="""
                                                   The number of samples in the longest step of the staircase.
                                                   """,
                                              pconstraints=[
                                                  pconstraints.enforce_positive
                                                  ]),
    PNames.STEP_INCREMENT:          PTemplate(PNames.STEP_INCREMENT,
                                              int,
                                              default=None,
                                              help="""
                                                   The length by which each step in the staircase is incremented.
                                                   """,
                                              pconstraints=[
                                                  pconstraints.enforce_positive,
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

    # Retrieve the shared PTemplate instance
    ptemplate = _base_ptemplates[parameter_name]
    
    return deepcopy(ptemplate)


def make_base_capture_template(*parameter_names: str):
    """Make a basic capture template, composed of pre-defined ptemplates in the parameter store."""
    capture_template = CaptureTemplate()
    for name in parameter_names:
        capture_template.add_ptemplate( get_base_ptemplate(name) )
    return capture_template


@dataclass(frozen=True)
class CaptureTypes:
    """Pre-defined capture modes"""
    FIXED_CENTER_FREQUENCY: str = "fixed-center-frequency"
    SWEPT_CENTER_FREQUENCY: str = "swept-center-frequency"


def make_fixed_frequency_capture_template(
) -> CaptureTemplate:
    """Base capture template for fixed center frequency capture"""
    return make_base_capture_template(
        PNames.BATCH_SIZE,
        PNames.CENTER_FREQUENCY,
        PNames.CHUNK_KEY,
        PNames.EVENT_HANDLER_KEY,
        PNames.FREQUENCY_RESOLUTION,
        PNames.INSTRUMENT,
        PNames.OBS_ALT,
        PNames.OBS_LAT,
        PNames.OBS_LON,
        PNames.OBJECT,
        PNames.ORIGIN,
        PNames.SAMPLE_RATE,
        PNames.TELESCOPE,
        PNames.TIME_RANGE,
        PNames.TIME_RESOLUTION,
        PNames.WATCH_EXTENSION,
        PNames.WINDOW_HOP,
        PNames.WINDOW_SIZE,
        PNames.WINDOW_TYPE,
    )


def make_swept_frequency_capture_template(
) -> CaptureTemplate:
    """Base capture template for swept center frequency capture"""
    return make_base_capture_template(
        PNames.BATCH_SIZE,
        PNames.CHUNK_KEY,
        PNames.EVENT_HANDLER_KEY,
        PNames.FREQUENCY_RESOLUTION,
        PNames.FREQUENCY_STEP,
        PNames.INSTRUMENT,
        PNames.MAX_FREQUENCY,
        PNames.MIN_FREQUENCY,
        PNames.OBS_ALT,
        PNames.OBS_LAT,
        PNames.OBS_LON,
        PNames.OBJECT,
        PNames.ORIGIN,
        PNames.SAMPLE_RATE,
        PNames.SAMPLES_PER_STEP,
        PNames.TELESCOPE,
        PNames.TIME_RANGE,
        PNames.TIME_RESOLUTION,
        PNames.WATCH_EXTENSION,
        PNames.WINDOW_HOP,
        PNames.WINDOW_SIZE,
        PNames.WINDOW_TYPE)

_base_capture_templates = {
    CaptureTypes.FIXED_CENTER_FREQUENCY: make_fixed_frequency_capture_template(),
    CaptureTypes.SWEPT_CENTER_FREQUENCY: make_swept_frequency_capture_template()
}

def get_base_capture_template(
       capture_mode: str
) -> CaptureTemplate:
    """Get a pre-defined base capture template. """
    if capture_mode not in _base_capture_templates:
        raise KeyError(f"No capture template found for the capture mode '{capture_mode}'. "
                       f"Expected one of {list(_base_capture_templates.keys())}")

    capture_template = _base_capture_templates[capture_mode]
    return deepcopy(capture_template)