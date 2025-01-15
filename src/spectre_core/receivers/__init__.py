# SPDX-FileCopyrightText: © 2024 Jimmy Fitzpatrick <jcfitzpatrick12@gmail.com>
# This file is part of SPECTRE
# SPDX-License-Identifier: GPL-3.0-or-later

# register decorators take effect on import.
# we do not expose them publically, and instead the classes and instances
# should be retrieved through the appropriate factory functions.
# from .plugins._test import Test
# from .plugins._rsp1a import RSP1A
# from .plugins._rspduo import RSPduo

# from ._base import BaseReceiver
# from ._factory import get_receiver
# from ._register import get_registered_receivers
# from ._spec_names import SpecName

# __all__ = [
#     "Test", "RSP1A", "RSPduo", "BaseReceiver", "get_receiver", 
#     "list_all_receiver_names", "SpecName"
# ]