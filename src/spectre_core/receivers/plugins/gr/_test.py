#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#
# SPDX-License-Identifier: GPL-3.0
#
# GNU Radio Python Flow Graph
# Title: Test receiver
# GNU Radio version: 3.10.1.1

# SPDX-FileCopyrightText: © 2024-2025 Jimmy Fitzpatrick <jcfitzpatrick12@gmail.com>
# This file is part of SPECTRE
# SPDX-License-Identifier: GPL-3.0-or-later

#
# Test receiver top blocks
#

from functools import partial
from typing import Callable
from dataclasses import dataclass

from gnuradio import gr
from gnuradio import blocks
from gnuradio import analog

from spectre_core.capture_configs import Parameters, PName
from spectre_core.config import get_batches_dir_path
from ._base import capture, spectre_top_block


class _cosine_signal_1(spectre_top_block):
    def flowgraph(self, tag: str, parameters: Parameters) -> None:
        # Inline imports
        from gnuradio import spectre

        # Unpack the capture config parameters
        samp_rate = parameters.get_parameter_value(PName.SAMPLE_RATE)
        batch_size = parameters.get_parameter_value(PName.BATCH_SIZE)
        frequency = parameters.get_parameter_value(PName.FREQUENCY)
        amplitude = parameters.get_parameter_value(PName.AMPLITUDE)

        # Blocks
        self.spectre_batched_file_sink_0 = spectre.batched_file_sink(
            get_batches_dir_path(), tag, batch_size, samp_rate
        )
        self.blocks_throttle_0_1 = blocks.throttle(gr.sizeof_float * 1, samp_rate, True)
        self.blocks_throttle_0 = blocks.throttle(gr.sizeof_float * 1, samp_rate, True)
        self.blocks_null_source_1 = blocks.null_source(gr.sizeof_float * 1)
        self.blocks_float_to_complex_1 = blocks.float_to_complex(1)
        self.analog_sig_source_x_0 = analog.sig_source_f(
            samp_rate, analog.GR_COS_WAVE, frequency, amplitude, 0, 0
        )

        ##################################################
        # Connections
        ##################################################
        self.connect((self.analog_sig_source_x_0, 0), (self.blocks_throttle_0, 0))
        self.connect(
            (self.blocks_float_to_complex_1, 0), (self.spectre_batched_file_sink_0, 0)
        )
        self.connect((self.blocks_null_source_1, 0), (self.blocks_throttle_0_1, 0))
        self.connect((self.blocks_throttle_0, 0), (self.blocks_float_to_complex_1, 0))
        self.connect((self.blocks_throttle_0_1, 0), (self.blocks_float_to_complex_1, 1))


class _tagged_staircase(spectre_top_block):
    def flowgraph(self, tag: str, parameters: Parameters) -> None:
        # Inline imports
        from gnuradio import spectre

        ##################################################
        # Unpack capture config
        ##################################################
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

        ##################################################
        # Blocks
        ##################################################
        self.spectre_tagged_staircase_0 = spectre.tagged_staircase(
            min_samples_per_step,
            max_samples_per_step,
            frequency_step,
            step_increment,
            samp_rate,
        )
        self.spectre_batched_file_sink_0 = spectre.batched_file_sink(
            get_batches_dir_path(), tag, batch_size, samp_rate, True, "rx_freq", 0
        )  # zero means the center frequency is unset
        self.blocks_throttle_0 = blocks.throttle(
            gr.sizeof_gr_complex * 1, samp_rate, True
        )

        ##################################################
        # Connections
        ##################################################
        self.connect((self.blocks_throttle_0, 0), (self.spectre_batched_file_sink_0, 0))
        self.connect((self.spectre_tagged_staircase_0, 0), (self.blocks_throttle_0, 0))


@dataclass(frozen=True)
class CaptureMethod:
    cosine_signal_1: Callable[[str, Parameters], None] = partial(
        capture, top_block_cls=_cosine_signal_1
    )
    tagged_staircase: Callable[[str, Parameters], None] = partial(
        capture, top_block_cls=_tagged_staircase
    )
