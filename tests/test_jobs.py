# SPDX-FileCopyrightText: © 2024-2025 Jimmy Fitzpatrick <jcfitzpatrick12@gmail.com>
# This file is part of SPECTRE
# SPDX-License-Identifier: GPL-3.0-or-later

import pytest
from time import sleep
from enum import Enum

from spectre_core.jobs import Worker, Job, make_worker, Duration


def _short_sleep() -> None:
    sleep(Duration.ONE_CENTISECOND)


def _sleep_forever() -> None:
    """Sleep indefinetely."""
    while True:
        _short_sleep()


def _fail_instantly() -> None:
    raise RuntimeError("Boom!")


def _make_successful_runtime_worker() -> Worker:
    return make_worker("successful_runtime_worker", _sleep_forever)


def _make_instantly_failing_runtime_worker() -> Worker:
    return make_worker("instantly_failing_runtime_worker", _fail_instantly)


@pytest.fixture
def successful_runtime_worker() -> Worker:
    """A worker which models successful runtime.

    The created `Worker` instance manages a process which sleeps indefinetely.
    """
    return _make_successful_runtime_worker()


@pytest.fixture
def instantly_failing_runtime_worker() -> Worker:
    """A worker which models runtime that fails instantly.

    The created `Worker` instance manages a process which instantly fails.
    """
    return _make_instantly_failing_runtime_worker()


@pytest.fixture
def successful_runtime_job() -> Job:
    """Create a job modelling successful runtime.

    Return a `Job` instance,  where each worker sleeps indefinitely.
    """
    _num_workers = 2  # arbitrarily choose two workers
    workers = [_make_successful_runtime_worker() for _ in range(_num_workers)]
    return Job(workers)


@pytest.fixture
def partially_failing_job() -> Job:
    """Create a job modelling partially failing runtime.

    Return a `Job` instance, where one worker sleeps indefinitely, and one fails instantly.
    """
    workers = [
        _make_instantly_failing_runtime_worker(),
        _make_successful_runtime_worker(),
    ]
    return Job(workers)


class TestWorker:
    def test_name(self, successful_runtime_worker: Worker) -> None:
        """Check that the name of the process is as expected."""
        assert successful_runtime_worker.name == "successful_runtime_worker"

    def test_is_alive(self, successful_runtime_worker: Worker) -> None:
        """Check that a process which is successfully running, evaluates as alive."""
        successful_runtime_worker.start()
        _short_sleep()
        assert successful_runtime_worker.is_alive() == True

        # Kill the process, since otherwise they would keep running until the parent process terminates.
        successful_runtime_worker.kill()

    def test_is_not_alive(self, instantly_failing_runtime_worker: Worker) -> None:
        """Check that a process which instantly failed, evaluates to not alive."""
        instantly_failing_runtime_worker.start()
        _short_sleep()
        assert instantly_failing_runtime_worker.is_alive() == False

    def test_kill(self, successful_runtime_worker: Worker) -> None:
        """Check that killing the process"""
        successful_runtime_worker.start()
        successful_runtime_worker.kill()
        _short_sleep()
        assert successful_runtime_worker.is_alive() == False

    def test_restart(self, successful_runtime_worker: Worker) -> None:
        successful_runtime_worker.restart()
        _short_sleep()
        assert successful_runtime_worker.is_alive() == True

        # Kill the process, since otherwise they would keep running until the parent process terminates.
        successful_runtime_worker.kill()


class TestJobs:

    def test_start(self, successful_runtime_job: Job):
        """Test that when a job starts, the workers are all alive."""
        successful_runtime_job.start()
        _short_sleep()
        assert successful_runtime_job.workers_are_alive == True

        # Kill the workers, since otherwise they would keep running until the parent process terminates.
        successful_runtime_job.kill()

    def test_kill(self, successful_runtime_job: Job):
        """Test that when a job is started, then killed, that the workers are not alive."""
        successful_runtime_job.start()
        successful_runtime_job.kill()
        _short_sleep()

        # Check all the workers are not alive.
        assert successful_runtime_job.workers_are_alive == False

    def test_monitor_successful_job(self, successful_runtime_job: Job):
        successful_runtime_job.start()
        successful_runtime_job.monitor(Duration.ONE_CENTISECOND)

        # Sleep for a moment, to give the job time to kill the workers once the total runtime has elapsed.
        _short_sleep()

        # Check all the workers are not alive.
        assert successful_runtime_job.workers_are_alive == False

    def test_monitor_failed_job(self, partially_failing_job: Job):
        partially_failing_job.start()
        with pytest.raises(RuntimeError):
            partially_failing_job.monitor(Duration.ONE_SECOND)

        # Check all the workers are not alive.
        assert partially_failing_job.workers_are_alive == False

    def test_max_restarts(self, partially_failing_job: Job):
        partially_failing_job.start()
        _max_restarts = 3
        with pytest.raises(
            RuntimeError,
            match=f"Maximum number of restarts has been reached: {_max_restarts}",
        ):
            partially_failing_job.monitor(
                Duration.TEN_SECONDS, force_restart=True, max_restarts=_max_restarts
            )

        # Check all the workers are not alive.
        assert partially_failing_job.workers_are_alive == False
