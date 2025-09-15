"""
config submodule initializer.

Simplifies access to loader and creator functions.
"""

from .loader import load_machine
from .creator import create_machine

import warnings

def _custom_warning_format(message, category, filename, lineno, file=None, line=None):
    return f"\n⚠️ {category.__name__}: {message}\n"

warnings.formatwarning = _custom_warning_format
