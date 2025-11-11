# SPDX-FileCopyrightText: © 2024-2025 Jimmy Fitzpatrick <jcfitzpatrick12@gmail.com>
# This file is part of SPECTRE
# SPDX-License-Identifier: GPL-3.0-or-later


import typing

import pydantic


class Field:
    """Shared `pydantic` fields for all models."""

    max_noutput_items = typing.Annotated[
        int,
        pydantic.Field(
            ...,
            gt=1000,
            description="The maximum number of samples handled at each call of the work function in GNU Radio.",
        ),
    ]
    sample_rate = typing.Annotated[
        int,
        pydantic.Field(
            ..., gt=0, description="The number of samples taken per second, in Hz."
        ),
    ]
    batch_size = typing.Annotated[
        float,
        pydantic.Field(
            ...,
            ge=1,
            description="Samples are recorded in batches of this size, specified in seconds.",
        ),
    ]
    frequency = typing.Annotated[
        float, pydantic.Field(..., gt=0, description="Frequency of the signal, in Hz.")
    ]
    amplitude = typing.Annotated[
        int,
        pydantic.Field(..., description="Amplitude of the signal, arbitrary units."),
    ]
    window_size = typing.Annotated[
        int,
        pydantic.Field(
            ...,
            gt=2,
            description="The size of the window, in samples, when performing the Short Time FFT.",
        ),
    ]
    window_hop = typing.Annotated[
        int,
        pydantic.Field(
            ...,
            gt=0,
            description="How much the window is shifted, in samples, when performing the Short Time FFT.",
        ),
    ]
    window_type = typing.Annotated[
        typing.Literal["blackman", "hann", "boxcar"],
        pydantic.Field(
            ...,
            description="The type of window applied when performing the Short Time FFT.",
        ),
    ]
    center_frequency = typing.Annotated[
        float,
        pydantic.Field(
            ...,
            gt=0.0,
            description="The center frequency, in Hz. This value determines the midpoint of the frequency range being processed.",
        ),
    ]
    frequency_resolution = typing.Annotated[
        float,
        pydantic.Field(
            ...,
            ge=0,
            description="Spectrograms are averaged up to the frequency resolution, in Hz. 0 for no averaging.",
        ),
    ]
    time_resolution = typing.Annotated[
        float,
        pydantic.Field(
            ...,
            ge=0,
            description="Spectrograms are averaged up to the time resolution, in seconds. 0 for no averaging.",
        ),
    ]
    time_range = typing.Annotated[
        float,
        pydantic.Field(
            ...,
            ge=0,
            description="Spectrograms are stitched together until the time range has elapsed. 0 for no stitching.",
        ),
    ]
    origin = typing.Annotated[
        str, pydantic.Field(..., description="Corresponds to the FITS keyword ORIGIN.")
    ]
    telescope = typing.Annotated[
        str,
        pydantic.Field(..., description="Corresponds to the FITS keyword TELESCOP."),
    ]
    instrument = typing.Annotated[
        str,
        pydantic.Field(..., description="Corresponds to the FITS keyword INSTRUMEN."),
    ]
    # Add an underscore to not conflict with the globally-scoped `object`.
    object_ = typing.Annotated[
        str, pydantic.Field(..., description="Corresponds to the FITS keyword OBJECT.")
    ]
    obs_lat = typing.Annotated[
        float,
        pydantic.Field(..., description="Corresponds to the FITS keyword OBS_LAT."),
    ]
    obs_alt = typing.Annotated[
        float,
        pydantic.Field(..., description="Corresponds to the FITS keyword OBS_ALT."),
    ]
    obs_lon = typing.Annotated[
        float,
        pydantic.Field(..., description="Corresponds to the FITS keyword OBS_LON."),
    ]
    keep_signal = typing.Annotated[
        bool,
        pydantic.Field(
            ...,
            description="If True, keep the signal after creating the spectrogram. Otherwise, it is deleted from the file system.",
        ),
    ]
    frequency_step = typing.Annotated[
        float,
        pydantic.Field(
            ...,
            gt=0,
            description="The amount, in Hz, by which the center frequency is incremented for each step in the frequency sweep.",
        ),
    ]
    step_increment = typing.Annotated[
        int,
        pydantic.Field(
            ...,
            gt=0,
            description="The length by which each step in the staircase is incremented.",
        ),
    ]
    min_samples_per_step = typing.Annotated[
        int,
        pydantic.Field(
            ...,
            gt=0,
            description="The minimum number of samples in the shortest step of the staircase.",
        ),
    ]
    max_samples_per_step = typing.Annotated[
        int,
        pydantic.Field(
            ...,
            gt=0,
            description="The maximum number of samples in the shortest step of the staircase.",
        ),
    ]
