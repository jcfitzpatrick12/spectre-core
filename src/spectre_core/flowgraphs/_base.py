# SPDX-FileCopyrightText: © 2024-2025 Jimmy Fitzpatrick <jcfitzpatrick12@gmail.com>
# This file is part of SPECTRE
# SPDX-License-Identifier: GPL-3.0-or-later

import sys
import signal
import typing
import pydantic

import gnuradio.gr


import spectre_core.config
import spectre_core.fields


class BaseModel(pydantic.BaseModel):
    """Base model to be inherited by all flowgraph models."""

    model_config = pydantic.ConfigDict(validate_assignment=True)
    max_noutput_items: spectre_core.fields.Field.max_noutput_items = 100000


class Base(gnuradio.gr.top_block):
    def __init__(
        self,
        tag,
        parameters: dict[str, typing.Any],
        batches_dir_path: typing.Optional[str] = None,
    ):
        """An abstract interface for a configurable GNU Radio flowgaph.

        :param tag: The data tag.
        :param parameters: Configurable parameters.
        :param batches_dir_path: Optionally specify the directory to store data produced at runtime.
        """
        super().__init__()
        self.__max_noutput_items = typing.cast(int, parameters["max_noutput_items"])
        self._batches_dir_path = (
            batches_dir_path or spectre_core.config.paths.get_batches_dir_path()
        )
        self.configure(tag, parameters)

    def configure(self, tag: str, parameters: dict[str, typing.Any]):
        """Configure the flowgraph for the block."""
        # TODO: Using the `@abc.abstractmethod` decorator causes static type checking to complain that subclasses are abstract, even
        # when they implement this method. I think inheriting from `gnuradio.gr.top_block` is throwing things off.
        raise NotImplementedError("Flowgraphs must implement the `configure` method.")

    def activate(self) -> None:
        """Activate the GNU Radio flowgraph."""

        def sig_handler(sig=None, frame=None):
            self.stop()
            self.wait()
            sys.exit(0)

        signal.signal(signal.SIGINT, sig_handler)
        signal.signal(signal.SIGTERM, sig_handler)

        self.run(self.__max_noutput_items)
