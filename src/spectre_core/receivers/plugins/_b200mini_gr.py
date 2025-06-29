# SPDX-FileCopyrightText: © 2024-2025 Jimmy Fitzpatrick <jcfitzpatrick12@gmail.com>
# This file is part of SPECTRE
# SPDX-License-Identifier: GPL-3.0-or-later

import time

from gnuradio import spectre
from gnuradio import uhd

from spectre_core.capture_configs import Parameters, PName
from spectre_core.config import get_batches_dir_path
from ._gr import spectre_top_block


class fixed_center_frequency(spectre_top_block):
    def flowgraph(self, tag: str, parameters: Parameters) -> None:

        # Unpack capture config parameters
        sample_rate = parameters.get_parameter_value(PName.SAMPLE_RATE)
        gain = parameters.get_parameter_value(PName.GAIN)
        center_freq = parameters.get_parameter_value(PName.CENTER_FREQUENCY)
        master_clock_rate = parameters.get_parameter_value(PName.MASTER_CLOCK_RATE)
        wire_format = parameters.get_parameter_value(PName.WIRE_FORMAT)
        batch_size = parameters.get_parameter_value(PName.BATCH_SIZE)
        bandwidth = parameters.get_parameter_value(PName.BANDWIDTH)

        # Blocks
        master_clock_rate = f"master_clock_rate={master_clock_rate}"
        self.uhd_usrp_source = uhd.usrp_source(
            ",".join(("", "", master_clock_rate)),
            uhd.stream_args(
                cpu_format="fc32",
                otw_format=wire_format,
                args="",
                channels=[0],
            ),
        )
        self.uhd_usrp_source.set_samp_rate(sample_rate)
        self.uhd_usrp_source.set_time_now(uhd.time_spec(time.time()), uhd.ALL_MBOARDS)

        self.uhd_usrp_source.set_center_freq(center_freq, 0)
        self.uhd_usrp_source.set_antenna("RX2", 0)
        self.uhd_usrp_source.set_bandwidth(bandwidth, 0)
        self.uhd_usrp_source.set_rx_agc(False, 0)
        self.uhd_usrp_source.set_auto_dc_offset(False, 0)
        self.uhd_usrp_source.set_auto_iq_balance(False, 0)
        self.uhd_usrp_source.set_gain(gain, 0)
        self.spectre_batched_file_sink = spectre.batched_file_sink(
            get_batches_dir_path(), tag, batch_size, sample_rate, False, "rx_freq", 0
        )

        # Connections
        self.connect((self.uhd_usrp_source, 0), (self.spectre_batched_file_sink, 0))


class swept_center_frequency(spectre_top_block):
    def flowgraph(self, tag: str, parameters: Parameters) -> None:
        # Unpack capture config parameters
        sample_rate = parameters.get_parameter_value(PName.SAMPLE_RATE)
        bandwidth = parameters.get_parameter_value(PName.BANDWIDTH)
        min_frequency = parameters.get_parameter_value(PName.MIN_FREQUENCY)
        max_frequency = parameters.get_parameter_value(PName.MAX_FREQUENCY)
        frequency_step = parameters.get_parameter_value(PName.FREQUENCY_STEP)
        samples_per_step = parameters.get_parameter_value(PName.SAMPLES_PER_STEP)
        master_clock_rate = parameters.get_parameter_value(PName.MASTER_CLOCK_RATE)
        master_clock_rate = master_clock_rate = parameters.get_parameter_value(
            PName.MASTER_CLOCK_RATE
        )
        wire_format = parameters.get_parameter_value(PName.WIRE_FORMAT)
        gain = parameters.get_parameter_value(PName.GAIN)
        batch_size = parameters.get_parameter_value(PName.BATCH_SIZE)

        master_clock_rate = f"master_clock_rate={master_clock_rate}"
        self.uhd_usrp_source = uhd.usrp_source(
            ",".join(("", "", master_clock_rate)),
            uhd.stream_args(
                cpu_format="fc32",
                otw_format=wire_format,
                args="",
                channels=[0],
            ),
        )
        self.uhd_usrp_source.set_samp_rate(sample_rate)
        self.uhd_usrp_source.set_time_now(uhd.time_spec(time.time()), uhd.ALL_MBOARDS)
        self.uhd_usrp_source.set_center_freq(min_frequency, 0)
        self.uhd_usrp_source.set_antenna("RX2", 0)
        self.uhd_usrp_source.set_bandwidth(bandwidth, 0)
        self.uhd_usrp_source.set_rx_agc(False, 0)
        self.uhd_usrp_source.set_auto_dc_offset(False, 0)
        self.uhd_usrp_source.set_auto_iq_balance(False, 0)
        self.uhd_usrp_source.set_gain(gain, 0)

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
            "rx_freq",
            min_frequency,
        )

        # Connections
        self.msg_connect(
            (self.spectre_sweep_driver, "retune_command"),
            (self.uhd_usrp_source, "command"),
        )
        self.connect((self.uhd_usrp_source, 0), (self.spectre_batched_file_sink, 0))
        self.connect((self.uhd_usrp_source, 0), (self.spectre_sweep_driver, 0))
