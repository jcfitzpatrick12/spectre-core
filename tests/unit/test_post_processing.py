# SPDX-FileCopyrightText: © 2024-2025 Jimmy Fitzpatrick <jcfitzpatrick12@gmail.com>
# This file is part of SPECTRE
# SPDX-License-Identifier: GPL-3.0-or-later

import numpy as np
import numpy.typing as npt
import pytest


def is_close(a, b, atol=1e-5, rtol=0):
    """Uniform closeness check for arrays."""
    return np.allclose(a, b, atol=atol, rtol=rtol)


from spectre_core.post_processing import (
    get_window,
    get_times,
    get_frequencies,
    get_num_spectrums,
    get_cosine_signal,
    get_buffer,
    get_fftw_obj,
    stfft,
    WindowType,
)


class TestSTFFT:
    def test_boxcar(self) -> None:
        """Check that the boxcar window produces expected results, consistent with SciPy."""
        window_size = 8
        expected_window = np.array([1, 1, 1, 1, 1, 1, 1, 1], dtype=np.float32)
        assert is_close(expected_window, get_window(WindowType.BOXCAR, window_size))

    def test_hann(self) -> None:
        """Check that the hann window produces expected results, consistent with SciPy."""
        window_size = 8
        expected_window = np.array(
            [
                0.0,
                0.14644660940672627,
                0.5,
                0.8535533905932737,
                1.0,
                0.8535533905932737,
                0.5,
                0.14644660940672627,
            ],
            dtype=np.float32,
        )
        assert is_close(expected_window, get_window(WindowType.HANN, window_size))

    def test_blackman(self) -> None:
        """Check that the blackman window produces expected results, consistent with SciPy."""
        window_size = 8
        expected_window = np.array(
            [
                0.0,
                0.06644660940672624,
                0.34,
                0.7735533905932738,
                1.0,
                0.7735533905932738,
                0.34,
                0.06644660940672624,
            ],
            dtype=np.float32,
        )
        assert is_close(expected_window, get_window(WindowType.BLACKMAN, window_size))

    def test_compute_times(self) -> None:
        """Check that we assign the correct times to each spectrum."""
        num_spectrums = 4
        sample_rate = 2
        window_hop = 4
        expected_times = np.array([0.0, 2.0, 4.0, 6.0], dtype=np.float32)
        assert is_close(
            get_times(num_spectrums, sample_rate, window_hop), expected_times
        )

    def test_compute_frequencies(self) -> None:
        """Check that we assign the correct frequencies to each spectral component."""
        window_size = 8
        sample_rate = 2
        expected_frequencies = [0.0, 0.25, 0.5, 0.75, -1.0, -0.75, -0.5, -0.25]
        assert is_close(get_frequencies(window_size, sample_rate), expected_frequencies)

    @pytest.mark.parametrize(
        ("signal_size", "window_size", "window_hop", "expected_num_spectrums"),
        [(16, 8, 8, 2), (16, 8, 4, 4), (16, 7, 2, 7)],
    )
    def test_num_spectrums(
        self,
        signal_size: int,
        window_size: int,
        window_hop: int,
        expected_num_spectrums: int,
    ) -> None:
        """Check that we compute the right number of spectrums for the stfft with given parameters."""
        assert expected_num_spectrums == get_num_spectrums(
            signal_size, window_size, window_hop
        )

    def test_stfft(self) -> None:
        """Verify STFFT output matches expected results for a simple cosine input signal."""
        # Define the cosine wave.
        num_samples = 32
        sample_rate = 8
        frequency = 1
        phase = 0
        amplitude = 1

        # Define the window.
        window_type = WindowType.BOXCAR
        window_size = 8
        window_hop = 8

        # Make the cosine signal, window and buffer.
        signal = get_cosine_signal(
            num_samples, sample_rate, frequency, amplitude, phase
        )
        window = get_window(window_type, window_size)
        buffer = get_buffer(window_size)

        # Plan, then compute the STFFT.
        fftw_obj = get_fftw_obj(buffer)
        dynamic_spectra = stfft(fftw_obj, buffer, signal, window, window_hop)

        print(dynamic_spectra)

        # TODO: Replace this "point-in-time" check, with something more robust and human readable.
        # I'll go through the derivation again, and check against a runtime-computed analytical
        # solution.
        expected_dynamic_spectra = np.array(
            [
                [9.9999994e-01, 0.0, 0.0, 0.0],
                [2.0000000e00, 4.0, 4.0, 4.0],
                [1.7320508e00, 0.0, 0.0, 0.0],
                [7.3914812e-08, 0.0, 0.0, 0.0],
                [9.9999994e-01, 0.0, 0.0, 0.0],
                [7.3914812e-08, 0.0, 0.0, 0.0],
                [1.7320508e00, 0.0, 0.0, 0.0],
                [2.0000000e00, 4.0, 4.0, 4.0],
            ],
            dtype=np.float32,
        )

        assert is_close(dynamic_spectra, expected_dynamic_spectra)
