# SPDX-FileCopyrightText: © 2024 Jimmy Fitzpatrick <jcfitzpatrick12@gmail.com>
# This file is part of SPECTRE
# SPDX-License-Identifier: GPL-3.0-or-later

import sys
import signal
from typing import Type
from abc import ABC, abstractmethod

from gnuradio import gr

from spectre_core.capture_configs import Parameters

class spectre_top_block(ABC, gr.top_block):
    """Thin wrapper around GNU Radio's `gr.top_block` class.
    
    Propagate through the input tag and parameters to the flowgraph definition,
    to make them easily configurable.
    """
    @abstractmethod
    def flowgraph(self,
                  tag: str,
                  parameters: Parameters):
        """Define the flowgraph for the block.
        
        This method uses inline imports to allow the `spectre_core.receivers` 
        module to work without requiring all Out-Of-Tree (OOT) modules to be installed. 
        Only import the necessary OOT modules when implementing this method.
        """
        
        
    def __init__(
        self,
        tag: str,
        parameters: Parameters
    ) -> None:
        """Create an instance of `spectre_top_block`.

        :param tag: The capture config tag.
        :param parameters: The capture config parameters
        """
        gr.top_block.__init__(self)
        self.flowgraph(tag, parameters)


def capture(
    tag: str,
    parameters: Parameters, 
    top_block_cls: Type[spectre_top_block],
    max_noutput_items: int = 10000000
) -> None:
    """Run a GNU Radio flowgraph with the given number of output items.
    
    Typically, this should be used with `partial` from `functools` to create
    a capture method:
    
    .. code-block:: python
        capture_method = partial(capture, top_block_cls=<your GNU Radio top block>)

    Top block classes 
    :param tag: _description_
    :param parameters: _description_
    :param top_block_cls: _description_
    :param max_noutput_items: _description_, defaults to 10000000
    """
    tb = top_block_cls(tag,
                       parameters)

    def sig_handler(sig=None, frame=None):
        tb.stop()
        tb.wait()
        sys.exit(0)

    signal.signal(signal.SIGINT, sig_handler)
    signal.signal(signal.SIGTERM, sig_handler)

    tb.run(max_noutput_items)