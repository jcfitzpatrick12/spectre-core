# SPDX-FileCopyrightText: © 2024 Jimmy Fitzpatrick <jcfitzpatrick12@gmail.com>
# This file is part of SPECTRE
# SPDX-License-Identifier: GPL-3.0-or-later

from logging import getLogger
_LOGGER = getLogger(__name__)

from functools import wraps
import time
from typing import Callable, TypeVar, ParamSpec
import multiprocessing

from spectre_core.logs import configure_root_logger, log_call, ProcessType
from spectre_core.capture_configs import CaptureConfig
from spectre_core.receivers import get_receiver, ReceiverName
from spectre_core.post_processing import start_post_processor


def _make_daemon_process(
    name: str, 
    target: Callable[[], None]
) -> multiprocessing.Process:
    """
    Creates and returns a daemon `multiprocessing.Process` instance.

    :param name: The name to assign to the process.
    :param target: The function to execute in the process.
    :return: A `multiprocessing.Process` instance configured as a daemon.
    """
    return multiprocessing.Process(target=target,
                                   name=name,
                                   daemon=True)


class Worker:
    """A lightweight wrapper for a `multiprocessing.Process` daemon.
    
    Provides a very simple API to start, and restart a multiprocessing process.
    """
    def __init__(
        self,
        name: str,
        target: Callable[[], None]
    ) -> None:
        """Initialise a `Worker` instance.

        :param name: The name assigned to the process.
        :param target: The callable to be executed by the worker process.
        """
        self._name = name
        self._target = target
        self._process = _make_daemon_process(name, target)


    @property
    def name(
        self
    ) -> str:
        """Get the name of the worker process.

        :return: The name of the multiprocessing process.
        """
        return self._process.name
    
    
    @property
    def process(
        self
    ) -> multiprocessing.Process:
        """Access the underlying multiprocessing process.

        :return: The wrapped `multiprocessing.Process` instance.
        """
        return self._process

    
    def start(
        self
    ) -> None:
        """Start the worker process.

        This method runs the `target` in the background as a daemon.
        """
        self._process.start()


    def restart(
        self
    ) -> None:
        """Restart the worker process.

        Terminates the existing process if it is alive and then starts a new process
        after a brief pause. 
        """
        _LOGGER.info(f"Restarting {self.name} worker")
        if self._process.is_alive():
            # forcibly stop if it is still alive
            self._process.terminate()
            self._process.join()
        # a moment of respite
        time.sleep(1)
        # make a new process, as we can't start the same process again.
        self._process = _make_daemon_process(self._name, self._target)
        self.start()


P = ParamSpec("P")
T = TypeVar("T", bound=Callable[..., None])
def make_worker(
    name: str
) -> Callable[[Callable[P, None]], Callable[P, Worker]]:
    """
    Turns a function into a worker.

    This decorator wraps a function, allowing it to run in a separate process
    managed by a `Worker` object. Use it to easily create long-running or
    isolated tasks without directly handling multiprocessing.

    :param name: A human-readable name for the worker process.
    :return: A decorator that creates a `Worker` to run the function in its own process.
    """

    def decorator(
        func: Callable[P, None]
    ) -> Callable[P, Worker]:
        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> Worker:
            # Worker target funcs must have no arguments
            def target():
                configure_root_logger(ProcessType.WORKER)
                func(*args, **kwargs)
            return Worker(name, target)
        return wrapper
    return decorator


@make_worker("capture")
@log_call
def do_capture(
    tag: str,
) -> None:
    """Start capturing data from an SDR in real time.

    :param tag: The capture config tag.
    """
    _LOGGER.info((f"Reading capture config with tag '{tag}'"))

    # load the receiver and mode from the capture config file
    capture_config = CaptureConfig(tag)

    _LOGGER.info((f"Starting capture with the receiver '{capture_config.receiver_name}' "
                  f"operating in mode '{capture_config.receiver_mode}' "
                  f"with tag '{tag}'"))

    name = ReceiverName( capture_config.receiver_name )
    receiver = get_receiver(name,
                            capture_config.receiver_mode)
    receiver.start_capture(tag)


@make_worker("post_processing")
@log_call
def do_post_processing(
    tag: str,
) -> None:
    """Start post processing SDR data into spectrograms in real time.

    :param tag: The capture config tag.
    """
    _LOGGER.info(f"Starting post processor with tag '{tag}'")
    start_post_processor(tag)