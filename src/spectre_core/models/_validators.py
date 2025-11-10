# SPDX-FileCopyrightText: © 2024-2025 Jimmy Fitzpatrick <jcfitzpatrick12@gmail.com>
# This file is part of SPECTRE
# SPDX-License-Identifier: GPL-3.0-or-later

# @pydantic.model_validator(mode="after")
# def validate(self):
#     validate_window_size(self.window_size)
#     if self.frequency_step < self.sample_rate:
#         raise NotImplementedError(
#             f"Spectre does not yet support spectral steps overlapping in frequency. "
#             f"Got frequency step {self.frequency_step * 1e-6} [MHz] which is less than the sample "
#             f"rate {self.sample_rate * 1e-6} [MHz]"
#         )
#     return self


# @pydantic.model_validator(mode="after")
# def validate(self):
#     validate_window_size(self.window_size)
#     return self


def validate_window_size(window_size: int):
    """Check that the window size is a power of two."""
    if window_size & (window_size - 1) != 0:
        raise ValueError("The window size must be a power of 2")
