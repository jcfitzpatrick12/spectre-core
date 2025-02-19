# 
# USRP top blocks
#

from functools import partial
from dataclasses import dataclass
import time

from spectre_core.capture_configs import Parameters, PName
from spectre_core.config import get_batches_dir_path
from ._base import capture, spectre_top_block


class _fixed_center_frequency(spectre_top_block):
    def flowgraph(
        self,
        tag: str,
        parameters: Parameters
    ) -> None:
        # OOT moudle inline imports
        from gnuradio import spectre
        from gnuradio import uhd

        # Variables
        sample_rate      = parameters.get_parameter_value(PName.SAMPLE_RATE)
        normalised_gain  = parameters.get_parameter_value(PName.NORMALISED_GAIN)
        center_freq      = parameters.get_parameter_value(PName.CENTER_FREQUENCY)
        batch_size       = parameters.get_parameter_value(PName.BATCH_SIZE)
        bandwidth        = parameters.get_parameter_value(PName.BANDWIDTH) 

        # Blocks
        self.uhd_usrp_source_0 = uhd.usrp_source(
            ",".join(("", '')),
            uhd.stream_args(
                cpu_format="fc32",
                args='',
                channels=list(range(0,1)),
            ),
        )
        self.uhd_usrp_source_0.set_samp_rate(sample_rate)
        self.uhd_usrp_source_0.set_time_now(uhd.time_spec(time.time()), uhd.ALL_MBOARDS)

        self.uhd_usrp_source_0.set_center_freq(center_freq, 0)
        self.uhd_usrp_source_0.set_antenna("RX2", 0)
        self.uhd_usrp_source_0.set_bandwidth(bandwidth, 0)
        self.uhd_usrp_source_0.set_rx_agc(False, 0)
        self.uhd_usrp_source_0.set_normalized_gain(normalised_gain, 0)
        self.spectre_batched_file_sink_0 = spectre.batched_file_sink(get_batches_dir_path(), 
                                                                     tag, 
                                                                     batch_size, 
                                                                     sample_rate, False, 
                                                                     'freq', 
                                                                     0)


        # Connections
        self.connect((self.uhd_usrp_source_0, 0), (self.spectre_batched_file_sink_0, 0))


@dataclass(frozen=True)
class CaptureMethod:
    fixed_center_frequency = partial(capture, top_block_cls=_fixed_center_frequency)
