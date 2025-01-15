# SPDX-FileCopyrightText: © 2024 Jimmy Fitzpatrick <jcfitzpatrick12@gmail.com>
# This file is part of SPECTRE
# SPDX-License-Identifier: GPL-3.0-or-later

from enum import Enum

class ReceiverName(Enum):  
    """`spectre` supported receivers.
    
    :ivar RSP1A: SDRPlay RSP1A
    :ivar RSPDUO: SDRPlay RSPduo
    :ivar TEST: `spectre` test receiver.
    """
    RSP1A  = "rsp1a"
    RSPDUO = "rspduo"
    TEST   = "test"