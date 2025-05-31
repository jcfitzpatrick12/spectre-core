# SPDX-FileCopyrightText: © 2024-2025 Jimmy Fitzpatrick <jcfitzpatrick12@gmail.com>
# This file is part of SPECTRE
# SPDX-License-Identifier: GPL-3.0-or-later

from dataclasses import dataclass
from typing import Callable, cast

from spectre_core.capture_configs import (
    CaptureTemplate,
    CaptureMode,
    Parameters,
    Bound,
    PName,
    get_base_capture_template,
    make_base_capture_template,
    get_base_ptemplate,
    validate_window,
)
from .gr._test import CaptureMethod
from ._receiver_names import ReceiverName
from .._spec_names import SpecName
from .._base import BaseReceiver
from .._register import register_receiver


@dataclass(frozen=True)
class Mode:
    """An operating mode for the `Test` receiver."""

    COSINE_SIGNAL_1 = "cosine_signal_1"
    TAGGED_STAIRCASE = "tagged_staircase"


@register_receiver(ReceiverName.TEST)
class Test(BaseReceiver):
    """An entirely software-defined receiver, which generates synthetic signals."""

    def _add_specs(self) -> None:
        self.add_spec(SpecName.SAMPLE_RATE_LOWER_BOUND, 64000)
        self.add_spec(SpecName.SAMPLE_RATE_UPPER_BOUND, 640000)
        self.add_spec(SpecName.FREQUENCY_LOWER_BOUND, 16000)
        self.add_spec(SpecName.FREQUENCY_UPPER_BOUND, 160000)

    def _add_capture_methods(self) -> None:
        self.add_capture_method(Mode.COSINE_SIGNAL_1, CaptureMethod.cosine_signal_1)
        self.add_capture_method(Mode.TAGGED_STAIRCASE, CaptureMethod.tagged_staircase)

    def _add_pvalidators(self) -> None:
        self.add_pvalidator(
            Mode.COSINE_SIGNAL_1, self.__get_pvalidator_cosine_signal_1()
        )
        self.add_pvalidator(
            Mode.TAGGED_STAIRCASE, self.__get_pvalidator_tagged_staircase()
        )

    def _add_capture_templates(self) -> None:
        self.add_capture_template(
            Mode.COSINE_SIGNAL_1, self.__get_capture_template_cosine_signal_1()
        )
        self.add_capture_template(
            Mode.TAGGED_STAIRCASE, self.__get_capture_template_tagged_staircase()
        )

    def __get_capture_template_cosine_signal_1(self) -> CaptureTemplate:
        capture_template = get_base_capture_template(CaptureMode.FIXED_CENTER_FREQUENCY)
        capture_template.add_ptemplate(get_base_ptemplate(PName.AMPLITUDE))
        capture_template.add_ptemplate(get_base_ptemplate(PName.FREQUENCY))

        capture_template.set_defaults(
            (PName.BATCH_SIZE, 3.0),
            (PName.CENTER_FREQUENCY, 16000),
            (PName.AMPLITUDE, 2.0),
            (PName.FREQUENCY, 32000),
            (PName.SAMPLE_RATE, 128000),
            (PName.WINDOW_HOP, 512),
            (PName.WINDOW_SIZE, 512),
            (PName.WINDOW_TYPE, "boxcar"),
        )

        capture_template.enforce_defaults(
            PName.TIME_RESOLUTION,
            PName.TIME_RANGE,
            PName.FREQUENCY_RESOLUTION,
            PName.WINDOW_TYPE,
        )

        capture_template.add_pconstraint(
            PName.SAMPLE_RATE,
            [
                Bound(
                    lower_bound=self.get_spec(SpecName.SAMPLE_RATE_LOWER_BOUND),
                    upper_bound=self.get_spec(SpecName.SAMPLE_RATE_UPPER_BOUND),
                )
            ],
        )
        capture_template.add_pconstraint(
            PName.FREQUENCY,
            [
                Bound(
                    lower_bound=self.get_spec(SpecName.FREQUENCY_LOWER_BOUND),
                    upper_bound=self.get_spec(SpecName.FREQUENCY_UPPER_BOUND),
                )
            ],
        )
        return capture_template

    def __get_capture_template_tagged_staircase(self) -> CaptureTemplate:
        capture_template = make_base_capture_template(
            PName.TIME_RESOLUTION,
            PName.FREQUENCY_RESOLUTION,
            PName.TIME_RANGE,
            PName.SAMPLE_RATE,
            PName.BATCH_SIZE,
            PName.WINDOW_TYPE,
            PName.WINDOW_HOP,
            PName.WINDOW_SIZE,
            PName.EVENT_HANDLER_KEY,
            PName.BATCH_KEY,
            PName.WATCH_EXTENSION,
            PName.MIN_SAMPLES_PER_STEP,
            PName.MAX_SAMPLES_PER_STEP,
            PName.FREQUENCY_STEP,
            PName.STEP_INCREMENT,
            PName.OBS_ALT,
            PName.OBS_LAT,
            PName.OBS_LON,
            PName.OBJECT,
            PName.ORIGIN,
            PName.TELESCOPE,
            PName.INSTRUMENT,
        )

        capture_template.set_defaults(
            (PName.BATCH_SIZE, 3.0),
            (PName.FREQUENCY_STEP, 128000),
            (PName.MAX_SAMPLES_PER_STEP, 5000),
            (PName.MIN_SAMPLES_PER_STEP, 4000),
            (PName.SAMPLE_RATE, 128000),
            (PName.STEP_INCREMENT, 200),
            (PName.WINDOW_HOP, 512),
            (PName.WINDOW_SIZE, 512),
            (PName.WINDOW_TYPE, "boxcar"),
            (PName.EVENT_HANDLER_KEY, "swept_center_frequency"),
            (PName.BATCH_KEY, "iq_stream"),
            (PName.WATCH_EXTENSION, "bin"),
        )

        capture_template.enforce_defaults(
            PName.TIME_RESOLUTION,
            PName.TIME_RANGE,
            PName.FREQUENCY_RESOLUTION,
            PName.WINDOW_TYPE,
            PName.EVENT_HANDLER_KEY,
            PName.BATCH_KEY,
            PName.WATCH_EXTENSION,
        )

        return capture_template

    def __get_pvalidator_cosine_signal_1(self) -> Callable[[Parameters], None]:
        def pvalidator(parameters: Parameters) -> None:
            validate_window(parameters)

            sample_rate = cast(int, parameters.get_parameter_value(PName.SAMPLE_RATE))
            window_size = cast(int, parameters.get_parameter_value(PName.WINDOW_SIZE))
            frequency = cast(float, parameters.get_parameter_value(PName.FREQUENCY))

            # check that the sample rate is an integer multiple of the underlying signal frequency
            if sample_rate % frequency != 0:
                raise ValueError(
                    "The sampling rate must be some integer multiple of frequency"
                )

            a = sample_rate / frequency
            if a < 2:
                raise ValueError(
                    (
                        f"The ratio of sampling rate over frequency must be greater than two. "
                        f"Got {a}"
                    )
                )

            # analytical requirement
            # if p is the number of sampled cycles, we can find that p = window_size / a
            # the number of sampled cycles must be a positive natural number.
            p = window_size / a
            if window_size % a != 0:
                raise ValueError(
                    (
                        f"The number of sampled cycles must be a positive natural number. "
                        f"Computed that p={p}"
                    )
                )

        return pvalidator

    def __get_pvalidator_tagged_staircase(self) -> Callable[[Parameters], None]:
        def pvalidator(parameters: Parameters) -> None:
            validate_window(parameters)

            freq_step = cast(
                float, parameters.get_parameter_value(PName.FREQUENCY_STEP)
            )
            sample_rate = cast(int, parameters.get_parameter_value(PName.SAMPLE_RATE))
            min_samples_per_step = cast(
                int, parameters.get_parameter_value(PName.MIN_SAMPLES_PER_STEP)
            )
            max_samples_per_step = cast(
                int, parameters.get_parameter_value(PName.MAX_SAMPLES_PER_STEP)
            )

            if freq_step != sample_rate:
                raise ValueError(
                    f"The frequency step must be equal to the sampling rate"
                )

            if min_samples_per_step > max_samples_per_step:
                raise ValueError(
                    (
                        f"Minimum samples per step cannot be greater than the maximum samples per step. "
                        f"Got {min_samples_per_step}, which is greater than {max_samples_per_step}"
                    )
                )

        return pvalidator
