# SPDX-FileCopyrightText: © 2024-2025 Jimmy Fitzpatrick <jcfitzpatrick12@gmail.com>
# This file is part of SPECTRE
# SPDX-License-Identifier: GPL-3.0-or-later

from gnuradio import spectre
from gnuradio import soapy

from spectre_core.capture_configs import Parameters, PName
from spectre_core.config import get_batches_dir_path
from ._gr import spectre_top_block


class fixed_center_frequency(spectre_top_block):
    def flowgraph(self, tag: str, parameters: Parameters) -> None:

        # Unpack capture config parameters
        sample_rate = parameters.get_parameter_value(PName.SAMPLE_RATE)
        bandwidth = parameters.get_parameter_value(PName.BANDWIDTH)
        batch_size = parameters.get_parameter_value(PName.BATCH_SIZE)
        center_frequency = parameters.get_parameter_value(PName.CENTER_FREQUENCY)
        amp_on = parameters.get_parameter_value(PName.AMP_ON)
        lna_gain = parameters.get_parameter_value(PName.LNA_GAIN)
        vga_gain = parameters.get_parameter_value(PName.VGA_GAIN)

        # Blocks
        stream_args = ""
        tune_args = [""]
        settings = [""]
        self.soapy_hackrf_source = soapy.source(
            "driver=hackrf", "fc32", 1, "", stream_args, tune_args, settings
        )
        self.soapy_hackrf_source.set_sample_rate(0, sample_rate)
        self.soapy_hackrf_source.set_bandwidth(0, bandwidth)
        self.soapy_hackrf_source.set_frequency(0, center_frequency)
        self.soapy_hackrf_source.set_gain(0, "AMP", amp_on)
        self.soapy_hackrf_source.set_gain(0, "LNA", lna_gain)
        self.soapy_hackrf_source.set_gain(0, "VGA", vga_gain)
        self.spectre_batched_file_sink = spectre.batched_file_sink(
            get_batches_dir_path(), tag, batch_size, sample_rate, False, "rx_freq", 0
        )

        # Connections
        self.connect((self.soapy_hackrf_source, 0), (self.spectre_batched_file_sink, 0))
