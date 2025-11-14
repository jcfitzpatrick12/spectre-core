# SPDX-FileCopyrightText: © 2024-2025 Jimmy Fitzpatrick <jcfitzpatrick12@gmail.com>
# This file is part of SPECTRE
# SPDX-License-Identifier: GPL-3.0-or-later

from gnuradio import gr
from gnuradio import blocks
from gnuradio import analog
from gnuradio import spectre

import spectre_core.fields

from ._base import Base, BaseModel


class SignalGeneratorCosineWaveModel(BaseModel):
    sample_rate: spectre_core.fields.Field.sample_rate = 128000
    batch_size: spectre_core.fields.Field.batch_size = 3
    frequency: spectre_core.fields.Field.frequency = 32000
    amplitude: spectre_core.fields.Field.amplitude = 1


class SignalGeneratorCosineWave(Base[SignalGeneratorCosineWaveModel]):
    def configure(self, tag: str, model: SignalGeneratorCosineWaveModel) -> None:
        """Record a complex-valued cosine signal to batched data files."""
        self.spectre_batched_file_sink = spectre.batched_file_sink(
            self._batches_dir_path, tag, model.batch_size, model.sample_rate
        )
        self.blocks_throttle_0 = blocks.throttle(
            gr.sizeof_float * 1, model.sample_rate, True
        )
        self.blocks_throttle_1 = blocks.throttle(
            gr.sizeof_float * 1, model.sample_rate, True
        )
        self.blocks_null_source = blocks.null_source(gr.sizeof_float * 1)
        self.blocks_float_to_complex = blocks.float_to_complex(1)
        self.analog_sig_source = analog.sig_source_f(
            model.sample_rate,
            analog.GR_COS_WAVE,
            model.frequency,
            model.amplitude,
            0,
            0,
        )

        self.connect((self.analog_sig_source, 0), (self.blocks_throttle_0, 0))
        self.connect((self.blocks_null_source, 0), (self.blocks_throttle_1, 0))
        self.connect((self.blocks_throttle_0, 0), (self.blocks_float_to_complex, 0))
        self.connect((self.blocks_throttle_1, 0), (self.blocks_float_to_complex, 1))
        self.connect(
            (self.blocks_float_to_complex, 0), (self.spectre_batched_file_sink, 0)
        )


class SignalGeneratorConstantStaircaseModel(BaseModel):
    step_increment: spectre_core.fields.Field.step_increment = 200
    sample_rate: spectre_core.fields.Field.sample_rate = 128000
    min_samples_per_step: spectre_core.fields.Field.min_samples_per_step = 4000
    max_samples_per_step: spectre_core.fields.Field.max_samples_per_step = 5000
    frequency_step: spectre_core.fields.Field.frequency_step = 128000
    batch_size: spectre_core.fields.Field.batch_size = 3


class SignalGeneratorConstantStaircase(Base[SignalGeneratorConstantStaircaseModel]):
    def configure(self, tag: str, model: SignalGeneratorConstantStaircaseModel) -> None:
        """Record a constant signal that periodically increments in value.
        Each step increases in duration, up to a maximum, before resetting."""
        self.spectre_constant_staircase = spectre.tagged_staircase(
            model.min_samples_per_step,
            model.max_samples_per_step,
            model.frequency_step,
            model.step_increment,
            model.sample_rate,
        )
        self.spectre_batched_file_sink = spectre.batched_file_sink(
            self._batches_dir_path,
            tag,
            model.batch_size,
            model.sample_rate,
            True,
            "rx_freq",
            0,
        )  # zero means the center frequency is unset
        self.blocks_throttle = blocks.throttle(
            gr.sizeof_gr_complex * 1, model.sample_rate, True
        )

        self.connect((self.spectre_constant_staircase, 0), (self.blocks_throttle, 0))
        self.connect((self.blocks_throttle, 0), (self.spectre_batched_file_sink, 0))
