# SPDX-FileCopyrightText: © 2024-2025 Jimmy Fitzpatrick <jcfitzpatrick12@gmail.com>
# This file is part of SPECTRE
# SPDX-License-Identifier: GPL-3.0-or-later

import time
import dataclasses

from gnuradio import spectre
from gnuradio import uhd

import spectre_core.fields

from ._base import Base, BaseModel


@dataclasses.dataclass(frozen=True)
class USRPWireFormat:
    """Indicates the form of the data over the bus/network."""

    SC8 = "sc8"
    SC12 = "sc12"
    SC16 = "sc16"


class USRPFixedCenterFrequencyModel(BaseModel):
    sample_rate: spectre_core.fields.Field.sample_rate = 600000
    batch_size: spectre_core.fields.Field.batch_size = 3
    center_frequency: spectre_core.fields.Field.center_frequency = 95.8e6
    bandwidth: spectre_core.fields.Field.bandwidth = 600000
    gain: spectre_core.fields.Field.gain = 35
    wire_format: spectre_core.fields.Field.wire_format = USRPWireFormat.SC12
    master_clock_rate: spectre_core.fields.Field.master_clock_rate = 60000000


class USRPFixedCenterFrequency(Base[USRPFixedCenterFrequencyModel]):
    def configure(self, tag: str, model: USRPFixedCenterFrequencyModel) -> None:
        master_clock_rate = f"master_clock_rate={model.master_clock_rate}"
        self.uhd_usrp_source = uhd.usrp_source(
            ",".join(("", "", master_clock_rate)),
            uhd.stream_args(
                cpu_format="fc32",
                otw_format=model.wire_format,
                args="",
                channels=[0],
            ),
        )
        self.uhd_usrp_source.set_samp_rate(model.sample_rate)
        self.uhd_usrp_source.set_time_now(uhd.time_spec(time.time()), uhd.ALL_MBOARDS)
        self.uhd_usrp_source.set_center_freq(model.center_frequency, 0)
        self.uhd_usrp_source.set_bandwidth(model.bandwidth, 0)
        self.uhd_usrp_source.set_rx_agc(False, 0)
        self.uhd_usrp_source.set_auto_dc_offset(False, 0)
        self.uhd_usrp_source.set_auto_iq_balance(False, 0)
        self.uhd_usrp_source.set_gain(model.gain, 0)
        self.spectre_batched_file_sink = spectre.batched_file_sink(
            self._batches_dir_path,
            tag,
            model.batch_size,
            model.sample_rate,
            False,
            "rx_freq",
            0,
        )
        self.connect((self.uhd_usrp_source, 0), (self.spectre_batched_file_sink, 0))


class USRPSweptCenterFrequencyModel(BaseModel):
    sample_rate: spectre_core.fields.Field.sample_rate = 2000000
    batch_size: spectre_core.fields.Field.batch_size = 3
    bandwidth: spectre_core.fields.Field.bandwidth = 2e6
    min_frequency: spectre_core.fields.Field.min_frequency = 95e6
    max_frequency: spectre_core.fields.Field.max_frequency = 101e6
    samples_per_step: spectre_core.fields.Field.samples_per_step = 60000
    frequency_step: spectre_core.fields.Field.frequency_step = 2e6
    gain: spectre_core.fields.Field.gain = 35
    wire_format: spectre_core.fields.Field.wire_format = USRPWireFormat.SC12
    master_clock_rate: spectre_core.fields.Field.master_clock_rate = 60000000


class USRPSweptCenterFrequency(Base[USRPSweptCenterFrequencyModel]):
    def configure(self, tag: str, model: USRPSweptCenterFrequencyModel) -> None:
        master_clock_rate = f"master_clock_rate={model.master_clock_rate}"
        self.uhd_usrp_source = uhd.usrp_source(
            ",".join(("", "", master_clock_rate)),
            uhd.stream_args(
                cpu_format="fc32",
                otw_format=model.wire_format,
                args="",
                channels=[0],
            ),
        )
        self.uhd_usrp_source.set_samp_rate(model.sample_rate)
        self.uhd_usrp_source.set_time_now(uhd.time_spec(time.time()), uhd.ALL_MBOARDS)
        self.uhd_usrp_source.set_center_freq(model.min_frequency, 0)
        self.uhd_usrp_source.set_bandwidth(model.bandwidth, 0)
        self.uhd_usrp_source.set_rx_agc(False, 0)
        self.uhd_usrp_source.set_auto_dc_offset(False, 0)
        self.uhd_usrp_source.set_auto_iq_balance(False, 0)
        self.uhd_usrp_source.set_gain(model.gain, 0)

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
            "rx_freq",
            model.min_frequency,
        )

        self.msg_connect(
            (self.spectre_sweep_driver, "retune_command"),
            (self.uhd_usrp_source, "command"),
        )
        self.connect((self.uhd_usrp_source, 0), (self.spectre_batched_file_sink, 0))
        self.connect((self.uhd_usrp_source, 0), (self.spectre_sweep_driver, 0))
