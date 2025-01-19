# SPDX-FileCopyrightText: © 2024 Jimmy Fitzpatrick <jcfitzpatrick12@gmail.com>
# This file is part of SPECTRE
# SPDX-License-Identifier: GPL-3.0-or-later


from ._batch_keys import BatchKey
from .._register import register_batch
from .._base import BaseBatch


@register_batch(BatchKey.NULL_BATCH)
class NullBatch(BaseBatch):
    """A placeholder batch, with no batch files."""