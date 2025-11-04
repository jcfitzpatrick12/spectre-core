# SPDX-FileCopyrightText: © 2024-2025 Jimmy Fitzpatrick <jcfitzpatrick12@gmail.com>
# This file is part of SPECTRE
# SPDX-License-Identifier: GPL-3.0-or-later

import sys
import signal
import typing
import pydantic

import spectre_core.config

import gnuradio.gr


class BaseFlowgraphModel(pydantic.BaseModel):
    max_noutput_items: int = pydantic.Field(
        100000,
        gt=0,
        description="The maximum number of items to be handled at each call of the work function.",
    )

    class Config:
        validate_assignment = True


class BaseFlowgraph(gnuradio.gr.top_block):
    def __init__(
        self,
        tag,
        batches_dir_path: typing.Optional[str] = None,
        **parameters,
    ):
        super().__init__()
        self.__max_noutput_items = typing.cast(int, parameters.pop("max_noutput_items"))
        self._batches_dir_path = (
            batches_dir_path or spectre_core.config.paths.get_batches_dir_path()
        )
        self.configure(tag, **parameters)

    def configure(self, tag: str, **parameters):
        """Configure the flowgraph for the block."""
        # TODO: Using the `@abc.abstractmethod` decorator causes static type checking to complain that subclasses are abstract, even
        # when they implement this method. I think inheriting from `gnuradio.gr.top_block` is throwing things off.
        raise NotImplementedError("Flowgraphs must implement the `configure` method.")

    def activate(self) -> None:

        def sig_handler(sig=None, frame=None):
            self.stop()
            self.wait()
            sys.exit(0)

        signal.signal(signal.SIGINT, sig_handler)
        signal.signal(signal.SIGTERM, sig_handler)

        self.run(self.__max_noutput_items)
