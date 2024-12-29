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
# RSPduo receiver top blocks
#

from functools import partial
from dataclasses import dataclass

from gnuradio import gr
from gnuradio import spectre
from gnuradio import sdrplay3

from spectre_core.capture_configs import Parameters, PNames
from spectre_core.config import get_chunks_dir_path
from ._base import capture


class _tuner_1_fixed_center_frequency(gr.top_block):
    def __init__(self, 
                 tag: str,
                 parameters: Parameters):
        gr.top_block.__init__(self, catch_exceptions=True)
        gr.top_block.__init__(self, "tuner_1_fixed", catch_exceptions=True)
        
        ##################################################
        # Unpack capture config
        ##################################################
        sample_rate = parameters.get_parameter_value(PNames.SAMPLE_RATE)
        batch_size  = parameters.get_parameter_value(PNames.BATCH_SIZE)
        center_freq = parameters.get_parameter_value(PNames.CENTER_FREQUENCY)
        bandwidth   = parameters.get_parameter_value(PNames.BANDWIDTH)
        if_gain     = parameters.get_parameter_value(PNames.IF_GAIN)
        rf_gain     = parameters.get_parameter_value(PNames.RF_GAIN)

        ##################################################
        # Blocks
        ##################################################
        self.spectre_batched_file_sink_0 = spectre.batched_file_sink(get_chunks_dir_path(), 
                                                                     tag, 
                                                                     batch_size, 
                                                                     sample_rate)
        self.sdrplay3_rspduo_0 = sdrplay3.rspduo(
            '',
            rspduo_mode="Single Tuner",
            antenna="Tuner 1 50 ohm",
            stream_args=sdrplay3.stream_args(
                output_type='fc32',
                channels_size=1
            ),
        )
        self.sdrplay3_rspduo_0.set_sample_rate(sample_rate)
        self.sdrplay3_rspduo_0.set_center_freq(center_freq)
        self.sdrplay3_rspduo_0.set_bandwidth(bandwidth)
        self.sdrplay3_rspduo_0.set_antenna("Tuner 1 50 ohm")
        self.sdrplay3_rspduo_0.set_gain_mode(False)
        self.sdrplay3_rspduo_0.set_gain(if_gain, 'IF')
        self.sdrplay3_rspduo_0.set_gain(rf_gain, 'RF')
        self.sdrplay3_rspduo_0.set_freq_corr(0)
        self.sdrplay3_rspduo_0.set_dc_offset_mode(False)
        self.sdrplay3_rspduo_0.set_iq_balance_mode(False)
        self.sdrplay3_rspduo_0.set_agc_setpoint(-30)
        self.sdrplay3_rspduo_0.set_rf_notch_filter(False)
        self.sdrplay3_rspduo_0.set_dab_notch_filter(False)
        self.sdrplay3_rspduo_0.set_am_notch_filter(False)
        self.sdrplay3_rspduo_0.set_biasT(False)
        self.sdrplay3_rspduo_0.set_debug_mode(False)
        self.sdrplay3_rspduo_0.set_sample_sequence_gaps_check(False)
        self.sdrplay3_rspduo_0.set_show_gain_changes(False)


        ##################################################
        # Connections
        ##################################################
        self.connect((self.sdrplay3_rspduo_0, 0), (self.spectre_batched_file_sink_0, 0))
    
        
class _tuner_2_fixed_center_frequency(gr.top_block):
    def __init__(self, 
                 tag: str,
                 parameters: Parameters):
        gr.top_block.__init__(self, catch_exceptions=True)
        gr.top_block.__init__(self, "tuner_1_fixed", catch_exceptions=True)
        
        ##################################################
        # Unpack capture config
        ##################################################
        sample_rate = parameters.get_parameter_value(PNames.SAMPLE_RATE)
        batch_size  = parameters.get_parameter_value(PNames.BATCH_SIZE)
        center_freq = parameters.get_parameter_value(PNames.CENTER_FREQUENCY)
        bandwidth   = parameters.get_parameter_value(PNames.BANDWIDTH)
        if_gain     = parameters.get_parameter_value(PNames.IF_GAIN)
        rf_gain     = parameters.get_parameter_value(PNames.RF_GAIN)

        ##################################################
        # Blocks
        ##################################################
        self.spectre_batched_file_sink_0 = spectre.batched_file_sink(get_chunks_dir_path(), 
                                                                     tag, 
                                                                     batch_size, 
                                                                     sample_rate)
        self.sdrplay3_rspduo_0 = sdrplay3.rspduo(
            '',
            rspduo_mode="Single Tuner",
            antenna="Tuner 2 50 ohm",
            stream_args=sdrplay3.stream_args(
                output_type='fc32',
                channels_size=1
            ),
        )
        self.sdrplay3_rspduo_0.set_sample_rate(sample_rate)
        self.sdrplay3_rspduo_0.set_center_freq(center_freq)
        self.sdrplay3_rspduo_0.set_bandwidth(bandwidth)
        self.sdrplay3_rspduo_0.set_antenna("Tuner 2 50 ohm")
        self.sdrplay3_rspduo_0.set_gain_mode(False)
        self.sdrplay3_rspduo_0.set_gain(if_gain, 'IF')
        self.sdrplay3_rspduo_0.set_gain(rf_gain, 'RF', False)
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


