# SPDX-FileCopyrightText: © 2024-2025 Jimmy Fitzpatrick <jcfitzpatrick12@gmail.com>
# This file is part of SPECTRE
# SPDX-License-Identifier: GPL-3.0-or-later

import dataclasses

import spectre_core.events
import spectre_core.flowgraphs
import spectre_core.models
import spectre_core.batches

from ._register import register_receiver
from ._base import Base
from ._names import ReceiverName


@dataclasses.dataclass(frozen=True)
class _Mode:
    FIXED_CENTER_FREQUENCY = "fixed_center_frequency"
    SWEPT_CENTER_FREQUENCY = "swept_center_frequency"


@register_receiver(ReceiverName.RSPDX)
class RSPdx(Base):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.add_mode(
            _Mode.FIXED_CENTER_FREQUENCY,
            spectre_core.models.RSPdxFixedCenterFrequency,
            spectre_core.flowgraphs.RSPdxFixedCenterFrequency,
            spectre_core.events.FixedCenterFrequency,
            spectre_core.batches.IQStreamBatch,
        )

        self.add_mode(
            _Mode.SWEPT_CENTER_FREQUENCY,
            spectre_core.models.RSPdxSweptCenterFrequency,
            spectre_core.flowgraphs.RSPdxSweptCenterFrequency,
            spectre_core.events.SweptCenterFrequency,
            spectre_core.batches.IQStreamBatch,
        )
