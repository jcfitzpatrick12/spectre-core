# SPDX-FileCopyrightText: © 2024 Jimmy Fitzpatrick <jcfitzpatrick12@gmail.com>
# This file is part of SPECTRE
# SPDX-License-Identifier: GPL-3.0-or-later

#  Global dictionaries to hold the mappings
batch_map = {}

# classes decorated with @register_batch([BATCH_KEY])
# will be added to batch_map
def register_batch(batch_key: str):
    def decorator(cls):
        batch_map[batch_key] = cls
        return cls
    return decorator

