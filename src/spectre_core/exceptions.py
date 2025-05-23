# SPDX-FileCopyrightText: © 2024-2025 Jimmy Fitzpatrick <jcfitzpatrick12@gmail.com>
# This file is part of SPECTRE
# SPDX-License-Identifier: GPL-3.0-or-later

"""
`spectre` custom exceptions.
"""

class BatchNotFoundError(KeyError): ...
class ModeNotFoundError(KeyError): ...
class EventHandlerNotFoundError(KeyError): ...
class ReceiverNotFoundError(KeyError): ...
class InvalidTagError(ValueError): ...
class InvalidSweepMetadataError(ValueError): ...
