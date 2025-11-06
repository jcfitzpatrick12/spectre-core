# SPDX-FileCopyrightText: © 2024-2025 Jimmy Fitzpatrick <jcfitzpatrick12@gmail.com>
# This file is part of SPECTRE
# SPDX-License-Identifier: GPL-3.0-or-later

import pydantic

import spectre_core.fields
import spectre_core.event_handlers
import spectre_core.flowgraphs


class CosineWaveModel(
    spectre_core.flowgraphs.CosineWaveModel,
    spectre_core.event_handlers.FixedCenterFrequencyModel,
):
    window_type: spectre_core.fields.Field.window_type = "boxcar"

    @pydantic.model_validator(mode="after")
    def validate(self):
        if not self.window_type == "boxcar":
            raise ValueError(
                f"The window type must be boxcar. Got '{self.window_type}'"
            )
        if self.sample_rate % self.frequency != 0:
            raise ValueError(
                "The sampling rate must be some integer multiple of frequency"
            )

        a = self.sample_rate / self.frequency
        if a < 2:
            raise ValueError(
                (
                    f"The ratio of sampling rate over frequency must be greater than two. "
                    f"Got {a}"
                )
            )
        p = self.window_size / a
        if self.window_size % a != 0:
            raise ValueError(
                f"The number of sampled cycles must be a positive natural number. Computed p={p}."
            )

        return self


class ConstantStaircaseModel(
    spectre_core.flowgraphs.ConstantStaircaseModel,
    spectre_core.event_handlers.FixedCenterFrequencyModel,
):
    window_type: spectre_core.fields.Field.window_type = "boxcar"

    @pydantic.model_validator(mode="after")
    def validate(self):
        if self.frequency_step != self.sample_rate:
            raise ValueError(f"The frequency step must be equal to the sampling rate")

        if self.min_samples_per_step > self.max_samples_per_step:
            raise ValueError(
                (
                    f"Minimum samples per step cannot be greater than the maximum samples per step. "
                    f"Got {self.min_samples_per_step}, which is greater than {self.max_samples_per_step}"
                )
            )
        return self
