# SPDX-FileCopyrightText: © 2024-2025 Jimmy Fitzpatrick <jcfitzpatrick12@gmail.com>
# This file is part of SPECTRE
# SPDX-License-Identifier: GPL-3.0-or-later

from gnuradio import spectre
from gnuradio import soapy

import spectre_core.fields

from ._base import Base, BaseModel


class HackRFFixedCenterFrequencyModel(BaseModel):
    sample_rate: spectre_core.fields.Field.sample_rate = 2000000
    bandwidth: spectre_core.fields.Field.bandwidth = 2e6
    center_frequency: spectre_core.fields.Field.center_frequency = 95.8e6
    amp_on: spectre_core.fields.Field.amp_on = False
    lna_gain: spectre_core.fields.Field.lna_gain = 20
    vga_gain: spectre_core.fields.Field.vga_gain = 20
    batch_size: spectre_core.fields.Field.batch_size = 3


class HackRFFixedCenterFrequency(Base[HackRFFixedCenterFrequencyModel]):
    def configure(self, tag: str, model: HackRFFixedCenterFrequencyModel) -> None:
        stream_args = ""
        tune_args = [""]
        settings = [""]
        self.soapy_hackrf_source = soapy.source(
            "driver=hackrf", "fc32", 1, "", stream_args, tune_args, settings
        )
        self.soapy_hackrf_source.set_sample_rate(0, model.sample_rate)
        self.soapy_hackrf_source.set_bandwidth(0, model.bandwidth)
        self.soapy_hackrf_source.set_frequency(0, model.center_frequency)
        self.soapy_hackrf_source.set_gain(0, "AMP", model.amp_on)
        self.soapy_hackrf_source.set_gain(0, "LNA", model.lna_gain)
        self.soapy_hackrf_source.set_gain(0, "VGA", model.vga_gain)
        self.spectre_batched_file_sink = spectre.batched_file_sink(
            self._batches_dir_path,
            tag,
            model.batch_size,
            model.sample_rate,
            False,
            "rx_freq",
            0,
        )
        self.connect((self.soapy_hackrf_source, 0), (self.spectre_batched_file_sink, 0))
