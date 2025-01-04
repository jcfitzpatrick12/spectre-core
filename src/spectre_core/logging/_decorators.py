# SPDX-FileCopyrightText: © 2024 Jimmy Fitzpatrick <jcfitzpatrick12@gmail.com>
# This file is part of SPECTRE
# SPDX-License-Identifier: GPL-3.0-or-later

import logging
from typing import Callable
from functools import wraps

def log_call(func: Callable) -> Callable:
    """Decorator to log the execution of a function.

    Logs an informational message when the decorated function is called and logs 
    an error message if the function raises any exception.
    
    Arguments:
        The function to be decorated.

    Returns:
        The decorated function with added logging behaviour.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        logger = logging.getLogger(func.__module__)
        try:
            logger.info(f"Calling the function: {func.__name__}")
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error in function: {func.__name__}", exc_info=True)
            raise
    return wrapper