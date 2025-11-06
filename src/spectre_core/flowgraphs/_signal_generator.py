# SPDX-FileCopyrightText: © 2024-2025 Jimmy Fitzpatrick <jcfitzpatrick12@gmail.com>
# This file is part of SPECTRE
# SPDX-License-Identifier: GPL-3.0-or-later

import typing

from gnuradio import gr
from gnuradio import blocks
from gnuradio import analog
from gnuradio import spectre

import spectre_core.fields

from ._base import Base, BaseModel


class CosineWaveModel(BaseModel):
    sample_rate: spectre_core.fields.Field.sample_rate = 128000
    batch_size: spectre_core.fields.Field.batch_size = 3.0
    frequency: spectre_core.fields.Field.frequency = 32000
    amplitude: spectre_core.fields.Field.amplitude = 1


class CosineWave(Base):
    """Record a complex-valued cosine signal to batched data files."""

    def configure(self, tag: str, parameters: dict[str, typing.Any]) -> None:
        sample_rate = typing.cast(float, parameters["sample_rate"])
        batch_size = typing.cast(float, parameters["batch_size"])
        frequency = typing.cast(float, parameters["frequency"])
        amplitude = typing.cast(float, parameters["amplitude"])

        self.spectre_batched_file_sink = spectre.batched_file_sink(
            self._batches_dir_path, tag, batch_size, sample_rate
        )
        self.blocks_throttle_0 = blocks.throttle(gr.sizeof_float * 1, sample_rate, True)
        self.blocks_throttle_1 = blocks.throttle(gr.sizeof_float * 1, sample_rate, True)
        self.blocks_null_source = blocks.null_source(gr.sizeof_float * 1)
        self.blocks_float_to_complex = blocks.float_to_complex(1)
        self.analog_sig_source = analog.sig_source_f(
            sample_rate, analog.GR_COS_WAVE, frequency, amplitude, 0, 0
        )

        self.connect((self.analog_sig_source, 0), (self.blocks_throttle_0, 0))
        self.connect((self.blocks_null_source, 0), (self.blocks_throttle_1, 0))
        self.connect((self.blocks_throttle_0, 0), (self.blocks_float_to_complex, 0))
        self.connect((self.blocks_throttle_1, 0), (self.blocks_float_to_complex, 1))
        self.connect(
            (self.blocks_float_to_complex, 0), (self.spectre_batched_file_sink, 0)
        )
