#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#
# SPDX-License-Identifier: GPL-3.0
#
# GNU Radio Python Flow Graph
# Title: Test receiver
# GNU Radio version: 3.10.1.1

# SPDX-FileCopyrightText: © 2024 Jimmy Fitzpatrick <jcfitzpatrick12@gmail.com>
# This file is part of SPECTRE
# SPDX-License-Identifier: GPL-3.0-or-later

#
# Test receiver top blocks
#

from functools import partial
from dataclasses import dataclass

from gnuradio import gr
from gnuradio import blocks
from gnuradio import spectre
from gnuradio import analog

from spectre_core.capture_configs import Parameters, PNames
from spectre_core.config import get_chunks_dir_path
from ._base import capture


class _cosine_signal_1(gr.top_block):
    def __init__(self, 
                 tag: str,
                 parameters: Parameters):
        gr.top_block.__init__(self, catch_exceptions=True)

        ##################################################
        # Unpack capture config
        ##################################################
        samp_rate   = parameters.get_parameter_value(PNames.SAMPLE_RATE)
        batch_size  = parameters.get_parameter_value(PNames.BATCH_SIZE)
        frequency   = parameters.get_parameter_value(PNames.FREQUENCY)
        amplitude   = parameters.get_parameter_value(PNames.AMPLITUDE)

        ##################################################
        # Blocks
        ##################################################
        self.spectre_batched_file_sink_0 = spectre.batched_file_sink(get_chunks_dir_path(), 
                                                                     tag, 
                                                                     batch_size, 
                                                                     samp_rate)
        self.blocks_throttle_0_1 = blocks.throttle(gr.sizeof_float*1, 
                                                   samp_rate,
                                                   True)
        self.blocks_throttle_0 = blocks.throttle(gr.sizeof_float*1, 
                                                 samp_rate,
                                                 True)
        self.blocks_null_source_1 = blocks.null_source(gr.sizeof_float*1)
        self.blocks_float_to_complex_1 = blocks.float_to_complex(1)
        self.analog_sig_source_x_0 = analog.sig_source_f(samp_rate, 
                                                         analog.GR_COS_WAVE, 
                                                         frequency, 
                                                         amplitude, 
                                                         0, 
                                                         0)


        ##################################################
        # Connections
        ##################################################
        self.connect((self.analog_sig_source_x_0, 0), (self.blocks_throttle_0, 0))
        self.connect((self.blocks_float_to_complex_1, 0), (self.spectre_batched_file_sink_0, 0))
        self.connect((self.blocks_null_source_1, 0), (self.blocks_throttle_0_1, 0))
        self.connect((self.blocks_throttle_0, 0), (self.blocks_float_to_complex_1, 0))
        self.connect((self.blocks_throttle_0_1, 0), (self.blocks_float_to_complex_1, 1))


class _tagged_staircase(gr.top_block):
    def __init__(self, 
                 tag: str,
                 parameters: Parameters):
        gr.top_block.__init__(self, catch_exceptions=True)

        ##################################################
        # Unpack capture config
        ##################################################
        step_increment       = parameters.get_parameter_value(PNames.STEP_INCREMENT)
        samp_rate            = parameters.get_parameter_value(PNames.SAMPLE_RATE)
        min_samples_per_step = parameters.get_parameter_value(PNames.MIN_SAMPLES_PER_STEP)
        max_samples_per_step = parameters.get_parameter_value(PNames.MAX_SAMPLES_PER_STEP)
        frequency_step       = parameters.get_parameter_value(PNames.FREQUENCY_STEP)
        batch_size           = parameters.get_parameter_value(PNames.BATCH_SIZE)

        ##################################################
        # Blocks
        ##################################################
        self.spectre_tagged_staircase_0 = spectre.tagged_staircase(min_samples_per_step, 
                                                                   max_samples_per_step, 
                                                                   frequency_step,
                                                                   step_increment, 
                                                                   samp_rate)
        self.spectre_batched_file_sink_0 = spectre.batched_file_sink(get_chunks_dir_path(),
                                                                     tag, 
                                                                     batch_size, 
                                                                     samp_rate, 
                                                                     True,
                                                                     'rx_freq',
                                                                     0) # zero means the center frequency is unset
        self.blocks_throttle_0 = blocks.throttle(gr.sizeof_gr_complex*1, samp_rate, True)


        ##################################################
        # Connections
        ##################################################
        self.connect((self.blocks_throttle_0, 0), (self.spectre_batched_file_sink_0, 0))
        self.connect((self.spectre_tagged_staircase_0, 0), (self.blocks_throttle_0, 0))


@dataclass(frozen=True)
class CaptureMethods:
    cosine_signal_1  = partial(capture, top_block_cls=_cosine_signal_1)
    tagged_staircase = partial(capture, top_block_cls=_tagged_staircase)