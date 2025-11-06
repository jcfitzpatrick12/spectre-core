# SPDX-FileCopyrightText: © 2024-2025 Jimmy Fitzpatrick <jcfitzpatrick12@gmail.com>
# This file is part of SPECTRE
# SPDX-License-Identifier: GPL-3.0-or-later


"""Templatise configurable parameters."""

from ._signal_generator import CosineWaveModel, ConstantStaircaseModel

__all__ = ["CosineWaveModel", "ConstantStaircaseModel"]
