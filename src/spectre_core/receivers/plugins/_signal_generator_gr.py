# SPDX-FileCopyrightText: © 2024-2025 Jimmy Fitzpatrick <jcfitzpatrick12@gmail.com>
# This file is part of SPECTRE
# SPDX-License-Identifier: GPL-3.0-or-later

from gnuradio import gr
from gnuradio import blocks
from gnuradio import analog
from gnuradio import spectre

from spectre_core.capture_configs import Parameters, PName
from spectre_core.config import get_batches_dir_path
from ._gr import spectre_top_block


class cosine_wave(spectre_top_block):
    def flowgraph(self, tag: str, parameters: Parameters) -> None:

        # Unpack the capture config parameters
        samp_rate = parameters.get_parameter_value(PName.SAMPLE_RATE)
        batch_size = parameters.get_parameter_value(PName.BATCH_SIZE)
        frequency = parameters.get_parameter_value(PName.FREQUENCY)
        amplitude = parameters.get_parameter_value(PName.AMPLITUDE)

        # Blocks
        self.spectre_batched_file_sink = spectre.batched_file_sink(
            get_batches_dir_path(), tag, batch_size, samp_rate
        )
        self.blocks_throttle_0 = blocks.throttle(gr.sizeof_float * 1, samp_rate, True)
        self.blocks_throttle_1 = blocks.throttle(gr.sizeof_float * 1, samp_rate, True)
        self.blocks_null_source = blocks.null_source(gr.sizeof_float * 1)
        self.blocks_float_to_complex = blocks.float_to_complex(1)
        self.analog_sig_source = analog.sig_source_f(
            samp_rate, analog.GR_COS_WAVE, frequency, amplitude, 0, 0
        )

        # Connections
        self.connect((self.analog_sig_source, 0), (self.blocks_throttle_0, 0))
        self.connect((self.blocks_null_source, 0), (self.blocks_throttle_1, 0))
        self.connect((self.blocks_throttle_0, 0), (self.blocks_float_to_complex, 0))
        self.connect((self.blocks_throttle_1, 0), (self.blocks_float_to_complex, 1))
        self.connect(
            (self.blocks_float_to_complex, 0), (self.spectre_batched_file_sink, 0)
        )


class constant_staircase(spectre_top_block):
    def flowgraph(self, tag: str, parameters: Parameters) -> None:
        # Unpack the capture config parameters
        step_increment = parameters.get_parameter_value(PName.STEP_INCREMENT)
        samp_rate = parameters.get_parameter_value(PName.SAMPLE_RATE)
        min_samples_per_step = parameters.get_parameter_value(
            PName.MIN_SAMPLES_PER_STEP
        )
        max_samples_per_step = parameters.get_parameter_value(
            PName.MAX_SAMPLES_PER_STEP
        )
        frequency_step = parameters.get_parameter_value(PName.FREQUENCY_STEP)
        batch_size = parameters.get_parameter_value(PName.BATCH_SIZE)

        # Blocks
        self.spectre_constant_staircase = spectre.tagged_staircase(
            min_samples_per_step,
            max_samples_per_step,
            frequency_step,
            step_increment,
            samp_rate,
        )
        self.spectre_batched_file_sink = spectre.batched_file_sink(
            get_batches_dir_path(), tag, batch_size, samp_rate, True, "rx_freq", 0
        )  # zero means the center frequency is unset
        self.blocks_throttle = blocks.throttle(
            gr.sizeof_gr_complex * 1, samp_rate, True
        )

        # Connections
        self.connect((self.spectre_constant_staircase, 0), (self.blocks_throttle, 0))
        self.connect((self.blocks_throttle, 0), (self.spectre_batched_file_sink, 0))
