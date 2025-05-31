# SPDX-FileCopyrightText: © 2024-2025 Jimmy Fitzpatrick <jcfitzpatrick12@gmail.com>
# This file is part of SPECTRE
# SPDX-License-Identifier: GPL-3.0-or-later

"""Download third-party spectrogram data."""

from ._callisto import download_callisto_data, CallistoInstrumentCode

__all__ = ["download_callisto_data", "CallistoInstrumentCode"]
