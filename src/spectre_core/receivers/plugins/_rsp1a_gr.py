# SPDX-FileCopyrightText: © 2024-2025 Jimmy Fitzpatrick <jcfitzpatrick12@gmail.com>
# This file is part of SPECTRE
# SPDX-License-Identifier: GPL-3.0-or-later


from spectre_core.capture_configs import Parameters, PName
from spectre_core.config import get_batches_dir_path
from ._gr import spectre_top_block

from gnuradio import spectre
from gnuradio import sdrplay3


class fixed_center_frequency(spectre_top_block):
    def flowgraph(self, tag: str, parameters: Parameters) -> None:
        # Unpack the capture config parameters
        sample_rate = parameters.get_parameter_value(PName.SAMPLE_RATE)
        batch_size = parameters.get_parameter_value(PName.BATCH_SIZE)
        center_freq = parameters.get_parameter_value(PName.CENTER_FREQUENCY)
        bandwidth = parameters.get_parameter_value(PName.BANDWIDTH)
        if_gain = parameters.get_parameter_value(PName.IF_GAIN)
        rf_gain = parameters.get_parameter_value(PName.RF_GAIN)

        # Blocks
        self.spectre_batched_file_sink = spectre.batched_file_sink(
            get_batches_dir_path(), tag, batch_size, sample_rate
        )
        self.sdrplay3_rsp1a = sdrplay3.rsp1a(
            "",
            stream_args=sdrplay3.stream_args(output_type="fc32", channels_size=1),
        )
        self.sdrplay3_rsp1a.set_sample_rate(sample_rate)
        self.sdrplay3_rsp1a.set_center_freq(center_freq)
        self.sdrplay3_rsp1a.set_bandwidth(bandwidth)
        self.sdrplay3_rsp1a.set_gain_mode(False)
        self.sdrplay3_rsp1a.set_gain(if_gain, "IF")
        self.sdrplay3_rsp1a.set_gain(rf_gain, "RF")
        self.sdrplay3_rsp1a.set_freq_corr(0)
        self.sdrplay3_rsp1a.set_dc_offset_mode(False)
        self.sdrplay3_rsp1a.set_iq_balance_mode(False)
        self.sdrplay3_rsp1a.set_agc_setpoint(-30)
        self.sdrplay3_rsp1a.set_rf_notch_filter(False)
        self.sdrplay3_rsp1a.set_dab_notch_filter(False)
        self.sdrplay3_rsp1a.set_biasT(False)
        self.sdrplay3_rsp1a.set_debug_mode(False)
        self.sdrplay3_rsp1a.set_sample_sequence_gaps_check(False)
        self.sdrplay3_rsp1a.set_show_gain_changes(False)

        # Connections
        self.connect((self.sdrplay3_rsp1a, 0), (self.spectre_batched_file_sink, 0))


class swept_center_frequency(spectre_top_block):
    def flowgraph(self, tag: str, parameters: Parameters) -> None:
        # Unpack the capture config parameters
        sample_rate = parameters.get_parameter_value(PName.SAMPLE_RATE)
        bandwidth = parameters.get_parameter_value(PName.BANDWIDTH)
        min_frequency = parameters.get_parameter_value(PName.MIN_FREQUENCY)
        max_frequency = parameters.get_parameter_value(PName.MAX_FREQUENCY)
        frequency_step = parameters.get_parameter_value(PName.FREQUENCY_STEP)
        samples_per_step = parameters.get_parameter_value(PName.SAMPLES_PER_STEP)
        if_gain = parameters.get_parameter_value(PName.IF_GAIN)
        rf_gain = parameters.get_parameter_value(PName.RF_GAIN)
        batch_size = parameters.get_parameter_value(PName.BATCH_SIZE)

        # Blocks
        self.spectre_sweep_driver = spectre.sweep_driver(
            min_frequency,
            max_frequency,
            frequency_step,
            sample_rate,
            samples_per_step,
            "freq",
        )
        self.spectre_batched_file_sink = spectre.batched_file_sink(
            get_batches_dir_path(),
            tag,
            batch_size,
            sample_rate,
            True,
            "freq",
            min_frequency,
        )
        self.sdrplay3_rsp1a = sdrplay3.rsp1a(
            "",
            stream_args=sdrplay3.stream_args(output_type="fc32", channels_size=1),
        )
        self.sdrplay3_rsp1a.set_sample_rate(sample_rate, True)
        self.sdrplay3_rsp1a.set_center_freq(min_frequency, True)
        self.sdrplay3_rsp1a.set_bandwidth(bandwidth)
        self.sdrplay3_rsp1a.set_gain_mode(False)
        self.sdrplay3_rsp1a.set_gain(if_gain, "IF", True)
        self.sdrplay3_rsp1a.set_gain(rf_gain, "RF", True)
        self.sdrplay3_rsp1a.set_freq_corr(0)
        self.sdrplay3_rsp1a.set_dc_offset_mode(False)
        self.sdrplay3_rsp1a.set_iq_balance_mode(False)
        self.sdrplay3_rsp1a.set_agc_setpoint(-30)
        self.sdrplay3_rsp1a.set_rf_notch_filter(False)
        self.sdrplay3_rsp1a.set_dab_notch_filter(False)
        self.sdrplay3_rsp1a.set_biasT(False)
        self.sdrplay3_rsp1a.set_stream_tags(True)
        self.sdrplay3_rsp1a.set_debug_mode(False)
        self.sdrplay3_rsp1a.set_sample_sequence_gaps_check(False)
        self.sdrplay3_rsp1a.set_show_gain_changes(False)

        # Connections
        self.msg_connect(
            (self.spectre_sweep_driver, "retune_command"),
            (self.sdrplay3_rsp1a, "command"),
        )
        self.connect((self.sdrplay3_rsp1a, 0), (self.spectre_batched_file_sink, 0))
        self.connect((self.sdrplay3_rsp1a, 0), (self.spectre_sweep_driver, 0))
