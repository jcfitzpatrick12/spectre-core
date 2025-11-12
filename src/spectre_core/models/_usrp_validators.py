# SPDX-FileCopyrightText: © 2024-2025 Jimmy Fitzpatrick <jcfitzpatrick12@gmail.com>
# This file is part of SPECTRE
# SPDX-License-Identifier: GPL-3.0-or-later

import spectre_core.flowgraphs

from ._validators import validate_one_of


def validate_wire_format(wire_format: str) -> None:
    validate_one_of(
        wire_format,
        [
            spectre_core.flowgraphs.USRPWireFormat.SC8,
            spectre_core.flowgraphs.USRPWireFormat.SC12,
            spectre_core.flowgraphs.USRPWireFormat.SC16,
        ],
        "wire_format",
    )
