# SPDX-FileCopyrightText: © 2024-2025 Jimmy Fitzpatrick <jcfitzpatrick12@gmail.com>
# This file is part of SPECTRE
# SPDX-License-Identifier: GPL-3.0-or-later

from logging import getLogger

_LOGGER = getLogger(__name__)

import time
from typing import Callable
import multiprocessing

from spectre_core.logs import configure_root_logger, ProcessType
from ._duration import Duration


def _make_daemon_process(
    name: str, target: Callable[[], None]
) -> multiprocessing.Process:
    """
    Creates and returns a daemon `multiprocessing.Process` instance.

    :param name: The name to assign to the process.
    :param target: The function to execute in the process.
    :return: A `multiprocessing.Process` instance configured as a daemon.
    """
    return multiprocessing.Process(target=target, name=name, daemon=True)


class Worker:
    """A lightweight wrapper for a `multiprocessing.Process` daemon.

    Provides a very simple API to start, and restart a multiprocessing process.
    """

    def __init__(self, name: str, target: Callable[[], None]) -> None:
        """Initialise a `Worker` instance.

        :param name: The name assigned to the process.
        :param target: The callable to be executed by the worker process.
        """
        self._name = name
        self._target = target
        self._process = _make_daemon_process(name, target)

    @property
    def name(self) -> str:
        """Get the name of the worker process.

        :return: The name of the multiprocessing process.
        """
        return self._process.name

    @property
    def is_alive(self) -> bool:
        """Return whether the managed process is alive."""
        return self._process.is_alive()

    def start(self) -> None:
        """Start the worker process.

        This method runs the `target` in the background as a daemon.
        """
        if self.is_alive:
            raise RuntimeError("A worker cannot be started twice.")

        self._process.start()

    def kill(self) -> None:
        """Kill the managed process."""
        if not self.is_alive:
            raise RuntimeError("Cannot kill a process which is not alive.")

        self._process.kill()

    def restart(self) -> None:
        """Restart the worker process.

        Kills the existing process if it is alive and then starts a new process
        after a brief pause.
        """
        _LOGGER.info(f"Restarting {self.name} worker")
        if self.is_alive:
            # forcibly stop if it is still alive
            self.kill()

        # a moment of respite
        time.sleep(0.5 * Duration.ONE_SECOND)

        # make a new process, as we can't start the same process again.
        self._process = _make_daemon_process(self._name, self._target)
        self.start()


# TODO: Somehow statically type check that `args` match the arguments to `target`
def make_worker(
    name: str,
    target: Callable[..., None],
    args: tuple = (),
    configure_logging: bool = True,
) -> Worker:
    """Create a `Worker` instance to manage a target function in a multiprocessing background daemon process.

    This function returns a `Worker` that is configured to run the given target function with the provided arguments
    in a separate process. The worker is not started automatically; you must call `start()` to call the target.  The target should not return anything,
    as its return value will be discarded.

    :param name: Human-readable name for the worker process.
    :param target: The function to be executed by the worker process.
    :param args: Arguments to pass to the target function.
    :param configure_root_logger: If True, configure the root logger to write log events to file. Defaults to True.
    :return: A `Worker` instance managing the background process (not started).
    """

    def _worker_target() -> None:
        if configure_logging:
            configure_root_logger(ProcessType.WORKER)
        _LOGGER.info(args)
        target(*args)

    return Worker(name, _worker_target)
