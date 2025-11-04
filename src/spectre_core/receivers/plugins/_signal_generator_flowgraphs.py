# SPDX-FileCopyrightText: © 2024-2025 Jimmy Fitzpatrick <jcfitzpatrick12@gmail.com>
# This file is part of SPECTRE
# SPDX-License-Identifier: GPL-3.0-or-later

import typing
import pydantic

from gnuradio import gr
from gnuradio import blocks
from gnuradio import analog
from gnuradio import spectre


from .._flowgraph import BaseFlowgraph, BaseFlowgraphModel


class CosineWaveModel(BaseFlowgraphModel):
    sample_rate: int = pydantic.Field(
        128000, gt=0, description="The number of samples per second in Hz."
    )
    batch_size: float = pydantic.Field(
        3,
        gt=1,
        description="SDR data is collected in batches of this size, specified in seconds.",
    )
    frequency: float = pydantic.Field(
        32000.0, gt=0, description="Frequency of the wave in Hz."
    )
    amplitude: float = pydantic.Field(1, gt=0, description="Amplitude of the wave.")


class CosineWave(BaseFlowgraph):
    def configure(self, tag: str, **parameters) -> None:
        sample_rate = typing.cast(float, parameters.pop("sample_rate"))
        batch_size = typing.cast(float, parameters.pop("batch_size"))
        frequency = typing.cast(float, parameters.pop("frequency"))
        amplitude = typing.cast(float, parameters.pop("amplitude"))

        # Blocks
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

        # Connections
        self.connect((self.analog_sig_source, 0), (self.blocks_throttle_0, 0))
        self.connect((self.blocks_null_source, 0), (self.blocks_throttle_1, 0))
        self.connect((self.blocks_throttle_0, 0), (self.blocks_float_to_complex, 0))
        self.connect((self.blocks_throttle_1, 0), (self.blocks_float_to_complex, 1))
        self.connect(
            (self.blocks_float_to_complex, 0), (self.spectre_batched_file_sink, 0)
        )
