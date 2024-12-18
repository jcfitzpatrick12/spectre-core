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

from gnuradio import gr
from gnuradio.filter import firdes
from gnuradio.fft import window
import sys
import signal
from argparse import ArgumentParser
from gnuradio.eng_arg import eng_float, intx
from gnuradio import eng_notation
from gnuradio import sdrplay3
from gnuradio import spectre

from spectre_core.paths import CHUNKS_DIR_PATH
from spectre_core.receivers.configs import CaptureConfig


class tuner_2_fixed(gr.top_block):

    def __init__(self,
                 capture_config: CaptureConfig):
        gr.top_block.__init__(self, "tuner_2_fixed", catch_exceptions=True)

        ##################################################
        # Unpack capture config
        ##################################################
        samp_rate = capture_config['samp_rate']
        tag = capture_config['tag']
        chunk_size = capture_config['chunk_size']
        center_freq = capture_config['center_freq']
        bandwidth = capture_config['bandwidth']
        IF_gain = capture_config['IF_gain']
        RF_gain = capture_config['RF_gain']
        is_sweeping = False

        ##################################################
        # Blocks
        ##################################################
        self.spectre_batched_file_sink_0 = spectre.batched_file_sink(CHUNKS_DIR_PATH, 
                                                                     tag, 
                                                                     chunk_size, 
                                                                     samp_rate, 
                                                                     is_sweeping)
        self.sdrplay3_rspduo_0 = sdrplay3.rspduo(
            '',
            rspduo_mode="Single Tuner",
            antenna="Tuner 2 50 ohm",
            stream_args=sdrplay3.stream_args(
                output_type='fc32',
                channels_size=1
            ),
        )
        self.sdrplay3_rspduo_0.set_sample_rate(samp_rate)
        self.sdrplay3_rspduo_0.set_center_freq(center_freq)
        self.sdrplay3_rspduo_0.set_bandwidth(bandwidth)
        self.sdrplay3_rspduo_0.set_antenna("Tuner 2 50 ohm")
        self.sdrplay3_rspduo_0.set_gain_mode(False)
        self.sdrplay3_rspduo_0.set_gain(IF_gain, 'IF')
        self.sdrplay3_rspduo_0.set_gain(RF_gain, 'RF', False)
        self.sdrplay3_rspduo_0.set_freq_corr(0)
        self.sdrplay3_rspduo_0.set_dc_offset_mode(False)
        self.sdrplay3_rspduo_0.set_iq_balance_mode(False)
        self.sdrplay3_rspduo_0.set_agc_setpoint(-30)
        self.sdrplay3_rspduo_0.set_rf_notch_filter(False)
        self.sdrplay3_rspduo_0.set_dab_notch_filter(False)
        self.sdrplay3_rspduo_0.set_am_notch_filter(False)
        self.sdrplay3_rspduo_0.set_biasT(False)
        self.sdrplay3_rspduo_0.set_stream_tags(False)
        self.sdrplay3_rspduo_0.set_debug_mode(False)
        self.sdrplay3_rspduo_0.set_sample_sequence_gaps_check(False)
        self.sdrplay3_rspduo_0.set_show_gain_changes(False)


        ##################################################
        # Connections
        ##################################################
        self.connect((self.sdrplay3_rspduo_0, 0), (self.spectre_batched_file_sink_0, 0))


    def get_samp_rate(self):
        return self.samp_rate

    def set_samp_rate(self, samp_rate):
        self.samp_rate = samp_rate
        self.sdrplay3_rspduo_0.set_sample_rate(self.samp_rate, False)




def main(capture_config: CaptureConfig, 
         top_block_cls=tuner_2_fixed, 
         options=None):

    tb = top_block_cls(capture_config)

    def sig_handler(sig=None, frame=None):
        tb.stop()
        tb.wait()

        sys.exit(0)

    signal.signal(signal.SIGINT, sig_handler)
    signal.signal(signal.SIGTERM, sig_handler)

    tb.start()

    tb.wait()

