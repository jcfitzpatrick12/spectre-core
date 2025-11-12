# SPDX-FileCopyrightText: © 2024-2025 Jimmy Fitzpatrick <jcfitzpatrick12@gmail.com>
# This file is part of SPECTRE
# SPDX-License-Identifier: GPL-3.0-or-later

from gnuradio import sdrplay3
from gnuradio import spectre

import spectre_core.fields

from ._base import Base, BaseModel


class RSP1AFixedCenterFrequencyModel(BaseModel):
    sample_rate: spectre_core.fields.Field.sample_rate = 500000
    batch_size: spectre_core.fields.Field.batch_size = 3
    center_frequency: spectre_core.fields.Field.center_frequency = 95.8e6
    bandwidth: spectre_core.fields.Field.bandwidth = 300000
    if_gain: spectre_core.fields.Field.if_gain = -30
    rf_gain: spectre_core.fields.Field.rf_gain = 0


class RSP1AFixedCenterFrequency(Base[RSP1AFixedCenterFrequencyModel]):
    def configure(self, tag: str, model: RSP1AFixedCenterFrequencyModel) -> None:
        self.spectre_batched_file_sink = spectre.batched_file_sink(
            self._batches_dir_path, tag, model.batch_size, model.sample_rate
        )
        self.sdrplay3_rsp1a = sdrplay3.rsp1a(
            "",
            stream_args=sdrplay3.stream_args(output_type="fc32", channels_size=1),
        )
        self.sdrplay3_rsp1a.set_sample_rate(model.sample_rate)
        self.sdrplay3_rsp1a.set_center_freq(model.center_frequency)
        self.sdrplay3_rsp1a.set_bandwidth(model.bandwidth)
        self.sdrplay3_rsp1a.set_gain_mode(False)
        self.sdrplay3_rsp1a.set_gain(model.if_gain, "IF")
        self.sdrplay3_rsp1a.set_gain(model.rf_gain, "RF")
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

        self.connect((self.sdrplay3_rsp1a, 0), (self.spectre_batched_file_sink, 0))


class RSP1ASweptCenterFrequencyModel(BaseModel):
    sample_rate: spectre_core.fields.Field.sample_rate = 2000000
    batch_size: spectre_core.fields.Field.batch_size = 3
    bandwidth: spectre_core.fields.Field.bandwidth = 1.536e6
    if_gain: spectre_core.fields.Field.if_gain = -30
    rf_gain: spectre_core.fields.Field.rf_gain = 0
    min_frequency: spectre_core.fields.Field.min_frequency = 95e6
    max_frequency: spectre_core.fields.Field.max_frequency = 100e6
    samples_per_step: spectre_core.fields.Field.samples_per_step = 120000
    frequency_step: spectre_core.fields.Field.frequency_step = 2e6


class RSP1ASweptCenterFrequency(Base[RSP1ASweptCenterFrequencyModel]):
    def configure(self, tag: str, model: RSP1ASweptCenterFrequencyModel) -> None:
        self.spectre_sweep_driver = spectre.sweep_driver(
            model.min_frequency,
            model.max_frequency,
            model.frequency_step,
            model.sample_rate,
            model.samples_per_step,
            "freq",
        )
        self.spectre_batched_file_sink = spectre.batched_file_sink(
            self._batches_dir_path,
            tag,
            model.batch_size,
            model.sample_rate,
            True,
            "freq",
            model.min_frequency,
        )
        self.sdrplay3_rsp1a = sdrplay3.rsp1a(
            "",
            stream_args=sdrplay3.stream_args(output_type="fc32", channels_size=1),
        )
        self.sdrplay3_rsp1a.set_sample_rate(model.sample_rate, True)
        self.sdrplay3_rsp1a.set_center_freq(model.min_frequency, True)
        self.sdrplay3_rsp1a.set_bandwidth(model.bandwidth)
        self.sdrplay3_rsp1a.set_gain_mode(False)
        self.sdrplay3_rsp1a.set_gain(model.if_gain, "IF", True)
        self.sdrplay3_rsp1a.set_gain(model.rf_gain, "RF", True)
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

        self.msg_connect(
            (self.spectre_sweep_driver, "retune_command"),
            (self.sdrplay3_rsp1a, "command"),
        )
        self.connect((self.sdrplay3_rsp1a, 0), (self.spectre_batched_file_sink, 0))
        self.connect((self.sdrplay3_rsp1a, 0), (self.spectre_sweep_driver, 0))
