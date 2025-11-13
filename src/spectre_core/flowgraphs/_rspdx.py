# SPDX-FileCopyrightText: © 2024-2025 Jimmy Fitzpatrick <jcfitzpatrick12@gmail.com>
# This file is part of SPECTRE
# SPDX-License-Identifier: GPL-3.0-or-later

import dataclasses

from gnuradio import sdrplay3
from gnuradio import spectre

import spectre_core.fields

from ._base import Base, BaseModel


@dataclasses.dataclass(frozen=True)
class RSPdxPort:
    """Specifies one of the antenna ports on the RSPdx.

    These are easier to type in the CLI tool, than the values we must pass to `gr-sdrplay3`.
    Namely 'Antenna A', 'Antenna B' and 'Antenna C'
    """

    ANT_A = "ant_a"
    ANT_B = "ant_b"


def _map_port(antenna_port: str | None) -> str:
    """Maps the CLI-typeable port, to the one used in the constructor for the RSPdx block in the gr-sdrplay3 OOT module."""
    # Add a typing check for None, to satisfy mypy
    if antenna_port == RSPdxPort.ANT_A:
        return "Antenna A"
    elif antenna_port == RSPdxPort.ANT_B:
        return "Antenna B"
    else:
        raise ValueError(f"{antenna_port} is not a valid antenna port.")


class RSPdxFixedCenterFrequencyModel(BaseModel):
    sample_rate: spectre_core.fields.Field.sample_rate = 500000
    batch_size: spectre_core.fields.Field.batch_size = 3
    center_frequency: spectre_core.fields.Field.center_frequency = 95.8e6
    bandwidth: spectre_core.fields.Field.bandwidth = 300000
    if_gain: spectre_core.fields.Field.if_gain = -30
    rf_gain: spectre_core.fields.Field.rf_gain = 0
    antenna_port: spectre_core.fields.Field.antenna_port = RSPdxPort.ANT_A


class RSPdxFixedCenterFrequency(Base[RSPdxFixedCenterFrequencyModel]):
    def configure(self, tag: str, model: RSPdxFixedCenterFrequencyModel) -> None:
        self.spectre_batched_file_sink = spectre.batched_file_sink(
            self._batches_dir_path, tag, model.batch_size, model.sample_rate
        )

        self.sdrplay3_rspdx = sdrplay3.rspdx(
            "",
            stream_args=sdrplay3.stream_args(output_type="fc32", channels_size=1),
        )
        self.sdrplay3_rspdx.set_sample_rate(model.sample_rate)
        self.sdrplay3_rspdx.set_center_freq(model.center_frequency)
        self.sdrplay3_rspdx.set_bandwidth(model.bandwidth)
        self.sdrplay3_rspdx.set_antenna(_map_port(model.antenna_port))
        self.sdrplay3_rspdx.set_gain_mode(False)
        self.sdrplay3_rspdx.set_gain(model.if_gain, "IF")
        self.sdrplay3_rspdx.set_gain(model.rf_gain, "RF", False)
        self.sdrplay3_rspdx.set_freq_corr(0)
        self.sdrplay3_rspdx.set_dc_offset_mode(False)
        self.sdrplay3_rspdx.set_iq_balance_mode(False)
        self.sdrplay3_rspdx.set_agc_setpoint(-30)
        self.sdrplay3_rspdx.set_hdr_mode(False)
        self.sdrplay3_rspdx.set_rf_notch_filter(False)
        self.sdrplay3_rspdx.set_dab_notch_filter(False)
        self.sdrplay3_rspdx.set_biasT(False)
        self.sdrplay3_rspdx.set_stream_tags(False)
        self.sdrplay3_rspdx.set_debug_mode(False)
        self.sdrplay3_rspdx.set_sample_sequence_gaps_check(False)
        self.sdrplay3_rspdx.set_show_gain_changes(False)

        self.connect((self.sdrplay3_rspdx, 0), (self.spectre_batched_file_sink, 0))


class RSPdxSweptCenterFrequencyModel(BaseModel):
    sample_rate: spectre_core.fields.Field.sample_rate = 2000000
    batch_size: spectre_core.fields.Field.batch_size = 3
    bandwidth: spectre_core.fields.Field.bandwidth = 1.536e6
    if_gain: spectre_core.fields.Field.if_gain = -30
    rf_gain: spectre_core.fields.Field.rf_gain = 0
    min_frequency: spectre_core.fields.Field.min_frequency = 95e6
    max_frequency: spectre_core.fields.Field.max_frequency = 100e6
    samples_per_step: spectre_core.fields.Field.samples_per_step = 120000
    frequency_step: spectre_core.fields.Field.frequency_step = 2e6
    antenna_port: spectre_core.fields.Field.antenna_port = RSPdxPort.ANT_A


class RSPdxSweptCenterFrequency(Base[RSPdxSweptCenterFrequencyModel]):
    def configure(self, tag: str, model: RSPdxSweptCenterFrequencyModel) -> None:
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
        self.sdrplay3_rspdx = sdrplay3.rspdx(
            "",
            stream_args=sdrplay3.stream_args(output_type="fc32", channels_size=1),
        )
        self.sdrplay3_rspdx.set_sample_rate(model.sample_rate)
        self.sdrplay3_rspdx.set_center_freq(model.min_frequency)
        self.sdrplay3_rspdx.set_bandwidth(model.bandwidth)
        self.sdrplay3_rspdx.set_antenna(_map_port(model.antenna_port))
        self.sdrplay3_rspdx.set_gain_mode(False)
        self.sdrplay3_rspdx.set_gain(model.if_gain, "IF")
        self.sdrplay3_rspdx.set_gain(model.rf_gain, "RF", False)
        self.sdrplay3_rspdx.set_freq_corr(0)
        self.sdrplay3_rspdx.set_dc_offset_mode(False)
        self.sdrplay3_rspdx.set_iq_balance_mode(False)
        self.sdrplay3_rspdx.set_agc_setpoint(-30)
        self.sdrplay3_rspdx.set_hdr_mode(False)
        self.sdrplay3_rspdx.set_rf_notch_filter(False)
        self.sdrplay3_rspdx.set_dab_notch_filter(False)
        self.sdrplay3_rspdx.set_biasT(False)
        self.sdrplay3_rspdx.set_stream_tags(True)
        self.sdrplay3_rspdx.set_debug_mode(False)
        self.sdrplay3_rspdx.set_sample_sequence_gaps_check(False)
        self.sdrplay3_rspdx.set_show_gain_changes(False)

        self.msg_connect(
            (self.spectre_sweep_driver, "retune_command"),
            (self.sdrplay3_rspdx, "command"),
        )
        self.connect((self.sdrplay3_rspdx, 0), (self.spectre_batched_file_sink, 0))
        self.connect((self.sdrplay3_rspdx, 0), (self.spectre_sweep_driver, 0))
