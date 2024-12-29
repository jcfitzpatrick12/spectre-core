# SPDX-FileCopyrightText: © 2024 Jimmy Fitzpatrick <jcfitzpatrick12@gmail.com>
# This file is part of SPECTRE
# SPDX-License-Identifier: GPL-3.0-or-later

import sys
import signal

from gnuradio import gr
from gnuradio import spectre

from spectre_core.capture_configs import Parameters, PNames
from spectre_core.config import get_chunks_dir_path

from spectre_core.capture_configs import Parameters


def capture(tag: str,
            parameters: Parameters, 
            top_block_cls: gr.top_block,
            max_noutput_items: int = 10000000):
    tb: gr.top_block = top_block_cls(tag,
                                     parameters)

    def sig_handler(sig=None, frame=None):
        tb.stop()
        tb.wait()
        sys.exit(0)

    signal.signal(signal.SIGINT, sig_handler)
    signal.signal(signal.SIGTERM, sig_handler)

    tb.start(max_noutput_items)
    tb.wait()