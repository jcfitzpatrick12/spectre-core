# SPDX-FileCopyrightText: © 2024 Jimmy Fitzpatrick <jcfitzpatrick12@gmail.com>
# This file is part of SPECTRE
# SPDX-License-Identifier: GPL-3.0-or-later

from logging import getLogger
_LOGGER = getLogger(__name__)

import time

from ._workers import Worker

class Job:
    """Represents a collection of workers that run long-running tasks as 
    multiprocessing processes.

    A `Job` manages the lifecycle of its workers, including starting, 
    monitoring, and terminating them.
    """
    def __init__(
        self,
        workers: list[Worker]
    ) -> None:
        """Initialise a `Job` with a list of workers.

        :param workers: A list of `Worker` instances to manage as part of the job.
        """
        self._workers = workers


    def start(
        self,
    ) -> None:
        """Tell each worker to call their functions in the background as multiprocessing processes."""
        for worker in self._workers:
            worker.start()
            
            
    def terminate(
        self,
    ) -> None:
        """Tell each worker to terminate their processes, if the processes are still running."""
        _LOGGER.info("Terminating workers...")
        for worker in self._workers:
            if worker.process.is_alive():
                worker.process.terminate()
                worker.process.join()
        _LOGGER.info("All workers successfully terminated")
        
        
    def monitor(
        self,
        total_runtime: float, 
        force_restart: bool = False
    ) -> None:
        """
        Monitor the workers during execution and handle unexpected exits.

        Periodically checks worker processes within the specified runtime duration. 
        If a worker exits unexpectedly:
        - Restarts all workers if `force_restart` is True.
        - Terminates all workers and raises an exception if `force_restart` is False.

        :param total_runtime: Total time to monitor the workers, in seconds.
        :param force_restart: Whether to restart all workers if one exits unexpectedly.
        :raises RuntimeError: If a worker exits and `force_restart` is False.
        """
        _LOGGER.info("Monitoring workers...")
        start_time = time.time()

        try:
            while time.time() - start_time < total_runtime:
                for worker in self._workers:
                    if not worker.process.is_alive():
                        error_message = f"Worker with name `{worker.name}` unexpectedly exited."
                        _LOGGER.error(error_message)
                        if force_restart:
                            # Restart all workers
                            for worker in self._workers:
                                worker.restart()
                        else:
                            self.terminate()
                            raise RuntimeError(error_message)
                time.sleep(1)  # Poll every second

            _LOGGER.info("Session duration reached. Terminating workers...")
            self.terminate()

        except KeyboardInterrupt:
            _LOGGER.info("Keyboard interrupt detected. Terminating workers...")
            self.terminate()

    
def start_job(
    workers: list[Worker],
    total_runtime: float,
    force_restart: bool = False
) -> None:
    """Create and run a job with the specified workers.

    Starts the workers, monitors them for the specified runtime, and handles 
    unexpected exits according to the `force_restart` policy.

    :param workers: A list of `Worker` instances to include in the job.
    :param total_runtime: Total time to monitor the job, in seconds.
    :param force_restart: Whether to restart all workers if one exits unexpectedly.
    Defaults to False.
    """
    job = Job(workers)
    job.start()
    job.monitor(total_runtime, force_restart)

