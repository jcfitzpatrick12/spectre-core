#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#
# SPDX-License-Identifier: GPL-3.0
#
# GNU Radio Python Flow Graph
# Title: Not titled yet
# GNU Radio version: 3.10.1.1

# SPDX-FileCopyrightText: © 2024 Jimmy Fitzpatrick <jcfitzpatrick12@gmail.com>
# This file is part of SPECTRE
# SPDX-License-Identifier: GPL-3.0-or-later

import sys
import signal
from argparse import ArgumentParser
from typing import Any

from gnuradio import blocks
from gnuradio import gr
from gnuradio.filter import firdes
from gnuradio.fft import window
from gnuradio.eng_arg import eng_float, intx
from gnuradio import eng_notation
from gnuradio import spectre

from spectre_core.paths import get_chunks_dir_path
from spectre_core.parameters import Parameters
from spectre_core.parameter_store import PNames

class tagged_staircase(gr.top_block):

    def __init__(self, 
                 tag: str,
                 parameters: Parameters):
        gr.top_block.__init__(self, "tagged-staircase", catch_exceptions=True)

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
                                                                     0
                                                                     )
        self.blocks_throttle_0 = blocks.throttle(gr.sizeof_gr_complex*1, samp_rate, True)


        ##################################################
        # Connections
        ##################################################
        self.connect((self.blocks_throttle_0, 0), (self.spectre_batched_file_sink_0, 0))
        self.connect((self.spectre_tagged_staircase_0, 0), (self.blocks_throttle_0, 0))




def capture(tag: str,
            parameters: Parameters, 
            top_block_cls=tagged_staircase, 
            options=None):
    tb = top_block_cls(tag,
                       parameters)

    def sig_handler(sig=None, frame=None):
        tb.stop()
        tb.wait()

        sys.exit(0)

    signal.signal(signal.SIGINT, sig_handler)
    signal.signal(signal.SIGTERM, sig_handler)

    tb.start()

    tb.wait()