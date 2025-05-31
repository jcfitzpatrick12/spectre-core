#
# USRP top blocks
#

from functools import partial
from dataclasses import dataclass
import time

from logging import getLogger

_LOGGER = getLogger(__name__)

from spectre_core.capture_configs import Parameters, PName
from spectre_core.config import get_batches_dir_path
from ._base import capture, spectre_top_block


class _fixed_center_frequency(spectre_top_block):
    def flowgraph(self, tag: str, parameters: Parameters) -> None:
        # OOT moudle inline imports
        from gnuradio import spectre
        from gnuradio import uhd

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
        self.uhd_usrp_source_0 = uhd.usrp_source(
            ",".join(("", "", master_clock_rate)),
            uhd.stream_args(
                cpu_format="fc32",
                otw_format=wire_format,
                args="",
                channels=[0],
            ),
        )
        self.uhd_usrp_source_0.set_samp_rate(sample_rate)
        self.uhd_usrp_source_0.set_time_now(uhd.time_spec(time.time()), uhd.ALL_MBOARDS)

        self.uhd_usrp_source_0.set_center_freq(center_freq, 0)
        self.uhd_usrp_source_0.set_antenna("RX2", 0)
        self.uhd_usrp_source_0.set_bandwidth(bandwidth, 0)
        self.uhd_usrp_source_0.set_rx_agc(False, 0)
        self.uhd_usrp_source_0.set_auto_dc_offset(False, 0)
        self.uhd_usrp_source_0.set_auto_iq_balance(False, 0)
        self.uhd_usrp_source_0.set_gain(gain, 0)
        self.spectre_batched_file_sink_0 = spectre.batched_file_sink(
            get_batches_dir_path(), tag, batch_size, sample_rate, False, "rx_freq", 0
        )

        # Connections
        self.connect((self.uhd_usrp_source_0, 0), (self.spectre_batched_file_sink_0, 0))


class _swept_center_frequency(spectre_top_block):
    def flowgraph(self, tag: str, parameters: Parameters) -> None:
        # OOT module inline imports
        from gnuradio import spectre
        from gnuradio import uhd

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

        # Blocks
        _LOGGER.warning(
            f"USRP frequency sweep modes will not work as expected until a known bug is fixed in the USRP source block. "
            f"Please refer to this GitHub issue for more information: https://github.com/gnuradio/gnuradio/issues/7725"
        )
        master_clock_rate = f"master_clock_rate={master_clock_rate}"
        self.uhd_usrp_source_0 = uhd.usrp_source(
            ",".join(("", "", master_clock_rate)),
            uhd.stream_args(
                cpu_format="fc32",
                otw_format=wire_format,
                args="",
                channels=[0],
            ),
        )
        self.uhd_usrp_source_0.set_samp_rate(sample_rate)
        self.uhd_usrp_source_0.set_time_now(uhd.time_spec(time.time()), uhd.ALL_MBOARDS)
        self.uhd_usrp_source_0.set_center_freq(min_frequency, 0)
        self.uhd_usrp_source_0.set_antenna("RX2", 0)
        self.uhd_usrp_source_0.set_bandwidth(bandwidth, 0)
        self.uhd_usrp_source_0.set_rx_agc(False, 0)
        self.uhd_usrp_source_0.set_auto_dc_offset(False, 0)
        self.uhd_usrp_source_0.set_auto_iq_balance(False, 0)
        self.uhd_usrp_source_0.set_gain(gain, 0)

        self.spectre_sweep_driver_0 = spectre.sweep_driver(
            min_frequency,
            max_frequency,
            frequency_step,
            sample_rate,
            samples_per_step,
            "freq",
        )

        self.spectre_batched_file_sink_0 = spectre.batched_file_sink(
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
            (self.spectre_sweep_driver_0, "retune_command"),
            (self.uhd_usrp_source_0, "command"),
        )
        self.connect((self.uhd_usrp_source_0, 0), (self.spectre_batched_file_sink_0, 0))
        self.connect((self.uhd_usrp_source_0, 0), (self.spectre_sweep_driver_0, 0))


@dataclass(frozen=True)
class CaptureMethod:
    fixed_center_frequency = partial(capture, top_block_cls=_fixed_center_frequency)
    swept_center_frequency = partial(
        capture, top_block_cls=_swept_center_frequency, max_noutput_items=1024
    )