class _tuner_1_swept_center_frequency(gr.top_block):
    def __init__(self, 
                 tag: str,
                 parameters: Parameters):
        gr.top_block.__init__(self, catch_exceptions=True)

        ##################################################
        # Unpack capture config
        ##################################################
        sample_rate      = parameters.get_parameter_value(PNames.SAMPLE_RATE)
        bandwidth        = parameters.get_parameter_value(PNames.BANDWIDTH)
        min_frequency    = parameters.get_parameter_value(PNames.MIN_FREQUENCY)
        max_frequency    = parameters.get_parameter_value(PNames.MAX_FREQUENCY)
        frequency_step   = parameters.get_parameter_value(PNames.FREQUENCY_STEP)
        samples_per_step = parameters.get_parameter_value(PNames.SAMPLES_PER_STEP)
        if_gain          = parameters.get_parameter_value(PNames.IF_GAIN)
        rf_gain          = parameters.get_parameter_value(PNames.RF_GAIN)
        batch_size       = parameters.get_parameter_value(PNames.BATCH_SIZE)

        ##################################################
        # Blocks
        ##################################################
        self.spectre_sweep_driver_0 = spectre.sweep_driver(min_frequency, 
                                                           max_frequency, 
                                                           frequency_step, 
                                                           sample_rate, 
                                                           samples_per_step,
                                                           'freq')
        self.spectre_batched_file_sink_0 = spectre.batched_file_sink(get_chunks_dir_path(), 
                                                                     tag, 
                                                                     batch_size, 
                                                                     sample_rate, 
                                                                     True, 
                                                                     'freq', 
                                                                     min_frequency)
        self.sdrplay3_rspduo_0 = sdrplay3.rspduo(
            '',
            rspduo_mode="Single Tuner",
            antenna="Tuner 1 50 ohm",
            stream_args=sdrplay3.stream_args(
                output_type='fc32',
                channels_size=1
            ),
        )
        self.sdrplay3_rspduo_0.set_sample_rate(sample_rate, True)
        self.sdrplay3_rspduo_0.set_center_freq(min_frequency, True)
        self.sdrplay3_rspduo_0.set_bandwidth(bandwidth)
        self.sdrplay3_rspduo_0.set_antenna("Tuner 1 50 ohm")
        self.sdrplay3_rspduo_0.set_gain_mode(False)
        self.sdrplay3_rspduo_0.set_gain(if_gain, 'IF', True)
        self.sdrplay3_rspduo_0.set_gain(rf_gain, 'RF', True)
        self.sdrplay3_rspduo_0.set_freq_corr(0)
        self.sdrplay3_rspduo_0.set_dc_offset_mode(False)
        self.sdrplay3_rspduo_0.set_iq_balance_mode(False)
        self.sdrplay3_rspduo_0.set_agc_setpoint(-30)
        self.sdrplay3_rspduo_0.set_rf_notch_filter(False)
        self.sdrplay3_rspduo_0.set_dab_notch_filter(True)
        self.sdrplay3_rspduo_0.set_am_notch_filter(False)
        self.sdrplay3_rspduo_0.set_biasT(False)
        self.sdrplay3_rspduo_0.set_stream_tags(True)
        self.sdrplay3_rspduo_0.set_debug_mode(False)
        self.sdrplay3_rspduo_0.set_sample_sequence_gaps_check(False)
        self.sdrplay3_rspduo_0.set_show_gain_changes(False)


        ##################################################
        # Connections
        ##################################################
        self.msg_connect((self.spectre_sweep_driver_0, 'freq'), (self.sdrplay3_rspduo_0, 'freq'))
        self.connect((self.sdrplay3_rspduo_0, 0), (self.spectre_batched_file_sink_0, 0))
        self.connect((self.sdrplay3_rspduo_0, 0), (self.spectre_sweep_driver_0, 0))
        
        
@dataclass(frozen=True)
class CaptureMethods:
    tuner_1_fixed_center_frequency  = partial(capture, top_block_cls=_tuner_1_fixed_center_frequency)
    tuner_2_fixed_center_frequency  = partial(capture, top_block_cls=_tuner_2_fixed_center_frequency)
    tuner_1_swept_center_frequency  = partial(capture, top_block_cls=_tuner_1_swept_center_frequency)