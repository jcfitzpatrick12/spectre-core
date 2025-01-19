# SPDX-FileCopyrightText: © 2024 Jimmy Fitzpatrick <jcfitzpatrick12@gmail.com>
# This file is part of SPECTRE
# SPDX-License-Identifier: GPL-3.0-or-later

from logging import getLogger
_LOGGER = getLogger(__name__)

from functools import wraps
import time
from typing import Callable, TypeVar
import multiprocessing

from spectre_core.logging import configure_root_logger, ProcessType


def make_daemon_process(
    name: str, 
    target_func: Callable[..., None]
) -> multiprocessing.Process:
    """
    Creates and returns a daemon `multiprocessing.Process` instance.

    :param name: The name to assign to the process.
    :param target_func: The function to execute in the process.
    :return: A `multiprocessing.Process` instance configured as a daemon.
    """
    return multiprocessing.Process(target=target_func,
                                   name=name,
                                   daemon=True)


class Worker:
    """A lightweight wrapper for a `multiprocessing.Process` daemon."""
    def __init__(
        self,
        name: str,
        target_func: Callable[..., None]
    ) -> None:
        """Initialise a `Worker` instance.

        :param name: The name assigned to the process.
        :param target_func: The callable to be executed by the worker process. This must be 
        a function with no arguments, that returns nothing.
        """
        self._name = name
        self._target_func = target_func
        self._process = make_daemon_process(name, target_func)


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
    
    def make_process(
        self
    ) -> None:
        return 
    
    def start(
        self
    ) -> None:
        """Start the worker process.

        This method runs the `target_func` in the background as a daemon.
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
        self._process = make_daemon_process(self._name, self._target_func)
        self.start()


def start_worker(
    name: str,
    target_func: Callable[[], None],
) -> Worker:
    """
    Create and start a worker process to execute the specified `target_func`.
    
    The `target_func` must not take any arguments. If arguments need to be passed 
    to `target_func`, use `functools.partial` to preconfigure the callable with 
    the required arguments. Or, alternatively use the `as_worker` decorator.

    :param name: The name assigned to the worker.
    :param target_func: A callable with no arguments that the worker will execute.
    :return: An instance of the `Worker` class managing the process.
    """
    _LOGGER.info(f"Starting {name} worker...")
    worker =  Worker(name,
                     target_func)
    worker.start()
    return worker
    

def terminate_workers(
    workers: list[Worker]
) -> None:
    """Terminate the processes of all provided workers.

    :param workers: A list of `Worker` instances whose processes should be terminated.
    """
    _LOGGER.info("Terminating workers...")
    for worker in workers:
        if worker.process.is_alive():
           worker.process.terminate()
           worker.process.join()
    _LOGGER.info("All workers successfully terminated")


def calculate_total_runtime(
    seconds: int = 0, 
    minutes: int = 0, 
    hours: int = 0
) -> float:
    """Calculate the total runtime in seconds.

    Combines hours, minutes, and seconds into a single total duration expressed in seconds.
    
    :param seconds: The seconds component of the runtime (default is 0).
    :param minutes: The minutes component of the runtime (default is 0).
    :param hours: The hours component of the runtime (default is 0).
    :raises ValueError: If the calculated total runtime is not strictly positive.
    :return: The total runtime in seconds as a float.
    """
    total_duration = seconds + (minutes * 60) + (hours * 3600) # [s]
    if total_duration <= 0:
        raise ValueError(f"Total duration must be strictly positive")
    return total_duration


def monitor_workers(
    workers: list[Worker], 
    total_runtime: float, 
    force_restart: bool = False
) -> None:
    """
    Monitor the provided worker processes during their runtime.

    Periodically checks if worker processes are alive within the specified runtime duration.
    If a worker unexpectedly exits, the behaviour depends on the `force_restart` flag:
    - If `force_restart` is True, all workers are restarted.
    - If `force_restart` is False, all workers are terminated, and an exception is raised.

    :param workers: A list of `Worker` instances to monitor.
    :param total_runtime: The total duration to monitor the workers, in seconds.
    :param force_restart: Whether to restart all workers if one unexpectedly exits.
    :raises RuntimeError: If a worker unexpectedly exits and `force_restart` is False.
    """
    _LOGGER.info("Monitoring workers...")
    start_time = time.time()

    try:
        while time.time() - start_time < total_runtime:
            for worker in workers:
                if not worker.process.is_alive():
                    error_message = f"Worker with name `{worker.name}` unexpectedly exited."
                    _LOGGER.error(error_message)
                    if force_restart:
                        # Restart all workers
                        for worker in workers:
                            worker.restart()
                    else:
                        terminate_workers(workers)
                        raise RuntimeError(error_message)
            time.sleep(1)  # Poll every second

        _LOGGER.info("Session duration reached. Terminating workers...")
        terminate_workers(workers)

    except KeyboardInterrupt:
        _LOGGER.info("Keyboard interrupt detected. Terminating workers...")
        terminate_workers(workers)


T = TypeVar("T", bound=Callable[..., None])
def as_worker(
    name: str
) -> Callable[[T], Callable[..., Worker]]:
    """
    A decorator to run a function in a Worker process.
    
    Implicitly configures the root logger for the process to write
    logs to file.

    :param name: The name of the worker process.
    :return: A decorator that transforms a function into one managed by a Worker.
    """
    def decorator(
        func: T
    ) -> Callable[..., Worker]:
        
        @wraps(func)
        def wrapper(*args, **kwargs) -> Worker:
            def target_func():
                configure_root_logger(ProcessType.WORKER) 
                func(*args, **kwargs)
            return start_worker(name, target_func)
        return wrapper
    
    return decorator