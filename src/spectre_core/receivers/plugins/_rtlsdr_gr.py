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
        rf_gain = parameters.get_parameter_value(PName.RF_GAIN)
        batch_size = parameters.get_parameter_value(PName.BATCH_SIZE)
        center_frequency = parameters.get_parameter_value(PName.CENTER_FREQUENCY)

        # Blocks
        stream_args = ""
        tune_args = [""]
        settings = [""]
        self.soapy_rtlsdr_source = soapy.source(
            "driver=rtlsdr", "fc32", 1, "", stream_args, tune_args, settings
        )
        self.soapy_rtlsdr_source.set_sample_rate(0, sample_rate)
        self.soapy_rtlsdr_source.set_gain_mode(0, False)
        self.soapy_rtlsdr_source.set_frequency(0, center_frequency)
        self.soapy_rtlsdr_source.set_frequency_correction(0, 0)
        self.soapy_rtlsdr_source.set_gain(0, rf_gain)
        self.spectre_batched_file_sink = spectre.batched_file_sink(
            get_batches_dir_path(), tag, batch_size, sample_rate, False, "rx_freq", 0
        )

        # Connections
        self.connect((self.soapy_rtlsdr_source, 0), (self.spectre_batched_file_sink, 0))
