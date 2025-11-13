# SPDX-FileCopyrightText: © 2024-2025 Jimmy Fitzpatrick <jcfitzpatrick12@gmail.com>
# This file is part of SPECTRE
# SPDX-License-Identifier: GPL-3.0-or-later

import pydantic

import spectre_core.events
import spectre_core.flowgraphs

from ._validators import (
    skip_validator,
    validate_window_size,
    validate_nyquist_criterion,
)


class HackRFFixedCenterFrequency(
    spectre_core.flowgraphs.HackRFFixedCenterFrequencyModel,
    spectre_core.events.FixedCenterFrequencyModel,
):
    @pydantic.model_validator(mode="after")
    def validator(self, info: pydantic.ValidationInfo):
        if skip_validator(info):
            return self
        validate_nyquist_criterion(self.sample_rate, self.bandwidth)
        validate_window_size(self.window_size)
        return self
