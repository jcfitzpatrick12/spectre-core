# SPDX-FileCopyrightText: © 2024-2025 Jimmy Fitzpatrick <jcfitzpatrick12@gmail.com>
# This file is part of SPECTRE
# SPDX-License-Identifier: GPL-3.0-or-later

import pydantic

import spectre_core.event_handlers
import spectre_core.flowgraphs


class CosineWaveModel(
    spectre_core.flowgraphs.CosineWaveModel,
    spectre_core.event_handlers.FixedCenterFrequencyModel,
):
    @pydantic.model_validator(mode="after")
    def validate(self):
        # Check that the sample rate is an integer multiple of the frequency
        if self.sample_rate % self.frequency != 0:
            raise ValueError(
                "The sampling rate must be an integer multiple of the frequency."
            )

        a = self.sample_rate / self.frequency
        if a < 2:
            raise ValueError(
                f"The ratio of sampling rate over frequency must be greater than two. Got {a}."
            )

        # Ensure the number of sampled cycles is a positive natural number
        p = self.window_size / a
        if self.window_size % a != 0:
            raise ValueError(
                f"The number of sampled cycles must be a positive natural number. Computed p={p}."
            )

        return self
